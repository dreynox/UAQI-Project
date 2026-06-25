"""Test forecast inference for a single ward."""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, SessionLocal
from app.engines.forecast.model import forecast_ward, persist_forecast_rows
from app.models.city import City
from app.models.ward import Ward
from sqlalchemy import desc

logging.basicConfig(level=logging.INFO)

init_db()
db = SessionLocal()
try:
    delhi = db.query(City).filter(City.code == "DEL").first()
    worst = db.query(Ward).filter(Ward.city_id == delhi.id).order_by(desc(Ward.current_aqi)).first()
    print(f"Forecasting for: {worst.name} (current AQI={worst.current_aqi:.1f})")
    rows = forecast_ward(db, worst)
    for r in rows:
        print(f"  +{r.horizon_hours}h: predicted={r.predicted_aqi:.1f} baseline={r.baseline_aqi:.1f} band=[{r.confidence_low:.1f}, {r.confidence_high:.1f}]")
    persist_forecast_rows(db, rows)
    db.commit()
    print(f"Persisted {len(rows)} forecast rows")
finally:
    db.close()
