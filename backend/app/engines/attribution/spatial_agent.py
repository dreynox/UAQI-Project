"""Spatial Agent.

Scores the contribution of physical proximity to registered sources
(industrial sites, construction sites) within and around a ward.

Approach:
1. Find all industrial + construction sites within bbox or up to MAX_DIST_KM.
2. For each site, apply a distance-decay weight (Gaussian falloff).
3. Apply wind-direction modifier (upwind sources weighted higher).
4. Normalize to 0..1 contribution score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, List, Tuple

from sqlalchemy.orm import Session

from app.engines.attribution.wind_modifier import downwind_factor
from app.models.construction_site import ConstructionSite
from app.models.industrial_site import IndustrialSite
from app.utils.geo import haversine_km

# Bounding-box query inflated by ~5 km picks up near-ward sources cheaply;
# exact distance check is then applied per-source.
BBOX_INFLATION_KM = 5.0
# Beyond this, sources contribute negligibly.
MAX_DIST_KM = 25.0


@dataclass
class AgentEvidence:
    """Standard evidence payload produced by every agent."""

    score: float
    contributors: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def _bbox_inflate(
    min_lat: float, min_lon: float, max_lat: float, max_lon: float, km: float
) -> Tuple[float, float, float, float]:
    """Inflate a bbox by km in all directions."""
    dlat = km / 111.0
    mean_lat = (min_lat + max_lat) / 2.0
    dlon = km / (111.0 * max(0.1, math.cos(math.radians(mean_lat))))
    return min_lat - dlat, min_lon - dlon, max_lat + dlat, max_lon + dlon


def _gauss(d: float, sigma: float) -> float:
    """Gaussian falloff; 1.0 at d=0, ~0.6 at d=sigma, ~0.13 at d=2*sigma."""
    return math.exp(-(d ** 2) / (2.0 * sigma ** 2))


def score_spatial_agent(
    session: Session,
    ward_lat: float,
    ward_lon: float,
    bbox: Tuple[float, float, float, float],
    city_id: int,
    wind_from_deg: float,
) -> AgentEvidence:
    """Score pollution from physical proximity to industrial + construction sites."""
    min_lat, min_lon, max_lat, max_lon = bbox
    ib_min_lat, ib_min_lon, ib_max_lat, ib_max_lon = _bbox_inflate(
        min_lat, min_lon, max_lat, max_lon, BBOX_INFLATION_KM
    )

    industries: List[IndustrialSite] = (
        session.query(IndustrialSite)
        .filter(
            IndustrialSite.city_id == city_id,
            IndustrialSite.lat >= ib_min_lat,
            IndustrialSite.lat <= ib_max_lat,
            IndustrialSite.lon >= ib_min_lon,
            IndustrialSite.lon <= ib_max_lon,
        )
        .all()
    )
    constructions: List[ConstructionSite] = (
        session.query(ConstructionSite)
        .filter(
            ConstructionSite.city_id == city_id,
            ConstructionSite.lat >= ib_min_lat,
            ConstructionSite.lat <= ib_max_lat,
            ConstructionSite.lon >= ib_min_lon,
            ConstructionSite.lon <= ib_max_lon,
        )
        .all()
    )

    contributors: List[dict] = []
    raw_score = 0.0

    for ind in industries:
        d = haversine_km(ward_lat, ward_lon, ind.lat, ind.lon)
        if d > MAX_DIST_KM:
            continue
        decay = _gauss(d, sigma=8.0)
        wind = downwind_factor(ind.lat, ind.lon, ward_lat, ward_lon, wind_from_deg)
        intensity_norm = ind.intensity / 100.0
        contrib = decay * wind * intensity_norm
        raw_score += contrib
        contributors.append({
            "source_type": "industrial",
            "source_id": ind.id,
            "name": ind.name,
            "distance_km": round(d, 2),
            "intensity": ind.intensity,
            "emission_type": ind.emission_type,
            "distance_decay": round(decay, 3),
            "wind_weight": round(wind, 3),
            "contribution": round(contrib, 4),
        })

    for c in constructions:
        d = haversine_km(ward_lat, ward_lon, c.lat, c.lon)
        if d > MAX_DIST_KM:
            continue
        decay = _gauss(d, sigma=6.0)
        wind = downwind_factor(c.lat, c.lon, ward_lat, ward_lon, wind_from_deg)
        intensity_norm = c.intensity / 100.0
        noncompliance_penalty = 1.3 if not c.is_compliant else 1.0
        contrib = decay * wind * intensity_norm * noncompliance_penalty
        raw_score += contrib
        contributors.append({
            "source_type": "construction",
            "source_id": c.id,
            "name": c.name,
            "distance_km": round(d, 2),
            "intensity": c.intensity,
            "is_compliant": c.is_compliant,
            "distance_decay": round(decay, 3),
            "wind_weight": round(wind, 3),
            "contribution": round(contrib, 4),
        })

    contributors.sort(key=lambda x: -x["contribution"])

    notes: List[str] = []
    if industries:
        notes.append(f"{len(industries)} industrial sites within {MAX_DIST_KM}km bbox")
    if constructions:
        non_compliant = sum(1 for c in constructions if not c.is_compliant)
        if non_compliant:
            notes.append(f"{non_compliant} non-compliant construction sites nearby")

    return AgentEvidence(
        score=min(1.0, raw_score),
        contributors=contributors[:10],  # cap to top 10
        notes=notes,
    )
