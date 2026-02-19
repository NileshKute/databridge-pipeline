from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.transfer import Transfer
    from backend.app.models.user import User

from backend.app.models.user import UserRole


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_id: Mapped[int] = mapped_column(
        ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    required_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda e: [x.value for x in e]), nullable=False,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, values_callable=lambda e: [x.value for x in e]),
        default=ApprovalStatus.PENDING, nullable=False,
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    transfer: Mapped[Transfer] = relationship("Transfer", back_populates="approvals")
    approver: Mapped[Optional[User]] = relationship(
        "User", back_populates="approvals_given", foreign_keys=[approver_id]
    )

    def __repr__(self) -> str:
        return f"<Approval transfer_id={self.transfer_id} role={self.required_role.value} status={self.status.value}>"
