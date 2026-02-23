from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional, Type, TypeVar

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval import Approval
    from app.models.history import TransferHistory
    from app.models.user import User

_E = TypeVar("_E", bound=enum.Enum)


def _enum_result_value(value: Optional[str], enum_cls: Type[_E]) -> Optional[_E]:
    """Try value, then name, then case-insensitive match."""
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


class _TransferStatusType(TypeDecorator):
    impl = String(50)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, TransferStatus):
            return value.value
        return str(value)

    def process_result_value(self, value, dialect):
        return _enum_result_value(value, TransferStatus)


class _TransferPriorityType(TypeDecorator):
    impl = String(50)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, TransferPriority):
            return value.value
        return str(value)

    def process_result_value(self, value, dialect):
        return _enum_result_value(value, TransferPriority)


class _TransferCategoryType(TypeDecorator):
    impl = String(50)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, TransferCategory):
            return value.value
        return str(value)

    def process_result_value(self, value, dialect):
        return _enum_result_value(value, TransferCategory)


class TransferStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PENDING_TEAM_LEAD = "pending_team_lead"
    PENDING_SUPERVISOR = "pending_supervisor"
    PENDING_LINE_PRODUCER = "pending_line_producer"
    APPROVED = "approved"
    SCANNING = "scanning"
    SCAN_PASSED = "scan_passed"
    SCAN_FAILED = "scan_failed"
    COPYING = "copying"
    READY_FOR_TRANSFER = "ready_for_transfer"
    TRANSFERRING = "transferring"
    VERIFYING = "verifying"
    TRANSFERRED = "transferred"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TransferPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TransferCategory(str, enum.Enum):
    VFX_ASSETS = "vfx_assets"
    ANIMATION = "animation"
    TEXTURES = "textures"
    LIGHTING = "lighting"
    COMPOSITING = "compositing"
    AUDIO = "audio"
    EDITORIAL = "editorial"
    MATCHMOVE = "matchmove"
    FX = "fx"
    OTHER = "other"


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[TransferCategory]] = mapped_column(
        _TransferCategoryType(), nullable=True,
    )
    status: Mapped[TransferStatus] = mapped_column(
        _TransferStatusType(),
        default=TransferStatus.UPLOADED, nullable=False, index=True,
    )
    priority: Mapped[TransferPriority] = mapped_column(
        _TransferPriorityType(),
        default=TransferPriority.NORMAL, nullable=False,
    )
    artist_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    staging_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    production_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    shotgrid_project_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shotgrid_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    shotgrid_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shotgrid_entity_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    shotgrid_task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shotgrid_version_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    scan_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scan_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scan_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scan_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    transfer_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    transfer_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    transfer_verified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    transfer_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    artist: Mapped[User] = relationship(
        "User", back_populates="transfers", foreign_keys=[artist_id]
    )
    files: Mapped[List[TransferFile]] = relationship(
        "TransferFile", back_populates="transfer", cascade="all, delete-orphan", lazy="selectin"
    )
    approvals: Mapped[List[Approval]] = relationship(
        "Approval", back_populates="transfer", cascade="all, delete-orphan", lazy="selectin"
    )
    history: Mapped[List[TransferHistory]] = relationship(
        "TransferHistory", back_populates="transfer", cascade="all, delete-orphan",
        lazy="selectin", order_by="TransferHistory.created_at.desc()"
    )

    @property
    def size_display(self) -> str:
        size = float(self.total_size_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if abs(size) < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def __repr__(self) -> str:
        return f"<Transfer {self.reference}>"


class TransferFile(Base):
    __tablename__ = "transfer_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_id: Mapped[int] = mapped_column(
        ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    checksum_verified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    virus_scan_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    virus_scan_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    transfer: Mapped[Transfer] = relationship("Transfer", back_populates="files")

    def __repr__(self) -> str:
        return f"<TransferFile {self.filename}>"
