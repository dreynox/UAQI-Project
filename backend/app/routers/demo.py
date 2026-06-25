"""Demo router: pre-canned story-mode scenarios."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engines.advisory.generator import (
    audience_for_ward,
    generate_advisory,
    severity_for_aqi,
    source_label,
)
from app.engines.advisory.languages import default_language_for_city
from app.engines.enforcement.action_library import recommended_actions_for_ward
from app.engines.enforcement.impact_estimator import estimate_for_action_codes
from app.engines.enforcement.priority import compute_urgency
from app.models.attribution import Attribution
from app.models.city import City
from app.models.construction_site import ConstructionSite
from app.models.forecast import Forecast
from app.models.industrial_site import IndustrialSite
from app.models.institutions import Institution
from app.models.intervention import Intervention
from app.models.thermal_anomaly import ThermalAnomaly
from app.models.vulnerable import VulnerablePopulation
from app.models.ward import Ward
from app.models.weather import WeatherForecast
from app.utils.envelope import ok

router = APIRouter()


def _curated_worst_ward(db: Session, city: City) -> Ward:
    """Return the highest-AQI ward in the city."""
    return (
        db.query(Ward)
        .filter(Ward.city_id == city.id)
        .order_by(desc(Ward.current_aqi))
        .first()
    )


def _attribution_block(db: Session, ward: Ward) -> dict | None:
    row = (
        db.query(Attribution)
        .filter(Attribution.ward_id == ward.id)
        .order_by(Attribution.computed_at.desc())
        .first()
    )
    if not row:
        return None
    return {
        "top_source": row.top_source,
        "confidence": round(row.confidence, 3),
        "source_breakdown": json.loads(row.source_breakdown_json),
        "agent_evidence": json.loads(row.agent_evidence_json),
        "explanation": row.explanation,
    }


def _forecast_block(db: Session, ward: Ward) -> dict:
    rows = (
        db.query(Forecast)
        .filter(Forecast.ward_id == ward.id)
        .order_by(Forecast.horizon_hours.asc())
        .all()
    )
    return {
        "horizons": [
            {
                "horizon_hours": int(r.horizon_hours),
                "predicted_aqi": round(r.predicted_aqi, 1),
                "baseline_aqi": round(r.baseline_aqi, 1),
                "improvement_vs_baseline": round(r.baseline_aqi - r.predicted_aqi, 1),
                "confidence_low": round(r.confidence_low, 1),
                "confidence_high": round(r.confidence_high, 1),
            }
            for r in rows
        ],
        "model_version": rows[0].model_version if rows else None,
    }


def _enforcement_block(db: Session, ward: Ward, attr: dict | None) -> dict:
    top_source = attr["top_source"] if attr else "mixed"
    confidence = attr["confidence"] if attr else 0.4
    recs = recommended_actions_for_ward(top_source, ward.current_aqi)
    codes = [r["action_code"] for r in recs]
    impacts = estimate_for_action_codes(db, ward, codes, attribution_confidence=confidence)
    impact_by_code = {i["action_code"]: i for i in impacts}
    for r in recs:
        est = impact_by_code.get(r["action_code"])
        if est:
            r["estimated_aqi_delta"] = est["expected_aqi_delta"]
            r["estimation_confidence"] = est["confidence"]
            r["estimation_method"] = est["method"]

    attr_row = (
        db.query(Attribution)
        .filter(Attribution.ward_id == ward.id)
        .order_by(Attribution.computed_at.desc())
        .first()
    )
    score = compute_urgency(db, ward, attribution=attr_row)
    return {
        "priority": score.to_dict(),
        "recommended_actions": recs,
    }


def _advisory_block(db: Session, ward: Ward, city: City) -> dict:
    """Render advisory preview in the city's primary language + English.

    Always includes `sample_en` (so the API returns both, in a stable order
    en → default_lang).
    """
    default_lang = default_language_for_city(city.code)
    out = {"default_language": default_lang}
    # Always include English.
    adv_en = generate_advisory(db, ward, city.code, "en", persist=False)
    out["sample_en"] = {
        "language": "en",
        "severity": severity_for_aqi(ward.current_aqi),
        "audience": audience_for_ward(ward),
        "title": adv_en.title,
        "body": adv_en.body,
    }
    # Add city-default language if different from English.
    if default_lang != "en":
        adv_local = generate_advisory(db, ward, city.code, default_lang, persist=False)
        out[f"sample_{default_lang}"] = {
            "language": default_lang,
            "severity": severity_for_aqi(ward.current_aqi),
            "audience": audience_for_ward(ward),
            "title": adv_local.title,
            "body": adv_local.body,
        }
    return out


def _interventions_block(db: Session, ward: Ward) -> dict:
    """Recent past interventions on this ward."""
    rows = (
        db.query(Intervention)
        .filter(Intervention.ward_id == ward.id)
        .order_by(desc(Intervention.started_at))
        .limit(5)
        .all()
    )
    return {
        "recent": [
            {
                "id": r.id,
                "action_type": r.action_type,
                "status": r.status,
                "started_at": r.started_at.isoformat(),
                "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                "measured_aqi_delta": r.measured_aqi_delta,
                "notes": r.notes,
            }
            for r in rows
        ],
        "total_completed": (
            db.query(func.count(Intervention.id))
            .filter(Intervention.ward_id == ward.id, Intervention.status == "completed")
            .scalar()
            or 0
        ),
    }


def _context_block(db: Session, ward: Ward) -> dict:
    bbox = (ward.bbox_min_lat, ward.bbox_min_lon, ward.bbox_max_lat, ward.bbox_max_lon)
    inst_count = (
        db.query(func.count(Institution.id))
        .filter(
            Institution.city_id == ward.city_id,
            Institution.lat.between(bbox[0], bbox[2]),
            Institution.lon.between(bbox[1], bbox[3]),
        )
        .scalar()
        or 0
    )
    const_count = (
        db.query(func.count(ConstructionSite.id))
        .filter(
            ConstructionSite.city_id == ward.city_id,
            ConstructionSite.lat.between(bbox[0], bbox[2]),
            ConstructionSite.lon.between(bbox[1], bbox[3]),
        )
        .scalar()
        or 0
    )
    ind_count = (
        db.query(func.count(IndustrialSite.id))
        .filter(
            IndustrialSite.city_id == ward.city_id,
            IndustrialSite.lat.between(bbox[0], bbox[2]),
            IndustrialSite.lon.between(bbox[1], bbox[3]),
        )
        .scalar()
        or 0
    )
    thermal_count = (
        db.query(func.count(ThermalAnomaly.id))
        .filter(
            ThermalAnomaly.city_id == ward.city_id,
            ThermalAnomaly.lat.between(bbox[0], bbox[2]),
            ThermalAnomaly.lon.between(bbox[1], bbox[3]),
        )
        .scalar()
        or 0
    )
    vuln = (
        db.query(VulnerablePopulation)
        .filter(VulnerablePopulation.ward_id == ward.id)
        .first()
    )
    latest_w = (
        db.query(WeatherForecast)
        .filter(WeatherForecast.city_id == ward.city_id)
        .order_by(WeatherForecast.timestamp.desc())
        .first()
    )
    return {
        "population": ward.population,
        "area_km2": ward.area_km2,
        "vulnerability": (
            {
                "index": round(ward.vulnerability_index, 1),
                "children_under_5": vuln.children_under_5 if vuln else None,
                "elderly_65_plus": vuln.elderly_65_plus if vuln else None,
                "outdoor_workers": vuln.outdoor_workers if vuln else None,
                "asthma_prev_pct": vuln.asthma_prev_pct if vuln else None,
                "pregnant_women": vuln.pregnant_women if vuln else None,
            }
            if vuln else {"index": round(ward.vulnerability_index, 1)}
        ),
        "nearby_institutions_count": int(inst_count),
        "nearby_construction_sites_count": int(const_count),
        "nearby_industrial_sites_count": int(ind_count),
        "nearby_thermal_anomalies_count": int(thermal_count),
        "weather": (
            {
                "temperature_c": latest_w.temperature_c,
                "humidity_pct": latest_w.humidity_pct,
                "wind_speed_kmh": latest_w.wind_speed_kmh,
                "wind_dir_deg": latest_w.wind_dir_deg,
                "stability_class": latest_w.stability_class,
                "timestamp": latest_w.timestamp.isoformat(),
            }
            if latest_w else None
        ),
    }


@router.get("/demo/scenario")
def demo_scenario(city_code: str = Query("DEL", description="DEL | BLR | BOM"), db: Session = Depends(get_db)):
    """Curated demo payload: the worst ward in a city with the full
    context bundle (attribution + forecast + enforcement + advisory +
    past interventions + nearby-source counts + vulnerability + weather)."""
    city = db.query(City).filter(City.code == city_code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {city_code} not found")
    worst = _curated_worst_ward(db, city)
    if not worst:
        raise HTTPException(status_code=404, detail=f"No wards for {city.code}")

    attr = _attribution_block(db, worst)
    return ok({
        "scenario": {
            "city": {"code": city.code, "name": city.name, "state": city.state},
            "ward": {
                "id": worst.id,
                "name": worst.name,
                "ward_code": worst.ward_code,
                "centroid_lat": worst.centroid_lat,
                "centroid_lon": worst.centroid_lon,
                "bbox": [
                    worst.bbox_min_lat, worst.bbox_min_lon,
                    worst.bbox_max_lat, worst.bbox_max_lon,
                ],
                "current_aqi": round(worst.current_aqi, 1),
                "aqi_category": worst.aqi_category,
                "vulnerability_index": round(worst.vulnerability_index, 1),
            },
            "headline": _scenario_headline(city, worst, attr),
        },
        "attribution": attr,
        "forecast": _forecast_block(db, worst),
        "enforcement": _enforcement_block(db, worst, attr),
        "advisory": _advisory_block(db, worst, city),
        "interventions": _interventions_block(db, worst),
        "context": _context_block(db, worst),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, city=city.code, model_version="v1")


def _scenario_headline(city: City, ward: Ward, attr: dict | None) -> str:
    """One-line story summary."""
    if not attr:
        return f"{ward.name} is at AQI {round(ward.current_aqi)} — investigation needed."
    source = attr["top_source"]
    src_label_en = source_label(source, "en")
    return (
        f"{ward.name} in {city.name} is at AQI {round(ward.current_aqi)} — "
        f"dominant source: {src_label_en} (confidence {round(attr['confidence'] * 100)}%)."
    )


@router.get("/demo/story")
def demo_story_steps(city_code: str = Query("DEL", description="DEL | BLR | BOM"), db: Session = Depends(get_db)):
    """Live 4-step guided demo script with actual data references.

    Step 1 — overview (city hotspots)
    Step 2 — attribution on the worst ward (why is it bad?)
    Step 3 — forecast (what will it be tomorrow?)
    Step 4 — enforcement (what should authorities do?)
    """
    city = db.query(City).filter(City.code == city_code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {city_code} not found")
    worst = _curated_worst_ward(db, city)
    if not worst:
        raise HTTPException(status_code=404, detail=f"No wards for {city.code}")
    attr = _attribution_block(db, worst)
    fc_rows = (
        db.query(Forecast)
        .filter(Forecast.ward_id == worst.id)
        .order_by(Forecast.horizon_hours.asc())
        .all()
    )
    fc_24h = next((r for r in fc_rows if r.horizon_hours == 24), None)
    fc_72h = next((r for r in fc_rows if r.horizon_hours == 72), None)

    return ok({
        "title": "From Signal to Intervention in 4 Steps",
        "city_code": city.code,
        "city_name": city.name,
        "steps": [
            {
                "id": 1,
                "title": f"Where is the pollution worst in {city.name}?",
                "description": (
                    f"{city.name} has {db.query(func.count(Ward.id)).filter(Ward.city_id == city.id).scalar()} "
                    f"wards. The worst is {worst.name} at AQI {round(worst.current_aqi)} "
                    f"(category: {worst.aqi_category})."
                ),
                "endpoint": f"/api/cities/{city.code}/overview",
                "key_data": {
                    "worst_ward_id": worst.id,
                    "worst_ward_name": worst.name,
                    "worst_ward_aqi": round(worst.current_aqi, 1),
                },
            },
            {
                "id": 2,
                "title": "Why is it bad here?",
                "description": (
                    f"Multi-agent attribution explains {worst.name}: "
                    f"top source is **{attr['top_source']}** with {round(attr['confidence'] * 100)}% confidence. "
                    "Each agent (spatial, satellite, traffic, land-use) contributes evidence."
                ),
                "endpoint": f"/api/wards/{worst.id}/attribution",
                "key_data": {
                    "ward_id": worst.id,
                    "top_source": attr["top_source"],
                    "confidence": attr["confidence"],
                    "source_breakdown": attr["source_breakdown"],
                },
            },
            {
                "id": 3,
                "title": "What will it be tomorrow?",
                "description": (
                    f"Forecast for {worst.name}: "
                    f"+24h predicted AQI **{round(fc_24h.predicted_aqi)}** "
                    f"(baseline {round(fc_24h.baseline_aqi)}, "
                    f"improvement {round(fc_24h.baseline_aqi - fc_24h.predicted_aqi)} AQI). "
                    f"+72h predicted **{round(fc_72h.predicted_aqi)}**."
                    if fc_24h and fc_72h else
                    f"Forecast data unavailable for {worst.name}."
                ),
                "endpoint": f"/api/wards/{worst.id}/forecast",
                "key_data": {
                    "ward_id": worst.id,
                    "horizons": [
                        {"h": int(r.horizon_hours), "predicted": round(r.predicted_aqi, 1),
                         "baseline": round(r.baseline_aqi, 1)}
                        for r in fc_rows
                    ],
                },
            },
            {
                "id": 4,
                "title": "What should authorities do?",
                "description": (
                    f"Recommended enforcement priority for {worst.name}: "
                    f"score **{round(_enforcement_priority(db, worst), 1)}** "
                    f"with top actions targeting **{attr['top_source']}**."
                ),
                "endpoint": f"/api/cities/{city.code}/enforcement/{worst.id}",
                "key_data": {
                    "ward_id": worst.id,
                    "city_code": city.code,
                },
            },
        ],
        "supporting_endpoints": {
            "advisory": f"/api/wards/{worst.id}/advisory?lang={default_language_for_city(city.code)}",
            "interventions_compare": "/api/compare/interventions",
            "city_compare": "/api/compare/cities",
            "city_advisory": f"/api/cities/{city.code}/advisory",
        },
    }, city=city.code)


def _enforcement_priority(db: Session, ward: Ward) -> float:
    attr = (
        db.query(Attribution)
        .filter(Attribution.ward_id == ward.id)
        .order_by(Attribution.computed_at.desc())
        .first()
    )
    return compute_urgency(db, ward, attribution=attr).score