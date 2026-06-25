/**
 * Shared types matching the backend API envelope.
 * Backend wraps every response in `{ data, meta, warnings, error }`.
 */

export interface ApiEnvelope<T> {
  data: T;
  meta?: Record<string, unknown>;
  warnings?: string[];
  error?: { code: string; message: string } | null;
}

export interface City {
  code: string;
  name: string;
  state: string;
  country: string;
  center_lat: number;
  center_lon: number;
  bbox: [number, number, number, number];
  population_millions: number;
  primary_language: string;
  wards_count?: number;
  mean_aqi?: number | null;
  latest_reading_at?: string | null;
}

export interface CityOverview {
  city: {
    code: string;
    name: string;
    center_lat: number;
    center_lon: number;
    population_millions: number;
    primary_language: string;
  };
  kpis: {
    mean_aqi: number;
    top10_mean_aqi: number;
    max_aqi: number;
    min_aqi: number;
    wards_count: number;
    institutions_count: number;
    construction_sites_count: number;
    industrial_sites_count: number;
    thermal_anomalies_count: number;
  };
  hotspots: Array<{
    ward_id: number;
    ward_code: string;
    ward_name: string;
    centroid_lat: number;
    centroid_lon: number;
    current_aqi: number;
    aqi_category: string;
    vulnerability_index: number;
    population: number;
  }>;
  weather: {
    temperature_c: number | null;
    humidity_pct: number | null;
    wind_speed_kmh: number | null;
    wind_dir_deg: number | null;
    stability_class: string | null;
    timestamp: string | null;
  };
}

export interface Ward {
  id: number;
  ward_code: string;
  name: string;
  city_code?: string;
  city_name?: string;
  centroid_lat: number;
  centroid_lon: number;
  bbox?: [number, number, number, number];
  current_aqi: number;
  aqi_category: string;
  vulnerability_index: number;
  population: number;
  area_km2?: number;
  aqi_series_48h?: Array<{ timestamp: string; aqi: number; pm25: number }>;
  vulnerable_population?: {
    children_under_5: number;
    elderly_65_plus: number;
    outdoor_workers: number;
    asthma_prev_pct: number;
    pregnant_women: number;
    vulnerability_index: number;
  } | null;
  nearby_institutions_count?: number;
  nearby_institutions_by_type?: Record<string, number>;
}

export interface AttributionResult {
  ward_id: number;
  ward_name: string;
  top_source: string;
  confidence: number;
  source_breakdown: Record<string, number>;
  agent_evidence: Record<string, unknown>;
  explanation: string;
  computed_at: string;
}

export interface ForecastHorizon {
  horizon_hours: number;
  target_time: string;
  generated_at: string;
  predicted_aqi: number;
  baseline_aqi: number;
  confidence_low: number;
  confidence_high: number;
  model_version: string;
}

export interface WardForecast {
  ward_id: number;
  ward_name: string;
  current_aqi: number;
  forecasts: ForecastHorizon[];
}

export interface PriorityScore {
  ward_id: number;
  priority_score: number;
  urgency: "low" | "medium" | "high" | "critical";
  components: {
    aqi: number;
    vulnerability: number;
    forecast_trend: number;
    attribution_confidence: number;
  };
}

export interface RecommendedAction {
  action_code: string;
  title: string;
  description: string;
  expected_aqi_delta: number;
  estimated_cost_inr: number;
  lead_time_hours: number;
  priority: "primary" | "secondary";
  estimated_aqi_delta?: number;
  estimation_confidence?: number;
  estimation_method?: string;
}

export interface EnforcementQueueItem {
  ward_id: number;
  ward_code: string;
  ward_name: string;
  current_aqi: number;
  vulnerability_index: number;
  top_source: string;
  priority_score: number;
  urgency: string;
  components: PriorityScore["components"];
  recommended_actions: RecommendedAction[];
}

export interface WardEnforcement {
  ward_id: number;
  ward_name: string;
  city_code: string;
  current_aqi: number;
  vulnerability_index: number;
  top_source: string;
  attribution_confidence: number;
  priority_score: number;
  urgency: string;
  components: PriorityScore["components"];
  recommended_actions: RecommendedAction[];
}

