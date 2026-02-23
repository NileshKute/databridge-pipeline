from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.transfers import _build_transfer_response
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.transfer import TransferResponse
from app.services.transfer_ops_service import transfer_ops_service

router = APIRouter()


@router.post("/{transfer_id}/execute", response_model=TransferResponse)
async def execute_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_ops_service.initiate_transfer(transfer_id, current_user, db)
    return _build_transfer_response(transfer)


@router.post("/{transfer_id}/complete", response_model=TransferResponse)
async def complete_transfer(
    transfer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    transfer = await transfer_ops_service.complete_transfer(transfer_id, current_user, db)
    return _build_transfer_response(transfer)
