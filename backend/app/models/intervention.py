"""Intervention history ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.ward import Ward


class Intervention(Base, IdMixin, TimestampMixin):
    """Past or planned enforcement / intervention action."""

    __tablename__ = "interventions"

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    ward_id: Mapped[int | None] = mapped_column(ForeignKey("wards.id", ondelete="SET NULL"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # inspection | dust_control | traffic_diversion | waste_burning | industrial_audit | public_advisory | odd_even | construction_shutdown
    status: Mapped[str] = mapped_column(String(16), default="completed", nullable=False)
    # planned | active | completed | failed
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    measured_aqi_delta: Mapped[float | None] = mapped_column(Float, nullable=True)  # negative = improvement
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    city: Mapped["City"] = relationship("City", back_populates="interventions")
    ward: Mapped["Ward | None"] = relationship("Ward", back_populates="interventions")
