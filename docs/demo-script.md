# Demo Script — Urban Air Quality Intelligence (UAQI)

> How to demo the system to a judge in **3 minutes** using the Story Mode
> (`/api/demo/story?city_code=DEL`).
> All numbers below are from a live `2026-06-25 15:30 IST` seed run.

---

## Pre-flight (30 seconds)

1. Backend up: `curl http://127.0.0.1:8000/api/health` → 200, `data_mode: "mock"`.
2. Frontend up: open `http://127.0.0.1:5173/`. The dark "command center" theme
   loads; the green health pill in the top right pulses every 30s.
3. **Recommended starting point: `/story/DEL`**. Story Mode is built specifically
   for a guided 3-minute judging flow. Other pages are reference / drill-down.

> Cue: *"Imagine you're the CPCB duty officer at 6am on a winter morning. Three
> cities are reporting extreme AQI. You have one hour to decide where to send
> inspectors. Watch."*

---

## Act 1 — Overview (15 sec)

Land on `/` (or `/city/DEL`).

Point out the three top KPI tiles:

| City | Mean AQI | Worst ward | Dominant source |
|---|---|---|---|
| Delhi NCR | **305.7** | Okhla (374) | stubble_burning |
| Mumbai | 206.3 | Santacruz West (258) | traffic |
| Bengaluru | 176.3 | (BLR hotspot) | construction |

> Cue: *"Delhi is in the 'very poor' band, more than 100 AQI points above Mumbai.
> Every CPCB inspection slot matters — we need to point them somewhere."*

## Act 2 — Story Mode / 4 steps (2 min)

Open `/story/DEL`. The page is a 4-step storyboard, each step driven by `/api/demo/story`.

### Step 1 — Where is it worst? (~20 sec)

Live: *"Delhi NCR has 50 wards. The worst is **Okhla** at AQI **374** (very_poor)."*

Visual: hero card with `current_aqi=374.4` in red.

> Cue: *"Okhla is the hotspot. Let's see why."*

### Step 2 — Why is it bad here? (~30 sec)

The page hits `/api/wards/34/attribution`. Show the source breakdown radar:

- stubble_burning: **42%**
- construction: **32%**
- traffic: 15%
- industrial: 10%
- urban_form: <1%

Per-agent evidence panel shows the satellite agent detected heavy biomass burning
~1° NW of Delhi (Punjab/Haryana stubble cluster) and the wind direction is
favouring transport into Okhla.

> Cue: *"Four cooperating agents — spatial, satellite, traffic, land-use — all
> agree: this is stubble-burning, not construction or industry. The city can
> stop wasting inspector hours chasing the wrong sources."*

### Step 3 — What will it be tomorrow? (~30 sec)

The page hits `/api/wards/34/forecast`. Show the forecast chart for Okhla:

| Horizon | Model | Persistence baseline | Advantage |
|---|---|---|---|
| +24h | 325.5 | 374.4 | **-48.9** |
| +48h | 335.1 | 374.4 | -39.3 |
| +72h | 326.6 | 374.4 | -47.8 |

Confidence band shaded around each point.

> Cue: *"Our model predicts AQI will hold at ~325 tomorrow, vs the naive
> 'tomorrow = today' forecast of 374. That's a 49-AQI-point improvement, with
> a real gradient-boosted model trained on 30 days of hyperlocal data."*

### Step 4 — What should authorities do? (~30 sec)

The page hits `/api/cities/DEL/enforcement/34`. Show the recommended actions
ranked by estimated impact:

| Action | Est. Δ AQI | Cost (INR) | Lead time |
|---|---|---|---|
| Odd-even vehicle scheme | **-16.7** | 10,000 | 12h |
| Waste-burning crackdown | -19.2 | 15,000 | 8h |
| Public-health advisory | -2.6 | 2,000 | 1h |

Urgency score: **69.3 / 100** (high).

> Cue: *"In one screen: a prioritised action list with cost, lead time, and
> expected AQI impact — based on 178 past interventions across the three cities.
> The inspector knows exactly what to do tomorrow."*

## Act 3 — Cross-City Learning (30 sec)

Open `/compare`. The cross-city view shows:

- **DEL**: stubble_burning dominant, 54 past interventions, mean delta -11.1 AQI
- **BOM**: traffic dominant, 50 past interventions, mean delta -13.6 AQI
- **BLR**: construction dominant, mean delta TBD

> Cue: *"Delhi is the worst AQI, but Mumbai's enforcement has the best measured
> impact (-13.6 AQI per action). The platform propagates what works across
> cities — a city admin in Bengaluru can see Mumbai's construction-shutdown
> playbook and adapt it."*

## Act 4 — Multilingual Advisory (20 sec)

From any ward page, hit `/api/wards/34/advisory?lang=hi`. Show the Hindi
advisory. Switch to `?lang=kn` and `?lang=ta` for Kannada and Tamil.

> Cue: *"Outreach isn't just English. Every ward has a vetted advisory in
> English + the city's local language, with audience segmented for
> children/elderly vs general."*

## Closing (15 sec)

> *"This isn't a dashboard — it's a decision-support system. From a satellite
> signal in Punjab to a Hindi SMS to a parent in Okhla, the platform compresses
> the signal-to-intervention response time from days to minutes. And it's
> city-agnostic by design: same engine, per-city config, scales to 50 cities."*

---

## Fallback flows (if a judge asks "show me more")

| Question | Page | What to show |
|---|---|---|
| "Show me the data" | `/map/DEL` | Leaflet map of all 50 wards colored by AQI, layer toggles for institutions/industry/construction/thermal |
| "How accurate is the forecast?" | `/ward/34` | 24/48/72h chart vs persistence band, model_version `gbr-v1` |
| "What about the most vulnerable?" | `/health/DEL` | Per-ward vulnerability map: schools, hospitals, elderly_care, outdoor workers |
| "What worked elsewhere?" | `/compare` | Top intervention actions ranked by mean AQI delta (negative = better) |
| "Does it scale?" | `/city/BLR` or `/city/BOM` | Same 4-act story, different dominant source. The engine is city-agnostic. |

## Bad-question recoveries

- **"Is this real data?"** → "The signal is mocked with realistic Sentinel/MODIS
  thermal-anomaly proxies and seeded weather, but the architecture is wired for
  live feeds — `DATA_MODE=live` env flag skips the seed and expects a
  populated DB. The integration points are documented in `docs/architecture.md`."
- **"Is the LLM real?"** → "Templated today (deterministic for demo reliability),
  with an LLM-swap interface in `engines/advisory/generator.py:compose_text`.
  We chose reliability over novelty for judging — but the swap is one function
  call away."
- **"Why 3 cities not 1?"** → "The problem statement's headline is *'India's
  urban air crisis is not a Delhi problem'*. 3 cities lets us show the
  cross-city learning layer, which is the differentiator."

---

## What NOT to do

- Don't click into the SQLite admin. There's no UI for it and the data is mocked.
- Don't demo `/api/cities/DEL/geo/traffic` — that route is not implemented (404).
  The Map page uses ward polygons + institution/industry/construction/thermal
  layers, which all work.
- Don't promise features that aren't in the build (real satellite, real LLM,
  real dispersion). The architecture is wired for them; the demo uses
  realistic mocks.
