from __future__ import annotations

from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str
    detail: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
