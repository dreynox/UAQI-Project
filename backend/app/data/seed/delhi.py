"""Delhi city builder."""

from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.data.seed.ward_geometries import DELHI_WARDS
from app.models.aqi import AQISation
from app.models.city import City
from app.models.construction_site import ConstructionSite
from app.models.industrial_site import IndustrialSite
from app.models.institutions import Institution
from app.models.thermal_anomaly import ThermalAnomaly
from app.models.ward import Ward


def _make_polygon(lat: float, lon: float, radius_km: float, n: int = 8):
    """Return (coordinates, bbox) for a simple n-gon polygon around (lat, lon)."""
    coords = []
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.1, math.cos(math.radians(lat))))
    for i in range(n):
        angle = 2 * math.pi * i / n
        coords.append([lon + dlon * math.cos(angle), lat + dlat * math.sin(angle)])
    coords.append(coords[0])
    lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
    return coords, {
        "min_lat": min(lats), "min_lon": min(lons),
        "max_lat": max(lats), "max_lon": max(lons),
    }


def build_delhi(session: Session, rng: random.Random):
    """Build Delhi (DEL) — primary demo city with stubble-burning story."""
    bbox = [28.40, 76.80, 28.90, 77.60]
    city_obj = City(
        code="DEL",
        name="Delhi NCR",
        state="Delhi / UP / Haryana",
        country="IN",
        center_lat=28.6139, center_lon=77.2090,
        bbox_min_lat=bbox[0], bbox_min_lon=bbox[1], bbox_max_lat=bbox[2], bbox_max_lon=bbox[3],
        population_millions=32.0,
        primary_language="hi",
    )
    session.add(city_obj); session.flush()

    wards: List[Ward] = []
    for w in DELHI_WARDS:
        coords, wb = _make_polygon(w["lat"], w["lon"], w["r"])
        base_vuln = 50 + (5 if any(k in w["name"] for k in ["Shahdara", "Nand Nagri", "Sadar", "Narela"]) else 0)
        base_vuln += rng.uniform(-10, 10)
        ward = Ward(
            city_id=city_obj.id, ward_code=w["code"], name=w["name"],
            population=rng.randint(60_000, 350_000),
            area_km2=round(math.pi * w["r"] ** 2, 2),
            centroid_lat=w["lat"], centroid_lon=w["lon"],
            geometry_geojson=json.dumps({"type": "Polygon", "coordinates": [coords]}),
            bbox_min_lat=wb["min_lat"], bbox_min_lon=wb["min_lon"],
            bbox_max_lat=wb["max_lat"], bbox_max_lon=wb["max_lon"],
            current_aqi=0.0, aqi_category="good",
            vulnerability_index=max(10.0, min(95.0, base_vuln)),
        )
        session.add(ward); wards.append(ward)
    session.flush()

    # Stations — 15 across NCR
    station_wards = rng.sample(wards, k=min(15, len(wards)))
    stations: List[AQISation] = []
    for i, w in enumerate(station_wards):
        st = AQISation(
            city_id=city_obj.id, name=f"{w.name} CAAQMS",
            station_code=f"DEL-CAAQMS-{i+1:03d}",
            lat=w.centroid_lat, lon=w.centroid_lon,
            station_type="CAAQMS", ward_id=w.id,
        )
        session.add(st); stations.append(st)
    session.flush()

    # Industries — 60 (heavy in Ghaziabad, Noida, Gurugram, Okhla)
    industrial_zones = ["D-GHA", "D-NOI", "D-NO2", "D-GUR", "D-GU2", "D-OKH", "D-FAR", "D-IND"]
    industrial_wards = [w for w in wards if w.ward_code in industrial_zones]
    industries: List[IndustrialSite] = []
    for i in range(60):
        anchor = rng.choice(industrial_wards) if industrial_wards else rng.choice(wards)
        industries.append(IndustrialSite(
            city_id=city_obj.id, name=f"Industrial Unit {i+1}",
            lat=anchor.centroid_lat + rng.uniform(-0.04, 0.04),
            lon=anchor.centroid_lon + rng.uniform(-0.04, 0.04),
            emission_type=rng.choice(["so2", "nox", "pm", "co", "mixed"]),
            intensity=round(rng.uniform(40, 90), 1),
            has_stack_monitor=rng.random() < 0.4,
            compliance_score=round(rng.uniform(40, 95), 1),
        ))
    session.add_all(industries); session.flush()

    # Construction — 180
    constructions: List[ConstructionSite] = []
    for i in range(180):
        w = rng.choice(wards)
        start = datetime(2024 + rng.randint(0, 2), rng.randint(1, 12), rng.randint(1, 28))
        c = ConstructionSite(
            city_id=city_obj.id, name=f"Construction Site {i+1}",
            lat=w.centroid_lat + rng.uniform(-0.03, 0.03),
            lon=w.centroid_lon + rng.uniform(-0.03, 0.03),
            intensity=round(rng.uniform(30, 95), 1),
            area_sqm=rng.uniform(500, 8000),
            is_compliant=rng.random() > 0.3,
            start_date=start,
            end_date=start + timedelta(days=rng.randint(180, 720)),
        )
        constructions.append(c)
    session.add_all(constructions); session.flush()

    # Thermal anomalies — 300 (heavy stubble cluster downwind)
    thermals: List[ThermalAnomaly] = []
    base_date = datetime(2026, 6, 20)
    for i in range(280):
        dlat = rng.uniform(0.3, 1.2)
        dlon = rng.uniform(-1.2, -0.4)
        ts = base_date + timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 23))
        thermals.append(ThermalAnomaly(
            city_id=city_obj.id, timestamp=ts,
            lat=city_obj.center_lat + dlat,
            lon=city_obj.center_lon + dlon,
            intensity_kelvin=round(rng.uniform(310, 360), 1),
            confidence=round(rng.uniform(0.5, 0.95), 2),
            source_type=rng.choice(["biomass", "biomass", "biomass", "industrial", "wildfire"]),
        ))
    for i in range(20):
        w = rng.choice(industrial_wards) if industrial_wards else rng.choice(wards)
        ts = base_date + timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 23))
        thermals.append(ThermalAnomaly(
            city_id=city_obj.id, timestamp=ts,
            lat=w.centroid_lat + rng.uniform(-0.05, 0.05),
            lon=w.centroid_lon + rng.uniform(-0.05, 0.05),
            intensity_kelvin=round(rng.uniform(305, 340), 1),
            confidence=round(rng.uniform(0.6, 0.9), 2),
            source_type="industrial",
        ))
    session.add_all(thermals); session.flush()

    # Institutions — 280
    institutions: List[Institution] = []
    institution_types = ["school", "hospital", "elderly_care", "outdoor_worker", "anganwadi", "orphanage"]
    weights = [0.50, 0.15, 0.08, 0.15, 0.08, 0.04]
    vuln_map = {"school": 0.85, "hospital": 0.75, "elderly_care": 0.95,
                "outdoor_worker": 0.70, "anganwadi": 0.90, "orphanage": 0.80}
    cap_map = {
        "school": (200, 1500), "hospital": (50, 500), "elderly_care": (20, 120),
        "outdoor_worker": (50, 400), "anganwadi": (30, 100), "orphanage": (30, 150),
    }
    for i in range(280):
        w = rng.choice(wards)
        itype = rng.choices(institution_types, weights=weights)[0]
        lo, hi = cap_map[itype]
        institutions.append(Institution(
            city_id=city_obj.id, name=f"{itype.replace('_',' ').title()} {i+1}",
            institution_type=itype,
            lat=w.centroid_lat + rng.uniform(-0.03, 0.03),
            lon=w.centroid_lon + rng.uniform(-0.03, 0.03),
            capacity=rng.randint(lo, hi),
            vulnerability_weight=vuln_map[itype],
        ))
    session.add_all(institutions); session.flush()

    return city_obj, wards, stations, industries, constructions, thermals, institutions


def code() -> str:
    return "DEL"