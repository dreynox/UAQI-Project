"""Forecast router: hyperlocal AQI forecasts."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.forecast import Forecast
from app.models.ward import Ward
from app.utils.envelope import ok

router = APIRouter()


@router.get("/wards/{ward_id}/forecast")
def ward_forecast(ward_id: int, horizons: str = "24,48,72", db: Session = Depends(get_db)):
    """Forecast for 24/48/72h horizons."""
    w = db.query(Ward).filter(Ward.id == ward_id).first()
    if not w:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    try:
        horizons_list = [int(h.strip()) for h in horizons.split(",") if h.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid horizons param")
    horizons_list = [h for h in horizons_list if h in (24, 48, 72)] or [24, 48, 72]

    rows = (
        db.query(Forecast)
        .filter(Forecast.ward_id == ward_id, Forecast.horizon_hours.in_(horizons_list))
        .all()
    )

    # Deduplicate by horizon, keeping the most recent generated_at
    by_horizon = {}
    for r in rows:
        if r.horizon_hours not in by_horizon or r.generated_at > by_horizon[r.horizon_hours].generated_at:
            by_horizon[r.horizon_hours] = r

    forecasts = []
    for h in horizons_list:
        r = by_horizon.get(h)
        if r:
            forecasts.append({
                "horizon_hours": h,
                "target_time": r.target_time.isoformat(),
                "generated_at": r.generated_at.isoformat(),
                "predicted_aqi": round(r.predicted_aqi, 1),
                "baseline_aqi": round(r.baseline_aqi, 1),
                "confidence_low": round(r.confidence_low, 1),
                "confidence_high": round(r.confidence_high, 1),
                "model_version": r.model_version,
            })

    return ok({
        "ward_id": w.id,
        "ward_name": w.name,
        "current_aqi": round(w.current_aqi, 1),
        "forecasts": forecasts,
    }, city=w.city_id)


@router.get("/wards/{ward_id}/forecast/compare")
def forecast_vs_baseline(ward_id: int, db: Session = Depends(get_db)):
    """Forecast vs persistence baseline summary (for the 'show our value' panel)."""
    w = db.query(Ward).filter(Ward.id == ward_id).first()
    if not w:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")
    rows = db.query(Forecast).filter(Forecast.ward_id == ward_id).all()
    if not rows:
        return ok({"ward_id": ward_id, "rmse_model_vs_persistence": None}, warnings=["No forecast rows"])

    # Use latest per horizon
    by_h = {}
    for r in rows:
        if r.horizon_hours not in by_h or r.generated_at > by_h[r.horizon_hours].generated_at:
            by_h[r.horizon_hours] = r

    out = []
    for h, r in by_h.items():
        improvement = round(r.baseline_aqi - r.predicted_aqi, 1)
        out.append({
            "horizon_hours": h,
            "model_prediction": round(r.predicted_aqi, 1),
            "persistence_baseline": round(r.baseline_aqi, 1),
            "model_advantage_aqi": improvement,
        })

    return ok({"ward_id": ward_id, "ward_name": w.name, "comparison": out}, city=w.city_id)