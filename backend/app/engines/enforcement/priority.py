"""Urgency / priority scoring for enforcement actions.

Priority blends:
- Current AQI severity (non-linear: hazardous > severe > poor).
- Vulnerability index of the ward (schools, hospitals, elderly).
- Forecast delta (if AQI is rising, escalate faster).
- Attribution confidence in the dominant source (so action targets the
  right thing).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.attribution import Attribution
from app.models.forecast import Forecast
from app.models.ward import Ward


@dataclass
class PriorityScore:
    ward_id: int
    score: float
    aqi_component: float
    vulnerability_component: float
    forecast_component: float
    attribution_component: float
    urgency: str  # low | medium | high | critical

    def to_dict(self) -> dict:
        return {
            "ward_id": self.ward_id,
            "priority_score": round(self.score, 1),
            "urgency": self.urgency,
            "components": {
                "aqi": round(self.aqi_component, 2),
                "vulnerability": round(self.vulnerability_component, 2),
                "forecast_trend": round(self.forecast_component, 2),
                "attribution_confidence": round(self.attribution_component, 2),
            },
        }


def _aqi_severity_score(aqi: float) -> float:
    """Map AQI to a 0-100 severity score.

    Uses the CPCB breakpoint anchors:
      0-50 good, 51-100 satisfactory, 101-200 moderate, 201-300 poor,
      301-400 very_poor, 401+ severe.
    """
    if aqi <= 50:
        return aqi * 0.4
    if aqi <= 100:
        return 20 + (aqi - 50) * 0.6
    if aqi <= 200:
        return 50 + (aqi - 100) * 0.3
    if aqi <= 300:
        return 80 + (aqi - 200) * 0.15
    if aqi <= 400:
        return 95 + (aqi - 300) * 0.04
    return 99.0


def _forecast_trend_score(session: Session, ward_id: int) -> float:
    """0-10: how fast AQI is forecast to rise over next 24h vs current."""
    rows = (
        session.query(Forecast)
        .filter(Forecast.ward_id == ward_id)
        .order_by(Forecast.horizon_hours.asc())
        .all()
    )
    if not rows:
        return 0.0
    nearest = rows[0]
    delta = nearest.predicted_aqi - nearest.baseline_aqi
    # Map delta to 0-10.
    return max(0.0, min(10.0, 5.0 + delta / 10.0))


def _attribution_confidence_score(session: Session, ward_id: int) -> float:
    """0-5: high-confidence attributions let us act decisively."""
    row = (
        session.query(Attribution)
        .filter(Attribution.ward_id == ward_id)
        .order_by(Attribution.computed_at.desc())
        .first()
    )
    if not row:
        return 0.0
    return max(0.0, min(5.0, row.confidence * 5.0))


def compute_urgency(
    session: Session,
    ward: Ward,
    *,
    attribution: Optional[Attribution] = None,
) -> PriorityScore:
    """Compute a single-ward priority score (0-100ish)."""
    aqi_score = _aqi_severity_score(ward.current_aqi)
    vuln_score = float(ward.vulnerability_index) * 0.3  # 0-30 if vuln in 0-100
    fc_score = _forecast_trend_score(session, ward.id)
    attr_row = attribution or (
        session.query(Attribution)
        .filter(Attribution.ward_id == ward.id)
        .order_by(Attribution.computed_at.desc())
        .first()
    )
    attr_score = (attr_row.confidence * 5.0) if attr_row else 0.0

    total = aqi_score * 0.55 + vuln_score + fc_score + attr_score

    # Urgency buckets.
    if total >= 80:
        urgency = "critical"
    elif total >= 60:
        urgency = "high"
    elif total >= 40:
        urgency = "medium"
    else:
        urgency = "low"

    return PriorityScore(
        ward_id=ward.id,
        score=total,
        aqi_component=aqi_score * 0.55,
        vulnerability_component=vuln_score,
        forecast_component=fc_score,
        attribution_component=attr_score,
        urgency=urgency,
    )


def compute_priority_queue(
    session: Session,
    wards: List[Ward],
    *,
    limit: int = 10,
) -> List[dict]:
    """Return top-N wards ranked by priority, with full scoring breakdown."""
    scored = [compute_urgency(session, w) for w in wards]
    scored.sort(key=lambda p: p.score, reverse=True)
    top = scored[:limit]
    return [p.to_dict() for p in top]
