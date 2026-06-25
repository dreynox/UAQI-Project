"""Land Use Agent.

Scores pollution contribution from land-use composition:
- Built-up density (inferred from institution density)
- Open waste-burning hotspots (proxy: industrial sites without stack monitors)

This agent provides the 'urban form' signal: a ward with many institutions
and few green spaces will trap pollutants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.construction_site import ConstructionSite
from app.models.industrial_site import IndustrialSite
from app.models.institutions import Institution


@dataclass
class AgentEvidence:
    score: float
    contributors: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def score_land_use_agent(
    session: Session,
    ward_lat: float,
    ward_lon: float,
    bbox: Tuple[float, float, float, float],
    city_id: int,
) -> AgentEvidence:
    """Score pollution from land-use composition + urban form."""
    min_lat, min_lon, max_lat, max_lon = bbox

    inst_count = (
        session.query(func.count(Institution.id))
        .filter(
            Institution.city_id == city_id,
            Institution.lat >= min_lat,
            Institution.lat <= max_lat,
            Institution.lon >= min_lon,
            Institution.lon <= max_lon,
        )
        .scalar()
        or 0
    )

    # Industries without stack monitors are an open-emission land-use signal.
    no_stack = (
        session.query(func.count(IndustrialSite.id))
        .filter(
            IndustrialSite.city_id == city_id,
            IndustrialSite.lat >= min_lat,
            IndustrialSite.lat <= max_lat,
            IndustrialSite.lon >= min_lon,
            IndustrialSite.lon <= max_lon,
            IndustrialSite.has_stack_monitor.is_(False),
        )
        .scalar()
        or 0
    )

    active_constructions = (
        session.query(func.count(ConstructionSite.id))
        .filter(
            ConstructionSite.city_id == city_id,
            ConstructionSite.lat >= min_lat,
            ConstructionSite.lat <= max_lat,
            ConstructionSite.lon >= min_lon,
            ConstructionSite.lon <= max_lon,
        )
        .scalar()
        or 0
    )

    contributors: List[dict] = []
    raw = 0.0

    # Built-up density: ~50 institutions in ward area = moderate urban form.
    built_up = min(1.0, inst_count / 50.0)
    raw += built_up * 0.35
    contributors.append({
        "metric": "built_up_density",
        "institutions_count": int(inst_count),
        "contribution": round(built_up * 0.35, 4),
    })

    # Open industrial emitters (no stack monitor) — strong land-use signal.
    open_emitters = min(1.0, no_stack / 8.0)
    raw += open_emitters * 0.35
    contributors.append({
        "metric": "open_industrial_emitters",
        "count_no_stack_monitor": int(no_stack),
        "contribution": round(open_emitters * 0.35, 4),
    })

    # Active construction = dust + diesel gensets = urban form signal.
    const_pressure = min(1.0, active_constructions / 15.0)
    raw += const_pressure * 0.30
    contributors.append({
        "metric": "active_construction_pressure",
        "count": int(active_constructions),
        "contribution": round(const_pressure * 0.30, 4),
    })

    notes: List[str] = []
    if inst_count > 30:
        notes.append(f"Dense urban form ({inst_count} institutions).")
    if no_stack > 5:
        notes.append(f"{no_stack} industrial sites lack stack monitors — open emissions likely.")
    if active_constructions > 20:
        notes.append(f"High construction pressure ({active_constructions} active sites).")

    return AgentEvidence(
        score=min(1.0, raw),
        contributors=contributors,
        notes=notes,
    )
