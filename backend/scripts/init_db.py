"""Initialize database + seed data (run manually)."""

import logging
import os
import sys

# Allow running this script directly: add the backend/ dir to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db  # noqa: E402
from app.data.seed.seed_all import run_seed  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("init_db")


def main():
    log.info("Creating tables...")
    init_db()
    log.info("Seeding demo data...")
    run_seed()
    log.info("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("Init failed: %s", e)
        sys.exit(1)