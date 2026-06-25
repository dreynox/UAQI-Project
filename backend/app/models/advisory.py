"""Citizen advisory ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ward import Ward


class Advisory(Base, IdMixin, TimestampMixin):
    """Generated multilingual public-health advisory for a ward."""

    __tablename__ = "advisories"
    __table_args__ = (
        Index("ix_adv_ward_lang", "ward_id", "language"),
    )

    ward_id: Mapped[int] = mapped_column(ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False)  # en | hi | kn | ta
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # good | moderate | poor | severe | hazardous
    audience: Mapped[str] = mapped_column(String(32), default="general", nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    ward: Mapped["Ward"] = relationship("Ward", back_populates="advisories")