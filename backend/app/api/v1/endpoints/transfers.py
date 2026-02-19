from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.transfer import TransferCategory, TransferStatus
from backend.app.models.user import User
from backend.app.schemas.transfer import (
    ApprovalChainItem,
    TransferCreate,
    TransferFileResponse,
    TransferListResponse,
    TransferResponse,
    TransferStatsResponse,
    TransferUpdate,
)
from backend.app.services.file_service import file_service
from backend.app.services.transfer_service import transfer_service

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


# ── Create ───────────────────────────────────────────────────────

@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    payload: TransferCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.create_transfer(payload, current_user, db)
    return _build_transfer_response(transfer)


# ── List ─────────────────────────────────────────────────────────

@router.get("/", response_model=TransferListResponse)
async def list_transfers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    transfer_status: Optional[TransferStatus] = Query(None, alias="status"),
    category: Optional[TransferCategory] = Query(None),
    search: Optional[str] = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    transfers, total = await transfer_service.list_transfers(
        db,
        user=current_user,
        transfer_status=transfer_status,
        category=category,
        search=search,
        page=page,
        per_page=per_page,
    )
    import math
    return TransferListResponse(
        items=[_build_transfer_response(t) for t in transfers],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


# ── Stats ────────────────────────────────────────────────────────

@router.get("/stats", response_model=TransferStatsResponse)
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await transfer_service.get_stats(db, current_user)


# ── Detail ───────────────────────────────────────────────────────

@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.get_transfer(transfer_id, db, current_user)
    return _build_transfer_response(transfer)


# ── Update ───────────────────────────────────────────────────────

@router.put("/{transfer_id}", response_model=TransferResponse)
async def update_transfer(
    transfer_id: int,
    payload: TransferUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.update_transfer(
        transfer_id, payload, current_user, db,
    )
    return _build_transfer_response(transfer)


# ── Cancel / Delete ──────────────────────────────────────────────

@router.delete("/{transfer_id}")
async def cancel_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await transfer_service.cancel_transfer(transfer_id, current_user, db)
    return {"message": "Transfer cancelled"}


# ── File Upload ──────────────────────────────────────────────────

@router.post(
    "/{transfer_id}/upload",
    response_model=List[TransferFileResponse],
)
async def upload_files(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    files: List[UploadFile] = File(...),
):
    from sqlalchemy import select as sa_select
    from backend.app.models.transfer import Transfer as TransferModel
    result = await db.execute(
        sa_select(TransferModel).where(TransferModel.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    if transfer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    user_role = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if transfer.artist_id != current_user.id and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the transfer owner can upload files",
        )

    records = await file_service.upload_files_batch(transfer_id, files, db)
    return [TransferFileResponse.model_validate(r) for r in records]


# ── List Files ───────────────────────────────────────────────────

@router.get(
    "/{transfer_id}/files",
    response_model=List[TransferFileResponse],
)
async def list_files(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.get_transfer(transfer_id, db, current_user)
    return [TransferFileResponse.model_validate(f) for f in transfer.files]


# ── Delete File ──────────────────────────────────────────────────

@router.delete("/{transfer_id}/files/{file_id}")
async def delete_file(
    transfer_id: int,
    file_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await file_service.delete_file(file_id, current_user, db)
    return {"message": "File deleted"}
