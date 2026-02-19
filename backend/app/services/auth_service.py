from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.app.integrations.ldap import (
    fallback_authenticator,
    ldap_authenticator,
)
from backend.app.models.user import User
from backend.app.schemas.user import TokenResponse, UserResponse

logger = logging.getLogger("databridge.auth_service")


class AuthService:
    def __init__(self) -> None:
        if settings.LDAP_ENABLED and ldap_authenticator is not None:
            self._authenticator = ldap_authenticator
            logger.info("AuthService using LDAP authenticator")
        else:
            self._authenticator = fallback_authenticator
            logger.info("AuthService using fallback authenticator (LDAP disabled)")

    async def login(self, username: str, password: str, db: AsyncSession) -> TokenResponse:
        auth_data = self._authenticator.authenticate(username, password)
        if auth_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        result = await db.execute(select(User).where(User.username == username))
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
                is_active=True,
            )
            db.add(user)
            await db.flush()
            logger.info("Created new user from auth: %s (role=%s)", username, auth_data["role"])
        else:
            user.display_name = auth_data["display_name"]
            user.email = auth_data["email"]
            user.role = auth_data["role"]
            user.department = auth_data.get("department")
            user.title = auth_data.get("title")
            user.ldap_dn = auth_data.get("ldap_dn")
            user.ldap_groups = auth_data.get("ldap_groups", "")

        if settings.SHOTGRID_ENABLED:
            try:
                from backend.app.integrations.shotgrid import shotgrid_client
                if shotgrid_client.connected and user.shotgrid_user_id is None:
                    sg = shotgrid_client._connect()
                    if sg:
                        sg_user = sg.find_one(
                            "HumanUser",
                            [["login", "is", username]],
                            ["id"],
                        )
                        if sg_user:
                            user.shotgrid_user_id = sg_user["id"]
                            logger.info("Linked ShotGrid user id=%d for %s", sg_user["id"], username)
            except Exception:
                logger.debug("ShotGrid user resolution skipped for %s", username)

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
