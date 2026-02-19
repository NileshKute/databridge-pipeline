"""Tests for approval workflow endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_approve_team_lead(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """Team lead approves → status advances to pending_supervisor."""
    artist = await sample_user("artist", username="art_ap1")
    tl = await sample_user("team_lead", username="tl_ap1")
    transfer = await sample_transfer(artist, reference="TRF-AP01")
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/approvals/{transfer.id}/approve",
        json={"comment": "Looks great"},
        headers=auth_headers(tl),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending_supervisor"


@pytest.mark.asyncio
async def test_approve_wrong_role(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """Artist cannot approve a transfer → 403."""
    artist = await sample_user("artist", username="art_ap2")
    transfer = await sample_transfer(artist, reference="TRF-AP02")
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/approvals/{transfer.id}/approve",
        json={"comment": None},
        headers=auth_headers(artist),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reject_saves_reason(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """Team lead rejects → rejection reason is stored."""
    artist = await sample_user("artist", username="art_ap3")
    tl = await sample_user("team_lead", username="tl_ap3")
    transfer = await sample_transfer(artist, reference="TRF-AP03")
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/approvals/{transfer.id}/reject",
        json={"reason": "Missing frame range — please re-export"},
        headers=auth_headers(tl),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["rejection_reason"] is not None
    assert "frame range" in data["rejection_reason"].lower()


@pytest.mark.asyncio
async def test_reject_empty_reason(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """Rejecting without a reason (< 10 chars) returns 422."""
    artist = await sample_user("artist", username="art_ap4")
    tl = await sample_user("team_lead", username="tl_ap4")
    transfer = await sample_transfer(artist, reference="TRF-AP04")
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/approvals/{transfer.id}/reject",
        json={"reason": "no"},
        headers=auth_headers(tl),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_full_chain(client: AsyncClient, sample_user, auth_headers, sample_transfer, db_session):
    """TL → SV → LP approve in sequence → status becomes approved."""
    artist = await sample_user("artist", username="art_fc")
    tl = await sample_user("team_lead", username="tl_fc")
    sv = await sample_user("supervisor", username="sv_fc")
    lp = await sample_user("line_producer", username="lp_fc")
    transfer = await sample_transfer(artist, reference="TRF-FULL")
    await db_session.commit()

    # Team Lead approves
    resp = await client.post(
        f"/api/v1/approvals/{transfer.id}/approve",
        json={"comment": None},
        headers=auth_headers(tl),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending_supervisor"

    # Supervisor approves
    resp = await client.post(
        f"/api/v1/approvals/{transfer.id}/approve",
        json={"comment": "Good to go"},
        headers=auth_headers(sv),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending_line_producer"

    # Line Producer approves
    resp = await client.post(
        f"/api/v1/approvals/{transfer.id}/approve",
        json={"comment": None},
        headers=auth_headers(lp),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
