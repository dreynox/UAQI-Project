"""Forecast ORM model: per-ward, per-horizon predicted AQI."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ward import Ward


class Forecast(Base, IdMixin, TimestampMixin):
    """Predicted AQI for a ward at a future timestamp, with confidence band."""

    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_fc_ward_target", "ward_id", "target_time"),
    )

    ward_id: Mapped[int] = mapped_column(ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    horizon_hours: Mapped[int] = mapped_column(Float, nullable=False)  # 24 | 48 | 72
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    target_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    predicted_aqi: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_aqi: Mapped[float] = mapped_column(Float, nullable=False)  # persistence baseline
    confidence_low: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_high: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), default="gbr-v1", nullable=False)

    ward: Mapped["Ward"] = relationship("Ward", back_populates="forecasts")
