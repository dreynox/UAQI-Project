"""Vulnerable population summary per ward."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IdMixin, TimestampMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ward import Ward


class VulnerablePopulation(Base, IdMixin, TimestampMixin):
    """Population vulnerability summary used for health-risk overlay & advisory."""

    __tablename__ = "vulnerable_population"

    ward_id: Mapped[int] = mapped_column(
        ForeignKey("wards.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    children_under_5: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    elderly_65_plus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outdoor_workers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    asthma_prev_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pregnant_women: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vulnerability_index: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # 0-100: higher = more vulnerable

    ward: Mapped["Ward"] = relationship("Ward", back_populates="vulnerable")
