from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.history import TransferHistory
from backend.app.models.transfer import Transfer, TransferStatus
from backend.app.models.user import User

logger = logging.getLogger("databridge.transfer_ops_service")


class TransferOpsService:

    async def initiate_transfer(
        self,
        transfer_id: int,
        user: User,
        db: AsyncSession,
    ) -> Transfer:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        if user_role not in ("it_team", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only it_team or admin can initiate transfers",
            )

        if transfer.status != TransferStatus.READY_FOR_TRANSFER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transfer status is '{transfer.status.value}', expected 'ready_for_transfer'",
            )

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=user.id,
            action="transfer_initiated",
            description=f"File transfer initiated by {user.display_name}",
        ))

        await db.flush()
        await db.commit()
        await db.refresh(transfer)

        from backend.app.tasks.transfer import execute_transfer
        execute_transfer.delay(transfer_id)

        logger.info("Transfer %s initiated by %s", transfer.reference, user.username)
        return transfer

    async def complete_transfer(
        self,
        transfer_id: int,
        user: User,
        db: AsyncSession,
    ) -> Transfer:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        if user_role not in ("it_team", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only it_team or admin can complete transfers",
            )

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=user.id,
            action="verification_started",
            description=f"Transfer verification triggered by {user.display_name}",
        ))

        await db.flush()
        await db.commit()
        await db.refresh(transfer)

        from backend.app.tasks.transfer import verify_transfer
        verify_transfer.delay(transfer_id)

        logger.info("Verification dispatched for %s by %s", transfer.reference, user.username)
        return transfer


transfer_ops_service = TransferOpsService()
