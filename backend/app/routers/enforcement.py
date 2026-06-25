"""Enforcement router: prioritized inspector action queue."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engines.enforcement import (
    compute_urgency,
    recommended_actions_for_ward,
)
from app.engines.enforcement.impact_estimator import estimate_for_action_codes
from app.models.attribution import Attribution
from app.models.city import City
from app.models.ward import Ward
from app.utils.envelope import ok

router = APIRouter()


@router.get("/cities/{code}/enforcement/queue")
def enforcement_queue(code: str, limit: int = 10, db: Session = Depends(get_db)):
    """Top N wards prioritized for enforcement action.

    Uses the priority engine (AQI severity + vulnerability + forecast
    trend + attribution confidence) instead of naive AQI × vuln.
    """
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")

    # Pre-load latest attribution per ward in this city to avoid N+1.
    ward_ids = [w.id for w in db.query(Ward.id).filter(Ward.city_id == city.id).all()]
    latest_attr_by_ward: dict[int, Attribution] = {}
    if ward_ids:
        attrs = (
            db.query(Attribution)
            .filter(Attribution.ward_id.in_(ward_ids))
            .order_by(Attribution.ward_id, Attribution.computed_at.desc())
            .all()
        )
        for a in attrs:
            latest_attr_by_ward.setdefault(a.ward_id, a)

    wards = db.query(Ward).filter(Ward.city_id == city.id).all()

    scored = []
    for w in wards:
        attr = latest_attr_by_ward.get(w.id)
        score = compute_urgency(db, w, attribution=attr)
        scored.append((score, w, attr))

    scored.sort(key=lambda x: x[0].score, reverse=True)
    top = scored[:limit]

    out = []
    for score, w, attr in top:
        top_source = attr.top_source if attr else "mixed"
        recs = recommended_actions_for_ward(top_source, w.current_aqi)
        out.append({
            "ward_id": w.id,
            "ward_code": w.ward_code,
            "ward_name": w.name,
            "current_aqi": round(w.current_aqi, 1),
            "vulnerability_index": round(w.vulnerability_index, 1),
            "top_source": top_source,
            **score.to_dict(),
            "recommended_actions": recs,
        })

    return ok(out, city=city.code, count=len(out))


@router.get("/cities/{code}/enforcement/{ward_id}")
def ward_enforcement(code: str, ward_id: int, db: Session = Depends(get_db)):
    """Per-ward enforcement detail: actions + estimated impact."""
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")
    w = db.query(Ward).filter(Ward.id == ward_id, Ward.city_id == city.id).first()
    if not w:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found in {city.code}")

    attr = (
        db.query(Attribution)
        .filter(Attribution.ward_id == w.id)
        .order_by(Attribution.computed_at.desc())
        .first()
    )
    top_source = attr.top_source if attr else "mixed"
    confidence = attr.confidence if attr else 0.4

    recs = recommended_actions_for_ward(top_source, w.current_aqi)
    codes = [r["action_code"] for r in recs]
    impacts = estimate_for_action_codes(db, w, codes, attribution_confidence=confidence)

    # Merge impact estimates into recs.
    impact_by_code = {i["action_code"]: i for i in impacts}
    for r in recs:
        est = impact_by_code.get(r["action_code"])
        if est:
            r["estimated_aqi_delta"] = est["expected_aqi_delta"]
            r["estimation_confidence"] = est["confidence"]
            r["estimation_method"] = est["method"]

    score = compute_urgency(db, w, attribution=attr)
    return ok({
        "ward_id": w.id,
        "ward_name": w.name,
        "city_code": city.code,
        "current_aqi": round(w.current_aqi, 1),
        "vulnerability_index": round(w.vulnerability_index, 1),
        "top_source": top_source,
        "attribution_confidence": round(confidence, 3),
        **score.to_dict(),
        "recommended_actions": recs,
    }, city=city.code)
