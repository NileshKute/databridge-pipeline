from __future__ import annotations

import math
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.database import get_db
from backend.app.models.transfer import TransferStatus
from backend.app.models.user import User, UserRole
from backend.app.schemas.transfer import (
    TransferCreate,
    TransferListResponse,
    TransferResponse,
    TransferStatsResponse,
    TransferUpdate,
    TransferFileResponse,
    ApprovalChainItem,
)
from backend.app.services import audit_service, transfer_service

router = APIRouter()


def _build_transfer_response(transfer) -> TransferResponse:
    files = [TransferFileResponse.model_validate(f) for f in transfer.files]
    approval_chain = [
        ApprovalChainItem(
            role=a.required_role,
            status=a.status,
            approver_name=a.approver.display_name if a.approver else None,
            comment=a.comment,
            decided_at=a.decided_at,
        )
        for a in transfer.approvals
    ]
    return TransferResponse(
        id=transfer.id,
        reference=transfer.reference,
        name=transfer.name,
        description=transfer.description,
        category=transfer.category,
        status=transfer.status,
        priority=transfer.priority,
        artist_id=transfer.artist_id,
        artist_name=transfer.artist.display_name if transfer.artist else "Unknown",
        total_files=transfer.total_files,
        total_size_bytes=transfer.total_size_bytes,
        staging_path=transfer.staging_path,
        production_path=transfer.production_path,
        shotgrid_project_id=transfer.shotgrid_project_id,
        shotgrid_entity_type=transfer.shotgrid_entity_type,
        shotgrid_entity_id=transfer.shotgrid_entity_id,
        shotgrid_entity_name=transfer.shotgrid_entity_name,
        shotgrid_task_id=transfer.shotgrid_task_id,
        shotgrid_version_id=transfer.shotgrid_version_id,
        scan_started_at=transfer.scan_started_at,
        scan_completed_at=transfer.scan_completed_at,
        scan_result=transfer.scan_result,
        scan_passed=transfer.scan_passed,
        transfer_started_at=transfer.transfer_started_at,
        transfer_completed_at=transfer.transfer_completed_at,
        transfer_verified=transfer.transfer_verified,
        transfer_method=transfer.transfer_method,
        notes=transfer.notes,
        rejection_reason=transfer.rejection_reason,
        tags=transfer.tags,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
        files=files,
        approval_chain=approval_chain,
        size_display=transfer.size_display,
    )


@router.get("/", response_model=TransferListResponse)
async def list_transfers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    transfer_status: Optional[TransferStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
):
    transfers, total = await transfer_service.list_transfers(
        db, status=transfer_status, page=page, per_page=per_page
    )
    return TransferListResponse(
        items=[_build_transfer_response(t) for t in transfers],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    payload: TransferCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.create_transfer(db, payload, current_user)

    await audit_service.log_action(
        db,
        transfer_id=transfer.id,
        user_id=current_user.id,
        action="transfer.created",
        description=f"Transfer {transfer.reference} created",
    )
    return _build_transfer_response(transfer)


@router.get("/stats", response_model=TransferStatsResponse)
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    return await transfer_service.get_transfer_stats(db)


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.get_transfer(db, transfer_id)
    if transfer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    return _build_transfer_response(transfer)


@router.patch("/{transfer_id}", response_model=TransferResponse)
async def update_transfer(
    transfer_id: int,
    payload: TransferUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.update_transfer(db, transfer_id, payload)
    if transfer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    return _build_transfer_response(transfer)


@router.post("/{transfer_id}/cancel")
async def cancel_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.cancel_transfer(db, transfer_id)
    if transfer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    await audit_service.log_action(
        db,
        transfer_id=transfer.id,
        user_id=current_user.id,
        action="transfer.cancelled",
        description=f"Transfer {transfer.reference} cancelled",
    )
    return {"message": "Transfer cancelled"}
