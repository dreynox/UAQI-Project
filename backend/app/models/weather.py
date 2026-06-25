"""Weather forecast ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.city import City


class WeatherForecast(Base, IdMixin, TimestampMixin):
    """Hourly weather forecast for a city.

    Wind direction is stored in degrees (0=N, 90=E). Stability class is a
    Pasquill-Gifford-inspired proxy used for dispersion-style features.
    """

    __tablename__ = "weather_forecast"
    __table_args__ = (
        Index("ix_wf_city_time", "city_id", "timestamp"),
    )

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    pressure_hpa: Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    wind_dir_deg: Mapped[float] = mapped_column(Float, nullable=False)
    cloud_cover_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stability_class: Mapped[str] = mapped_column(String(4), default="D", nullable=False)  # A..F
    precip_mm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    city: Mapped["City"] = relationship("City")

    def __repr__(self) -> str:
        return f"<WeatherForecast city={self.city_id} ts={self.timestamp}>"
