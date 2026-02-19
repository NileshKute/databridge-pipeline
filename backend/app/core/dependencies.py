from __future__ import annotations

import logging
from typing import Annotated, Callable, List

import jwt
import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import decode_token
from backend.app.models.user import User

logger = logging.getLogger("databridge.auth")
bearer_scheme = HTTPBearer()

_redis_client = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()
        except Exception:
            logger.warning("Redis unavailable — token blacklist disabled")
            _redis_client = None
    return _redis_client


def is_token_blacklisted(token: str) -> bool:
    r = _get_redis()
    if r is None:
        return False
    try:
        return r.exists(f"blacklist:{token}") > 0
    except Exception:
        return False


def blacklist_token(token: str, ttl_seconds: int) -> None:
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(f"blacklist:{token}", ttl_seconds, "1")
    except Exception:
        logger.warning("Failed to blacklist token in Redis")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = credentials.credentials

    if is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_role(*allowed_roles: str) -> Callable:
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        user_role = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker
