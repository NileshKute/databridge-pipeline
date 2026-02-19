from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.v1.endpoints.transfers import _build_transfer_response
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.approval import ApprovalAction, RejectAction
from backend.app.schemas.transfer import ApprovalChainItem, TransferResponse
from backend.app.services.approval_service import approval_service

router = APIRouter()


class OverrideRequest(BaseModel):
    target_status: str
    reason: str = Field(..., min_length=5)


# ── Pending items for current user ───────────────────────────────

@router.get("/pending", response_model=List[TransferResponse])
async def get_pending(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfers = await approval_service.get_pending(current_user, db)
    return [_build_transfer_response(t) for t in transfers]


@router.get("/pending/count")
async def get_pending_count(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    count = await approval_service.get_pending_count(current_user, db)
    return {"count": count}


# ── Approve ──────────────────────────────────────────────────────

@router.post("/{transfer_id}/approve", response_model=TransferResponse)
async def approve_transfer(
    transfer_id: int,
    payload: ApprovalAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await approval_service.approve(
        transfer_id, current_user, payload.comment, db,
    )
    return _build_transfer_response(transfer)


# ── Reject ───────────────────────────────────────────────────────

@router.post("/{transfer_id}/reject", response_model=TransferResponse)
async def reject_transfer(
    transfer_id: int,
    payload: RejectAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await approval_service.reject(
        transfer_id, current_user, payload.reason, db,
    )
    return _build_transfer_response(transfer)


# ── Approval chain ───────────────────────────────────────────────

@router.get("/{transfer_id}/chain", response_model=List[ApprovalChainItem])
async def get_approval_chain(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    return await approval_service.get_approval_chain(transfer_id, db)


# ── Admin override ───────────────────────────────────────────────

@router.post("/{transfer_id}/override", response_model=TransferResponse)
async def admin_override(
    transfer_id: int,
    payload: OverrideRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await approval_service.admin_override(
        transfer_id, payload.target_status, current_user, payload.reason, db,
    )
    return _build_transfer_response(transfer)
