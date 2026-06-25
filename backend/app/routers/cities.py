"""Cities router: list cities, city overview dashboard data."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.aqi import AQITimeSeries
from app.models.city import City
from app.models.ward import Ward
from app.models.weather import WeatherForecast
from app.models.institutions import Institution
from app.models.construction_site import ConstructionSite
from app.models.industrial_site import IndustrialSite
from app.models.thermal_anomaly import ThermalAnomaly
from app.models.vulnerable import VulnerablePopulation
from app.utils.envelope import ok

router = APIRouter()


@router.get("/cities")
def list_cities(db: Session = Depends(get_db)):
    """List all seeded cities with at-a-glance summary."""
    cities = db.query(City).order_by(City.code).all()
    out = []
    for c in cities:
        wards_count = db.query(func.count(Ward.id)).filter(Ward.city_id == c.id).scalar() or 0
        latest = (
            db.query(AQITimeSeries)
            .filter(AQITimeSeries.ward_id.in_(
                db.query(Ward.id).filter(Ward.city_id == c.id)
            ))
            .order_by(AQITimeSeries.timestamp.desc())
            .first()
        )
        mean_aqi = (
            db.query(func.avg(Ward.current_aqi))
            .filter(Ward.city_id == c.id)
            .scalar()
        )
        out.append({
            "code": c.code,
            "name": c.name,
            "state": c.state,
            "country": c.country,
            "center_lat": c.center_lat,
            "center_lon": c.center_lon,
            "bbox": [c.bbox_min_lat, c.bbox_min_lon, c.bbox_max_lat, c.bbox_max_lon],
            "population_millions": c.population_millions,
            "primary_language": c.primary_language,
            "wards_count": int(wards_count),
            "mean_aqi": round(float(mean_aqi), 1) if mean_aqi else None,
            "latest_reading_at": latest.timestamp.isoformat() if latest else None,
        })
    return ok(out, model_version="v1")


@router.get("/cities/{code}")
def get_city(code: str, db: Session = Depends(get_db)):
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")
    return ok({
        "code": city.code,
        "name": city.name,
        "state": city.state,
        "country": city.country,
        "center_lat": city.center_lat,
        "center_lon": city.center_lon,
        "bbox": [city.bbox_min_lat, city.bbox_min_lon, city.bbox_max_lat, city.bbox_max_lon],
        "population_millions": city.population_millions,
        "primary_language": city.primary_language,
    })


@router.get("/cities/{code}/overview")
def city_overview(code: str, db: Session = Depends(get_db)):
    """Full city dashboard payload: hotspots, top recommendation, KPIs."""
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")

    wards = db.query(Ward).filter(Ward.city_id == city.id).all()
    if not wards:
        return ok({"city": city.code, "hotspots": [], "kpis": {}},
                  warnings=["No wards for this city"])

    # KPIs
    aqis = [w.current_aqi for w in wards if w.current_aqi > 0]
    aqis_sorted = sorted(aqis, reverse=True)
    top10_mean = round(sum(aqis_sorted[:10]) / max(1, min(10, len(aqis_sorted))), 1)
    mean_aqi = round(sum(aqis) / max(1, len(aqis)), 1)

    # Hotspots: top 5 worst wards
    hotspots = sorted(wards, key=lambda w: -w.current_aqi)[:5]

    # Counts
    inst_count = db.query(func.count(Institution.id)).filter(Institution.city_id == city.id).scalar() or 0
    const_count = db.query(func.count(ConstructionSite.id)).filter(ConstructionSite.city_id == city.id).scalar() or 0
    ind_count = db.query(func.count(IndustrialSite.id)).filter(IndustrialSite.city_id == city.id).scalar() or 0
    ta_count = db.query(func.count(ThermalAnomaly.id)).filter(ThermalAnomaly.city_id == city.id).scalar() or 0

    # Latest weather
    latest_w = db.query(WeatherForecast).filter(
        WeatherForecast.city_id == city.id
    ).order_by(WeatherForecast.timestamp.desc()).first()

    return ok({
        "city": {
            "code": city.code,
            "name": city.name,
            "center_lat": city.center_lat,
            "center_lon": city.center_lon,
            "population_millions": city.population_millions,
            "primary_language": city.primary_language,
        },
        "kpis": {
            "mean_aqi": mean_aqi,
            "top10_mean_aqi": top10_mean,
            "max_aqi": max(aqis) if aqis else 0,
            "min_aqi": min(aqis) if aqis else 0,
            "wards_count": len(wards),
            "institutions_count": int(inst_count),
            "construction_sites_count": int(const_count),
            "industrial_sites_count": int(ind_count),
            "thermal_anomalies_count": int(ta_count),
        },
        "hotspots": [
            {
                "ward_id": w.id,
                "ward_code": w.ward_code,
                "ward_name": w.name,
                "centroid_lat": w.centroid_lat,
                "centroid_lon": w.centroid_lon,
                "current_aqi": round(w.current_aqi, 1),
                "aqi_category": w.aqi_category,
                "vulnerability_index": round(w.vulnerability_index, 1),
                "population": w.population,
            }
            for w in hotspots
        ],
        "weather": {
            "temperature_c": latest_w.temperature_c if latest_w else None,
            "humidity_pct": latest_w.humidity_pct if latest_w else None,
            "wind_speed_kmh": latest_w.wind_speed_kmh if latest_w else None,
            "wind_dir_deg": latest_w.wind_dir_deg if latest_w else None,
            "stability_class": latest_w.stability_class if latest_w else None,
            "timestamp": latest_w.timestamp.isoformat() if latest_w else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, city=city.code)