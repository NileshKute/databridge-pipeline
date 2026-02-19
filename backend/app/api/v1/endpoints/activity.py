from __future__ import annotations

import math
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.history import TransferHistory
from backend.app.models.user import User

router = APIRouter()


class HistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transfer_id: int
    user_id: Optional[int] = None
    action: str
    description: Optional[str] = None
    metadata_json: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class HistoryListResponse(BaseModel):
    items: List[HistoryEntry]
    total: int
    page: int
    per_page: int
    pages: int


@router.get("/", response_model=HistoryListResponse)
async def list_activity(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    transfer_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    query = select(TransferHistory).order_by(TransferHistory.created_at.desc())
    count_q = select(func.count()).select_from(TransferHistory)

    if transfer_id is not None:
        query = query.where(TransferHistory.transfer_id == transfer_id)
        count_q = count_q.where(TransferHistory.transfer_id == transfer_id)

    if user_id is not None:
        query = query.where(TransferHistory.user_id == user_id)
        count_q = count_q.where(TransferHistory.user_id == user_id)

    if action:
        query = query.where(TransferHistory.action == action)
        count_q = count_q.where(TransferHistory.action == action)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)

    items = [HistoryEntry.model_validate(h) for h in result.scalars().all()]

    return HistoryListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )
