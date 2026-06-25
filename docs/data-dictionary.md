# Data Dictionary — Urban Air Quality Intelligence (UAQI)

> Every table, every column, what it means, what range it lives in.
> Source of truth: `backend/app/models/*.py`. All tables live in SQLite (demo) or
> Postgres (production) — schema is portable.

All tables inherit `id` (autoincrement PK) and `created_at` / `updated_at`
timestamps from `IdMixin` and `TimestampMixin` in `backend/app/models/base.py`
(unless noted otherwise).

---

## 1. `cities`

A covered Indian metro. Seeded: DEL, BLR, BOM.

| Column | Type | Notes |
|---|---|---|
| `code` | string(8) | `DEL` / `BLR` / `BOM` — unique, indexed |
| `name` | string(64) | Display name |
| `state` | string(64) | Indian state / UT |
| `country` | string(8) | Always `IN` |
| `center_lat`, `center_lon` | float | Map center |
| `bbox_min_lat`, `bbox_min_lon`, `bbox_max_lat`, `bbox_max_lat` | float | Bounding box for the city |
| `population_millions` | float | e.g. DEL = 32.0 |
| `primary_language` | string(16) | `hi` / `kn` / `mr` / `en` |

## 2. `wards`

Administrative ward / zone. Seeded: 50 DEL + 40 BLR + 35 BOM = 125.

| Column | Type | Notes |
|---|---|---|
| `city_id` | FK→cities | indexed |
| `ward_code` | string(32) | indexed |
| `name` | string(128) | Display name |
| `population` | int | e.g. 60k–350k |
| `area_km2` | float | |
| `centroid_lat`, `centroid_lon` | float | Ward center |
| `geometry_geojson` | text | GeoJSON `Polygon` (stringified for SQLite portability) |
| `bbox_*` | float | Ward bounding box |
| `current_aqi` | float | Latest snapshot, kept up-to-date by seed |
| `aqi_category` | string(16) | `good` / `satisfactory` / `moderate` / `poor` / `very_poor` / `severe` |
| `vulnerability_index` | float | 0–100, indexed. Higher = more vulnerable population |

## 3. `aqi_stations` (model class `AQISation`)

Continuous Ambient Air Quality Monitoring Stations (CAAQMS). Seeded: 15 DEL + 12 BLR + 14 BOM = 41.

| Column | Type | Notes |
|---|---|---|
| `city_id` | FK→cities | indexed |
| `name` | string(128) | |
| `station_code` | string(32) | unique, indexed |
| `lat`, `lon` | float | |
| `station_type` | string(32) | `CAAQMS` |
| `ward_id` | FK→wards? | nullable. A station typically maps to one ward. |

