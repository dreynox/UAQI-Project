"""Advisory engine: multilingual citizen advisories."""

from app.engines.advisory.generator import (
    AdvisoryInput,
    audience_for_ward,
    build_advisory_input,
    compose_text,
    default_language_for,
    generate_advisory,
    generate_all_languages,
    severity_for_aqi,
    source_label,
)
from app.engines.advisory.languages import (
    CITY_DEFAULT_LANGUAGE,
    LANGUAGE_LABELS,
    SUPPORTED_LANGUAGES,
    default_language_for_city,
    is_supported,
    normalize,
)
from app.engines.advisory.templates import body_for, title_for

__all__ = [
    "AdvisoryInput",
    "CITY_DEFAULT_LANGUAGE",
    "LANGUAGE_LABELS",
    "SUPPORTED_LANGUAGES",
    "audience_for_ward",
    "body_for",
    "build_advisory_input",
    "compose_text",
    "default_language_for",
    "default_language_for_city",
    "generate_advisory",
    "generate_all_languages",
    "is_supported",
    "normalize",
    "severity_for_aqi",
    "source_label",
    "title_for",
]
