from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Type, TypeVar

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.transfer import Transfer
    from app.models.user import User

from app.models.user import UserRole, _UserRoleType

_E = TypeVar("_E", bound=enum.Enum)


def _enum_result_value(value, enum_cls: Type[_E]):
    if value is None:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        pass
    try:
        return enum_cls[value]
    except KeyError:
        pass
    val_str = str(value).lower()
    for member in enum_cls:
        if member.value.lower() == val_str or member.name.lower() == val_str:
            return member
    raise ValueError(f"Invalid value for {enum_cls.__name__}: {value!r}")


class _ApprovalStatusType(TypeDecorator):
    impl = String(50)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, ApprovalStatus):
            return value.value
        return str(value)

    def process_result_value(self, value, dialect):
        return _enum_result_value(value, ApprovalStatus)


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
        _UserRoleType(), nullable=False,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        _ApprovalStatusType(),
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
