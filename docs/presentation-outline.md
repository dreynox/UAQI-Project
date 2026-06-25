# Presentation Outline — UAQI for ET-AI-2026

> 5-minute judge-facing pitch. Built around the **4-question loop every city
> admin needs answered in 5 seconds**: Where? Why? What'll it be? What do I do?
> Plus the **cross-city layer** (differentiator).

---

## Slide 1 — The problem (30 sec)

**Title:** *India's air pollution crisis: we measure it, we don't act on it.*

- India: 1.67M annual deaths attributed to air pollution (Lancet).
- 900+ CAAQMS stations, every minute a new AQI reading.
- **The gap is not measurement — it's intelligence.**
- A city admin sees a number. They don't know *where, why, when, or what to do*.
- Average signal-to-intervention response time: days. It can be minutes.

> *Visuals: a wall of AQI numbers, an inspector looking confused.*

## Slide 2 — The 4-question loop (30 sec)

**Title:** *What every city admin actually needs.*

| # | Question | Our module |
|---|---|---|
| 1 | Where is it worst? | Interactive Map + Hotspots |
| 2 | Why is it bad? | Multi-Agent Attribution |
| 3 | What'll it be? | Hyperlocal Forecast |
| 4 | What do I do? | Enforcement + Advisory |

A platform that answers all four, in 5 seconds, per ward, per city, **in the
city's local language**.

## Slide 3 — The differentiators (60 sec)

**Title:** *What's novel.*

1. **Multi-modal attribution.** Four cooperating AI agents — spatial, satellite,
   traffic, land-use — score their domain, then an orchestrator fuses with
   per-city weights. Each agent produces *evidence*, not just a number, so the
   call is auditable.
2. **Atmospheric-dispersion-inspired features.** Forecast model is a
   gradient-boosted regressor per city with physics-shaped features
   (wind-direction exposure, downwind source weighting, stability class).
3. **Intervention feedback loop.** 178 past enforcement actions with measured
   AQI deltas feed the priority + impact estimator. The platform *learns* what
   works in each city.
4. **Multi-city comparative learning.** Same engine + per-city config scales
   to 50 cities. Mumbai's construction-shutdown playbook can be adapted to
   Bengaluru.
5. **Vulnerability-weighted advisories.** Not just AQI → text. AQI + nearby
   sensitive populations (schools, hospitals, elderly care) → audience-targeted
   advisory in en/hi/kn/ta.

> *Visuals: a single screen with all 4 answers side-by-side. The "aha" moment.*

## Slide 4 — Architecture (60 sec)

**Title:** *How it's built.*

- **Backend:** FastAPI + SQLAlchemy 2.0 (SQLite → Postgres) + Pydantic v2 +
  scikit-learn. 11 routers, 4 engines, 15 ORM models, ~30k seeded rows.
- **AI:**
  - Attribution: 4 modular agents + weighted orchestrator
  - Forecast: per-city GBR, RMSE 22-29 AQI vs persistence 59-66 (~30-44
    AQI advantage)
  - Enforcement: rule-based priority (AQI severity × vulnerability ×
    forecast trend × attribution confidence) + 8-action library
  - Advisory: templates × languages × severity × audience = 48 cells in
    en/hi/kn/ta
- **Frontend:** React 18 + TypeScript + Vite + Tailwind + Leaflet + Recharts +
  Zustand + TanStack Query. 7 pages, all dark "command center" theme.
- **Deployment:** Backend Dockerfile + render.yaml; frontend static build
  to Vercel/Netlify.

> *Visuals: the architecture diagram from `docs/architecture.md`.*

## Slide 5 — Live demo (90 sec)

**Hand off to the Story Mode demo.** Follow `docs/demo-script.md` exactly:

1. `/` — three cities, Delhi worst (305.7 mean, 374 max in Okhla).
2. `/story/DEL` — 4-step storyboard, 60-90 sec total:
   1. Worst ward: Okhla, AQI 374.
   2. Why: stubble_burning 46%, 4 agents agree.
   3. Forecast: 326 in 24h vs 374 baseline (-49 AQI).
   4. Action: odd-even, waste-burning crackdown, public advisory. Cost and
      lead time shown.
3. `/compare` — Delhi worst, but Mumbai's enforcement has best measured impact
   (-13.6 AQI per action). Cross-city learning.
4. `/api/wards/34/advisory?lang=hi` — Hindi advisory shown in one click.

## Slide 6 — Scalability (30 sec)

**Title:** *City-agnostic by design.*

- Same engine, per-city config. Add a 4th city = ~50 lines of seed data.
- 11 routers, all versioned, all returning the same `{data, meta, warnings,
  error}` envelope.
