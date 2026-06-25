"""Populate attribution + forecast rows for all wards in all cities."""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, SessionLocal
from app.engines.attribution import compute_attribution, persist_attribution
from app.engines.forecast.model import forecast_ward, persist_forecast_rows
from app.models.city import City
from app.models.ward import Ward

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("populate")

init_db()
db = SessionLocal()
try:
    cities = db.query(City).all()
    total_attr = 0
    total_fc = 0
    for c in cities:
        wards = db.query(Ward).filter(Ward.city_id == c.id).all()
        log.info("Processing city %s: %d wards", c.code, len(wards))
        for w in wards:
            r = compute_attribution(db, w, c)
            persist_attribution(db, w, r)
            total_attr += 1

            frows = forecast_ward(db, w)
            persist_forecast_rows(db, frows)
            total_fc += len(frows)
        db.commit()
        log.info("  -> committed batch for %s", c.code)
    log.info("DONE. Attributions: %d, Forecast rows: %d", total_attr, total_fc)
finally:
    db.close()
