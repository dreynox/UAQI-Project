"""City ORM model."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ward import Ward
    from app.models.aqi import AQISation
    from app.models.intervention import Intervention


class City(Base, IdMixin, TimestampMixin):
    """An Indian metro city covered by the platform."""

    __tablename__ = "cities"

    code: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    country: Mapped[str] = mapped_column(String(8), default="IN", nullable=False)
    center_lat: Mapped[float] = mapped_column(Float, nullable=False)
    center_lon: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_min_lat: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_min_lon: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_max_lat: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_max_lon: Mapped[float] = mapped_column(Float, nullable=False)
    population_millions: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    primary_language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)

    wards: Mapped[List["Ward"]] = relationship(
        "Ward", back_populates="city", cascade="all, delete-orphan"
    )
    stations: Mapped[List["AQISation"]] = relationship(
        "AQISation", back_populates="city", cascade="all, delete-orphan"
    )
    interventions: Mapped[List["Intervention"]] = relationship(
        "Intervention", back_populates="city", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<City {self.code} {self.name}>"
