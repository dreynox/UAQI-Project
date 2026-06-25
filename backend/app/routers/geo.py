"""Geo router: GeoJSON layers for the map."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.city import City
from app.models.construction_site import ConstructionSite
from app.models.industrial_site import IndustrialSite
from app.models.institutions import Institution
from app.models.thermal_anomaly import ThermalAnomaly
from app.models.ward import Ward
from app.utils.envelope import ok

router = APIRouter()


@router.get("/cities/{code}/geo/wards")
def ward_polygons(code: str, db: Session = Depends(get_db)):
    """Ward polygons as GeoJSON FeatureCollection."""
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")
    wards = db.query(Ward).filter(Ward.city_id == city.id).all()
    features = []
    for w in wards:
        try:
            geom = json.loads(w.geometry_geojson)
        except Exception:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "id": w.id,
                "ward_code": w.ward_code,
                "name": w.name,
                "current_aqi": round(w.current_aqi, 1),
                "aqi_category": w.aqi_category,
                "vulnerability_index": round(w.vulnerability_index, 1),
                "population": w.population,
            },
            "geometry": geom,
        })
    return ok({"type": "FeatureCollection", "features": features}, city=city.code, count=len(features))


@router.get("/cities/{code}/geo/layers/{layer}")
def layer_geojson(code: str, layer: str, db: Session = Depends(get_db)):
    """Layer-based GeoJSON for toggleable overlays.

    layer: institutions | industry | construction | thermal
    """
    city = db.query(City).filter(City.code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail=f"City {code} not found")

    features = []
    if layer == "institutions":
        items = db.query(Institution).filter(Institution.city_id == city.id).all()
        for i in items:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": i.id,
                    "name": i.name,
                    "type": i.institution_type,
                    "capacity": i.capacity,
                    "vulnerability_weight": i.vulnerability_weight,
                },
                "geometry": {"type": "Point", "coordinates": [i.lon, i.lat]},
            })
    elif layer == "industry":
        items = db.query(IndustrialSite).filter(IndustrialSite.city_id == city.id).all()
        for i in items:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": i.id,
                    "name": i.name,
                    "emission_type": i.emission_type,
                    "intensity": i.intensity,
                    "compliance_score": i.compliance_score,
                    "has_stack_monitor": i.has_stack_monitor,
                },
                "geometry": {"type": "Point", "coordinates": [i.lon, i.lat]},
            })
    elif layer == "construction":
        items = db.query(ConstructionSite).filter(ConstructionSite.city_id == city.id).all()
        for i in items:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": i.id,
                    "name": i.name,
                    "intensity": i.intensity,
                    "is_compliant": i.is_compliant,
                    "area_sqm": i.area_sqm,
                },
                "geometry": {"type": "Point", "coordinates": [i.lon, i.lat]},
            })
    elif layer == "thermal":
        items = db.query(ThermalAnomaly).filter(ThermalAnomaly.city_id == city.id).limit(500).all()
        for i in items:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": i.id,
                    "intensity_kelvin": i.intensity_kelvin,
                    "confidence": i.confidence,
                    "source_type": i.source_type,
                    "timestamp": i.timestamp.isoformat(),
                },
                "geometry": {"type": "Point", "coordinates": [i.lon, i.lat]},
            })
    else:
        raise HTTPException(status_code=400, detail=f"Unknown layer: {layer}")

    return ok({"type": "FeatureCollection", "features": features}, city=city.code, layer=layer, count=len(features))