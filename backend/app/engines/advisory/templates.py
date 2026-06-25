"""Multilingual advisory templates.

Structure: severity × audience × language → title + body.

Severities (CPCB):
  good | satisfactory | moderate | poor | very_poor | severe

Audiences:
  general | children_elderly | outdoor_workers | asthma
"""

from __future__ import annotations

from typing import Dict, Tuple


# Tuple key: (severity, audience, language)
TemplateKey = Tuple[str, str, str]


# Title templates by (severity, language).
TITLES: Dict[Tuple[str, str], str] = {
    ("good", "en"): "Air quality is good",
    ("good", "hi"): "वायु गुणवत्ता अच्छी है",
    ("good", "kn"): "ವಾಯು ಗುಣಮಟ್ಟ ಉತ್ತಮವಾಗಿದೆ",
    ("good", "ta"): "காற்றின் தரம் நல்லது",

    ("satisfactory", "en"): "Air quality is satisfactory",
    ("satisfactory", "hi"): "वायु गुणवत्ता संतोषजनक है",
    ("satisfactory", "kn"): "ವಾಯು ಗುಣಮಟ್ಟ ತೃಪ್ತಿಕರವಾಗಿದೆ",
    ("satisfactory", "ta"): "காற்றின் தரம் ஏற்கத்தக்கது",

    ("moderate", "en"): "Air quality is moderate — sensitive groups take care",
    ("moderate", "hi"): "वायु गुणवत्ता मध्यम है — संवेदनशील समूह सावधानी बरतें",
    ("moderate", "kn"): "ವಾಯು ಗುಣಮಟ್ಟ ಮಧ್ಯಮ — ಸೂಕ್ಷ್ಮ ಗುಂಪುಗಳು ಎಚ್ಚರಿಕೆ ವಹಿಸಿ",
    ("moderate", "ta"): "காற்றின் தரம் நடுத்தரம் — உணர்வுள்ள குழுக்கள் கவனமாக இருங்கள்",

    ("poor", "en"): "Air quality is poor — limit outdoor activity",
    ("poor", "hi"): "वायु गुणवत्ता खराब है — बाहरी गतिविधि सीमित करें",
    ("poor", "kn"): "ವಾಯು ಗುಣಮಟ್ಟ ಕಳಪೆ — ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆ ಮಿತಿಗೊಳಿಸಿ",
    ("poor", "ta"): "காற்றின் தரம் மோசம் — வெளிப்புற செயல்பாட்டை கட்டுப்படுத்துங்கள்",

    ("very_poor", "en"): "Air quality is very poor — stay indoors",
    ("very_poor", "hi"): "वायु गुणवत्ता बहुत खराब है — घर के अंदर रहें",
    ("very_poor", "kn"): "ವಾಯು ಗುಣಮಟ್ಟ ಅತ್ಯಂತ ಕಳಪೆ — ಒಳಗಡೆ ಇರಿ",
    ("very_poor", "ta"): "காற்றின் தரம் மிக மோசம் — உள்ளே இருங்கள்",

    ("severe", "en"): "Hazardous air — avoid all outdoor exertion",
    ("severe", "hi"): "खतरनाक वायु — सभी बाहरी परिश्रम से बचें",
    ("severe", "kn"): "ಅಪಾಯಕಾರಿ ವಾಯು — ಎಲ್ಲಾ ಹೊರಾಂಗಣ ಶ್ರಮ ತಪ್ಪಿಸಿ",
    ("severe", "ta"): "ஆபத்தான காற்று — அனைத்து வெளிப்புற செயல்பாடுகளையும் தவிர்க்கவும்",
}


