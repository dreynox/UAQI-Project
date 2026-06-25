"""Attribution result ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ward import Ward


class Attribution(Base, IdMixin, TimestampMixin):
    """Multi-modal source attribution result for a ward."""

    __tablename__ = "attributions"
    __table_args__ = (
        Index("ix_attr_ward_time", "ward_id", "computed_at"),
    )

    ward_id: Mapped[int] = mapped_column(ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    top_source: Mapped[str] = mapped_column(String(32), nullable=False)
    # traffic | construction | industrial | waste_burning | stubble_burning | mixed
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    # Per-source percentage shares (JSON string, simple & portable).
    source_breakdown_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Per-agent evidence JSON: each agent's score, top contributors.
    agent_evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    ward: Mapped["Ward"] = relationship("Ward", back_populates="attributions")
