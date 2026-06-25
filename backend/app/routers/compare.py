"""Compare router: cross-city comparative intelligence."""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.attribution import Attribution
from app.models.city import City
from app.models.ward import Ward
from app.models.intervention import Intervention
from app.utils.envelope import ok

router = APIRouter()


# Canonical buckets surfaced in /compare/cities (matches attribution engine).
SOURCE_BUCKETS = (
    "traffic",
    "construction",
    "industrial",
    "stubble_burning",
    "biomass_burning",
    "waste_burning",
    "urban_form",
    "mixed",
)


@router.get("/compare/cities")
def compare_cities(metric: str = "aqi", db: Session = Depends(get_db)):
    """Cross-city comparison on mean AQI, max AQI, or vulnerability.

    Each row includes:
    - mean / max AQI
    - mean vulnerability index
    - worst ward + its AQI
    - per-source ward counts (how many wards attribute to traffic / construction / etc.)
    - dominant_source (most common attribution across the city's wards)
    - past-intervention totals (count + mean delta)
    """
    cities = db.query(City).all()

    # Pre-load per-city attribution distributions to avoid N+1.
    city_ids = [c.id for c in cities]
    latest_attr_by_ward: dict[int, Attribution] = {}
    if city_ids:
        ward_ids = [wid for (wid,) in (
            db.query(Ward.id).filter(Ward.city_id.in_(city_ids)).all()
        )]
        if ward_ids:
            attrs = (
                db.query(Attribution)
                .filter(Attribution.ward_id.in_(ward_ids))
                .order_by(Attribution.ward_id, Attribution.computed_at.desc())
                .all()
            )
            for a in attrs:
                latest_attr_by_ward.setdefault(a.ward_id, a)

    # Per-city intervention stats.
    interv_rows = db.query(Intervention).all()
    interv_by_city: dict[int, list[Intervention]] = defaultdict(list)
    for r in interv_rows:
        if r.measured_aqi_delta is not None:
            interv_by_city[r.city_id].append(r)

    out = []
    for c in cities:
        mean_aqi = db.query(func.avg(Ward.current_aqi)).filter(Ward.city_id == c.id).scalar() or 0
        max_aqi = db.query(func.max(Ward.current_aqi)).filter(Ward.city_id == c.id).scalar() or 0
        mean_vuln = db.query(func.avg(Ward.vulnerability_index)).filter(Ward.city_id == c.id).scalar() or 0
        worst_ward = (
            db.query(Ward)
            .filter(Ward.city_id == c.id)
            .order_by(Ward.current_aqi.desc())
            .first()
        )
        # Per-source ward counts.
        city_wards = db.query(Ward).filter(Ward.city_id == c.id).all()
        source_counts: dict[str, int] = {s: 0 for s in SOURCE_BUCKETS}
        city_attributions = []
        for w in city_wards:
            attr = latest_attr_by_ward.get(w.id)
            if attr:
                source_counts[attr.top_source] = source_counts.get(attr.top_source, 0) + 1
                city_attributions.append(attr)
        # Dominant = source with most wards; tiebreak by mean share across wards.
        if any(v > 0 for v in source_counts.values()):
            dominant_source = max(source_counts.items(), key=lambda kv: kv[1])[0]
        else:
            dominant_source = "mixed"
        # Mean share for each source across wards.
        share_per_source: dict[str, float] = {}
        if city_attributions:
            agg: dict[str, float] = defaultdict(float)
            for a in city_attributions:
                try:
                    breakdown = json.loads(a.source_breakdown_json)
                except (json.JSONDecodeError, TypeError):
                    continue
                for k, v in breakdown.items():
                    agg[k] += float(v)
            n = len(city_attributions)
            share_per_source = {k: round(v / n, 4) for k, v in agg.items()}

        # Intervention stats.
        ints = interv_by_city.get(c.id, [])
        int_count = len(ints)
        int_mean = (
            round(sum(r.measured_aqi_delta for r in ints) / int_count, 1)
            if int_count else None
        )

        out.append({
            "code": c.code,
            "name": c.name,
            "state": c.state,
            "mean_aqi": round(float(mean_aqi), 1),
            "max_aqi": round(float(max_aqi), 1),
            "mean_vulnerability": round(float(mean_vuln), 1),
            "population_millions": c.population_millions,
            "primary_language": c.primary_language,
            "wards_count": len(city_wards),
            "worst_ward": worst_ward.name if worst_ward else None,
            "worst_ward_aqi": round(worst_ward.current_aqi, 1) if worst_ward else None,
            "worst_ward_id": worst_ward.id if worst_ward else None,
            "dominant_source": dominant_source,
            "source_counts": source_counts,
            "source_share": share_per_source,
            "interventions_count": int_count,
            "interventions_mean_delta": int_mean,
        })

    # Sort by selected metric.
    sort_key = {
        "aqi": lambda x: -x["mean_aqi"],
        "vulnerability": lambda x: -x["mean_vulnerability"],
        "interventions": lambda x: -(x["interventions_mean_delta"] or 0),
    }.get(metric, lambda x: -x["mean_aqi"])
    out.sort(key=sort_key)
    return ok(out, metric=metric, count=len(out))


