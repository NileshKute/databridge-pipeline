from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.integrations.ldap import LDAPUser, ldap_client
from backend.app.models.user import User, UserRole
from backend.app.schemas.user import TokenResponse, UserResponse

logger = logging.getLogger("databridge.auth_service")


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    # Local user (non-LDAP)
    if user and user.ldap_dn is None:
        if verify_password(password, user.ldap_groups or ""):
            return user
        return None

    # LDAP authentication
    ldap_user: LDAPUser | None = ldap_client.authenticate(username, password)
    if ldap_user is None:
        return None

    role = ldap_client.resolve_role(ldap_user.groups)

    if user is None:
        user = User(
            username=ldap_user.username,
            email=ldap_user.email,
            display_name=ldap_user.display_name,
            department=ldap_user.department,
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        logger.info("Auto-provisioned LDAP user: %s (role=%s)", username, role)
    else:
        user.email = ldap_user.email
        user.display_name = ldap_user.display_name
        user.department = ldap_user.department

    user.last_login = datetime.now(timezone.utc)
    await db.flush()
    return user


def generate_tokens(user: User) -> TokenResponse:
    extra_claims = {"role": user.role.value, "display_name": user.display_name}
    access_token = create_access_token(user.username, extra_claims=extra_claims)
    refresh_token = create_refresh_token(user.username)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse | None:
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            return None
        username = payload.get("sub")
    except Exception:
        return None

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None

    return generate_tokens(user)


async def create_local_user(
    db: AsyncSession,
    username: str,
    email: str,
    display_name: str,
    password: str,
    role: str = "artist",
    department: str | None = None,
) -> User:
    user = User(
        username=username,
        email=email,
        display_name=display_name,
        role=role,
        department=department,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user
