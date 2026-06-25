"""Language registry for multilingual advisories.

Four official Indian languages covered by the platform:
- en: English (national)
- hi: Hindi (Delhi)
- kn: Kannada (Bengaluru)
- ta: Tamil (Mumbai)
"""

from __future__ import annotations

from typing import Dict


SUPPORTED_LANGUAGES = ("en", "hi", "kn", "ta")

LANGUAGE_LABELS: Dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी",
    "kn": "ಕನ್ನಡ",
    "ta": "தமிழ்",
}


# City → primary language hint (used when caller doesn't pass `lang`).
CITY_DEFAULT_LANGUAGE: Dict[str, str] = {
    "DEL": "hi",
    "BLR": "kn",
    "BOM": "ta",
}


def default_language_for_city(city_code: str) -> str:
    return CITY_DEFAULT_LANGUAGE.get(city_code.upper(), "en")


def is_supported(lang: str) -> bool:
    return (lang or "").lower() in SUPPORTED_LANGUAGES


def normalize(lang: str) -> str:
    """Return the supported language code or default to 'en'."""
    lang = (lang or "").lower()
    return lang if lang in SUPPORTED_LANGUAGES else "en"
