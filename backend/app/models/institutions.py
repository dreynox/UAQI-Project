"""Vulnerable institutions: schools, hospitals, elderly care, worker zones."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.city import City


class Institution(Base, IdMixin, TimestampMixin):
    """A vulnerable point-of-interest used in public-health overlay."""

    __tablename__ = "institutions"

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    institution_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # school | hospital | elderly_care | outdoor_worker | orphanage | anganwadi
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vulnerability_weight: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0-1

    def __repr__(self) -> str:
        return f"<Institution {self.institution_type} {self.name}>"