export interface Advisory {
  ward_id: number;
  ward_name: string;
  city_code: string | null;
  language: string;
  severity: string;
  audience: string;
  title: string;
  body: string;
  valid_from: string;
  valid_until: string;
}

export interface CityAdvisory {
  city_code: string;
  city_name: string;
  default_language: string;
  supported_languages: string[];
  sample_advisory: {
    ward_id: number;
    ward_name: string;
    title: string;
    body: string;
    severity: string;
    audience: string;
  } | null;
}

export interface CompareCity {
  code: string;
  name: string;
  state: string;
  mean_aqi: number;
  max_aqi: number;
  mean_vulnerability: number;
  population_millions: number;
  primary_language: string;
  wards_count: number;
  worst_ward: string | null;
  worst_ward_aqi: number | null;
  worst_ward_id: number | null;
  dominant_source: string;
  source_counts: Record<string, number>;
  source_share: Record<string, number>;
  interventions_count: number;
  interventions_mean_delta: number | null;
}

export interface CompareInterventionRow {
  city_code: string;
  action_type: string;
  count: number;
  mean_aqi_delta: number;
  median_aqi_delta: number;
  best_delta: number;
  worst_delta: number;
}

export interface DemoScenario {
  scenario: {
    city: { code: string; name: string; state: string };
    ward: {
      id: number;
      name: string;
      ward_code: string;
      centroid_lat: number;
      centroid_lon: number;
      bbox: [number, number, number, number];
      current_aqi: number;
      aqi_category: string;
      vulnerability_index: number;
    };
    headline: string;
  };
  attribution: {
    top_source: string;
    confidence: number;
    source_breakdown: Record<string, number>;
    agent_evidence: Record<string, unknown>;
    explanation: string;
  } | null;
  forecast: {
    horizons: Array<{
      horizon_hours: number;
      predicted_aqi: number;
      baseline_aqi: number;
      improvement_vs_baseline: number;
      confidence_low: number;
      confidence_high: number;
    }>;
    model_version: string | null;
  };
  enforcement: {
    priority: PriorityScore & { urgency: string };
    recommended_actions: RecommendedAction[];
  };
  advisory: {
    default_language: string;
    sample_en?: { language: string; severity: string; audience: string; title: string; body: string };
    sample_hi?: { language: string; severity: string; audience: string; title: string; body: string };
    sample_kn?: { language: string; severity: string; audience: string; title: string; body: string };
    sample_ta?: { language: string; severity: string; audience: string; title: string; body: string };
  };
  interventions: {
    recent: Array<{
      id: number;
      action_type: string;
      status: string;
      started_at: string;
      ended_at: string | null;
      measured_aqi_delta: number | null;
      notes: string | null;
    }>;
    total_completed: number;
  };
  context: {
    population: number;
    area_km2: number;
    vulnerability: Record<string, unknown>;
    nearby_institutions_count: number;
    nearby_construction_sites_count: number;
    nearby_industrial_sites_count: number;
    nearby_thermal_anomalies_count: number;
    weather: Record<string, unknown> | null;
  };
  generated_at: string;
}

export interface DemoStory {
  title: string;
  city_code: string;
  city_name: string;
  steps: Array<{
    id: number;
    title: string;
    description: string;
    endpoint: string;
    key_data: Record<string, unknown>;
  }>;
  supporting_endpoints: Record<string, string>;
}

export interface GeoFeatureCollection {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: Record<string, unknown>;
    geometry: GeoJSON.Geometry;
  }>;
}

export interface HealthOverlay {
  ward_id: number;
  ward_code: string;
  ward_name: string;
  centroid_lat: number;
  centroid_lon: number;
  current_aqi: number;
  vulnerability_index: number;
  population: number;
  nearby_institutions: number;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  env: string;
  data_mode: string;
  database_ok: boolean;
  database_error: string | null;
  timestamp: string;
}
