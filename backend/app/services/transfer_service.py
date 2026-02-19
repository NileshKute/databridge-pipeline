from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.transfer import Transfer, TransferFile, TransferStatus
from backend.app.models.user import User
from backend.app.schemas.transfer import TransferCreate, TransferUpdate

logger = logging.getLogger("databridge.transfer_service")


def _generate_reference_id() -> str:
    return f"DB-{uuid.uuid4().hex[:8].upper()}"


def _scan_source_files(source_path: str) -> list[dict]:
    files: list[dict] = []
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")
    if src.is_file():
        files.append({"relative_path": src.name, "file_size_bytes": src.stat().st_size})
    else:
        for root, _dirs, filenames in os.walk(src):
            for fname in filenames:
                fpath = Path(root) / fname
                rel = str(fpath.relative_to(src))
                files.append({"relative_path": rel, "file_size_bytes": fpath.stat().st_size})
    return files


async def create_transfer(
    db: AsyncSession, data: TransferCreate, user: User
) -> Transfer:
    file_list = _scan_source_files(data.source_path)

    transfer = Transfer(
        reference_id=_generate_reference_id(),
        project_id=data.project_id,
        created_by=user.id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        source_path=data.source_path,
        destination_path=data.destination_path,
        total_size_bytes=sum(f["file_size_bytes"] for f in file_list),
        file_count=len(file_list),
        shotgrid_task_id=data.shotgrid_task_id,
        shotgrid_version_id=data.shotgrid_version_id,
        status=TransferStatus.PENDING,
    )
    db.add(transfer)
    await db.flush()

    for f in file_list:
        db.add(TransferFile(transfer_id=transfer.id, **f))
    await db.flush()

    logger.info("Transfer %s created by %s with %d files", transfer.reference_id, user.username, len(file_list))
    return transfer


async def get_transfer(db: AsyncSession, transfer_id: int) -> Transfer | None:
    result = await db.execute(select(Transfer).where(Transfer.id == transfer_id))
    return result.scalar_one_or_none()


async def get_transfer_by_ref(db: AsyncSession, reference_id: str) -> Transfer | None:
    result = await db.execute(select(Transfer).where(Transfer.reference_id == reference_id))
    return result.scalar_one_or_none()


async def list_transfers(
    db: AsyncSession,
    project_id: int | None = None,
    status: TransferStatus | None = None,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[Transfer], int]:
    query = select(Transfer).order_by(Transfer.created_at.desc())
    count_query = select(func.count()).select_from(Transfer)

    if project_id:
        query = query.where(Transfer.project_id == project_id)
        count_query = count_query.where(Transfer.project_id == project_id)
    if status:
        query = query.where(Transfer.status == status)
        count_query = count_query.where(Transfer.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
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
    if transfer.status in (TransferStatus.COMPLETED, TransferStatus.CANCELLED):
        return transfer
    transfer.status = TransferStatus.CANCELLED
    await db.flush()
    return transfer
