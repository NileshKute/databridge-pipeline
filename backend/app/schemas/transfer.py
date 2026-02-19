from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.app.models.transfer import TransferPriority, TransferStatus


class TransferFileRead(BaseModel):
    id: int
    relative_path: str
    file_size_bytes: int
    checksum_source: Optional[str]
    checksum_destination: Optional[str]
    checksum_verified: Optional[bool]
    transferred: bool

    model_config = {"from_attributes": True}


class TransferCreate(BaseModel):
    project_id: int
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    priority: TransferPriority = TransferPriority.NORMAL
    source_path: str = Field(..., min_length=1)
    destination_path: str = Field(..., min_length=1)
    shotgrid_task_id: Optional[int] = None
    shotgrid_version_id: Optional[int] = None


class TransferRead(BaseModel):
    id: int
    reference_id: str
    project_id: int
    created_by: int
    approved_by: Optional[int]
    title: str
    description: Optional[str]
    status: TransferStatus
    priority: TransferPriority
    source_path: str
    destination_path: str
    total_size_bytes: int
    transferred_bytes: int
    file_count: int
    progress_percent: float
    shotgrid_task_id: Optional[int]
    shotgrid_version_id: Optional[int]
    error_message: Optional[str]
    celery_task_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    files: List[TransferFileRead] = []

    model_config = {"from_attributes": True}


class TransferUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TransferPriority] = None
    status: Optional[TransferStatus] = None


class TransferListRead(BaseModel):
    id: int
    reference_id: str
    project_id: int
    created_by: int
    title: str
    status: TransferStatus
    priority: TransferPriority
    total_size_bytes: int
    progress_percent: float
    file_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
