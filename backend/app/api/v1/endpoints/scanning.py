from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.v1.endpoints.transfers import _build_transfer_response
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.transfer import TransferResponse
from backend.app.services.scanning_service import scanning_service

router = APIRouter()


@router.post("/{transfer_id}/start", response_model=TransferResponse)
async def start_scan(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await scanning_service.start_scan(transfer_id, current_user, db)
    return _build_transfer_response(transfer)


@router.get("/{transfer_id}/status")
async def scan_status(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    return await scanning_service.get_scan_status(transfer_id, db)


@router.post("/{transfer_id}/complete", response_model=TransferResponse)
async def complete_scan(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await scanning_service.complete_scan(transfer_id, current_user, db)
    return _build_transfer_response(transfer)
