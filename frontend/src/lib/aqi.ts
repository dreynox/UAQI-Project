/**
 * AQI helpers — CPCB breakpoint mapping + display formatting.
 */

import type { PriorityScore, RecommendedAction } from "@/api/types";

export type AqiCategory =
  | "good"
  | "satisfactory"
  | "moderate"
  | "poor"
  | "very_poor"
  | "severe";

export function aqiCategory(aqi: number): AqiCategory {
  if (aqi <= 50) return "good";
  if (aqi <= 100) return "satisfactory";
  if (aqi <= 200) return "moderate";
  if (aqi <= 300) return "poor";
  if (aqi <= 400) return "very_poor";
  return "severe";
}

export const AQI_COLOR: Record<AqiCategory, string> = {
  good: "#22c55e",
  satisfactory: "#84cc16",
  moderate: "#eab308",
  poor: "#f97316",
  very_poor: "#ef4444",
  severe: "#a21caf",
};

export const AQI_LABEL: Record<AqiCategory, string> = {
  good: "Good",
  satisfactory: "Satisfactory",
  moderate: "Moderate",
  poor: "Poor",
  very_poor: "Very Poor",
  severe: "Severe",
};

export function aqiColor(aqi: number): string {
  return AQI_COLOR[aqiCategory(aqi)];
}

export function aqiLabel(aqi: number): string {
  return AQI_LABEL[aqiCategory(aqi)];
}

export const URGENCY_COLOR: Record<string, string> = {
  low: "#22c55e",
  medium: "#eab308",
  high: "#f97316",
  critical: "#ef4444",
};

export function urgencyColor(urgency: string): string {
  return URGENCY_COLOR[urgency] || "#64748b";
}

export function formatNumber(n: number | null | undefined, digits = 0): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toLocaleString("en-IN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export const SOURCE_LABEL_EN: Record<string, string> = {
  traffic: "Vehicular traffic",
  construction: "Construction dust",
  industrial: "Industrial emissions",
  stubble_burning: "Crop stubble burning",
  biomass_burning: "Biomass burning",
  waste_burning: "Waste burning",
  urban_form: "Dense built-up",
  mixed: "Multiple sources",
};

export function sourceLabel(source: string): string {
  return SOURCE_LABEL_EN[source] || source;
}

export const LANGUAGE_LABEL: Record<string, string> = {
  en: "English",
  hi: "हिन्दी (Hindi)",
  kn: "ಕನ್ನಡ (Kannada)",
  ta: "தமிழ் (Tamil)",
};

export function languageLabel(code: string): string {
  return LANGUAGE_LABEL[code] || code.toUpperCase();
}

/** Recharts-friendly palette for breakdowns */
export const SOURCE_CHART_COLORS: Record<string, string> = {
  traffic: "#f97316",
  construction: "#eab308",
  industrial: "#a21caf",
  stubble_burning: "#dc2626",
  biomass_burning: "#f43f5e",
  waste_burning: "#fb923c",
  urban_form: "#7dd3fc",
  mixed: "#94a3b8",
};

export function actionIcon(code: string): string {
  switch (code) {
    case "inspection":
      return "🔍";
    case "dust_control":
      return "💧";
    case "traffic_diversion":
      return "🚦";
    case "waste_burning":
      return "🚒";
    case "industrial_audit":
      return "🏭";
    case "public_advisory":
      return "📢";
    case "odd_even":
      return "🚗";
    case "construction_shutdown":
      return "🏗️";
    default:
      return "⚙️";
  }
}

export function topActionDelta(actions: RecommendedAction[] | undefined): number | null {
  if (!actions || actions.length === 0) return null;
  const primary = actions.find((a) => a.priority === "primary") ?? actions[0];
  const v = primary.estimated_aqi_delta ?? primary.expected_aqi_delta;
  return typeof v === "number" ? v : null;
}

export function priorityTone(score: PriorityScore): string {
  switch (score.urgency) {
    case "critical":
      return "bg-red-500/15 text-red-300 border-red-500/30";
    case "high":
      return "bg-orange-500/15 text-orange-300 border-orange-500/30";
    case "medium":
      return "bg-amber-500/15 text-amber-300 border-amber-500/30";
    case "low":
      return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
    default:
      return "bg-slate-500/15 text-slate-300 border-slate-500/30";
  }
}
