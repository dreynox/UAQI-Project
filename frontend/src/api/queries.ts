/**
 * High-level endpoint functions (one per backend route). Components call these
 * directly via React Query.
 */

import { getEnvelope } from "./client";
import type {
  Advisory,
  AttributionResult,
  City,
  CityAdvisory,
  CityOverview,
  CompareCity,
  CompareInterventionRow,
  DemoScenario,
  DemoStory,
  EnforcementQueueItem,
  GeoFeatureCollection,
  HealthOverlay,
  HealthStatus,
  Ward,
  WardEnforcement,
  WardForecast,
} from "./types";

export const fetchHealth = () => getEnvelope<HealthStatus>("/health");

export const fetchCities = () => getEnvelope<City[]>("/cities");

export const fetchCityOverview = (code: string) =>
  getEnvelope<CityOverview>(`/cities/${code}/overview`);

export const fetchCityWards = (code: string) =>
  getEnvelope<Ward[]>(`/cities/${code}/wards`);

export const fetchCityHotspots = (code: string, limit = 10) =>
  getEnvelope<Ward[]>(`/cities/${code}/hotspots`, { limit });

export const fetchWard = (wardId: number) => getEnvelope<Ward>(`/wards/${wardId}`);

export const fetchWardGeo = (code: string) =>
  getEnvelope<GeoFeatureCollection>(`/cities/${code}/geo/wards`);

export const fetchLayer = (code: string, layer: string) =>
  getEnvelope<GeoFeatureCollection>(`/cities/${code}/geo/layers/${layer}`);

export const fetchAttribution = (wardId: number) =>
  getEnvelope<AttributionResult>(`/wards/${wardId}/attribution`);

export const fetchForecast = (wardId: number, horizons = "24,48,72") =>
  getEnvelope<WardForecast>(`/wards/${wardId}/forecast`, { horizons });

export const fetchEnforcementQueue = (code: string, limit = 10) =>
  getEnvelope<EnforcementQueueItem[]>(`/cities/${code}/enforcement/queue`, { limit });

export const fetchWardEnforcement = (code: string, wardId: number) =>
  getEnvelope<WardEnforcement>(`/cities/${code}/enforcement/${wardId}`);

export const fetchHealthOverlay = (code: string) =>
  getEnvelope<HealthOverlay[]>(`/cities/${code}/health/overlay`);

export const fetchAdvisory = (wardId: number, lang = "en") =>
  getEnvelope<Advisory>(`/wards/${wardId}/advisory`, { lang });

export const fetchCityAdvisory = (code: string) =>
  getEnvelope<CityAdvisory>(`/cities/${code}/advisory`);

export const fetchCompareCities = (metric = "aqi") =>
  getEnvelope<CompareCity[]>("/compare/cities", { metric });

export const fetchCompareInterventions = () =>
  getEnvelope<CompareInterventionRow[]>("/compare/interventions");

export const fetchCompareInterventionsForCity = (code: string) =>
  getEnvelope<CompareInterventionRow[]>(`/compare/interventions/${code}`);

export const fetchDemoScenario = (code: string) =>
  getEnvelope<DemoScenario>("/demo/scenario", { city_code: code });

export const fetchDemoStory = (code: string) =>
  getEnvelope<DemoStory>("/demo/story", { city_code: code });
