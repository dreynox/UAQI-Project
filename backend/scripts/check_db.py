"""Check DB row counts."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, SessionLocal
from app.models import city, ward, attribution, forecast

init_db()
db = SessionLocal()
try:
    print("Attribution rows:", db.query(attribution.Attribution).count())
    print("Forecast rows:", db.query(forecast.Forecast).count())
    print("Attribution for ward 34:", db.query(attribution.Attribution).filter(attribution.Attribution.ward_id == 34).count())
    print("Forecast for ward 34:", db.query(forecast.Forecast).filter(forecast.Forecast.ward_id == 34).count())
    a = db.query(attribution.Attribution).first()
    if a:
        print("Sample attr ward_id:", a.ward_id, "computed_at:", a.computed_at)
    f = db.query(forecast.Forecast).first()
    if f:
        print("Sample fc ward_id:", f.ward_id, "horizon:", f.horizon_hours, "gen:", f.generated_at)
finally:
    db.close()