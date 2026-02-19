from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.models.approval import Approval, ApprovalStatus
from backend.app.models.history import TransferHistory
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.transfer import (
    Transfer,
    TransferCategory,
    TransferStatus,
)
from backend.app.models.user import User, UserRole
from backend.app.schemas.transfer import (
    TransferCreate,
    TransferStatsResponse,
    TransferUpdate,
)

logger = logging.getLogger("databridge.transfer_service")

APPROVAL_CHAIN = [
    UserRole.TEAM_LEAD,
    UserRole.SUPERVISOR,
    UserRole.LINE_PRODUCER,
]

_ROLE_VISIBLE_STATUSES = {
    UserRole.DATA_TEAM: {
        TransferStatus.APPROVED,
        TransferStatus.SCANNING,
        TransferStatus.SCAN_PASSED,
        TransferStatus.SCAN_FAILED,
        TransferStatus.COPYING,
        TransferStatus.READY_FOR_TRANSFER,
    },
    UserRole.IT_TEAM: {
        TransferStatus.READY_FOR_TRANSFER,
        TransferStatus.TRANSFERRING,
        TransferStatus.VERIFYING,
        TransferStatus.TRANSFERRED,
    },
}


class TransferService:

    async def _generate_reference(self, db: AsyncSession) -> str:
        result = await db.execute(
            select(Transfer.reference)
            .order_by(Transfer.id.desc())
            .limit(1)
        )
        last_ref = result.scalar_one_or_none()
        if last_ref and last_ref.startswith("TRF-"):
            try:
                num = int(last_ref.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1
        return f"TRF-{num:05d}"

    async def create_transfer(
        self,
        data: TransferCreate,
        user: User,
        db: AsyncSession,
    ) -> Transfer:
        reference = await self._generate_reference(db)

        staging_dir = Path(settings.STAGING_NETWORK_PATH) / reference
        staging_dir.mkdir(parents=True, exist_ok=True)

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
            staging_path=str(staging_dir),
        )
        db.add(transfer)
        await db.flush()

        for role in APPROVAL_CHAIN:
            db.add(Approval(
                transfer_id=transfer.id,
                required_role=role,
                status=ApprovalStatus.PENDING,
            ))

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=user.id,
            action="uploaded",
            description=f"Transfer '{transfer.name}' created by {user.display_name}",
        ))

        transfer.status = TransferStatus.PENDING_TEAM_LEAD
        await db.flush()

        tl_result = await db.execute(
            select(User).where(
                User.role == UserRole.TEAM_LEAD,
                User.is_active.is_(True),
            )
        )
        for tl in tl_result.scalars().all():
            db.add(Notification(
                user_id=tl.id,
                transfer_id=transfer.id,
                type=NotificationType.APPROVAL_REQUIRED,
                title=f"Approval needed: {reference}",
                message=f"Transfer '{transfer.name}' from {user.display_name} needs team lead approval.",
            ))

        await db.flush()
        await db.commit()

        result = await db.execute(
            select(Transfer)
            .options(
                selectinload(Transfer.artist),
                selectinload(Transfer.files),
                selectinload(Transfer.approvals).selectinload(Approval.approver),
            )
            .where(Transfer.id == transfer.id)
        )
        transfer = result.scalar_one()

        logger.info("Transfer %s created by %s", reference, user.username)
        return transfer

    def _build_visibility_filter(self, user: User):
        role = user.role
        if role == UserRole.ADMIN:
            return None
        if role == UserRole.ARTIST:
            return Transfer.artist_id == user.id
        if role == UserRole.TEAM_LEAD:
            return or_(
                Transfer.status == TransferStatus.PENDING_TEAM_LEAD,
                Transfer.artist_id == user.id,
            )
        if role == UserRole.SUPERVISOR:
            return or_(
                Transfer.status == TransferStatus.PENDING_SUPERVISOR,
                Transfer.status != TransferStatus.UPLOADED,
            )
        if role == UserRole.LINE_PRODUCER:
            return or_(
                Transfer.status == TransferStatus.PENDING_LINE_PRODUCER,
                Transfer.status != TransferStatus.UPLOADED,
            )
        visible = _ROLE_VISIBLE_STATUSES.get(role)
        if visible:
            return Transfer.status.in_(visible)
        return Transfer.artist_id == user.id

    async def list_transfers(
        self,
        db: AsyncSession,
        user: User,
        transfer_status: Optional[TransferStatus] = None,
        category: Optional[TransferCategory] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Transfer], int]:
        query = (
            select(Transfer)
            .options(
                selectinload(Transfer.artist),
                selectinload(Transfer.files),
                selectinload(Transfer.approvals).selectinload(Approval.approver),
            )
            .order_by(Transfer.created_at.desc())
        )
        count_q = select(func.count()).select_from(Transfer)

        vis = self._build_visibility_filter(user)
        if vis is not None:
            query = query.where(vis)
            count_q = count_q.where(vis)

        if transfer_status:
            query = query.where(Transfer.status == transfer_status)
            count_q = count_q.where(Transfer.status == transfer_status)

        if category:
            query = query.where(Transfer.category == category)
            count_q = count_q.where(Transfer.category == category)

        if search:
            pattern = f"%{search}%"
            search_filter = or_(
                Transfer.name.ilike(pattern),
                Transfer.reference.ilike(pattern),
            )
            query = query.where(search_filter)
            count_q = count_q.where(search_filter)

        total = (await db.execute(count_q)).scalar() or 0
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        transfers = list(result.scalars().all())

        return transfers, total

    async def get_transfer(
        self,
        transfer_id: int,
        db: AsyncSession,
        user: User,
    ) -> Transfer:
        result = await db.execute(
            select(Transfer)
            .options(
                selectinload(Transfer.artist),
                selectinload(Transfer.files),
                selectinload(Transfer.approvals).selectinload(Approval.approver),
            )
            .where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found",
            )

        vis = self._build_visibility_filter(user)
        if vis is not None:
            check = await db.execute(
                select(Transfer.id).where(Transfer.id == transfer_id, vis)
            )
            if check.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this transfer",
                )
        return transfer

    async def update_transfer(
        self,
        transfer_id: int,
        data: TransferUpdate,
        user: User,
        db: AsyncSession,
    ) -> Transfer:
        transfer = await self.get_transfer(transfer_id, db, user)

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        if transfer.artist_id != user.id and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the transfer owner or admin can update",
            )

        if transfer.status not in {
            TransferStatus.UPLOADED,
            TransferStatus.PENDING_TEAM_LEAD,
            TransferStatus.REJECTED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer cannot be modified at this stage",
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(transfer, field, value)

        await db.flush()
        await db.commit()
        await db.refresh(transfer)
        return transfer

    async def get_stats(
        self,
        db: AsyncSession,
        user: User,
    ) -> TransferStatsResponse:
        base = select(func.count()).select_from(Transfer)
        vis = self._build_visibility_filter(user)
        if vis is not None:
            base = base.where(vis)

        total = (await db.execute(base)).scalar() or 0

        pending_statuses = [
            TransferStatus.UPLOADED,
            TransferStatus.PENDING_TEAM_LEAD,
            TransferStatus.PENDING_SUPERVISOR,
            TransferStatus.PENDING_LINE_PRODUCER,
        ]
        q_pending = base.where(Transfer.status.in_(pending_statuses))
        pending = (await db.execute(q_pending)).scalar() or 0

        approved = (await db.execute(
            base.where(Transfer.status == TransferStatus.APPROVED)
        )).scalar() or 0

        scanning_statuses = [
            TransferStatus.SCANNING,
            TransferStatus.SCAN_PASSED,
            TransferStatus.SCAN_FAILED,
        ]
        scanning = (await db.execute(
            base.where(Transfer.status.in_(scanning_statuses))
        )).scalar() or 0

        transferred = (await db.execute(
            base.where(Transfer.status == TransferStatus.TRANSFERRED)
        )).scalar() or 0

        rejected = (await db.execute(
            base.where(Transfer.status == TransferStatus.REJECTED)
        )).scalar() or 0

        avg_time_hours: Optional[float] = None
        try:
            avg_q = select(
                func.avg(
                    extract(
                        "epoch",
                        Transfer.transfer_completed_at - Transfer.created_at,
                    )
                )
            ).where(
                Transfer.transfer_completed_at.isnot(None),
            )
            if vis is not None:
                avg_q = avg_q.where(vis)
            avg_sec = (await db.execute(avg_q)).scalar()
            if avg_sec is not None:
                avg_time_hours = round(float(avg_sec) / 3600.0, 2)
        except Exception:
            pass

        return TransferStatsResponse(
            total=total,
            pending=pending,
            approved=approved,
            scanning=scanning,
            transferred=transferred,
            rejected=rejected,
            avg_time_hours=avg_time_hours,
        )

    async def cancel_transfer(
        self,
        transfer_id: int,
        user: User,
        db: AsyncSession,
    ) -> None:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found",
            )

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        if transfer.artist_id != user.id and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the transfer owner or admin can cancel",
            )

        if transfer.status == TransferStatus.TRANSFERRED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel an already-transferred transfer",
            )
        if transfer.status == TransferStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer is already cancelled",
            )

        transfer.status = TransferStatus.CANCELLED

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=user.id,
            action="cancelled",
            description=f"Cancelled by {user.display_name}",
        ))

        await db.flush()
        await db.commit()

        logger.info("Transfer %s cancelled by %s", transfer.reference, user.username)


transfer_service = TransferService()