# Body templates: (severity, audience, language) → body template with placeholders.
# Placeholders:
#   {ward_name}, {aqi}, {dominant_source}, {forecast_24h}, {valid_until}
BODIES: Dict[TemplateKey, str] = {
    # general audience
    ("good", "general", "en"):
        "Current AQI in {ward_name} is {aqi}. Air quality is good — enjoy outdoor activities.",
    ("good", "general", "hi"):
        "{ward_name} में वर्तमान AQI {aqi} है। वायु गुणवत्ता अच्छी है — बाहरी गतिविधियों का आनंद लें।",
    ("good", "general", "kn"):
        "{ward_name} ನಲ್ಲಿ ಪ್ರಸ್ತುತ AQI {aqi} ಆಗಿದೆ. ವಾಯು ಗುಣಮಟ್ಟ ಉತ್ತಮವಾಗಿದೆ — ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳನ್ನು ಆನಂದಿಸಿ.",
    ("good", "general", "ta"):
        "{ward_name} இல் தற்போதைய AQI {aqi}. காற்றின் தரம் நல்லது — வெளிப்புற செயல்பாடுகளை அனுபவியுங்கள்.",

    ("satisfactory", "general", "en"):
        "Current AQI in {ward_name} is {aqi}. Acceptable for most; unusually sensitive people should monitor symptoms.",
    ("satisfactory", "general", "hi"):
        "{ward_name} में वर्तमान AQI {aqi} है। अधिकांश लोगों के लिए स्वीकार्य; अत्यधिक संवेदनशील लोग लक्षणों पर नज़र रखें।",
    ("satisfactory", "general", "kn"):
        "{ward_name} ನಲ್ಲಿ ಪ್ರಸ್ತುತ AQI {aqi}. ಹೆಚ್ಚಿನವರಿಗೆ ಸ್ವೀಕಾರಾರ್ಹ; ಅತಿ ಸೂಕ್ಷ್ಮ ವ್ಯಕ್ತಿಗಳು ಲಕ್ಷಣಗಳನ್ನು ಗಮನಿಸಿ.",
    ("satisfactory", "general", "ta"):
        "{ward_name} இல் தற்போதைய AQI {aqi}. பெரும்பாலானவர்களுக்கு ஏற்கத்தக்கது; மிகவும் உணர்வுள்ளவர்கள் அறிகுறிகளை கவனியுங்கள்.",

    ("moderate", "general", "en"):
        "Current AQI in {ward_name} is {aqi}. Sensitive groups should reduce prolonged outdoor exertion. Dominant source: {dominant_source}.",
    ("moderate", "general", "hi"):
        "{ward_name} में वर्तमान AQI {aqi} है। संवेदनशील समूह लंबी बाहरी गतिविधि कम करें। प्रमुख स्रोत: {dominant_source}।",
    ("moderate", "general", "kn"):
        "{ward_name} ನಲ್ಲಿ ಪ್ರಸ್ತುತ AQI {aqi}. ಸೂಕ್ಷ್ಮ ಗುಂಪುಗಳು ದೀರ್ಘ ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆ ಕಡಿಮೆ ಮಾಡಿ. ಪ್ರಮುಖ ಮೂಲ: {dominant_source}.",
    ("moderate", "general", "ta"):
        "{ward_name} இல் தற்போதைய AQI {aqi}. உணர்வுள்ள குழுக்கள் நீண்ட வெளிப்புற செயல்பாட்டை குறைக்கவும். முக்கிய ஆதாரம்: {dominant_source}.",

    ("poor", "general", "en"):
        "AQI in {ward_name} is {aqi} (poor). Limit outdoor activity; wear an N95 mask if you must go out. Main source: {dominant_source}.",
    ("poor", "general", "hi"):
        "{ward_name} में AQI {aqi} है (खराब)। बाहरी गतिविधि सीमित करें; बाहर जाना पड़े तो N95 मास्क पहनें। मुख्य स्रोत: {dominant_source}।",
    ("poor", "general", "kn"):
        "{ward_name} ನಲ್ಲಿ AQI {aqi} (ಕಳಪೆ). ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆ ಮಿತಿಗೊಳಿಸಿ; ಹೊರಗೆ ಹೋಗಬೇಕಾದರೆ N95 ಮಾಸ್ಕ್ ಧರಿಸಿ. ಮುಖ್ಯ ಮೂಲ: {dominant_source}.",
    ("poor", "general", "ta"):
        "{ward_name} இல் AQI {aqi} (மோசம்). வெளிப்புற செயல்பாட்டை கட்டுப்படுத்துங்கள்; வெளியே செல்ல வேண்டியிருந்தால் N95 முகக்கவசம் அணியுங்கள். முக்கிய ஆதாரம்: {dominant_source}.",

    ("very_poor", "general", "en"):
        "AQI in {ward_name} is {aqi} (very poor). Stay indoors, close windows during peak hours, run an air purifier if available. Forecast 24h: {forecast_24h}.",
    ("very_poor", "general", "hi"):
        "{ward_name} में AQI {aqi} है (बहुत खराब)। घर के अंदर रहें, पीक आवर्स में खिड़कियाँ बंद रखें, एयर प्यूरीफायर चलाएँ। 24 घंटे का पूर्वानुमान: {forecast_24h}।",
    ("very_poor", "general", "kn"):
        "{ward_name} ನಲ್ಲಿ AQI {aqi} (ಅತ್ಯಂತ ಕಳಪೆ). ಒಳಗಡೆ ಇರಿ, ಪೀಕ್ ಸಮಯದಲ್ಲಿ ಕಿಟಕಿಗಳನ್ನು ಮುಚ್ಚಿ, ಏರ್ ಪ್ಯೂರಿಫೈಯರ್ ಬಳಸಿ. 24 ಗಂಟೆಗಳ ಮುನ್ಸೂಚನೆ: {forecast_24h}.",
    ("very_poor", "general", "ta"):
        "{ward_name} இல் AQI {aqi} (மிக மோசம்). உள்ளே இருங்கள், உச்ச நேரங்களில் சன்னல்களை மூடுங்கள், காற்று சுத்திகரிப்பான் இயக்குங்கள். 24 மணி நேர முன்னறிவிப்பு: {forecast_24h}.",

    ("severe", "general", "en"):
        "AQI in {ward_name} is {aqi} (hazardous). Avoid ALL outdoor exertion. Schools suspend outdoor activities. Forecast 24h: {forecast_24h}.",
    ("severe", "general", "hi"):
        "{ward_name} में AQI {aqi} है (खतरनाक)। सभी बाहरी परिश्रम से बचें। विद्यालय बाहरी गतिविधियाँ निलंबित करें। 24 घंटे का पूर्वानुमान: {forecast_24h}।",
    ("severe", "general", "kn"):
        "{ward_name} ನಲ್ಲಿ AQI {aqi} (ಅಪಾಯಕಾರಿ). ಎಲ್ಲಾ ಹೊರಾಂಗಣ ಶ್ರಮ ತಪ್ಪಿಸಿ. ಶಾಲೆಗಳು ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳನ್ನು ಸ್ಥಗಿತಗೊಳಿಸುತ್ತವೆ. 24 ಗಂಟೆಗಳ ಮುನ್ಸೂಚನೆ: {forecast_24h}.",
    ("severe", "general", "ta"):
        "{ward_name} இல் AQI {aqi} (ஆபத்தான). அனைத்து வெளிப்புற செயல்பாடுகளையும் தவிர்க்கவும். பள்ளிகள் வெளிப்புற செயல்பாடுகளை இடைநிறுத்தும். 24 மணி நேர முன்னறிவிப்பு: {forecast_24h}.",

    # children_elderly audience — used when vulnerability is high
    ("poor", "children_elderly", "en"):
        "AQI in {ward_name} is {aqi}. Children and elderly should stay indoors today; postpone any outdoor sports.",
    ("poor", "children_elderly", "hi"):
        "{ward_name} में AQI {aqi} है। बच्चे और बुज़ुर्ग आज घर पर रहें; बाहरी खेल स्थगित करें।",
    ("poor", "children_elderly", "kn"):
        "{ward_name} ನಲ್ಲಿ AQI {aqi}. ಮಕ್ಕಳು ಮತ್ತು ವೃದ್ಧರು ಇಂದು ಒಳಗಡೆ ಇರಬೇಕು; ಹೊರಾಂಗಣ ಕ್ರೀಡೆಗಳನ್ನು ಮುಂದೂಡಿ.",
    ("poor", "children_elderly", "ta"):
        "{ward_name} இல் AQI {aqi}. குழந்தைகள் மற்றும் முதியவர்கள் இன்று உள்ளே இருக்க வேண்டும்; வெளிப்புற விளையாட்டுகளை ஒத்திவைக்கவும்.",

    ("very_poor", "children_elderly", "en"):
        "AQI in {ward_name} is {aqi}. Children, elderly, pregnant women — stay home, seal gaps under doors, monitor symptoms. Forecast: {forecast_24h}.",
    ("very_poor", "children_elderly", "hi"):
        "{ward_name} में AQI {aqi} है। बच्चे, बुज़ुर्ग, गर्भवती महिलाएँ — घर पर रहें, दरवाज़ों के नीचे की दरारें बंद करें, लक्षणों पर नज़र रखें। पूर्वानुमान: {forecast_24h}।",
    ("very_poor", "children_elderly", "kn"):
        "{ward_name} ನಲ್ಲಿ AQI {aqi}. ಮಕ್ಕಳು, ವೃದ್ಧರು, ಗರ್ಭಿಣಿಯರು — ಮನೆಯಲ್ಲಿ ಇರಿ, ಬಾಗಿಲುಗಳ ಕೆಳಗಿನ ಅಂತರಗಳನ್ನು ಮುಚ್ಚಿ, ಲಕ್ಷಣಗಳನ್ನು ಗಮನಿಸಿ. ಮುನ್ಸೂಚನೆ: {forecast_24h}.",
    ("very_poor", "children_elderly", "ta"):
        "{ward_name} இல் AQI {aqi}. குழந்தைகள், முதியவர்கள், கர்ப்பிணிப் பெண்கள் — வீட்டில் இருங்கள், கதவுகளின் கீழ் இடைவெளிகளை மூடுங்கள், அறிகுறிகளை கவனியுங்கள். முன்னறிவிப்பு: {forecast_24h}.",

    ("severe", "children_elderly", "en"):
        "AQI in {ward_name} is {aqi} (hazardous). Do NOT send children to school; keep elderly indoors. Seek medical help for any breathing difficulty.",
    ("severe", "children_elderly", "hi"):
        "{ward_name} में AQI {aqi} है (खतरनाक)। बच्चों को स्कूल न भेजें; बुज़ुर्गों को घर में रखें। साँस लेने में कठिनाई हो तो चिकित्सा सहायता लें।",
    ("severe", "children_elderly", "kn"):
        "{ward_name} ನಲ್ಲಿ AQI {aqi} (ಅಪಾಯಕಾರಿ). ಮಕ್ಕಳನ್ನು ಶಾಲೆಗೆ ಕಳುಹಿಸಬೇಡಿ; ವೃದ್ಧರನ್ನು ಒಳಗಡೆ ಇಡಿ. ಉಸಿರಾಟದ ತೊಂದರೆಗಾಗಿ ವೈದ್ಯಕೀಯ ಸಹಾಯ ಪಡೆಯಿರಿ.",
    ("severe", "children_elderly", "ta"):
        "{ward_name} இல் AQI {aqi} (ஆபத்தான). குழந்தைகளை பள்ளிக்கு அனுப்ப வேண்டாம்; முதியவர்களை உள்ளே வைத்திருங்கள். சுவாசிப்பதில் சிரமம் இருந்தால் மருத்துவ உதவி பெறவும்.",
}


# Audience fallback order: if specific audience not found, fall back to general.
AUDIENCE_FALLBACK = ("general",)


def title_for(severity: str, language: str) -> str:
    """Pick title template; falls back to English if missing."""
    return (
        TITLES.get((severity, language))
        or TITLES.get((severity, "en"))
        or TITLES[("moderate", "en")]
    )


def body_for(severity: str, audience: str, language: str) -> str:
    """Pick body template with audience and language fallback chain."""
    for aud in (audience, *AUDIENCE_FALLBACK):
        for lang in (language, "en"):
            key = (severity, aud, lang)
            if key in BODIES:
                return BODIES[key]
    # Final fallback: moderate / general / English
    return BODIES[("moderate", "general", "en")]
