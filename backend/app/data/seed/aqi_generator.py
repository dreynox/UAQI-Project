"""AQI + pollutant time-series generator.

Generates 30 days of hourly readings per station, then aggregates to wards
(so the forecast model has features even for wards without a station).
Includes realistic diurnal cycle + weekly cycle + city-specific base levels.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.aqi import AQISation, AQITimeSeries
from app.models.ward import Ward


# City-specific baseline AQI (winter-affected; for June demo we use base)
CITY_BASELINE: Dict[str, Tuple[float, float]] = {
    "DEL": (180.0, 80.0),   # mean, std
    "BLR": (95.0, 30.0),
    "BOM": (115.0, 45.0),
}


def _aqi_from_pm25(pm25: float) -> float:
    """Simple linear AQI approx from PM2.5 (µg/m³).

    Uses CPCB breakpoints: 0-30→0-50, 30-60→50-100, 60-90→100-200, 90-150→200-300, 150+→300+.
    """
    if pm25 < 0:
        pm25 = 0
    if pm25 <= 30:
        return pm25 * (50 / 30)
    if pm25 <= 60:
        return 50 + (pm25 - 30) * (50 / 30)
    if pm25 <= 90:
        return 100 + (pm25 - 60) * (100 / 30)
    if pm25 <= 150:
        return 200 + (pm25 - 90) * (100 / 60)
    return min(500.0, 300 + (pm25 - 150) * (200 / 150))


def _category(aqi: float) -> str:
    if aqi <= 50:
        return "good"
    if aqi <= 100:
        return "satisfactory"
    if aqi <= 200:
        return "moderate"
    if aqi <= 300:
        return "poor"
    if aqi <= 400:
        return "very_poor"
    return "severe"


def _station_offset(rng: random.Random) -> float:
    return rng.uniform(-15.0, 15.0)


def _diurnal_factor(hour: int) -> float:
    h = hour % 24
    if 3 <= h <= 5:
        return 0.7
    if 6 <= h <= 10:
        return 1.15 + 0.05 * math.sin((h - 8) * math.pi / 2)
    if 11 <= h <= 16:
        return 1.0
    if 17 <= h <= 21:
        return 1.25
    return 0.95


def _weekly_factor(weekday: int) -> float:
    return 0.95 if weekday >= 5 else 1.0


def _seasonal_factor(date: datetime) -> float:
    return 0.92  # Monsoon: dust suppressed, but humidity raises secondary PM


def _generate_station_series(
    city_code: str,
    station: AQISation,
    rng: random.Random,
    hours: int = 30 * 24,
) -> List[AQITimeSeries]:
    base_mean, base_std = CITY_BASELINE.get(city_code, (100.0, 40.0))
    offset = _station_offset(rng)
    out: List[AQITimeSeries] = []
    now = datetime(2026, 6, 25, 23, 0, 0)
    start = now - timedelta(hours=hours - 1)
    for i in range(hours):
        ts = start + timedelta(hours=i)
        pm25 = (
            base_mean
            * _diurnal_factor(ts.hour)
            * _weekly_factor(ts.weekday())
            * _seasonal_factor(ts)
            + offset
            + rng.gauss(0, base_std * 0.25)
        )
        pm25 = max(5.0, pm25)
        aqi = _aqi_from_pm25(pm25)
        pm10 = pm25 * rng.uniform(1.4, 1.8)
        no2 = max(5.0, pm25 * 0.4 + rng.gauss(0, 8))
        so2 = max(2.0, pm25 * 0.15 + rng.gauss(0, 3))
        o3 = max(8.0, 60 - pm25 * 0.2 + rng.gauss(0, 12))
        co = max(0.3, pm25 * 0.02 + rng.gauss(0, 0.4))
        out.append(AQITimeSeries(
            station_id=station.id,
            ward_id=station.ward_id,
            timestamp=ts,
            aqi=round(aqi, 1),
            pm25=round(pm25, 1),
            pm10=round(pm10, 1),
            no2=round(no2, 1),
            so2=round(so2, 1),
            o3=round(o3, 1),
            co=round(co, 2),
        ))
    return out


def _aggregate_to_wards(
    session: Session,
    city,
    wards: List[Ward],
    rng: random.Random,
    hours: int = 30 * 24,
) -> List[AQITimeSeries]:
    """For wards without a station, synthesize a correlated series."""
    out: List[AQITimeSeries] = []
    city_base, _ = CITY_BASELINE.get(city.code, (100.0, 40.0))
    now = datetime(2026, 6, 25, 23, 0, 0)
    start = now - timedelta(hours=hours - 1)
    for w in wards:
        offset = rng.uniform(-25.0, 25.0)
        for i in range(hours):
            ts = start + timedelta(hours=i)
            pm25 = (
                city_base
                * _diurnal_factor(ts.hour)
                * _weekly_factor(ts.weekday())
                * _seasonal_factor(ts)
                + offset
                + rng.gauss(0, 12)
            )
            pm25 = max(5.0, pm25)
            aqi = _aqi_from_pm25(pm25)
            pm10 = pm25 * rng.uniform(1.4, 1.8)
            out.append(AQITimeSeries(
                station_id=None,
                ward_id=w.id,
                timestamp=ts,
                aqi=round(aqi, 1),
                pm25=round(pm25, 1),
                pm10=round(pm10, 1),
                no2=round(max(5.0, pm25 * 0.4 + rng.gauss(0, 6)), 1),
                so2=round(max(2.0, pm25 * 0.15 + rng.gauss(0, 2)), 1),
                o3=round(max(8.0, 60 - pm25 * 0.2 + rng.gauss(0, 8)), 1),
                co=round(max(0.3, pm25 * 0.02 + rng.gauss(0, 0.3)), 2),
            ))
    return out


def generate_aqi_series_for_city(
    session: Session,
    city,
    stations: List[AQISation],
    wards: List[Ward],
    rng: random.Random,
    days: int = 30,
) -> int:
    """Generate AQI series for all stations in a city and aggregate to wards.

    Returns total rows inserted.
    """
    hours = days * 24
    rows: List[AQITimeSeries] = []
    for st in stations:
        rows.extend(_generate_station_series(city.code, st, rng, hours=hours))

    ward_ids_with_station = {s.ward_id for s in stations if s.ward_id is not None}
    wards_without = [w for w in wards if w.id not in ward_ids_with_station]
    if wards_without:
        rows.extend(_aggregate_to_wards(session, city, wards_without, rng, hours=hours))

    session.add_all(rows)

    # Update ward.current_aqi to last reading
    if rows:
        latest_ts = max(r.timestamp for r in rows)
        for w in wards:
            w_rows = [r for r in rows if r.ward_id == w.id and r.timestamp == latest_ts]
            if w_rows:
                w.current_aqi = w_rows[0].aqi
                w.aqi_category = _category(w_rows[0].aqi)

    return len(rows)
