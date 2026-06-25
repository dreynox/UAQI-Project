"""Bengaluru city builder."""

from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.data.seed.ward_geometries import BENGALURU_WARDS
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


def build_bengaluru(session: Session, rng: random.Random):
    bbox = [12.80, 77.40, 13.20, 77.80]
    city_obj = City(
        code="BLR",
        name="Bengaluru",
        state="Karnataka",
        country="IN",
        center_lat=12.9716, center_lon=77.5946,
        bbox_min_lat=bbox[0], bbox_min_lon=bbox[1], bbox_max_lat=bbox[2], bbox_max_lon=bbox[3],
        population_millions=13.6,
        primary_language="kn",
    )
    session.add(city_obj)
    session.flush()

    wards: List[Ward] = []
    for w in BENGALURU_WARDS:
        coords, wb = _make_polygon(w["lat"], w["lon"], w["r"])
        base_vuln = 45 + rng.uniform(-8, 12)
        ward = Ward(
            city_id=city_obj.id, ward_code=w["code"], name=w["name"],
            population=rng.randint(40_000, 200_000),
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

    # Stations
    station_wards = rng.sample(wards, k=min(12, len(wards)))
    stations = []
    for i, w in enumerate(station_wards):
        st = AQISation(
            city_id=city_obj.id, name=f"{w.name} KSPCB",
            station_code=f"BLR-KSPCB-{i+1:03d}",
            lat=w.centroid_lat, lon=w.centroid_lon,
            station_type="CAAQMS", ward_id=w.id,
        )
        session.add(st); stations.append(st)
    session.flush()

    # Industries — 30 (Bengaluru is not heavily industrial)
    industries = []
    industrial_zones = ["B-PES", "B-TUM", "B-ELE", "B-WHI", "B-BEL"]
    industrial_wards = [w for w in wards if w.ward_code in industrial_zones]
    for i in range(30):
        anchor = rng.choice(industrial_wards) if industrial_wards else rng.choice(wards)
        industries.append(IndustrialSite(
            city_id=city_obj.id, name=f"Industry {i+1}",
            lat=anchor.centroid_lat + rng.uniform(-0.03, 0.03),
            lon=anchor.centroid_lon + rng.uniform(-0.03, 0.03),
            emission_type=rng.choice(["pm", "co", "mixed"]),
            intensity=round(rng.uniform(30, 70), 1),
            has_stack_monitor=rng.random() < 0.5,
            compliance_score=round(rng.uniform(60, 95), 1),
        ))
    session.add_all(industries); session.flush()

    # Construction — 220 (tech-boom = construction boom)
    constructions = []
    for i in range(220):
        w = rng.choice(wards)
        c = ConstructionSite(
            city_id=city_obj.id, name=f"Construction {i+1}",
            lat=w.centroid_lat + rng.uniform(-0.03, 0.03),
            lon=w.centroid_lon + rng.uniform(-0.03, 0.03),
            intensity=round(rng.uniform(40, 95), 1),
            area_sqm=rng.uniform(500, 10000),
            is_compliant=rng.random() > 0.25,
            start_date=datetime(2024 + rng.randint(0, 2), rng.randint(1, 12), rng.randint(1, 28)),
            end_date=datetime(2025 + rng.randint(0, 2), rng.randint(1, 12), rng.randint(1, 28)),
        )
        c.end_date = c.start_date + timedelta(days=rng.randint(180, 720))
        constructions.append(c)
    session.add_all(constructions); session.flush()

    # Thermals — 50 (low; not stubble-belt, but some biomass + industrial)
    thermals = []
    base_date = datetime(2026, 6, 20)
    for i in range(50):
        ts = base_date + timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 23))
        thermals.append(ThermalAnomaly(
            city_id=city_obj.id, timestamp=ts,
            lat=city_obj.center_lat + rng.uniform(-0.2, 0.2),
            lon=city_obj.center_lon + rng.uniform(-0.2, 0.2),
            intensity_kelvin=round(rng.uniform(305, 340), 1),
            confidence=round(rng.uniform(0.4, 0.85), 2),
            source_type=rng.choice(["biomass", "industrial", "wildfire"]),
        ))
    session.add_all(thermals); session.flush()

    # Institutions — 320
    institutions = []
    institution_types = ["school", "hospital", "elderly_care", "outdoor_worker", "anganwadi", "orphanage"]
    weights = [0.55, 0.15, 0.06, 0.13, 0.07, 0.04]
    for i in range(320):
        w = rng.choice(wards)
        itype = rng.choices(institution_types, weights=weights)[0]
        cap = {"school": rng.randint(200, 2000), "hospital": rng.randint(50, 600),
               "elderly_care": rng.randint(15, 100), "outdoor_worker": rng.randint(40, 350),
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
    return "BLR"