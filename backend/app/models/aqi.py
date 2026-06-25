"""AQI station and time-series ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.ward import Ward


class AQISation(Base, IdMixin, TimestampMixin):
    """Continuous Ambient Air Quality Monitoring Station (CAAQMS)."""

    __tablename__ = "aqi_stations"

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    station_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    station_type: Mapped[str] = mapped_column(String(32), default="CAAQMS", nullable=False)
    ward_id: Mapped[int | None] = mapped_column(ForeignKey("wards.id", ondelete="SET NULL"), nullable=True)

    city: Mapped["City"] = relationship("City", back_populates="stations")
    readings: Mapped[List["AQITimeSeries"]] = relationship(
        "AQITimeSeries", back_populates="station", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AQISation {self.station_code} {self.name}>"


class AQITimeSeries(Base, IdMixin, TimestampMixin):
    """Hourly air-quality readings from a station or aggregated to a ward."""

    __tablename__ = "aqi_time_series"
    __table_args__ = (
        Index("ix_aqi_ts_station_time", "station_id", "timestamp"),
        Index("ix_aqi_ts_ward_time", "ward_id", "timestamp"),
    )

    station_id: Mapped[int | None] = mapped_column(
        ForeignKey("aqi_stations.id", ondelete="CASCADE"), nullable=True
    )
    ward_id: Mapped[int | None] = mapped_column(
        ForeignKey("wards.id", ondelete="CASCADE"), nullable=True, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    aqi: Mapped[float] = mapped_column(Float, nullable=False)
    pm25: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pm10: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    no2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    so2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    o3: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    co: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    station: Mapped["AQISation | None"] = relationship("AQISation", back_populates="readings")
    ward: Mapped["Ward | None"] = relationship("Ward", back_populates="aqi_series")

    def __repr__(self) -> str:
        return f"<AQITimeSeries station={self.station_id} ts={self.timestamp} aqi={self.aqi:.0f}>"
