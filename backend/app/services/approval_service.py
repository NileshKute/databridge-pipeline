from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.approval import Approval, ApprovalStatus
from backend.app.models.history import TransferHistory
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.transfer import Transfer, TransferStatus
from backend.app.models.user import User, UserRole
from backend.app.schemas.transfer import ApprovalChainItem

logger = logging.getLogger("databridge.approval_service")

WORKFLOW: Dict[str, dict] = {
    "pending_team_lead": {
        "required_role": "team_lead",
        "next_status": "pending_supervisor",
        "notify_roles": ["supervisor"],
        "label": "Team Lead Review",
    },
    "pending_supervisor": {
        "required_role": "supervisor",
        "next_status": "pending_line_producer",
        "notify_roles": ["line_producer"],
        "label": "Supervisor Validation",
    },
    "pending_line_producer": {
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


class ApprovalService:

    async def get_pending(self, user: User, db: AsyncSession) -> List[Transfer]:
        role = user.role.value if hasattr(user.role, "value") else user.role

        base = select(Transfer).options(
            selectinload(Transfer.artist),
            selectinload(Transfer.files),
            selectinload(Transfer.approvals).selectinload(Approval.approver),
        )

        if role == "admin":
            statuses = [
                TransferStatus.PENDING_TEAM_LEAD,
                TransferStatus.PENDING_SUPERVISOR,
                TransferStatus.PENDING_LINE_PRODUCER,
            ]
            q = base.where(Transfer.status.in_(statuses))
        elif role == "team_lead":
            q = base.where(Transfer.status == TransferStatus.PENDING_TEAM_LEAD)
        elif role == "supervisor":
            q = base.where(Transfer.status == TransferStatus.PENDING_SUPERVISOR)
        elif role == "line_producer":
            q = base.where(Transfer.status == TransferStatus.PENDING_LINE_PRODUCER)
        elif role == "data_team":
            q = base.where(
                Transfer.status.in_([TransferStatus.APPROVED, TransferStatus.SCAN_PASSED])
            )
        elif role == "it_team":
            q = base.where(Transfer.status == TransferStatus.READY_FOR_TRANSFER)
        else:
            return []

        q = q.order_by(Transfer.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().unique().all())

    async def get_pending_count(self, user: User, db: AsyncSession) -> int:
        items = await self.get_pending(user, db)
        return len(items)

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
        if user_role != step["required_role"] and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' cannot approve at stage '{step['label']}'",
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
        approval.status = ApprovalStatus.APPROVED
        approval.approver_id = user.id
        approval.comment = comment
        approval.decided_at = now

        old_status = current_status
        new_status = step["next_status"]
        transfer.status = TransferStatus(new_status)

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=user.id,
            action="approved",
            description=f"{step['label']} approved by {user.display_name}",
            metadata_json={
                "old_status": old_status,
                "new_status": new_status,
                "approver": user.username,
                "comment": comment,
            },
        ))

        for notify_role in step.get("notify_roles", []):
            role_enum = _ROLE_TO_ENUM.get(notify_role)
            if role_enum is None:
                continue
            users_result = await db.execute(
                select(User).where(User.role == role_enum, User.is_active.is_(True))
            )
            for target_user in users_result.scalars().all():
                db.add(Notification(
                    user_id=target_user.id,
                    transfer_id=transfer.id,
                    type=NotificationType.APPROVAL_REQUIRED,
                    title=f"Approval needed: {transfer.reference}",
                    message=(
                        f"Transfer '{transfer.name}' has been approved at {step['label']} "
                        f"and now requires your review."
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
            "Transfer %s approved at %s by %s → %s",
            transfer.reference, step["label"], user.username, new_status,
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
        if user_role != step["required_role"] and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' cannot reject at stage '{step['label']}'",
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
