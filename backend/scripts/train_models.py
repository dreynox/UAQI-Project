"""Train per-city forecast GradientBoosting models and save .joblib artifacts.

Usage (from backend/):
    python scripts/train_models.py
    python scripts/train_models.py --retrain
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

# Allow running from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.engines.forecast.model import train_all_city_models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("train_models")


def main():
    parser = argparse.ArgumentParser(description="Train per-city AQI forecast models.")
    parser.add_argument(
        "--retrain", action="store_true",
        help="Force retrain even if cached models exist.",
    )
    args = parser.parse_args()

    init_db()
    session = SessionLocal()
    try:
        if args.retrain:
            # Clear the in-memory cache so train_all_city_models rebuilds.
            from app.engines.forecast import model as fm
            fm._MODEL_CACHE.clear()
            fm._TRAIN_META.clear()
            log.info("Cleared in-memory cache; will retrain.")
        out = train_all_city_models(session)
        log.info("DONE. Trained models for cities: %s", list(out.keys()))
        for cid, bundle in out.items():
            meta = bundle.get("meta", {})
            for h, hmeta in meta.get("horizons", {}).items():
                log.info(
                    "  city=%s horizon=%sh model_rmse=%s baseline_rmse=%s advantage=%s",
                    cid, h, hmeta.get("rmse_model"), hmeta.get("rmse_persistence"),
                    hmeta.get("model_advantage"),
                )
    finally:
        session.close()


if __name__ == "__main__":
    main()