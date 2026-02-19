"""Tests for ShotGrid integration endpoints (uses mock client)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, sample_user, auth_headers, db_session):
    """ShotGrid projects endpoint returns data."""
    user = await sample_user("artist")
    await db_session.commit()

    resp = await client.get("/api/v1/shotgrid/projects", headers=auth_headers(user))
    assert resp.status_code == 200
    data = resp.json()
    assert "projects" in data
    assert isinstance(data["projects"], list)


@pytest.mark.asyncio
async def test_list_shots(client: AsyncClient, sample_user, auth_headers, db_session):
    """ShotGrid shots endpoint returns data for a project."""
    user = await sample_user("artist")
    await db_session.commit()

    resp = await client.get("/api/v1/shotgrid/projects/100/shots", headers=auth_headers(user))
    assert resp.status_code == 200
    data = resp.json()
    assert "shots" in data
    assert isinstance(data["shots"], list)


@pytest.mark.asyncio
async def test_link_entity(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """Linking a transfer to a ShotGrid entity updates the transfer."""
    artist = await sample_user("artist", username="art_sg1")
    transfer = await sample_transfer(artist, reference="TRF-SG01")
    await db_session.commit()

    resp = await client.post("/api/v1/shotgrid/link", json={
        "transfer_id": transfer.id,
        "entity_type": "Shot",
        "entity_id": 1001,
    }, headers=auth_headers(artist))
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity_type"] == "Shot"
    assert data["entity_id"] == 1001
