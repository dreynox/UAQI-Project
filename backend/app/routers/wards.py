"""Wards router: list, details."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.aqi import AQITimeSeries
from app.models.city import City
from app.models.ward import Ward
from app.models.vulnerable import VulnerablePopulation
from app.models.institutions import Institution
from app.utils.envelope import ok

router = APIRouter()


@router.get("/cities/{code}/wards")
def list_wards(code: str, db: Session = Depends(get_db)):
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")
    wards = db.query(Ward).filter(Ward.city_id == city.id).order_by(Ward.name).all()
    return ok([
        {
            "id": w.id,
            "ward_code": w.ward_code,
            "name": w.name,
            "centroid_lat": w.centroid_lat,
            "centroid_lon": w.centroid_lon,
            "current_aqi": round(w.current_aqi, 1),
            "aqi_category": w.aqi_category,
            "vulnerability_index": round(w.vulnerability_index, 1),
            "population": w.population,
            "area_km2": w.area_km2,
        }
        for w in wards
    ], city=city.code, count=len(wards))


@router.get("/cities/{code}/hotspots")
def hotspots(code: str, limit: int = 10, db: Session = Depends(get_db)):
    """Top N worst wards (highest current AQI) in a city."""
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")
    wards = (
        db.query(Ward)
        .filter(Ward.city_id == city.id)
        .order_by(desc(Ward.current_aqi))
        .limit(limit)
        .all()
    )
    return ok([
        {
            "id": w.id,
            "ward_code": w.ward_code,
            "name": w.name,
            "centroid_lat": w.centroid_lat,
            "centroid_lon": w.centroid_lon,
            "current_aqi": round(w.current_aqi, 1),
            "aqi_category": w.aqi_category,
            "vulnerability_index": round(w.vulnerability_index, 1),
            "population": w.population,
        }
        for w in wards
    ], city=city.code, limit=limit)


@router.get("/wards/{ward_id}")
def ward_detail(ward_id: int, db: Session = Depends(get_db)):
    w = db.query(Ward).filter(Ward.id == ward_id).first()
    if not w:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")
    city = db.query(City).filter(City.id == w.city_id).first()

    # Last 48h series for sparkline
    from datetime import datetime, timedelta
    cutoff = datetime(2026, 6, 23, 23, 0, 0)
    series = (
        db.query(AQITimeSeries)
        .filter(AQITimeSeries.ward_id == ward_id, AQITimeSeries.timestamp >= cutoff)
        .order_by(AQITimeSeries.timestamp)
        .all()
    )

    # Vulnerability
    vuln = db.query(VulnerablePopulation).filter(VulnerablePopulation.ward_id == ward_id).first()

    # Nearby institutions (within ward bbox only as proxy)
    insts = (
        db.query(Institution)
        .filter(
            Institution.city_id == city.id,
            Institution.lat >= w.bbox_min_lat,
            Institution.lat <= w.bbox_max_lat,
            Institution.lon >= w.bbox_min_lon,
            Institution.lon <= w.bbox_max_lon,
        )
        .limit(50)
        .all()
    )

    return ok({
        "id": w.id,
        "ward_code": w.ward_code,
        "name": w.name,
        "city_code": city.code,
        "city_name": city.name,
        "centroid_lat": w.centroid_lat,
        "centroid_lon": w.centroid_lon,
        "bbox": [w.bbox_min_lat, w.bbox_min_lon, w.bbox_max_lat, w.bbox_max_lon],
        "population": w.population,
        "area_km2": w.area_km2,
        "current_aqi": round(w.current_aqi, 1),
        "aqi_category": w.aqi_category,
        "vulnerability_index": round(w.vulnerability_index, 1),
        "aqi_series_48h": [
            {"timestamp": s.timestamp.isoformat(), "aqi": round(s.aqi, 1), "pm25": round(s.pm25, 1)}
            for s in series
        ],
        "vulnerable_population": {
            "children_under_5": vuln.children_under_5 if vuln else 0,
            "elderly_65_plus": vuln.elderly_65_plus if vuln else 0,
            "outdoor_workers": vuln.outdoor_workers if vuln else 0,
            "asthma_prev_pct": vuln.asthma_prev_pct if vuln else 0,
            "pregnant_women": vuln.pregnant_women if vuln else 0,
            "vulnerability_index": vuln.vulnerability_index if vuln else 0,
        } if vuln else None,
        "nearby_institutions_count": len(insts),
        "nearby_institutions_by_type": _count_by_type(insts),
    }, city=city.code)


def _count_by_type(insts):
    from collections import Counter
    return dict(Counter(i.institution_type for i in insts))