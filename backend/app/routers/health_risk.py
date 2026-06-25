"""Health risk router: vulnerability overlay."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.city import City
from app.models.institutions import Institution
from app.models.ward import Ward
from app.utils.envelope import ok

router = APIRouter()


@router.get("/cities/{code}/health/overlay")
def health_overlay(code: str, db: Session = Depends(get_db)):
    """Per-ward vulnerability + nearby institutions count."""
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")
    wards = db.query(Ward).filter(Ward.city_id == city.id).all()
    out = []
    for w in wards:
        nearby_count = db.query(func.count(Institution.id)).filter(
            Institution.city_id == city.id,
            Institution.lat >= w.bbox_min_lat,
            Institution.lat <= w.bbox_max_lat,
            Institution.lon >= w.bbox_min_lon,
            Institution.lon <= w.bbox_max_lon,
        ).scalar() or 0
        out.append({
            "ward_id": w.id,
            "ward_code": w.ward_code,
            "ward_name": w.name,
            "centroid_lat": w.centroid_lat,
            "centroid_lon": w.centroid_lon,
            "current_aqi": round(w.current_aqi, 1),
            "vulnerability_index": round(w.vulnerability_index, 1),
            "population": w.population,
            "nearby_institutions": int(nearby_count),
        })
    return ok(out, city=city.code, count=len(out))