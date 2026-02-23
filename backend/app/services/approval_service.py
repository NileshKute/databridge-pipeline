from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.approval import Approval, ApprovalStatus
from app.models.history import TransferHistory
from app.models.notification import Notification, NotificationType
from app.models.transfer import Transfer, TransferStatus
from app.models.user import User, UserRole
from app.schemas.transfer import ApprovalChainItem

logger = logging.getLogger("databridge.approval_service")

ROLE_HIERARCHY: Dict[str, int] = getattr(settings, "ROLE_HIERARCHY", {})

WORKFLOW: Dict[str, dict] = {
    "pending_team_lead": {
        "min_role_level": 2,
        "required_role": "team_lead",
        "next_status": "pending_supervisor",
        "notify_roles": ["supervisor"],
        "label": "Team Lead Review",
    },
    "pending_supervisor": {
        "min_role_level": 3,
        "required_role": "supervisor",
        "next_status": "pending_line_producer",
        "notify_roles": ["line_producer"],
        "label": "Supervisor Validation",
    },
    "pending_line_producer": {
        "min_role_level": 4,
        "required_role": "line_producer",
        "next_status": "approved",
        "notify_roles": ["data_team"],
        "label": "Line Producer Approval",
    },
}

_ROLE_TO_ENUM = {r.value: r for r in UserRole}

_CHAIN_ORDER = [
    UserRole.TEAM_LEAD,
    UserRole.SUPERVISOR,
    UserRole.LINE_PRODUCER,
    UserRole.DATA_TEAM,
    UserRole.IT_TEAM,
]

_STATUS_ORDER = ["pending_team_lead", "pending_supervisor", "pending_line_producer", "approved"]