> ⚠ The SQLAlchemy class is intentionally named `AQISation` (a pun on "Ambient
> Air Quality Monitoring Station"). All code uses this name; the underlying
> table is `aqi_stations`.

## 4. `aqi_time_series` (model class `AQITimeSeries`)

Hourly readings from a station or ward-aggregated synthetic readings. Seeded: 90,000 rows (30 days × 3 cities).

| Column | Type | Notes |
|---|---|---|
| `station_id` | FK→aqi_stations? | nullable. If null, this is a ward-aggregated synthetic reading. |
| `ward_id` | FK→wards? | nullable, indexed. Set for synthetic ward readings. |
| `timestamp` | datetime | indexed |
| `aqi` | float | Computed AQI from PM2.5 |
| `pm25`, `pm10` | float | µg/m³ |
| `no2`, `so2` | float | µg/m³ |
| `o3` | float | µg/m³ |
| `co` | float | mg/m³ |

Indexes: `(station_id, timestamp)`, `(ward_id, timestamp)`.

## 5. `weather_forecast`

7-day hourly weather per city. Seeded: 168 rows × 3 cities = 504.

| Column | Type | Notes |
|---|---|---|
| `city_id` | FK→cities | indexed |
| `timestamp` | datetime | indexed |
| `temperature_c` | float | |
| `humidity_pct` | float | |
| `pressure_hpa` | float | |
| `wind_speed_kmh` | float | |
| `wind_dir_deg` | float | 0=N, 90=E, 180=S, 270=W (meteorological convention) |
| `cloud_cover_pct` | float | |
| `stability_class` | string(4) | Pasquill-Gifford-inspired: `A`…`F`. A=very unstable, F=very stable. |
| `precip_mm` | float | |

## 6. `construction_sites`

Active construction sites. Seeded: 180 DEL + 220 BLR + 150 BOM = 550.

| Column | Type | Notes |
|---|---|---|
| `city_id` | FK→cities | indexed |
| `name` | string(128) | |
| `lat`, `lon` | float | |
| `intensity` | float | 0–100 |
| `area_sqm` | float | |
| `is_compliant` | bool | |
| `start_date`, `end_date` | datetime | |

## 7. `industrial_sites`

Registered industrial emitters. Seeded: 60 DEL + 30 BLR + 70 BOM = 160.

| Column | Type | Notes |
|---|---|---|
| `city_id` | FK→cities | indexed |
| `name` | string(128) | |
| `lat`, `lon` | float | |
| `emission_type` | string(32) | `so2` / `nox` / `pm` / `co` / `mixed` |
| `intensity` | float | 0–100 |
| `has_stack_monitor` | bool | Whether CEMS installed |
| `compliance_score` | float | 0–100 |

## 8. `thermal_anomalies`

Sentinel/MODIS proxy feed (mocked in demo). Seeded: 300 DEL + 50 BLR + 40 BOM = 390.

| Column | Type | Notes |
|---|---|---|
| `city_id` | FK→cities | indexed |
| `timestamp` | datetime | indexed |
| `lat`, `lon` | float | |
| `intensity_kelvin` | float | Brightness temperature proxy |
| `confidence` | float | 0–1 |
| `source_type` | string(32) | `biomass` / `industrial` / `wildfire` |

## 9. `institutions`

Vulnerable points-of-interest. Seeded: 280 DEL + 320 BLR + 290 BOM = 890.

| Column | Type | Notes |
|---|---|---|
| `city_id` | FK→cities | indexed |
| `name` | string(128) | |
| `institution_type` | string(32) | `school` / `hospital` / `elderly_care` / `outdoor_worker` / `anganwadi` / `orphanage` (indexed) |
| `lat`, `lon` | float | |
| `capacity` | int | Persons (e.g. school students, hospital beds) |
| `vulnerability_weight` | float | 0–1. Elderly_care & anganwadi = 0.90–0.95; outdoor_worker = 0.70. |

## 10. `traffic_density`

Hourly per-ward traffic. Used by `traffic_agent.py` for source attribution.

| Column | Type | Notes |
|---|---|---|
| `ward_id` | FK→wards | indexed |
| `timestamp` | datetime | indexed |
| `traffic_index` | float | 0–100 |
| `heavy_vehicle_pct` | float | 0–100 |
| `avg_speed_kmh` | float | |

## 11. `interventions`

Past enforcement actions. Seeded: 178 (60 DEL + 45 BLR + 55 BOM + 18 force-injected on top-AQI wards).

| Column | Type | Notes |
|---|---|---|
| `city_id` | FK→cities | indexed |
| `ward_id` | FK→wards? | nullable, indexed |
| `action_type` | string(32) | `inspection` / `dust_control` / `traffic_diversion` / `waste_burning` / `industrial_audit` / `public_advisory` / `odd_even` / `construction_shutdown` |
| `status` | string(16) | `planned` / `active` / `completed` / `failed` |
| `started_at` | datetime | |
| `ended_at` | datetime? | |
| `measured_aqi_delta` | float? | **Negative = AQI improvement.** Drives `/compare/interventions`. |
| `notes` | text | |

## 12. `forecasts`

Per-ward, per-horizon predicted AQI. Auto-computed on backend startup. 375 rows total (125 wards × 3 horizons).

| Column | Type | Notes |
|---|---|---|
| `ward_id` | FK→wards | indexed |
| `horizon_hours` | float | 24 / 48 / 72 |
| `generated_at` | datetime | When this forecast was made |
| `target_time` | datetime | When the predicted AQI applies (now + horizon) |
| `predicted_aqi` | float | GBR prediction |
| `baseline_aqi` | float | Persistence baseline ("tomorrow = today") |
| `confidence_low`, `confidence_high` | float | 90% CI band |
| `model_version` | string(32) | `gbr-v1` |

Indexes: `(ward_id, target_time)`.

## 13. `attributions`

Multi-agent attribution result. Auto-computed on backend startup. 125 rows (one per ward).

| Column | Type | Notes |
|---|---|---|
| `ward_id` | FK→wards | indexed |
| `computed_at` | datetime | indexed |
| `top_source` | string(32) | One of the canonical buckets (see below) |
| `confidence` | float | 0–1 |
| `source_breakdown_json` | text | `{"traffic": 0.34, "construction": 0.41, ...}` — sums to 1.0 |
| `agent_evidence_json` | text | `{"spatial": {"score": 0.7, "top_signals": [...]}, "satellite": {...}, ...}` |
| `explanation` | text | 1–2 sentence human-readable narrative |

Indexes: `(ward_id, computed_at)`.

## 14. `vulnerable_population`

Per-ward aggregate vulnerability summary.

| Column | Type | Notes |
|---|---|---|
| `ward_id` | FK→wards | unique, indexed |
| `children_under_5` | int | |
| `elderly_65_plus` | int | |
| `outdoor_workers` | int | |
| `asthma_prev_pct` | float | Asthma prevalence % |
| `pregnant_women` | int | |
| `vulnerability_index` | float | 0–100, mirrors `wards.vulnerability_index` |

## 15. `advisories`

Generated multilingual advisories. Seeded: 250 (one per ward × `en` + city's local language).

| Column | Type | Notes |
|---|---|---|
| `ward_id` | FK→wards | indexed |
| `language` | string(8) | `en` / `hi` / `kn` / `ta` / `mr` |
| `severity` | string(16) | `good` / `satisfactory` / `moderate` / `poor` / `very_poor` / `severe` |
| `audience` | string(32) | `general` or `children_elderly` (derived from ward vulnerability) |
| `title` | string(256) | One-line headline in target language |
| `body` | text | Full advisory in target language |
| `valid_from`, `valid_until` | datetime | Validity window |

Indexes: `(ward_id, language)`.

---

## 16. Canonical enums

### Source buckets (`top_source` / `source_breakdown` keys)

```
traffic, construction, industrial, stubble_burning,
biomass_burning, waste_burning, urban_form, mixed
```

### AQI categories (`aqi_category`)

| Category | AQI range |
|---|---|
| `good` | 0–50 |
| `satisfactory` | 51–100 |
| `moderate` | 101–200 |
| `poor` | 201–300 |
| `very_poor` | 301–400 |
| `severe` | 401+ |

### Intervention action types (`action_type`)

```
inspection, dust_control, traffic_diversion, waste_burning,
industrial_audit, public_advisory, odd_even, construction_shutdown
```

### Stability class (`stability_class`)

Pasquill-Gifford-inspired: `A` (very unstable) → `F` (very stable). Used by
dispersion-inspired features in `forecast/features.py`.

---

## 17. Row counts after seed (2026-06-25 verified)

| Table | Rows | Notes |
|---|---|---|
| `cities` | 3 | DEL, BLR, BOM |
| `wards` | 125 | 50 + 40 + 35 |
| `aqi_stations` | 41 | 15 + 12 + 14 |
| `aqi_time_series` | 90,000 | 30 days × 24h × ~125 wards |
| `weather_forecast` | 504 | 7 days × 24h × 3 cities |
| `construction_sites` | 550 | 180 + 220 + 150 |
| `industrial_sites` | 160 | 60 + 30 + 70 |
| `thermal_anomalies` | 390 | 300 + 50 + 40 |
| `institutions` | 890 | 280 + 320 + 290 |
| `interventions` | 178 | 60 + 45 + 55 + 18 force-injected |
| `attributions` | 125 | one per ward |
| `forecasts` | 375 | 125 × 3 horizons |
| `vulnerable_population` | 125 | one per ward |
| `advisories` | 250 | 125 × 2 languages |
