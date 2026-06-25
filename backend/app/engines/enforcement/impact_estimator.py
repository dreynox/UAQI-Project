"""Impact estimation: given an action + a ward, predict the AQI delta.

Combines:
- The action's max_expected_delta (ceiling).
- Attribution confidence (high confidence → action hits the right target).
- AQI severity multiplier (extreme AQI → bigger absolute reductions).
- Past-intervention empirical mean delta for that city+action (when available).
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.engines.enforcement.action_library import ACTION_TYPES, ActionDef
from app.models.city import City
from app.models.intervention import Intervention


def _empirical_mean_delta(
    session: Session,
    city_id: int,
    action_code: str,
) -> Optional[float]:
    rows = (
        session.query(Intervention)
        .filter(
            Intervention.city_id == city_id,
            Intervention.action_type == action_code,
            Intervention.measured_aqi_delta.isnot(None),
        )
        .all()
    )
    if len(rows) < 3:
        return None
    deltas = [r.measured_aqi_delta for r in rows if r.measured_aqi_delta is not None]
    return sum(deltas) / len(deltas) if deltas else None


def estimate_aqi_delta(
    session: Session,
    ward,
    action: ActionDef,
    *,
    attribution_confidence: float = 0.5,
) -> dict:
    """Estimate the AQI delta from running `action` on `ward`.

    Returns a dict with `expected_delta`, `confidence`, and `method`.
    """
    city: Optional[City] = ward.city if hasattr(ward, "city") else None
    empirical = (
        _empirical_mean_delta(session, city.id, action.code) if city else None
    )

    ceiling = action.max_expected_delta
    aqi_factor = max(0.4, min(1.0, ward.current_aqi / 400.0))
    target_match = 1.0 if not action.target_sources else attribution_confidence

    expected = ceiling * aqi_factor * (0.5 + 0.5 * target_match)

    method = "modeled"
    if empirical is not None and abs(empirical) < abs(ceiling) * 1.3:
        # Use empirical as anchor, blend with model.
        expected = 0.6 * empirical + 0.4 * expected
        method = "modeled+historical"

    return {
        "action_code": action.code,
        "expected_aqi_delta": round(expected, 1),
        "confidence": round(min(1.0, 0.4 + target_match * 0.5 + (0.2 if empirical else 0.0)), 2),
        "method": method,
    }


def estimate_for_action_codes(
    session: Session,
    ward,
    codes: list,
    attribution_confidence: float = 0.5,
) -> list:
    return [
        estimate_aqi_delta(session, ward, ACTION_TYPES[c], attribution_confidence=attribution_confidence)
        for c in codes
        if c in ACTION_TYPES
    ]
