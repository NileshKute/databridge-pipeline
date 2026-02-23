from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import bearer_scheme, blacklist_token, get_current_user
from app.core.security import decode_token
from app.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.get("/ldap-test")
async def test_ldap():
    """Test LDAP connectivity — only available in debug mode."""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    from ldap3 import ALL, Connection, Server
    result = {
        "ldap_server": settings.LDAP_SERVER,
        "ldap_bind_dn": settings.LDAP_BIND_DN,
        "ldap_base_dn": settings.LDAP_BASE_DN,
        "ldap_user_dn": settings.LDAP_USER_DN,
        "ldap_use_ssl": settings.LDAP_USE_SSL,
        "connection": "not tested",
        "bind": "not tested",
        "search": "not tested",
    }
    try:
        server = Server(settings.LDAP_SERVER, use_ssl=settings.LDAP_USE_SSL, get_info=ALL)
        result["connection"] = "success"
    except Exception as e:
        result["connection"] = f"FAILED: {str(e)}"
        return result
    try:
        conn = Connection(
            server,
            user=settings.LDAP_BIND_DN,
            password=settings.LDAP_BIND_PASSWORD,
            auto_bind=True,
        )
        result["bind"] = "success"
    except Exception as e:
        result["bind"] = f"FAILED: {str(e)}"
        return result
    try:
        conn.search(
            search_base=settings.LDAP_USER_DN or settings.LDAP_BASE_DN,
            search_filter="(objectClass=person)",
            attributes=["cn", "sAMAccountName", "mail", "department"],
            size_limit=3,
        )
        result["search"] = f"success — found {len(conn.entries)} users"
        result["sample_users"] = [str(e.entry_dn) for e in conn.entries[:3]]
    except Exception as e:
        result["search"] = f"FAILED: {str(e)}"
    try:
        conn.unbind()
    except Exception:
        pass
    return result


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.login(payload.username, payload.password, db)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.refresh(payload.refresh_token, db)


@router.post("/logout")
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
):
    token = credentials.credentials
    try:
        payload = decode_token(token)
        import time
        exp = payload.get("exp", 0)
        ttl = max(int(exp - time.time()), 1)
    except Exception:
        ttl = 3600

    blacklist_token(token, ttl)
    return {"message": "Logged out"}