class ApprovalService:

    async def get_pending(self, user: User, db: AsyncSession) -> List[Transfer]:
        user_role = user.role.value if hasattr(user.role, "value") else user.role
        user_level = ROLE_HIERARCHY.get(user_role, 0)

        if user_role == "admin":
            approvable_statuses = [
                TransferStatus.PENDING_TEAM_LEAD,
                TransferStatus.PENDING_SUPERVISOR,
                TransferStatus.PENDING_LINE_PRODUCER,
            ]
        elif user_level >= 2:
            approvable_statuses = []
            for status_key, stage in WORKFLOW.items():
                if user_level >= stage["min_role_level"]:
                    try:
                        approvable_statuses.append(TransferStatus(status_key))
                    except ValueError:
                        pass
            if not approvable_statuses:
                return []
        else:
            return []

        base = select(Transfer).options(
            selectinload(Transfer.artist),
            selectinload(Transfer.files),
            selectinload(Transfer.approvals).selectinload(Approval.approver),
        )
        q = base.where(Transfer.status.in_(approvable_statuses))
        q = q.where(Transfer.artist_id != user.id)
        q = q.order_by(Transfer.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().unique().all())

    async def get_pending_count(self, user: User, db: AsyncSession) -> int:
        items = await self.get_pending(user, db)
        return len(items)

    async def _find_pending_approval(
        self, transfer_id: int, required_role: str, db: AsyncSession
    ) -> Optional[Approval]:
        role_enum = _ROLE_TO_ENUM.get(required_role)
        if role_enum is None:
            return None
        result = await db.execute(
            select(Approval).where(
                Approval.transfer_id == transfer_id,
                Approval.required_role == role_enum,
                Approval.status == ApprovalStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def _skip_intermediate_approvals(
        self,
        transfer_id: int,
        from_status: str,
        to_status: str,
        user: User,
        db: AsyncSession,
    ) -> None:
        try:
            from_idx = _STATUS_ORDER.index(from_status)
        except ValueError:
            from_idx = 0
        try:
            to_idx = _STATUS_ORDER.index(to_status)
        except ValueError:
            to_idx = len(_STATUS_ORDER)
        for status_key in _STATUS_ORDER[from_idx + 1 : to_idx]:
            stage = WORKFLOW.get(status_key)
            if not stage:
                continue
            approval = await self._find_pending_approval(
                transfer_id, stage["required_role"], db
            )
            if approval and (
                approval.status.value == "pending"
                if hasattr(approval.status, "value")
                else approval.status == "pending"
            ):
                approval.status = ApprovalStatus.SKIPPED
                approval.approver_id = user.id
                approval.comment = f"Skipped — approved by {user.display_name}"
                approval.decided_at = datetime.now(timezone.utc)

    async def approve(
        self,
        transfer_id: int,
        user: User,
        comment: Optional[str],
        db: AsyncSession,
    ) -> Transfer:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

        current_status = transfer.status.value if hasattr(transfer.status, "value") else transfer.status
        step = WORKFLOW.get(current_status)
        if step is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transfer status '{current_status}' is not an approval stage",
            )

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        user_level = ROLE_HIERARCHY.get(user_role, 0)

        if user_level < step["min_role_level"] and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role cannot approve at this stage. Requires {step['label']} level or higher.",
            )
        if transfer.artist_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot approve your own transfer request.",
            )

        approval = await self._find_pending_approval(
            transfer_id, step["required_role"], db
        )
        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending approval record found for this stage",
            )

        now = datetime.now(timezone.utc)
        approval.status = ApprovalStatus.APPROVED
        approval.approver_id = user.id
        approval.comment = comment
        approval.decided_at = now

        old_status = current_status
        next_status = step["next_status"]
        if user_level >= 4:
            next_status = "approved"
            await self._skip_intermediate_approvals(
                transfer_id, current_status, "approved", user, db
            )
        elif user_level >= 3 and current_status == "pending_team_lead":
            next_status = "pending_line_producer"
            await self._skip_intermediate_approvals(
                transfer_id, "pending_team_lead", "pending_line_producer", user, db
            )

        transfer.status = TransferStatus(next_status)

        db.add(
            TransferHistory(
                transfer_id=transfer.id,
                user_id=user.id,
                action="approved",
                description=f"{step['label']} approved by {user.display_name}",
                metadata_json={
                    "old_status": old_status,
                    "new_status": next_status,
                    "approver": user.username,
                    "comment": comment,
                },
            )
        )

        if next_status == "approved":
            for notify_role in ["data_team"]:
                role_enum = _ROLE_TO_ENUM.get(notify_role)
                if role_enum is None:
                    continue
                users_result = await db.execute(
                    select(User).where(User.role == role_enum, User.is_active.is_(True))
                )
                for target_user in users_result.scalars().all():
                    db.add(
                        Notification(
                            user_id=target_user.id,
                            transfer_id=transfer.id,
                            type=NotificationType.APPROVAL_REQUIRED,
                            title=f"Approval needed: {transfer.reference}",
                            message=f"Transfer '{transfer.name}' has been fully approved and is ready for data team.",
                        )
                    )
        else:
            for notify_role in WORKFLOW.get(next_status, {}).get("notify_roles", []):
                role_enum = _ROLE_TO_ENUM.get(notify_role)
                if role_enum is None:
                    continue
                users_result = await db.execute(
                    select(User).where(User.role == role_enum, User.is_active.is_(True))
                )
                for target_user in users_result.scalars().all():
                    db.add(
                        Notification(
                            user_id=target_user.id,
                            transfer_id=transfer.id,
                            type=NotificationType.APPROVAL_REQUIRED,
                            title=f"Approval needed: {transfer.reference}",
                            message=(
                                f"Transfer '{transfer.name}' has been approved at {step['label']} "
                                f"and now requires your review."
                            ),
                        )
                    )

        await db.flush()
        await db.commit()

        refreshed = await db.execute(
            select(Transfer).options(
                selectinload(Transfer.artist),
                selectinload(Transfer.files),
                selectinload(Transfer.approvals).selectinload(Approval.approver),
            ).where(Transfer.id == transfer.id)
        )
        transfer = refreshed.scalar_one()

        logger.info(
            "Transfer %s approved at %s by %s → %s",
            transfer.reference, step["label"], user.username, next_status,
        )
        return transfer

    async def reject(
        self,
        transfer_id: int,
        user: User,
        reason: str,
        db: AsyncSession,
    ) -> Transfer:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

        current_status = transfer.status.value if hasattr(transfer.status, "value") else transfer.status
        step = WORKFLOW.get(current_status)
        if step is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transfer status '{current_status}' is not an approval stage",
            )

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        if user_level < step["min_role_level"] and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role cannot reject at this stage. Requires {step['label']} level or higher.",
            )
        if transfer.artist_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot reject your own transfer request.",
            )

        required_role_enum = _ROLE_TO_ENUM[step["required_role"]]
        approval_result = await db.execute(
            select(Approval).where(
                Approval.transfer_id == transfer_id,
                Approval.required_role == required_role_enum,
                Approval.status == ApprovalStatus.PENDING,
            )
        )
        approval = approval_result.scalar_one_or_none()
        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending approval record found for this stage",
            )

        now = datetime.now(timezone.utc)
        approval.status = ApprovalStatus.REJECTED
        approval.approver_id = user.id
        approval.comment = reason
        approval.decided_at = now

        old_status = current_status
        transfer.status = TransferStatus.REJECTED
        transfer.rejection_reason = reason

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=user.id,
            action="rejected",
            description=f"Rejected at {step['label']} by {user.display_name}: {reason}",
            metadata_json={
                "old_status": old_status,
                "new_status": "rejected",
                "rejector": user.username,
                "reason": reason,
            },
        ))

        db.add(Notification(
            user_id=transfer.artist_id,
            transfer_id=transfer.id,
            type=NotificationType.REJECTED,
            title=f"Transfer rejected: {transfer.reference}",
            message=f"Your transfer '{transfer.name}' was rejected at {step['label']}. Reason: {reason}",
        ))

        prev_approvals = await db.execute(
            select(Approval).where(
                Approval.transfer_id == transfer_id,
                Approval.status == ApprovalStatus.APPROVED,
                Approval.approver_id.isnot(None),
            )
        )
        for prev in prev_approvals.scalars().all():
            if prev.approver_id and prev.approver_id != transfer.artist_id:
                db.add(Notification(
                    user_id=prev.approver_id,
                    transfer_id=transfer.id,
                    type=NotificationType.REJECTED,
                    title=f"Transfer rejected: {transfer.reference}",
                    message=(
                        f"Transfer '{transfer.name}' (which you previously approved) "
                        f"was rejected at {step['label']}. Reason: {reason}"
                    ),
                ))

        await db.flush()
        await db.commit()

        refreshed = await db.execute(
            select(Transfer).options(
                selectinload(Transfer.artist),
                selectinload(Transfer.files),
                selectinload(Transfer.approvals).selectinload(Approval.approver),
            ).where(Transfer.id == transfer.id)
        )
        transfer = refreshed.scalar_one()

        logger.info(
            "Transfer %s rejected at %s by %s: %s",
            transfer.reference, step["label"], user.username, reason,
        )
        return transfer

    async def get_approval_chain(
        self,
        transfer_id: int,
        db: AsyncSession,
    ) -> List[ApprovalChainItem]:
        result = await db.execute(
            select(Approval)
            .options(selectinload(Approval.approver))
            .where(Approval.transfer_id == transfer_id)
            .order_by(Approval.id)
        )
        approvals = {a.required_role: a for a in result.scalars().all()}

        chain: List[ApprovalChainItem] = []
        for role_enum in _CHAIN_ORDER:
            approval = approvals.get(role_enum)
            if approval:
                chain.append(ApprovalChainItem(
                    role=role_enum,
                    status=approval.status,
                    approver_name=approval.approver.display_name if approval.approver else None,
                    comment=approval.comment,
                    decided_at=approval.decided_at,
                ))
            else:
                chain.append(ApprovalChainItem(
                    role=role_enum,
                    status=ApprovalStatus.PENDING,
                ))

        return chain

    async def admin_override(
        self,
        transfer_id: int,
        target_status: str,
        admin_user: User,
        reason: str,
        db: AsyncSession,
    ) -> Transfer:
        admin_role = admin_user.role.value if hasattr(admin_user.role, "value") else admin_user.role
        if admin_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can force-advance transfers",
            )

        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

        try:
            new_status = TransferStatus(target_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target status: {target_status}",
            )

        old_status = transfer.status.value if hasattr(transfer.status, "value") else transfer.status

        pending_approvals = await db.execute(
            select(Approval).where(
                Approval.transfer_id == transfer_id,
                Approval.status == ApprovalStatus.PENDING,
            )
        )
        now = datetime.now(timezone.utc)
        for approval in pending_approvals.scalars().all():
            approval.status = ApprovalStatus.SKIPPED
            approval.approver_id = admin_user.id
            approval.comment = f"Skipped by admin override: {reason}"
            approval.decided_at = now

        transfer.status = new_status

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=admin_user.id,
            action="admin_override",
            description=f"Admin {admin_user.display_name} forced status {old_status} → {target_status}: {reason}",
            metadata_json={
                "old_status": old_status,
                "new_status": target_status,
                "admin": admin_user.username,
                "reason": reason,
            },
        ))

        db.add(Notification(
            user_id=transfer.artist_id,
            transfer_id=transfer.id,
            type=NotificationType.SYSTEM,
            title=f"Admin override: {transfer.reference}",
            message=f"Transfer status changed to '{target_status}' by admin. Reason: {reason}",
        ))

        await db.flush()
        await db.commit()

        refreshed = await db.execute(
            select(Transfer).options(
                selectinload(Transfer.artist),
                selectinload(Transfer.files),
                selectinload(Transfer.approvals).selectinload(Approval.approver),
            ).where(Transfer.id == transfer.id)
        )
        transfer = refreshed.scalar_one()

        logger.info(
            "Admin override: %s %s → %s by %s: %s",
            transfer.reference, old_status, target_status, admin_user.username, reason,
        )
        return transfer


approval_service = ApprovalService()
