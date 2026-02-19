from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.history import TransferHistory

logger = logging.getLogger("databridge.audit")


async def log_action(
    db: AsyncSession,
    transfer_id: int,
    action: str,
    user_id: Optional[int] = None,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> TransferHistory:
    entry = TransferHistory(
        transfer_id=transfer_id,
        user_id=user_id,
        action=action,
        description=description,
        metadata_json=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_transfer_history(
    db: AsyncSession,
    transfer_id: int,
    limit: int = 100,
) -> list[TransferHistory]:
    query = (
        select(TransferHistory)
        .where(TransferHistory.transfer_id == transfer_id)
        .order_by(TransferHistory.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
