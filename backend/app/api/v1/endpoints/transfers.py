from __future__ import annotations

import math
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.database import get_db
from backend.app.models.transfer import TransferStatus
from backend.app.models.user import User, UserRole
from backend.app.schemas.common import MessageResponse, PaginatedResponse
from backend.app.schemas.transfer import (
    TransferCreate,
    TransferListRead,
    TransferRead,
    TransferUpdate,
)
from backend.app.services import audit_service, transfer_service
from backend.app.tasks.transfer_tasks import execute_transfer_task

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_transfers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    project_id: Optional[int] = Query(None),
    transfer_status: Optional[TransferStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    transfers, total = await transfer_service.list_transfers(
        db, project_id=project_id, status=transfer_status, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[TransferListRead.model_validate(t) for t in transfers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    payload: TransferCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        transfer = await transfer_service.create_transfer(db, payload, current_user)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await audit_service.log_action(
        db,
        user_id=current_user.id,
        action="transfer.created",
        resource_type="transfer",
        resource_id=transfer.id,
        details={"reference_id": transfer.reference_id, "source": transfer.source_path},
    )
    return transfer


@router.get("/{transfer_id}", response_model=TransferRead)
async def get_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.get_transfer(db, transfer_id)
    if transfer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    return transfer


@router.patch("/{transfer_id}", response_model=TransferRead)
async def update_transfer(
    transfer_id: int,
    payload: TransferUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_service.update_transfer(db, transfer_id, payload)
    if transfer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    return transfer


@router.post("/{transfer_id}/approve", response_model=TransferRead)
async def approve_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_role(UserRole.LEAD, UserRole.SUPERVISOR, UserRole.PRODUCER, UserRole.ADMIN))
    ],
):
    transfer = await transfer_service.get_transfer(db, transfer_id)
    if transfer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    if transfer.status != TransferStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer is not in pending state")

    transfer.status = TransferStatus.APPROVED
    transfer.approved_by = current_user.id
    await db.flush()

    await audit_service.log_action(
        db,
        user_id=current_user.id,
        action="transfer.approved",
        resource_type="transfer",
        resource_id=transfer.id,
    )
    return transfer


@router.post("/{transfer_id}/start", response_model=TransferRead)
async def start_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_role(UserRole.LEAD, UserRole.SUPERVISOR, UserRole.PRODUCER, UserRole.ADMIN))
    ],
):
    transfer = await transfer_service.get_transfer(db, transfer_id)
    if transfer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    if transfer.status != TransferStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer must be approved before starting")

    task = execute_transfer_task.delay(transfer.id)
    transfer.celery_task_id = task.id
    transfer.status = TransferStatus.IN_PROGRESS
    await db.flush()

    await audit_service.log_action(
        db,
        user_id=current_user.id,
        action="transfer.started",
        resource_type="transfer",
        resource_id=transfer.id,
        details={"celery_task_id": task.id},
    )
    return transfer


@router.post("/{transfer_id}/cancel", response_model=MessageResponse)
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
        user_id=current_user.id,
        action="transfer.cancelled",
        resource_type="transfer",
        resource_id=transfer.id,
    )
    return MessageResponse(message="Transfer cancelled")
