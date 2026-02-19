"""Tests for transfer CRUD endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_create_transfer(client: AsyncClient, sample_user, auth_headers, db_session):
    """Artist can create a transfer and receives a reference."""
    user = await sample_user("artist")
    await db_session.commit()
    headers = auth_headers(user)

    resp = await client.post("/api/v1/transfers/", json={
        "name": "My Test Package",
        "category": "vfx_assets",
        "priority": "normal",
    }, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["reference"].startswith("TRF-")
    assert data["name"] == "My Test Package"
    assert data["status"] == "pending_team_lead"
    assert data["artist_name"] == user.display_name


@pytest.mark.asyncio
async def test_list_own_transfers(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """Artist only sees their own transfers."""
    artist1 = await sample_user("artist", username="art_a")
    artist2 = await sample_user("artist", username="art_b")
    await sample_transfer(artist1, reference="TRF-A001", name="Artist1 Package")
    await sample_transfer(artist2, reference="TRF-B001", name="Artist2 Package")
    await db_session.commit()

    resp = await client.get("/api/v1/transfers/", headers=auth_headers(artist1))
    assert resp.status_code == 200
    data = resp.json()
    names = [t["name"] for t in data["items"]]
    assert "Artist1 Package" in names
    assert "Artist2 Package" not in names


@pytest.mark.asyncio
async def test_list_all_as_admin(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """Admin sees all transfers."""
    artist = await sample_user("artist", username="art_x")
    admin = await sample_user("admin", username="adm_x")
    await sample_transfer(artist, reference="TRF-X001", name="Some Package")
    await db_session.commit()

    resp = await client.get("/api/v1/transfers/", headers=auth_headers(admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_detail(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """Fetching transfer detail includes approval chain."""
    artist = await sample_user("artist")
    transfer = await sample_transfer(artist, reference="TRF-D001")
    await db_session.commit()

    resp = await client.get(f"/api/v1/transfers/{transfer.id}", headers=auth_headers(artist))
    assert resp.status_code == 200
    data = resp.json()
    assert data["reference"] == "TRF-D001"
    assert "approval_chain" in data
    assert len(data["approval_chain"]) == 5


@pytest.mark.asyncio
async def test_unauthorized_create(client: AsyncClient):
    """No token returns 403 on create."""
    resp = await client.post("/api/v1/transfers/", json={
        "name": "Should fail",
    })
    assert resp.status_code == 403
