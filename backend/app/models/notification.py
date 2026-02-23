from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Type, TypeVar

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User

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


class _NotificationTypeType(TypeDecorator):
    impl = String(50)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, NotificationType):
            return value.value
        return str(value)

    def process_result_value(self, value, dialect):
        return _enum_result_value(value, NotificationType)


class NotificationType(str, enum.Enum):
    UPLOAD = "upload"
    APPROVAL_REQUIRED = "approval_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETE = "scan_complete"
    SCAN_FAILED = "scan_failed"
    TRANSFER_STARTED = "transfer_started"
    TRANSFER_COMPLETE = "transfer_complete"
    TRANSFER_FAILED = "transfer_failed"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    transfer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transfers.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[NotificationType] = mapped_column(
        _NotificationTypeType(), nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped[User] = relationship(
        "User", back_populates="notifications", foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return f"<Notification user_id={self.user_id} type={self.type.value}>"
