"""Main seed orchestrator.

Idempotent: re-running drops + recreates demo data so the demo is reproducible.

Seeded for: Delhi, Bengaluru, Mumbai.
"""

from __future__ import annotations

import logging
import random

from sqlalchemy import delete

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.data.seed.advisories_generator import seed_advisories
from app.data.seed.aqi_generator import generate_aqi_series_for_city
from app.data.seed.bengaluru import build_bengaluru
from app.data.seed.delhi import build_delhi
from app.data.seed.interventions_generator import seed_interventions
from app.data.seed.mumbai import build_mumbai
from app.data.seed.weather_generator import generate_weather_for_city
from app.models.advisory import Advisory
from app.models.aqi import AQISation, AQITimeSeries
from app.models.attribution import Attribution
from app.models.city import City
from app.models.construction_site import ConstructionSite
from app.models.forecast import Forecast
from app.models.industrial_site import IndustrialSite
from app.models.institutions import Institution
from app.models.intervention import Intervention
from app.models.thermal_anomaly import ThermalAnomaly
from app.models.traffic import TrafficDensity
from app.models.vulnerable import VulnerablePopulation
from app.models.ward import Ward
from app.models.weather import WeatherForecast

log = logging.getLogger("uaqi.seed")


def _wipe_all(session) -> None:
    """Wipe all rows in dependency-correct order."""
    tables = [
        Advisory,
        Attribution,
        Forecast,
        Intervention,
        VulnerablePopulation,
        TrafficDensity,
        AQITimeSeries,
        AQISation,
        WeatherForecast,
        ThermalAnomaly,
        ConstructionSite,
        IndustrialSite,
        Institution,
        Ward,
        City,
    ]
    for tbl in tables:
        session.execute(delete(tbl))
    session.commit()


def _seed_city(session, builder, rng: random.Random) -> int:
    """Seed one city. Returns number of wards inserted."""
    log.info("Seeding city: %s", builder.__name__)
    city_obj, wards, stations, industries, constructions, thermals, insts = builder(session, rng)
    log.info(
        "  wards=%d stations=%d industries=%d constructions=%d thermals=%d institutions=%d",
        len(wards), len(stations), len(industries),
        len(constructions), len(thermals), len(insts),
    )

    aqi_count = generate_aqi_series_for_city(session, city_obj, stations, wards, rng)
    log.info("  aqi_readings=%d", aqi_count)

    wf_count = generate_weather_for_city(session, city_obj, rng)
    log.info("  weather_rows=%d", wf_count)

    return len(wards)


def run_seed() -> None:
    """Wipe + seed all demo data."""
    settings = get_settings()
    rng = random.Random(settings.seed_random_seed)

    session = SessionLocal()
    try:
        log.info("Wiping existing demo data...")
        _wipe_all(session)

        _seed_city(session, build_delhi, rng)
        _seed_city(session, build_bengaluru, rng)
        _seed_city(session, build_mumbai, rng)

        # Past interventions: ~160 historical rows across all cities.
        intervention_count = seed_interventions(session, rng)
        log.info("interventions=%d", intervention_count)

        # Multilingual advisories: one per ward × city-language pair.
        advisory_count = seed_advisories(session)
        log.info("advisories=%d", advisory_count)

        session.commit()
        log.info("All cities seeded successfully.")
    except Exception:
        session.rollback()
        log.exception("Seed failed")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    run_seed()