"""Advisory router: multilingual citizen advisories."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engines.advisory import (
    CITY_DEFAULT_LANGUAGE,
    default_language_for,
    generate_advisory,
    normalize,
)
from app.models.advisory import Advisory
from app.models.city import City
from app.models.ward import Ward
from app.utils.envelope import ok

router = APIRouter()


@router.get("/wards/{ward_id}/advisory")
def ward_advisory(
    ward_id: int,
    lang: str = Query("en", description="en | hi | kn | ta"),
    db: Session = Depends(get_db),
):
    """Generate (or fetch cached) advisory for a ward in a language.

    If a fresh advisory (valid_until >= now) exists for (ward, language),
    return it. Otherwise generate + persist a new one via the engine.
    """
    from datetime import datetime

    w = db.query(Ward).filter(Ward.id == ward_id).first()
    if not w:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    city = db.query(City).filter(City.id == w.city_id).first()
    lang_norm = normalize(lang)

    now = datetime.utcnow()
    a = (
        db.query(Advisory)
        .filter(
            Advisory.ward_id == ward_id,
            Advisory.language == lang_norm,
            Advisory.valid_until >= now,
        )
        .order_by(Advisory.created_at.desc())
        .first()
    )
    if not a:
        # Generate fresh + persist (engine-driven, multilingual).
        a = generate_advisory(db, w, city.code if city else "?", lang_norm, persist=True)
        db.commit()

    return ok({
        "ward_id": w.id,
        "ward_name": w.name,
        "city_code": city.code if city else None,
        "language": a.language,
        "severity": a.severity,
        "audience": a.audience,
        "title": a.title,
        "body": a.body,
        "valid_from": a.valid_from.isoformat(),
        "valid_until": a.valid_until.isoformat(),
    }, city=city.code if city else None)


@router.get("/cities/{code}/advisory")
def city_default_advisory(code: str, db: Session = Depends(get_db)):
    """Return the default advisory language + a sample ward advisory."""
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")
    default_lang = default_language_for(city.code)
    # Use the worst ward in the city.
    worst = (
        db.query(Ward)
        .filter(Ward.city_id == city.id)
        .order_by(Ward.current_aqi.desc())
        .first()
    )
    sample = None
    if worst:
        sample_advisory = generate_advisory(
            db, worst, city.code, default_lang, persist=False
        )
        sample = {
            "ward_id": worst.id,
            "ward_name": worst.name,
            "title": sample_advisory.title,
            "body": sample_advisory.body,
            "severity": sample_advisory.severity,
            "audience": sample_advisory.audience,
        }
    return ok({
        "city_code": city.code,
        "city_name": city.name,
        "default_language": default_lang,
        "supported_languages": ["en", CITY_DEFAULT_LANGUAGE.get(city.code, "en")],
        "sample_advisory": sample,
    }, city=city.code)
