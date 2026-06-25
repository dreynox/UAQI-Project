"""Thermal anomaly (Sentinel/MODIS proxy) ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.city import City


class ThermalAnomaly(Base, IdMixin, TimestampMixin):
    """Sentinel/MODIS thermal anomaly proxy (active fire / biomass burning)."""

    __tablename__ = "thermal_anomalies"
    __table_args__ = (
        Index("ix_ta_city_time", "city_id", "timestamp"),
    )

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    intensity_kelvin: Mapped[float] = mapped_column(Float, default=320.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), default="biomass", nullable=False)  # biomass|industrial|wildfire

    def __repr__(self) -> str:
        return f"<ThermalAnomaly city={self.city_id} type={self.source_type}>"