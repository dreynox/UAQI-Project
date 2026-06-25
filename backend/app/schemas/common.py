"""Common Pydantic schemas (envelope, pagination, error)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class EnvelopeMeta(BaseModel):
    generated_at: datetime
    city: Optional[str] = None
    model_version: Optional[str] = None
    extras: Dict[str, Any] = Field(default_factory=dict)


class EnvelopeError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class Envelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    meta: EnvelopeMeta = Field(default_factory=lambda: EnvelopeMeta(generated_at=datetime.utcnow()))
    warnings: List[str] = Field(default_factory=list)
    error: Optional[EnvelopeError] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 50
    total: int = 0
