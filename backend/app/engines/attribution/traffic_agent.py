"""Traffic Agent.

Scores pollution contribution from traffic patterns.

Approach:
- Use city center as proxy for CBD; central wards get a traffic intensity bump.
- Heavier weight during weekday rush hours (already-baked traffic_index
  table exists in seed data, but we keep this engine self-contained for
  API-style use).
- Distance from city center is a soft proxy for traffic exposure
  (closer to center → more commuter traffic).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.city import City
from app.utils.geo import haversine_km


@dataclass
class AgentEvidence:
    score: float
    contributors: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


# Inverse-distance traffic exposure. At distance D km from city center,
# the exposure factor is exp(-D / DECAY_KM).
DECAY_KM = 12.0


def _rush_factor(hour: int) -> float:
    """Multiplicative rush-hour factor (1.0 = baseline)."""
    if 7 <= hour <= 10:
        return 1.25
    if 17 <= hour <= 20:
        return 1.30
    if 0 <= hour <= 5:
        return 0.55
    return 1.0


def score_traffic_agent(
    session: Session,
    ward_lat: float,
    ward_lon: float,
    bbox: Tuple[float, float, float, float],
    city: City,
    as_of: datetime,
) -> AgentEvidence:
    """Score traffic pollution contribution to this ward at this hour."""
    d_center = haversine_km(ward_lat, ward_lon, city.center_lat, city.center_lon)
    proximity = math.exp(-d_center / DECAY_KM)  # 1.0 at center, 0.5 at ~8km, etc.

    rush = _rush_factor(as_of.hour)

    score = min(1.0, proximity * rush * 0.85)
    notes: List[str] = []
    if proximity > 0.7:
        notes.append(f"Within {round(d_center, 1)}km of city center — high commuter exposure.")
    if rush > 1.2:
        notes.append("Rush-hour window active — elevated traffic contribution.")

    contributors = [
        {
            "metric": "distance_to_center_km",
            "value": round(d_center, 2),
        },
        {
            "metric": "rush_hour_multiplier",
            "value": rush,
            "hour_local": as_of.hour,
        },
        {
            "metric": "traffic_exposure",
            "value": round(score, 4),
        },
    ]

    return AgentEvidence(
        score=score,
        contributors=contributors,
        notes=notes,
    )
