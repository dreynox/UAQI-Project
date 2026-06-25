"""Traffic density ORM model (hourly per ward)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ward import Ward


class TrafficDensity(Base, IdMixin, TimestampMixin):
    """Hourly traffic intensity index (0-100) per ward."""

    __tablename__ = "traffic_density"
    __table_args__ = (
        Index("ix_td_ward_time", "ward_id", "timestamp"),
    )

    ward_id: Mapped[int] = mapped_column(ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    traffic_index: Mapped[float] = mapped_column(Float, nullable=False)
    heavy_vehicle_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_speed_kmh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    ward: Mapped["Ward"] = relationship("Ward", back_populates="traffic")
