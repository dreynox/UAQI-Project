"""Ward (administrative zone) ORM model with simplified polygon geometry."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.aqi import AQITimeSeries
    from app.models.traffic import TrafficDensity
    from app.models.intervention import Intervention
    from app.models.forecast import Forecast
    from app.models.attribution import Attribution
    from app.models.vulnerable import VulnerablePopulation
    from app.models.advisory import Advisory


class Ward(Base, IdMixin, TimestampMixin):
    """Administrative ward / zone inside a city.

    Geometry is stored as a GeoJSON Polygon string (text) for portability
    across SQLite (demo) and Postgres (production).
    """

    __tablename__ = "wards"

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), index=True, nullable=False)
    ward_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    population: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    centroid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_lon: Mapped[float] = mapped_column(Float, nullable=False)
    # GeoJSON Polygon coordinates (stringified for SQLite portability).
    geometry_geojson: Mapped[str] = mapped_column(Text, nullable=False)
    bbox_min_lat: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_min_lon: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_max_lat: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_max_lon: Mapped[float] = mapped_column(Float, nullable=False)
    # Aggregate current AQI snapshot (kept up to date by seed / ingestion).
    current_aqi: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    aqi_category: Mapped[str] = mapped_column(String(16), default="good", nullable=False)
    vulnerability_index: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)

    city: Mapped["City"] = relationship("City", back_populates="wards")
    aqi_series: Mapped[List["AQITimeSeries"]] = relationship(
        "AQITimeSeries", back_populates="ward", cascade="all, delete-orphan"
    )
    traffic: Mapped[List["TrafficDensity"]] = relationship(
        "TrafficDensity", back_populates="ward", cascade="all, delete-orphan"
    )
    interventions: Mapped[List["Intervention"]] = relationship(
        "Intervention", back_populates="ward", cascade="all, delete-orphan"
    )
    forecasts: Mapped[List["Forecast"]] = relationship(
        "Forecast", back_populates="ward", cascade="all, delete-orphan"
    )
    attributions: Mapped[List["Attribution"]] = relationship(
        "Attribution", back_populates="ward", cascade="all, delete-orphan"
    )
    vulnerable: Mapped[Optional["VulnerablePopulation"]] = relationship(
        "VulnerablePopulation", back_populates="ward", uselist=False, cascade="all, delete-orphan"
    )
    advisories: Mapped[List["Advisory"]] = relationship(
        "Advisory", back_populates="ward", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ward {self.ward_code} {self.name}>"
