"""Weather forecast generator for seeded cities.

Generates 7 days of hourly weather. June in India = pre-monsoon / monsoon onset:
warm, humid, mixed wind directions, occasional rain events.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.city import City
from app.models.weather import WeatherForecast


# City baselines for June
CITY_BASELINE: Dict[str, Dict[str, float]] = {
    "DEL": {
        "temp_day": 38.0, "temp_night": 27.0, "humidity": 55.0,
        "wind_speed": 9.0, "wind_dir": 270.0, "pressure": 1003.0,
    },
    "BLR": {
        "temp_day": 29.0, "temp_night": 20.0, "humidity": 75.0,
        "wind_speed": 13.0, "wind_dir": 240.0, "pressure": 1010.0,
    },
    "BOM": {
        "temp_day": 31.0, "temp_night": 26.0, "humidity": 85.0,
        "wind_speed": 18.0, "wind_dir": 220.0, "pressure": 1007.0,
    },
}


def _diurnal_temp(hour: int, t_day: float, t_night: float) -> float:
    """Smooth diurnal temperature curve."""
    phase = (hour - 14) / 24.0 * 2 * math.pi  # peak ~14:00
    return (t_day + t_night) / 2 + (t_day - t_night) / 2 * math.cos(phase)


def _stability_class(cloud: float, wind: float, hour: int) -> str:
    """Pasquill-Gifford-inspired stability class proxy."""
    day = 6 <= hour <= 18
    if day:
        if wind < 8 and cloud < 50:
            return "A"
        if wind < 10 and cloud < 80:
            return "B"
        if wind < 12:
            return "C"
        return "D"
    # Night
    if wind < 6 and cloud < 50:
        return "F"
    if wind < 10:
        return "E"
    return "D"


def generate_weather_for_city(
    session: Session,
    city: City,
    rng: random.Random,
    days: int = 7,
) -> int:
    """Generate hourly weather rows for the next `days` days (forecast window)."""
    base = CITY_BASELINE.get(city.code, CITY_BASELINE["DEL"])
    start = datetime(2026, 6, 25, 0, 0, 0)
    hours = days * 24
    rows: List[WeatherForecast] = []
    for i in range(hours):
        ts = start + timedelta(hours=i)
        temp = _diurnal_temp(ts.hour, base["temp_day"], base["temp_night"]) + rng.gauss(0, 1.5)
        humidity = max(20.0, min(98.0, base["humidity"] + rng.gauss(0, 6) - 5 * math.sin(ts.hour / 24 * 2 * math.pi)))
        wind_speed = max(1.0, base["wind_speed"] + rng.gauss(0, 2.5))
        wind_dir = (base["wind_dir"] + rng.gauss(0, 25)) % 360
        pressure = base["pressure"] + rng.gauss(0, 2)
        cloud = max(0.0, min(100.0, 50 + rng.gauss(0, 25)))
        stability = _stability_class(cloud, wind_speed, ts.hour)
        precip = max(0.0, rng.gauss(1.0, 3.0) if city.code == "BOM" else rng.gauss(0.4, 1.5))
        if precip < 0:
            precip = 0
        rows.append(WeatherForecast(
            city_id=city.id,
            timestamp=ts,
            temperature_c=round(temp, 1),
            humidity_pct=round(humidity, 1),
            pressure_hpa=round(pressure, 1),
            wind_speed_kmh=round(wind_speed, 1),
            wind_dir_deg=round(wind_dir, 1),
            cloud_cover_pct=round(cloud, 1),
            stability_class=stability,
            precip_mm=round(precip, 2),
        ))
    session.add_all(rows)
    return len(rows)