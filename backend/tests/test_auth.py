"""Tests for authentication endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, sample_user, db_session):
    """Valid fallback credentials return 200 + tokens."""
    user: User = await sample_user("artist", username="artist1")
    await db_session.commit()

    resp = await client.post("/api/v1/auth/login", json={
        "username": "artist1",
        "password": "artist123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "artist1"


@pytest.mark.asyncio
async def test_login_bad_password(client: AsyncClient, sample_user, db_session):
    """Wrong password returns 401."""
    await sample_user("artist", username="artist1")
    await db_session.commit()

    resp = await client.post("/api/v1/auth/login", json={
        "username": "artist1",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    """Nonexistent user returns 401."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "nobody",
        "password": "whatever",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, sample_user, auth_headers, db_session):
    """Valid token returns user profile."""
    user = await sample_user("team_lead")
    await db_session.commit()
    headers = auth_headers(user)

    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == user.username
    assert data["role"] == "team_lead"


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    """No auth header returns 403 (HTTPBearer)."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient):
    """Garbage token returns 401."""
    resp = await client.get("/api/v1/auth/me", headers={
        "Authorization": "Bearer totally.invalid.token",
    })
    assert resp.status_code == 401
