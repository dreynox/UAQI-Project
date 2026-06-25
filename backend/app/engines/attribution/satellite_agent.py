"""Satellite Agent.

Scores the contribution of thermal anomalies (Sentinel/MODIS proxy)
affecting a ward. This is the 'stubble burning' signal that drives Delhi's
winter pollution episodes.

Approach:
1. Look back WINDOW_HOURS for thermal anomalies in the city's bbox.
2. Weight each anomaly by intensity * confidence * distance-decay.
3. Heavy weight on biomass/stubble source_type for Delhi-style stories.
4. Apply wind-direction modifier (NW anomalies matter most when wind
   is from the NW).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.engines.attribution.wind_modifier import downwind_factor
from app.models.thermal_anomaly import ThermalAnomaly
from app.utils.geo import haversine_km

# How far back to look for thermal anomalies (matches a smoke transport window).
WINDOW_HOURS = 48
# Max distance to consider a thermal anomaly relevant to a ward.
MAX_DIST_KM = 150.0


@dataclass
class AgentEvidence:
    score: float
    contributors: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def _gauss(d: float, sigma: float) -> float:
    return math.exp(-(d ** 2) / (2.0 * sigma ** 2))


# Source-type multipliers — biomass (stubble burning) is the headline story.
SOURCE_WEIGHTS = {
    "biomass": 1.0,
    "wildfire": 0.9,
    "industrial": 0.4,
}


def score_satellite_agent(
    session: Session,
    ward_lat: float,
    ward_lon: float,
    bbox: Tuple[float, float, float, float],
    city_id: int,
    wind_from_deg: float,
    as_of: datetime,
) -> AgentEvidence:
    """Score pollution contribution from thermal anomalies (Sentinel/MODIS proxy)."""
    min_lat, min_lon, max_lat, max_lon = bbox
    # Inflate to allow long-range stubble transport (upwind Punjab/Haryana).
    SPATIAL_BUFFER_DEG = 1.5
    window_start = as_of - timedelta(hours=WINDOW_HOURS)

    rows: List[ThermalAnomaly] = (
        session.query(ThermalAnomaly)
        .filter(
            and_(
                ThermalAnomaly.city_id == city_id,
                ThermalAnomaly.timestamp >= window_start,
                ThermalAnomaly.lat >= min_lat - SPATIAL_BUFFER_DEG,
                ThermalAnomaly.lat <= max_lat + SPATIAL_BUFFER_DEG,
                ThermalAnomaly.lon >= min_lon - SPATIAL_BUFFER_DEG,
                ThermalAnomaly.lon <= max_lon + SPATIAL_BUFFER_DEG,
            )
        )
        .all()
    )

    contributors: List[dict] = []
    raw_score = 0.0

    biomass_count = 0
    industrial_count = 0

    for ta in rows:
        d = haversine_km(ward_lat, ward_lon, ta.lat, ta.lon)
        if d > MAX_DIST_KM:
            continue
        distance_decay = _gauss(d, sigma=50.0)  # long-range transport
        wind = downwind_factor(ta.lat, ta.lon, ward_lat, ward_lon, wind_from_deg)
        intensity_norm = (ta.intensity_kelvin - 300.0) / 60.0  # 300K baseline, 360K → 1.0
        intensity_norm = max(0.0, min(1.0, intensity_norm))
        source_weight = SOURCE_WEIGHTS.get(ta.source_type, 0.5)
        contrib = distance_decay * wind * intensity_norm * ta.confidence * source_weight
        raw_score += contrib
        if ta.source_type == "biomass":
            biomass_count += 1
        elif ta.source_type == "industrial":
            industrial_count += 1
        contributors.append({
            "source_type": "thermal_anomaly",
            "anomaly_id": ta.id,
            "anomaly_source_type": ta.source_type,
            "lat": round(ta.lat, 4),
            "lon": round(ta.lon, 4),
            "distance_km": round(d, 2),
            "intensity_kelvin": ta.intensity_kelvin,
            "confidence": ta.confidence,
            "distance_decay": round(distance_decay, 3),
            "wind_weight": round(wind, 3),
            "contribution": round(contrib, 4),
        })

    contributors.sort(key=lambda x: -x["contribution"])

    notes: List[str] = []
    if biomass_count > 20:
        notes.append(
            f"{biomass_count} biomass thermal anomalies in last 48h — "
            "consistent with active stubble/waste burning in region."
        )
    elif biomass_count > 0:
        notes.append(f"{biomass_count} biomass thermal anomalies in last 48h.")
    if industrial_count > 5:
        notes.append(f"{industrial_count} industrial thermal anomalies flagged.")

    return AgentEvidence(
        score=min(1.0, raw_score),
        contributors=contributors[:10],
        notes=notes,
    )
