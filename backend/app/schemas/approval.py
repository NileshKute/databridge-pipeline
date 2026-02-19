from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.approval import ApprovalStatus
from backend.app.models.user import UserRole


class ApprovalAction(BaseModel):
    comment: Optional[str] = None


class RejectAction(BaseModel):
    reason: str = Field(..., min_length=10)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transfer_id: int
    required_role: UserRole
    status: ApprovalStatus
    approver_name: Optional[str] = None
    comment: Optional[str] = None
    decided_at: Optional[datetime] = None
