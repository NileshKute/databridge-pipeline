from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.approval import ApprovalStatus
from backend.app.models.transfer import TransferCategory, TransferPriority, TransferStatus
from backend.app.models.user import UserRole


class TransferCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    category: Optional[TransferCategory] = None
    priority: TransferPriority = TransferPriority.NORMAL
    notes: Optional[str] = None
    shotgrid_project_id: Optional[int] = None
    shotgrid_entity_type: Optional[str] = None
    shotgrid_entity_id: Optional[int] = None


class TransferUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=300)
    notes: Optional[str] = None
    priority: Optional[TransferPriority] = None
    tags: Optional[List[str]] = None


class TransferFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    size_bytes: int
    checksum_sha256: Optional[str] = None
    virus_scan_status: str
    uploaded_at: datetime


class ApprovalChainItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: UserRole
    status: ApprovalStatus
    approver_name: Optional[str] = None
    comment: Optional[str] = None
    decided_at: Optional[datetime] = None


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    name: str
    description: Optional[str] = None
    category: Optional[TransferCategory] = None
    status: TransferStatus
    priority: TransferPriority
    artist_id: int
    artist_name: str

    total_files: int
    total_size_bytes: int
    staging_path: Optional[str] = None
    production_path: Optional[str] = None

    shotgrid_project_id: Optional[int] = None
    shotgrid_entity_type: Optional[str] = None
    shotgrid_entity_id: Optional[int] = None
    shotgrid_entity_name: Optional[str] = None
    shotgrid_task_id: Optional[int] = None
    shotgrid_version_id: Optional[int] = None

    scan_started_at: Optional[datetime] = None
    scan_completed_at: Optional[datetime] = None
    scan_result: Optional[dict] = None
    scan_passed: Optional[bool] = None

    transfer_started_at: Optional[datetime] = None
    transfer_completed_at: Optional[datetime] = None
    transfer_verified: Optional[bool] = None
    transfer_method: Optional[str] = None

    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    tags: Optional[List[str]] = None

    created_at: datetime
    updated_at: datetime

    files: List[TransferFileResponse] = []
    approval_chain: List[ApprovalChainItem] = []
    size_display: str = ""


class TransferListResponse(BaseModel):
    items: List[TransferResponse]
    total: int
    page: int
    per_page: int
    pages: int


class TransferStatsResponse(BaseModel):
    total: int = 0
    pending: int = 0
    approved: int = 0
    scanning: int = 0
    transferred: int = 0
    rejected: int = 0
    avg_time_hours: Optional[float] = None
