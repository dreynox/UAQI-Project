"""Mumbai city builder."""

from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.data.seed.ward_geometries import MUMBAI_WARDS
from app.models.aqi import AQISation
from app.models.city import City
from app.models.construction_site import ConstructionSite
from app.models.industrial_site import IndustrialSite
from app.models.institutions import Institution
from app.models.thermal_anomaly import ThermalAnomaly
from app.models.ward import Ward


def _make_polygon(lat: float, lon: float, radius_km: float, n: int = 8):
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


def build_mumbai(session: Session, rng: random.Random):
    bbox = [18.85, 72.75, 19.30, 73.10]
    city_obj = City(
        code="BOM",
        name="Mumbai",
        state="Maharashtra",
        country="IN",
        center_lat=19.0760, center_lon=72.8777,
        bbox_min_lat=bbox[0], bbox_min_lon=bbox[1], bbox_max_lat=bbox[2], bbox_max_lon=bbox[3],
        population_millions=21.7,
        primary_language="hi",  # Mumbai is multilingual; "hi" used as practical default for advisories
    )
    session.add(city_obj); session.flush()

    wards: List[Ward] = []
    for w in MUMBAI_WARDS:
        coords, wb = _make_polygon(w["lat"], w["lon"], w["r"])
        base_vuln = 50 + rng.uniform(-10, 12)
        ward = Ward(
            city_id=city_obj.id, ward_code=w["code"], name=w["name"],
            population=rng.randint(80_000, 500_000),
            area_km2=round(math.pi * w["r"] ** 2, 2),
            centroid_lat=w["lat"], centroid_lon=w["lon"],
            geometry_geojson=json.dumps({"type": "Polygon", "coordinates": [coords]}),
            bbox_min_lat=wb["min_lat"], bbox_min_lon=wb["min_lon"],
            bbox_max_lat=wb["max_lat"], bbox_max_lon=wb["max_lon"],
            current_aqi=0.0, aqi_category="good",
            vulnerability_index=max(10.0, min(90.0, base_vuln)),
        )
        session.add(ward); wards.append(ward)
    session.flush()

    # Stations — 14
    station_wards = rng.sample(wards, k=min(14, len(wards)))
    stations = []
    for i, w in enumerate(station_wards):
        st = AQISation(
            city_id=city_obj.id, name=f"{w.name} MPCB",
            station_code=f"BOM-MPCB-{i+1:03d}",
            lat=w.centroid_lat, lon=w.centroid_lon,
            station_type="CAAQMS", ward_id=w.id,
        )
        session.add(st); stations.append(st)
    session.flush()

    # Industries — 70 (Mumbai + Thane + Navi Mumbai industrial belt)
    industrial_zones = ["M-THN", "M-NAI", "M-BEL", "M-CHE", "M-AIR", "M-MUL", "M-KAN"]
    industrial_wards = [w for w in wards if w.ward_code in industrial_zones]
    industries = []
    for i in range(70):
        anchor = rng.choice(industrial_wards) if industrial_wards else rng.choice(wards)
        industries.append(IndustrialSite(
            city_id=city_obj.id, name=f"Industrial Unit {i+1}",
            lat=anchor.centroid_lat + rng.uniform(-0.04, 0.04),
            lon=anchor.centroid_lon + rng.uniform(-0.04, 0.04),
            emission_type=rng.choice(["so2", "nox", "pm", "co", "mixed"]),
            intensity=round(rng.uniform(40, 85), 1),
            has_stack_monitor=rng.random() < 0.45,
            compliance_score=round(rng.uniform(45, 92), 1),
        ))
    session.add_all(industries); session.flush()

    # Construction — 150
    constructions = []
    for i in range(150):
        w = rng.choice(wards)
        c = ConstructionSite(
            city_id=city_obj.id, name=f"Construction Site {i+1}",
            lat=w.centroid_lat + rng.uniform(-0.03, 0.03),
            lon=w.centroid_lon + rng.uniform(-0.03, 0.03),
            intensity=round(rng.uniform(35, 90), 1),
            area_sqm=rng.uniform(500, 9000),
            is_compliant=rng.random() > 0.3,
            start_date=datetime(2024 + rng.randint(0, 2), rng.randint(1, 12), rng.randint(1, 28)),
            end_date=datetime(2025 + rng.randint(0, 2), rng.randint(1, 12), rng.randint(1, 28)),
        )
        c.end_date = c.start_date + timedelta(days=rng.randint(180, 720))
        constructions.append(c)
    session.add_all(constructions); session.flush()

    # Thermals — 40 (coastal Mumbai; lower fire risk)
    thermals = []
    base_date = datetime(2026, 6, 20)
    for i in range(40):
        ts = base_date + timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 23))
        thermals.append(ThermalAnomaly(
            city_id=city_obj.id, timestamp=ts,
            lat=city_obj.center_lat + rng.uniform(-0.2, 0.2),
            lon=city_obj.center_lon + rng.uniform(-0.2, 0.2),
            intensity_kelvin=round(rng.uniform(305, 340), 1),
            confidence=round(rng.uniform(0.4, 0.85), 2),
            source_type=rng.choice(["industrial", "biomass", "wildfire"]),
        ))
    session.add_all(thermals); session.flush()

    # Institutions — 290
    institutions = []
    institution_types = ["school", "hospital", "elderly_care", "outdoor_worker", "anganwadi", "orphanage"]
    weights = [0.50, 0.16, 0.08, 0.14, 0.08, 0.04]
    for i in range(290):
        w = rng.choice(wards)
        itype = rng.choices(institution_types, weights=weights)[0]
        cap = {"school": rng.randint(200, 1800), "hospital": rng.randint(50, 600),
               "elderly_care": rng.randint(20, 130), "outdoor_worker": rng.randint(50, 400),
               "anganwadi": rng.randint(30, 120), "orphanage": rng.randint(30, 150)}[itype]
        institutions.append(Institution(
            city_id=city_obj.id, name=f"{itype.replace('_',' ').title()} {i+1}",
            institution_type=itype,
            lat=w.centroid_lat + rng.uniform(-0.03, 0.03),
            lon=w.centroid_lon + rng.uniform(-0.03, 0.03),
            capacity=cap,
            vulnerability_weight={"school": 0.85, "hospital": 0.75, "elderly_care": 0.95,
                                  "outdoor_worker": 0.70, "anganwadi": 0.90, "orphanage": 0.80}[itype],
        ))
    session.add_all(institutions); session.flush()

    return city_obj, wards, stations, industries, constructions, thermals, institutions


def code() -> str:
    return "BOM"