- Documented integration points for live Sentinel/MODIS, OpenAQ, CAAQMS feeds
  (env flag `DATA_MODE=live` skips seed).
- Frontend static build; deploy to any CDN.
- Path to 50 cities: 1 backend instance + per-city `cities` row + per-city
  trained GBR. No code changes.

## Slide 7 — Business impact (30 sec)

**Title:** *Why this matters.*

- **Time to action:** Days → minutes. The platform tells inspectors where to
  go before they've finished their morning tea.
- **Lives saved:** Vulnerability-weighted advisories reach children and the
  elderly first — the populations the 1.67M-death statistic is built from.
- **Cost-effective enforcement:** Estimated AQI impact per rupee, ranked,
  shown to the inspector. No more gut calls.
- **Cross-city learning:** Mumbai figured out construction-shutdown works.
  Delhi gets it for free. Bengaluru's hospitals get the Hindi-advisory
  template Mumbai built.
- **Auditable:** Every attribution has per-agent evidence. Every action has
  measured AQI delta. Every advisory has source severity + audience. No
  black boxes.

## Slide 8 — What's next (30 sec)

**Title:** *This is the foundation. Here's what's next.*

- **Phase 1 (done):** 3 cities, 9 modules, mocked data.
- **Phase 2 (next 90 days):** Live CAAQMS ingestion (CPCB / OpenAQ), real
  Sentinel-2 thermal anomaly pipeline, actual LLM advisory generation
  (Hindi/Kannada/Tamil via a fine-tuned 7B model).
- **Phase 3 (180 days):** Add 12 more Indian cities. Mobile-app push
  notifications. Public-display board integration. WhatsApp Business API for
  citizen advisories.
- **Phase 4 (1 year):** Cross-state learning. Winter inversion forecast
  (Delhi-specific). Industrial-emission CEMS integration.

> *Closing line:*
> *"This isn't another AQI dashboard. It's a decision-support system that
> compresses the time between signal and intervention from days to minutes,
> learns across cities, and speaks the language of the people it serves."*

---

## Backup slides (use only if asked)

### B1 — Why not just an LSTM?

We chose gradient-boosted regressors over LSTM for three reasons:
1. Feature importance is interpretable — judges can ask "why is Delhi 49 AQI
   better?" and we can answer "wind direction contributed 34%".
2. Train + inference is <30 seconds for 30 days × 3 cities. LSTM would need
   GPUs and longer train times.
3. The features are physics-shaped (dispersion-inspired), so the model
   generalises — adding a new city doesn't require retraining from scratch.

### B2 — Why multi-agent and not a single big model?

Each "agent" is a Python function with a clear input/output (e.g. the
satellite agent takes thermal anomalies + wind direction and returns a
0-1 score for biomass burning). The orchestrator fuses with per-city
weights. This means:
- Each agent is auditable in isolation
- Per-city weights are explainable
- Adding a new agent (e.g. a future traffic-camera feed agent) is one
  Python file

A single big model would be a black box — exactly what the problem
statement's "Explainable AI" requirement pushes against.

### B3 — Why 3 cities and not 1?

The problem statement is explicit: *"India's air quality crisis is not a
Delhi problem — it is a national urban crisis."* A single-city demo would
score low on scalability (15% of judging). Three cities lets us show:
- Different source mixes (Delhi = biomass, Mumbai = traffic, Bengaluru =
  construction) → the system is general
- Cross-city learning → the system compounds value
- Per-city config → the system scales

### B4 — Tech stack rationale

| Choice | Why |
|---|---|
| FastAPI | Async, OpenAPI, Pydantic v2 types — fastest backend-to-frontend contract |
| SQLite → Postgres | Zero setup for demo, one-line swap via `DATABASE_URL` for prod |
| React 18 + Vite | Fast HMR, small bundle, the standard for 2026 frontend |
| TanStack Query | Server state with caching, refetch, optimistic updates — no Redux |
| Zustand | 50-line store for selected city + selected ward. That's it. |
| Leaflet | Free, no API key, perfect for hackathon. Mapbox locked us to a key. |
| Recharts | SVG charts, easy to theme, no D3 boilerplate |
| GradientBoostingRegressor | Interpretable, fast, no GPU needed. Beats persistence by 30+ AQI. |

---

## Stage directions

- **Speaker:** 1 person, 3-5 min.
- **Demo operator:** 1 person running Story Mode.
- **Hand-off cue:** Slide 5 → "Let's see it live." Operator takes the clicker.
- **Recovery if demo dies:** Switch to screenshots in `docs/screenshots/` (or
  curl outputs in `docs/api-contract.md` section 10). The Story Mode text is
  fully scripted so a verbal walkthrough still works without the screen.
- **Q&A buffer:** Last 1-2 minutes of the 5-minute slot.
