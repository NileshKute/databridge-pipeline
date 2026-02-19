from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from backend.app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Z0-9_]+$")
    description: Optional[str] = None
    shotgrid_id: Optional[int] = None
    staging_path: str
    production_path: str


class ProjectRead(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    status: ProjectStatus
    shotgrid_id: Optional[int]
    staging_path: str
    production_path: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    shotgrid_id: Optional[int] = None
    staging_path: Optional[str] = None
    production_path: Optional[str] = None
