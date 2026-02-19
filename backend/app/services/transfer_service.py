from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.approval import Approval, ApprovalStatus
from backend.app.models.transfer import Transfer, TransferStatus
from backend.app.models.user import User, UserRole
from backend.app.schemas.transfer import TransferCreate, TransferUpdate

logger = logging.getLogger("databridge.transfer_service")

_counter_lock = None
APPROVAL_CHAIN = [
    UserRole.TEAM_LEAD,
    UserRole.SUPERVISOR,
    UserRole.LINE_PRODUCER,
]


async def _next_reference(db: AsyncSession) -> str:
    result = await db.execute(select(func.count()).select_from(Transfer))
    count = (result.scalar() or 0) + 1
    return f"TRF-{count:05d}"


async def create_transfer(
    db: AsyncSession, data: TransferCreate, user: User
) -> Transfer:
    reference = await _next_reference(db)

    transfer = Transfer(
        reference=reference,
        name=data.name,
        category=data.category,
        priority=data.priority,
        notes=data.notes,
        artist_id=user.id,
        shotgrid_project_id=data.shotgrid_project_id,
        shotgrid_entity_type=data.shotgrid_entity_type,
        shotgrid_entity_id=data.shotgrid_entity_id,
        status=TransferStatus.UPLOADED,
    )
    db.add(transfer)
    await db.flush()

    for role in APPROVAL_CHAIN:
        db.add(Approval(
            transfer_id=transfer.id,
            required_role=role,
            status=ApprovalStatus.PENDING,
        ))
    await db.flush()

    logger.info("Transfer %s created by %s", transfer.reference, user.username)
    return transfer


async def get_transfer(db: AsyncSession, transfer_id: int) -> Transfer | None:
    result = await db.execute(select(Transfer).where(Transfer.id == transfer_id))
    return result.scalar_one_or_none()


async def get_transfer_by_ref(db: AsyncSession, reference: str) -> Transfer | None:
    result = await db.execute(select(Transfer).where(Transfer.reference == reference))
    return result.scalar_one_or_none()


async def list_transfers(
    db: AsyncSession,
    status: TransferStatus | None = None,
    artist_id: int | None = None,
    page: int = 1,
    per_page: int = 25,
) -> tuple[list[Transfer], int]:
    query = select(Transfer).order_by(Transfer.created_at.desc())
    count_query = select(func.count()).select_from(Transfer)

    if status:
        query = query.where(Transfer.status == status)
        count_query = count_query.where(Transfer.status == status)
    if artist_id:
        query = query.where(Transfer.artist_id == artist_id)
        count_query = count_query.where(Transfer.artist_id == artist_id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def update_transfer(
    db: AsyncSession, transfer_id: int, data: TransferUpdate
) -> Transfer | None:
    transfer = await get_transfer(db, transfer_id)
    if transfer is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(transfer, field, value)
    await db.flush()
    return transfer


async def cancel_transfer(db: AsyncSession, transfer_id: int) -> Transfer | None:
    transfer = await get_transfer(db, transfer_id)
    if transfer is None:
        return None
    if transfer.status in (TransferStatus.TRANSFERRED, TransferStatus.CANCELLED):
        return transfer
    transfer.status = TransferStatus.CANCELLED
    await db.flush()
    return transfer


async def get_transfer_stats(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count()).select_from(Transfer))).scalar() or 0

    pending_statuses = [
        TransferStatus.UPLOADED,
        TransferStatus.PENDING_TEAM_LEAD,
        TransferStatus.PENDING_SUPERVISOR,
        TransferStatus.PENDING_LINE_PRODUCER,
    ]
    pending = (await db.execute(
        select(func.count()).select_from(Transfer).where(Transfer.status.in_(pending_statuses))
    )).scalar() or 0

    approved = (await db.execute(
        select(func.count()).select_from(Transfer).where(Transfer.status == TransferStatus.APPROVED)
    )).scalar() or 0

    scanning_statuses = [TransferStatus.SCANNING, TransferStatus.SCAN_PASSED, TransferStatus.SCAN_FAILED]
    scanning = (await db.execute(
        select(func.count()).select_from(Transfer).where(Transfer.status.in_(scanning_statuses))
    )).scalar() or 0

    transferred = (await db.execute(
        select(func.count()).select_from(Transfer).where(Transfer.status == TransferStatus.TRANSFERRED)
    )).scalar() or 0

    rejected = (await db.execute(
        select(func.count()).select_from(Transfer).where(Transfer.status == TransferStatus.REJECTED)
    )).scalar() or 0

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "scanning": scanning,
        "transferred": transferred,
        "rejected": rejected,
        "avg_time_hours": None,
    }
