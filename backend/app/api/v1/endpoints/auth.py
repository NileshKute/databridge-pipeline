from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.dependencies import bearer_scheme, blacklist_token, get_current_user
from backend.app.core.security import decode_token
from backend.app.models.user import User
from backend.app.schemas.user import TokenResponse, UserLogin, UserResponse
from backend.app.services.auth_service import auth_service

router = APIRouter()


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
