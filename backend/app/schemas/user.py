from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from backend.app.models.user import UserRole


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.ARTIST
    department: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    role: UserRole
    department: Optional[str]
    is_active: bool
    is_ldap_user: bool
    last_login: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
