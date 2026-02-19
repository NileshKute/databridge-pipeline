from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.approval import Approval
    from backend.app.models.history import TransferHistory
    from backend.app.models.notification import Notification
    from backend.app.models.transfer import Transfer


class UserRole(str, enum.Enum):
    ARTIST = "artist"
    TEAM_LEAD = "team_lead"
    SUPERVISOR = "supervisor"
    LINE_PRODUCER = "line_producer"
    DATA_TEAM = "data_team"
    IT_TEAM = "it_team"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda e: [x.value for x in e]),
        default=UserRole.ARTIST, nullable=False,
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ldap_dn: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ldap_groups: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shotgrid_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    transfers: Mapped[List[Transfer]] = relationship(
        "Transfer", back_populates="artist", foreign_keys="Transfer.artist_id", lazy="selectin"
    )
    approvals_given: Mapped[List[Approval]] = relationship(
        "Approval", back_populates="approver", foreign_keys="Approval.approver_id", lazy="selectin"
    )
    history_entries: Mapped[List[TransferHistory]] = relationship(
        "TransferHistory", back_populates="user", foreign_keys="TransferHistory.user_id", lazy="selectin"
    )
    notifications: Mapped[List[Notification]] = relationship(
        "Notification", back_populates="user", foreign_keys="Notification.user_id", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"
