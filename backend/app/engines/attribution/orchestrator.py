"""Orchestrator: fuse the four agents into a single attribution result.

Each agent emits a score in [0, 1] and per-agent evidence.
The orchestrator:
1. Collects per-agent scores + evidence.
2. Applies city-specific fusion weights (Delhi weights stubble higher;
   Mumbai weights industrial; Bengaluru weights traffic + construction).
3. Maps the agent-level result to 5 canonical pollution source buckets:
   traffic | construction | industrial | biomass_burning | urban_form
4. Computes a confidence score (how decisively one source dominates).
5. Persists the result as an Attribution row.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.engines.attribution.explainer import build_explanation
from app.engines.attribution.land_use_agent import score_land_use_agent
from app.engines.attribution.satellite_agent import score_satellite_agent
from app.engines.attribution.spatial_agent import score_spatial_agent
from app.engines.attribution.traffic_agent import score_traffic_agent
from app.models.attribution import Attribution
from app.models.city import City
from app.models.ward import Ward


# City-specific fusion weights. Maps agent -> weight.
# Each row sums to ~1.0 (small slack for stability).
CITY_AGENT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "DEL": {  # Delhi: stubble (satellite biomass) is the headline story
        "traffic": 0.25,
        "construction": 0.20,
        "industrial": 0.20,
        "satellite": 0.30,
        "land_use": 0.05,
    },
    "BLR": {  # Bengaluru: traffic + construction boom
        "traffic": 0.35,
        "construction": 0.35,
        "industrial": 0.10,
        "satellite": 0.10,
        "land_use": 0.10,
    },
    "BOM": {  # Mumbai: industrial belt (Thane/Belapur) + coastal traffic
        "traffic": 0.30,
        "construction": 0.15,
        "industrial": 0.35,
        "satellite": 0.05,
        "land_use": 0.15,
    },
}
DEFAULT_AGENT_WEIGHTS = {
    "traffic": 0.25,
    "construction": 0.25,
    "industrial": 0.25,
    "satellite": 0.15,
    "land_use": 0.10,
}


# Map agent -> which source bucket it contributes to, and how much.
AGENT_TO_SOURCE = {
    "traffic": ("traffic", 1.0),
    "construction": ("construction", 1.0),
    "industrial": ("industrial", 1.0),
    "satellite_biomass": ("biomass_burning", 1.0),
    "satellite_industrial": ("industrial", 0.5),  # industrial thermals also count
    "land_use_construction": ("construction", 0.4),
    "land_use_open_industrial": ("industrial", 0.4),
    "land_use_builtup": ("urban_form", 0.3),
}


@dataclass
class AgentEvidence:
    score: float
    contributors: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class AttributionResult:
    top_source: str
    confidence: float
    source_breakdown: Dict[str, float]
    per_agent_scores: Dict[str, float]
    per_agent_evidence: Dict[str, dict]
    agent_notes: Dict[str, List[str]]
    explanation: str
    computed_at: datetime


def _latest_wind(session: Session, city_id: int, as_of: datetime) -> float:
    """Pull the latest wind_from_deg from weather forecast. Default 270 (W)."""
    from app.models.weather import WeatherForecast

    row = (
        session.query(WeatherForecast)
        .filter(WeatherForecast.city_id == city_id, WeatherForecast.timestamp <= as_of)
        .order_by(WeatherForecast.timestamp.desc())
        .first()
    )
    return row.wind_dir_deg if row else 270.0


def compute_attribution(
    session: Session,
    ward: Ward,
    city: City,
    as_of: Optional[datetime] = None,
) -> AttributionResult:
    """Run all 4 agents and fuse into a canonical attribution result."""
    as_of = as_of or datetime(2026, 6, 25, 23, 0, 0)
    bbox = (ward.bbox_min_lat, ward.bbox_min_lon, ward.bbox_max_lat, ward.bbox_max_lon)
    wind = _latest_wind(session, city.id, as_of)

    # Run agents
    spatial = score_spatial_agent(
        session, ward.centroid_lat, ward.centroid_lon, bbox, city.id, wind
    )
    satellite = score_satellite_agent(
        session, ward.centroid_lat, ward.centroid_lon, bbox, city.id, wind, as_of
    )
    traffic = score_traffic_agent(
        session, ward.centroid_lat, ward.centroid_lon, bbox, city, as_of
    )
    land_use = score_land_use_agent(
        session, ward.centroid_lat, ward.centroid_lon, bbox, city.id
    )

    per_agent_scores = {
        "spatial": spatial.score,
        "satellite": satellite.score,
        "traffic": traffic.score,
        "land_use": land_use.score,
    }

    # Get city-specific fusion weights.
    weights = CITY_AGENT_WEIGHTS.get(city.code, DEFAULT_AGENT_WEIGHTS)

    # Build source bucket breakdown. Spatial is split between construction
    # and industrial based on contributors; satellite is biomass-heavy.
    source_raw: Dict[str, float] = {
        "traffic": 0.0,
        "construction": 0.0,
        "industrial": 0.0,
        "biomass_burning": 0.0,
        "urban_form": 0.0,
    }

    # Traffic agent → traffic bucket
    source_raw["traffic"] += traffic.score * weights["traffic"] * 1.0

    # Land use → splits between construction, industrial, urban_form
    source_raw["construction"] += land_use.score * weights["land_use"] * 0.4
    source_raw["industrial"] += land_use.score * weights["land_use"] * 0.3
    source_raw["urban_form"] += land_use.score * weights["land_use"] * 0.3

    # Satellite → biomass-burning (mostly), with industrial thermals as a small add
    biomass_contribs = sum(
        1 for c in satellite.contributors
        if c.get("anomaly_source_type") in ("biomass", "wildfire")
    )
    industrial_thermal_contribs = sum(
        1 for c in satellite.contributors
        if c.get("anomaly_source_type") == "industrial"
    )
    biomass_share = biomass_contribs / max(1, biomass_contribs + industrial_thermal_contribs)
    industrial_thermal_share = 1.0 - biomass_share
    source_raw["biomass_burning"] += satellite.score * weights["satellite"] * biomass_share
    source_raw["industrial"] += satellite.score * weights["satellite"] * industrial_thermal_share * 0.5

    # Spatial → split between construction and industrial based on contributors.
    spatial_construction = sum(
        c.get("contribution", 0.0)
        for c in spatial.contributors
        if c.get("source_type") == "construction"
    )
    spatial_industrial = sum(
        c.get("contribution", 0.0)
        for c in spatial.contributors
        if c.get("source_type") == "industrial"
    )
    spatial_total = spatial_construction + spatial_industrial
    if spatial_total > 0:
        c_share = spatial_construction / spatial_total
        i_share = spatial_industrial / spatial_total
    else:
        c_share = i_share = 0.5

    # Map "construction" weight from spatial into construction bucket
    source_raw["construction"] += (
        spatial.score * weights["construction"] * c_share
    )
    # Map "industrial" weight from spatial into industrial bucket
    source_raw["industrial"] += (
        spatial.score * weights["industrial"] * i_share
    )

    # Normalize source breakdown to [0, 1] (sum to 1).
    total = sum(source_raw.values()) or 1.0
    source_breakdown = {k: round(v / total, 4) for k, v in source_raw.items()}

    # Pick top source.
    top_source = max(source_breakdown.items(), key=lambda kv: kv[1])[0]

    # Confidence = (top share) - (second share). High gap = high confidence.
    sorted_shares = sorted(source_breakdown.values(), reverse=True)
    confidence = max(0.0, min(1.0, sorted_shares[0] - sorted_shares[1] + 0.35))

    per_agent_evidence = {
        "spatial": {
            "score": round(spatial.score, 4),
            "top_contributors": spatial.contributors[:5],
            "notes": spatial.notes,
        },
        "satellite": {
            "score": round(satellite.score, 4),
            "top_contributors": satellite.contributors[:5],
            "notes": satellite.notes,
        },
        "traffic": {
            "score": round(traffic.score, 4),
            "top_contributors": traffic.contributors,
            "notes": traffic.notes,
        },
        "land_use": {
            "score": round(land_use.score, 4),
            "top_contributors": land_use.contributors,
            "notes": land_use.notes,
        },
    }

    agent_notes = {
        "spatial": spatial.notes,
        "satellite": satellite.notes,
        "traffic": traffic.notes,
        "land_use": land_use.notes,
    }

    explanation = build_explanation(
        top_source=top_source,  # canonical bucket name as in source_breakdown
        source_breakdown=source_breakdown,
        per_agent_scores={
            "spatial": spatial.score,
            "satellite": satellite.score,
            "traffic": traffic.score,
            "land_use": land_use.score,
        },
        agent_notes=agent_notes,
        ward_name=ward.name,
        current_aqi=ward.current_aqi,
    )

    return AttributionResult(
        top_source=top_source,
        confidence=round(confidence, 3),
        source_breakdown=source_breakdown,
        per_agent_scores={k: round(v, 4) for k, v in per_agent_scores.items()},
        per_agent_evidence=per_agent_evidence,
        agent_notes=agent_notes,
        explanation=explanation,
        computed_at=as_of,
    )


def persist_attribution(
    session: Session,
    ward: Ward,
    result: AttributionResult,
) -> Attribution:
    """Write a new Attribution row for this ward."""
    top_source = result.top_source
    if top_source == "biomass_burning":
        # Map to canonical bucket name used in DB
        top_source = "stubble_burning"

    row = Attribution(
        ward_id=ward.id,
        computed_at=result.computed_at,
        top_source=top_source,
        confidence=result.confidence,
        source_breakdown_json=json.dumps(result.source_breakdown),
        agent_evidence_json=json.dumps(result.per_agent_evidence),
        explanation=result.explanation,
    )
    session.add(row)
    session.flush()
    return row
