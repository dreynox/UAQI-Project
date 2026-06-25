"""Seed ~160 historical interventions across Delhi, Bengaluru, Mumbai.

Realistic-ish spread of action types per city:
- DEL: heavy stubble-burning → public_advisory, waste_burning, odd_even, traffic_diversion
- BLR: construction boom → construction_shutdown, dust_control, inspection
- BOM: industrial belt → industrial_audit, inspection, traffic_diversion

Each row has a `measured_aqi_delta` (negative = improvement) anchored to
realistic effect sizes per action type, with ±30% jitter.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.attribution import Attribution
from app.models.intervention import Intervention
from app.models.ward import Ward

log = logging.getLogger("uaqi.seed.interventions")


# Action → expected AQI delta (mean, jitter) per the enforcement action library.
ACTION_DELTA_CENTERS = {
    "inspection": -8.0,
    "dust_control": -18.0,
    "traffic_diversion": -14.0,
    "waste_burning": -22.0,
    "industrial_audit": -25.0,
    "public_advisory": -3.0,
    "odd_even": -22.0,
    "construction_shutdown": -30.0,
}
ACTION_DELTA_JITTER = 0.3  # ±30%


# City → (action_weights, total_count).  Action weights are relative probabilities.
CITY_INTERVENTIONS = {
    "DEL": (
        {
            "public_advisory": 0.18,
            "odd_even": 0.16,
            "traffic_diversion": 0.14,
            "waste_burning": 0.16,
            "dust_control": 0.10,
            "inspection": 0.14,
            "industrial_audit": 0.06,
            "construction_shutdown": 0.06,
        },
        60,
    ),
    "BLR": (
        {
            "construction_shutdown": 0.22,
            "dust_control": 0.20,
            "inspection": 0.18,
            "traffic_diversion": 0.12,
            "public_advisory": 0.12,
            "odd_even": 0.08,
            "industrial_audit": 0.04,
            "waste_burning": 0.04,
        },
        45,
    ),
    "BOM": (
        {
            "industrial_audit": 0.22,
            "inspection": 0.20,
            "traffic_diversion": 0.18,
            "odd_even": 0.10,
            "waste_burning": 0.08,
            "public_advisory": 0.10,
            "construction_shutdown": 0.06,
            "dust_control": 0.06,
        },
        55,
    ),
}


STATUSES = ["completed", "completed", "completed", "completed", "active", "failed"]


def _sample_delta(rng: random.Random, action: str) -> float:
    center = ACTION_DELTA_CENTERS[action]
    # Jitter ±30% but keep negative (improvement).
    jitter = 1.0 + rng.uniform(-ACTION_DELTA_JITTER, ACTION_DELTA_JITTER)
    delta = center * jitter
    # Add tiny noise so it's not too smooth.
    delta += rng.uniform(-1.5, 1.5)
    # Round to 1 decimal, clamp max improvement at -50 AQI.
    return round(max(-50.0, delta), 1)


def _weighted_action(rng: random.Random, weights: dict) -> str:
    actions = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(actions, weights=probs, k=1)[0]


def _build_aqi_weighted_pool(wards: List[Ward]) -> List[float]:
    """Build ward-sampling weights biased toward high-AQI wards.

    Weight = (aqi / 100) ** 2.0 so the worst-AQI wards are 5-6x more
    likely to receive interventions than the median ward. Combined with
    the top-3 force-inject in seed_interventions, the demo's worst ward
    always has visible intervention history.
    """
    weights = []
    for w in wards:
        aqi = max(50.0, w.current_aqi)
        weights.append((aqi / 100.0) ** 2.0)
    return weights


def _make_intervention(
    ward: Ward,
    action: str,
    status: str,
    now: datetime,
    offset_hours: int,
    rng: random.Random,
) -> Intervention:
    started = now - timedelta(hours=offset_hours)
    duration_h = rng.randint(4, 48)
    ended = started + timedelta(hours=duration_h) if status != "active" else None
    if status == "active":
        measured = None
    elif status == "failed":
        measured = round(rng.uniform(-3.0, 5.0), 1)
    else:
        measured = _sample_delta(rng, action)
    return Intervention(
        city_id=ward.city_id,
        ward_id=ward.id,
        action_type=action,
        status=status,
        started_at=started,
        ended_at=ended,
        measured_aqi_delta=measured,
        notes=_notes_for(action, status, rng),
    )


def seed_interventions(session: Session, rng: random.Random) -> int:
    """Insert historical interventions for all cities.

    Returns number of rows inserted. Replaces any pre-existing rows.
    """
    from app.models.city import City

    total = 0
    for city_code, (weights, count) in CITY_INTERVENTIONS.items():
        city = session.query(City).filter(City.code == city_code).first()
        if not city:
            log.warning("City %s not found; skipping interventions", city_code)
            continue
        wards: List[Ward] = (
            session.query(Ward).filter(Ward.city_id == city.id).all()
        )
        if not wards:
            log.warning("No wards found for %s; skipping interventions", city_code)
            continue

        rows: List[Intervention] = []
        # Spread over the last 28 days, anchored at the demo "now".
        now = datetime(2026, 6, 25, 23, 0, 0)
        # Sort wards by AQI desc, then build a strong bias so the top-5
        # wards collectively get ~40% of all interventions and the worst
        # ward is guaranteed to receive at least 2-3.
        wards_by_aqi = sorted(wards, key=lambda w: -w.current_aqi)
        ward_weights = _build_aqi_weighted_pool(wards)
        # Guarantee the top 3 wards each get a minimum share by force-
        # injecting early interventions for them before the random loop.
        for i, w in enumerate(wards_by_aqi[:3]):
            for _ in range(3 - i):  # worst=3, 2nd=2, 3rd=1 guaranteed
                action = _weighted_action(rng, weights)
                offset_hours = rng.randint(4, 28 * 24)
                rows.append(_make_intervention(w, action, "completed", now, offset_hours, rng))
        for i in range(count):
            ward = rng.choices(wards, weights=ward_weights, k=1)[0]
            action = _weighted_action(rng, weights)
            # Start time: random within last 28 days.
            offset_hours = rng.randint(4, 28 * 24)
            status = rng.choice(STATUSES)
            rows.append(_make_intervention(ward, action, status, now, offset_hours, rng))
        session.add_all(rows)
        total += len(rows)
        log.info("  %s: %d interventions", city_code, len(rows))
    return total


def _notes_for(action: str, status: str, rng: random.Random) -> str:
    if status == "active":
        return f"{action.replace('_', ' ').title()} ongoing."
    if status == "failed":
        return f"{action.replace('_', ' ').title()} halted early due to non-compliance."
    return f"{action.replace('_', ' ').title()} completed; {rng.choice(['CPCB', 'DPCC', 'KSPCB', 'MPCB'])}-logged."
