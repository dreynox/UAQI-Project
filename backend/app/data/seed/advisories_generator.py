"""Seed advisory rows for all wards in all supported languages.

Uses the advisory engine directly so seed output matches API output exactly.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy.orm import Session

from app.engines.advisory.generator import generate_advisory
from app.models.advisory import Advisory
from app.models.city import City
from app.models.ward import Ward

log = logging.getLogger("uaqi.seed.advisories")


# City → which languages to seed for that city.
CITY_LANGUAGES = {
    "DEL": ("en", "hi"),
    "BLR": ("en", "kn"),
    "BOM": ("en", "ta"),
}


def seed_advisories(session: Session) -> int:
    """Generate Advisory rows for all wards × city-language pairs.

    Returns number of rows inserted.
    """
    cities: List[City] = session.query(City).all()
    total = 0
    for city in cities:
        wards: List[Ward] = (
            session.query(Ward).filter(Ward.city_id == city.id).all()
        )
        langs = CITY_LANGUAGES.get(city.code, ("en",))
        for ward in wards:
            for lang in langs:
                _ = generate_advisory(session, ward, city.code, lang, persist=True)
                total += 1
        log.info("  %s: advisories for %d wards × %d langs", city.code, len(wards), len(langs))
    session.commit()
    return total