@router.get("/compare/interventions")
def compare_interventions(db: Session = Depends(get_db)):
    """Cross-city intervention effectiveness summary."""
    rows = (
        db.query(Intervention)
        .filter(Intervention.measured_aqi_delta.isnot(None))
        .all()
    )
    by_city_action = {}
    for r in rows:
        city = db.query(City).filter(City.id == r.city_id).first()
        key = (city.code if city else "?", r.action_type)
        by_city_action.setdefault(key, {"count": 0, "deltas": []})
        by_city_action[key]["count"] += 1
        by_city_action[key]["deltas"].append(r.measured_aqi_delta)

    out = []
    for (city_code, action_type), info in by_city_action.items():
        deltas = info["deltas"]
        # Median is more robust than mean for small samples.
        sorted_d = sorted(deltas)
        n = len(sorted_d)
        median = (
            sorted_d[n // 2]
            if n % 2 == 1
            else round((sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2, 1)
        )
        out.append({
            "city_code": city_code,
            "action_type": action_type,
            "count": info["count"],
            "mean_aqi_delta": round(sum(deltas) / len(deltas), 1),
            "median_aqi_delta": round(median, 1),
            "best_delta": min(deltas),
            "worst_delta": max(deltas),
        })
    out.sort(key=lambda x: x["mean_aqi_delta"])  # best (most negative) first
    return ok(out, count=len(out))


@router.get("/compare/interventions/{city_code}")
def compare_interventions_for_city(city_code: str, db: Session = Depends(get_db)):
    """City-specific intervention effectiveness — same shape as the global
    endpoint but filtered. Useful for a city detail page."""
    city = db.query(City).filter(City.code == city_code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {city_code} not found")
    rows = (
        db.query(Intervention)
        .filter(Intervention.city_id == city.id, Intervention.measured_aqi_delta.isnot(None))
        .all()
    )
    by_action: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by_action[r.action_type].append(r.measured_aqi_delta)
    out = []
    for action_type, deltas in by_action.items():
        n = len(deltas)
        sorted_d = sorted(deltas)
        median = (
            sorted_d[n // 2]
            if n % 2 == 1
            else round((sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2, 1)
        )
        out.append({
            "city_code": city.code,
            "action_type": action_type,
            "count": n,
            "mean_aqi_delta": round(sum(deltas) / n, 1),
            "median_aqi_delta": round(median, 1),
            "best_delta": min(deltas),
            "worst_delta": max(deltas),
        })
    out.sort(key=lambda x: x["mean_aqi_delta"])
    return ok(out, city=city.code, count=len(out))