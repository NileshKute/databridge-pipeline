from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.integrations.ldap import (
    fallback_authenticator,
    ldap_authenticator,
)
from app.models.user import User
from app.schemas.user import TokenResponse, UserResponse

logger = logging.getLogger("databridge.auth_service")


class AuthService:
    def __init__(self) -> None:
        if settings.LDAP_ENABLED and ldap_authenticator is not None:
            self._authenticator = ldap_authenticator
            logger.info("AuthService using LDAP authenticator")
        else:
            self._authenticator = fallback_authenticator
            logger.info("AuthService using fallback authenticator (LDAP disabled)")

    def _map_department_to_role(self, department: str) -> str:
        """Map ShotGrid department name to app role."""
        if not department:
            return settings.SHOTGRID_DEFAULT_ROLE
        dept_map = settings.SHOTGRID_DEPARTMENT_ROLE_MAP
        dept_lower = department.strip().lower()
        for dept_name, role in dept_map.items():
            if dept_name.lower() == dept_lower:
                return role
        for dept_name, role in dept_map.items():
            if dept_name.lower() in dept_lower or dept_lower in dept_name.lower():
                return role
        return settings.SHOTGRID_DEFAULT_ROLE

    async def login(self, username: str, password: str, db: AsyncSession) -> TokenResponse:
        # --- Superadmin bypass (always works, ignores LDAP) ---
        if username == settings.SUPERADMIN_USERNAME and password == settings.SUPERADMIN_PASSWORD:
            auth_data = {
                "username": settings.SUPERADMIN_USERNAME,
                "display_name": "Super Admin",
                "email": settings.SUPERADMIN_EMAIL,
                "department": "Administration",
                "title": "System Administrator",
                "role": "admin",
                "ldap_dn": "",
                "ldap_groups": "",
                "shotgrid_user_id": None,
            }
        else:
            # Step 1: Authenticate via LDAP (verify credentials only)
            ldap_info = self._authenticator.authenticate(username, password)
            if ldap_info is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )

            # Step 2: Get role from ShotGrid Department
            role = settings.SHOTGRID_DEFAULT_ROLE
            sg_department = ""
            sg_user_id = None

            if settings.SHOTGRID_ENABLED:
                try:
                    from app.integrations.shotgrid import shotgrid_client
                    if shotgrid_client and getattr(shotgrid_client, "enabled", True):
                        sg_user = shotgrid_client.get_user_by_login(username)
                        if not sg_user:
                            sg_user = shotgrid_client.get_user_by_email(ldap_info.get("email") or "")
                        if sg_user:
                            sg_user_id = sg_user.get("id")
                            sg_department_raw = sg_user.get("department")
                            if isinstance(sg_department_raw, dict):
                                sg_department = sg_department_raw.get("name", "")
                            elif isinstance(sg_department_raw, list) and len(sg_department_raw) > 0:
                                first = sg_department_raw[0]
                                sg_department = first.get("name", "") if isinstance(first, dict) else str(first)
                            else:
                                sg_department = str(sg_department_raw or "")
                            role = self._map_department_to_role(sg_department)
                except Exception as e:
                    logger.warning("ShotGrid lookup failed for %s, using default role: %s", username, e)

            auth_data = {
                "username": username,
                "display_name": ldap_info.get("display_name", username),
                "email": ldap_info.get("email", ""),
                "department": sg_department or ldap_info.get("department", ""),
                "title": ldap_info.get("title", ""),
                "role": role,
                "ldap_dn": ldap_info.get("ldap_dn", ""),
                "ldap_groups": ldap_info.get("ldap_groups", ""),
                "shotgrid_user_id": sg_user_id,
            }

        result = await db.execute(select(User).where(User.username == auth_data["username"]))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                username=auth_data["username"],
                display_name=auth_data["display_name"],
                email=auth_data["email"],
                role=auth_data["role"],
                department=auth_data.get("department"),
                title=auth_data.get("title"),
                ldap_dn=auth_data.get("ldap_dn"),
                ldap_groups=auth_data.get("ldap_groups", ""),
                shotgrid_user_id=auth_data.get("shotgrid_user_id"),
                is_active=True,
            )
            db.add(user)
            await db.flush()
            logger.info("Created new user from auth: %s (role=%s)", auth_data["username"], auth_data["role"])
        else:
            user.display_name = auth_data["display_name"]
            user.email = auth_data["email"]
            user.role = auth_data["role"]
            user.department = auth_data.get("department")
            user.title = auth_data.get("title")
            user.ldap_dn = auth_data.get("ldap_dn")
            user.ldap_groups = auth_data.get("ldap_groups", "")
            if auth_data.get("shotgrid_user_id") is not None:
                user.shotgrid_user_id = auth_data["shotgrid_user_id"]

        user.last_login = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()

        access_token = create_access_token(
            subject=user.username,
            extra_claims={
                "role": user.role.value if hasattr(user.role, "value") else user.role,
                "user_id": user.id,
            },
        )
        refresh_token = create_refresh_token(subject=user.username)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def get_current_user_from_token(self, token: str, db: AsyncSession) -> User:
        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return user

    async def refresh(self, refresh_token: str, db: AsyncSession) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        username = payload.get("sub")
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        access_token = create_access_token(
            subject=user.username,
            extra_claims={
                "role": user.role.value if hasattr(user.role, "value") else user.role,
                "user_id": user.id,
            },
        )
        new_refresh_token = create_refresh_token(subject=user.username)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user=UserResponse.model_validate(user),
        )


auth_service = AuthService()
