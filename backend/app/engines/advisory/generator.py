"""Advisory generator: fill templates with ward-specific facts and persist.

Produces one Advisory row per (ward, language, audience) on demand,
valid for a fixed 6-hour window. Designed so an LLM can drop in later
by overriding `compose_text`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.engines.advisory.languages import (
    SUPPORTED_LANGUAGES,
    default_language_for_city,
    normalize,
)
from app.engines.advisory.templates import body_for, title_for
from app.models.advisory import Advisory
from app.models.attribution import Attribution
from app.models.forecast import Forecast
from app.models.ward import Ward

log = logging.getLogger("uaqi.advisory")


# Map AQI to CPCB severity bucket.
def severity_for_aqi(aqi: float) -> str:
    if aqi <= 50:
        return "good"
    if aqi <= 100:
        return "satisfactory"
    if aqi <= 200:
        return "moderate"
    if aqi <= 300:
        return "poor"
    if aqi <= 400:
        return "very_poor"
    return "severe"


# Audience selection: prefer the more specific audience when vulnerability is high.
def audience_for_ward(ward: Ward) -> str:
    vuln = ward.vulnerability_index or 0
    if vuln >= 55:
        return "children_elderly"
    return "general"


# Friendly source label per attribution bucket (per language).
SOURCE_LABELS_EN = {
    "traffic": "vehicular traffic",
    "construction": "construction dust",
    "industrial": "industrial emissions",
    "stubble_burning": "crop stubble burning",
    "biomass_burning": "biomass burning",
    "waste_burning": "waste burning",
    "urban_form": "dense built-up area",
    "mixed": "multiple sources",
}
SOURCE_LABELS_HI = {
    "traffic": "वाहनों का यातायात",
    "construction": "निर्माण धूल",
    "industrial": "औद्योगिक उत्सर्जन",
    "stubble_burning": "फसल अवशेष जलाना",
    "biomass_burning": "जैविक दहन",
    "waste_burning": "कचरा जलाना",
    "urban_form": "घनी बस्ती",
    "mixed": "कई स्रोत",
}
SOURCE_LABELS_KN = {
    "traffic": "ವಾಹನ ದಟ್ಟಣೆ",
    "construction": "ನಿರ್ಮಾಣ ಧೂಳು",
    "industrial": "ಕೈಗಾರಿಕಾ ಹೊರಸೂಸುವಿಕೆ",
    "stubble_burning": "ಬೆಳೆ ಕಡ್ಡಿ ಸುಡುವಿಕೆ",
    "biomass_burning": "ಜೈವಿಕ ದಹನ",
    "waste_burning": "ತ್ಯಾಜ್ಯ ಸುಡುವಿಕೆ",
    "urban_form": "ದಟ್ಟಿದ ನಗರ ಪ್ರದೇಶ",
    "mixed": "ಹಲವು ಮೂಲಗಳು",
}
SOURCE_LABELS_TA = {
    "traffic": "வாகன போக்குவரத்து",
    "construction": "கட்டுமான தூசி",
    "industrial": "தொழில்துறை உமிழ்வு",
    "stubble_burning": "பயிர் கழிவுகள் எரிப்பு",
    "biomass_burning": "உயிரியல் எரிப்பு",
    "waste_burning": "கழிவுகள் எரிப்பு",
    "urban_form": "நெரிசலான நகர்ப்பகுதி",
    "mixed": "பல்வேறு ஆதாரங்கள்",
}


def source_label(source: str, language: str) -> str:
    table = {
        "en": SOURCE_LABELS_EN,
        "hi": SOURCE_LABELS_HI,
        "kn": SOURCE_LABELS_KN,
        "ta": SOURCE_LABELS_TA,
    }.get(language, SOURCE_LABELS_EN)
    return table.get(source or "mixed", table["mixed"])


@dataclass
class AdvisoryInput:
    ward: Ward
    city_code: str
    current_aqi: float
    dominant_source: str
    forecast_24h: Optional[float]
    severity: str
    audience: str
    language: str
    valid_from: datetime
    valid_until: datetime


def compose_text(input: AdvisoryInput) -> tuple[str, str]:
    """Fill title + body templates. LLM-ready interface (swap later)."""
    title = title_for(input.severity, input.language)
    body = body_for(input.severity, input.audience, input.language).format(
        ward_name=input.ward.name,
        aqi=int(round(input.current_aqi)),
        dominant_source=source_label(input.dominant_source, input.language),
        forecast_24h=(
            int(round(input.forecast_24h)) if input.forecast_24h is not None else "—"
        ),
        valid_until=input.valid_until.strftime("%Y-%m-%d %H:%M"),
    )
    return title, body


def _latest_forecast_24h(session: Session, ward_id: int) -> Optional[float]:
    row = (
        session.query(Forecast)
        .filter(Forecast.ward_id == ward_id, Forecast.horizon_hours == 24)
        .order_by(Forecast.generated_at.desc())
        .first()
    )
    return row.predicted_aqi if row else None


def _latest_attribution_source(session: Session, ward_id: int) -> str:
    row = (
        session.query(Attribution)
        .filter(Attribution.ward_id == ward_id)
        .order_by(Attribution.computed_at.desc())
        .first()
    )
    return row.top_source if row else "mixed"


def build_advisory_input(
    session: Session,
    ward: Ward,
    city_code: str,
    language: str,
    *,
    as_of: Optional[datetime] = None,
    valid_hours: int = 6,
) -> AdvisoryInput:
    """Assemble facts for advisory generation."""
    as_of = as_of or datetime(2026, 6, 25, 23, 0, 0)
    lang = normalize(language)
    return AdvisoryInput(
        ward=ward,
        city_code=city_code,
        current_aqi=ward.current_aqi,
        dominant_source=_latest_attribution_source(session, ward.id),
        forecast_24h=_latest_forecast_24h(session, ward.id),
        severity=severity_for_aqi(ward.current_aqi),
        audience=audience_for_ward(ward),
        language=lang,
        valid_from=as_of,
        valid_until=as_of + timedelta(hours=valid_hours),
    )


def generate_advisory(
    session: Session,
    ward: Ward,
    city_code: str,
    language: str = "en",
    *,
    persist: bool = True,
    as_of: Optional[datetime] = None,
) -> Advisory:
    """Generate one advisory row, fill templates, and persist if requested."""
    language = normalize(language)
    inp = build_advisory_input(session, ward, city_code, language, as_of=as_of)
    title, body = compose_text(inp)

    if not persist:
        # Build a transient Advisory for read-only callers (don't add to session).
        return Advisory(
            ward_id=ward.id,
            language=language,
            severity=inp.severity,
            audience=inp.audience,
            title=title,
            body=body,
            valid_from=inp.valid_from,
            valid_until=inp.valid_until,
        )

    row = Advisory(
        ward_id=ward.id,
        language=language,
        severity=inp.severity,
        audience=inp.audience,
        title=title,
        body=body,
        valid_from=inp.valid_from,
        valid_until=inp.valid_until,
    )
    session.add(row)
    session.flush()
    return row


def generate_all_languages(
    session: Session,
    ward: Ward,
    city_code: str,
    *,
    as_of: Optional[datetime] = None,
) -> List[Advisory]:
    """Generate advisories in all supported languages for a ward."""
    out: List[Advisory] = []
    languages = list(SUPPORTED_LANGUAGES)
    if city_code.upper() == "DEL":
        languages = ["en", "hi"]
    elif city_code.upper() == "BLR":
        languages = ["en", "kn"]
    elif city_code.upper() == "BOM":
        languages = ["en", "ta"]
    for lang in languages:
        out.append(generate_advisory(session, ward, city_code, lang, as_of=as_of))
    session.commit()
    return out


def default_language_for(city_code: str) -> str:
    return default_language_for_city(city_code)
