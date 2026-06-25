"""Industrial site ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.city import City


class IndustrialSite(Base, IdMixin, TimestampMixin):
    """Registered industrial emitter."""

    __tablename__ = "industrial_sites"

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    emission_type: Mapped[str] = mapped_column(String(32), default="mixed", nullable=False)  # so2|nox|pm|co|mixed
    intensity: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)  # 0-100
    has_stack_monitor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    compliance_score: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)  # 0-100

    def __repr__(self) -> str:
        return f"<IndustrialSite {self.name} type={self.emission_type}>"