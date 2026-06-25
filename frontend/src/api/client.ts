/**
 * Axios-based API client targeting the FastAPI backend.
 *
 * All responses are unwrapped from the { data, meta, warnings, error } envelope.
 */

import axios from "axios";

const baseURL = (import.meta.env.VITE_API_BASE as string) || "/api";

export const api = axios.create({
  baseURL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (resp) => resp,
  (err) => {
    // Surface backend error envelopes for the UI
    const payload = err?.response?.data;
    const message =
      payload?.error?.message ||
      payload?.detail ||
      err.message ||
      "Network error";
    return Promise.reject(new Error(message));
  }
);

/** Helper: extract `data` field from envelope (with fallback). */
export function unwrap<T>(payload: { data: T } | T): T {
  if (payload && typeof payload === "object" && "data" in (payload as object)) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

/** GET helper that auto-unwraps the envelope. */
export async function getEnvelope<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const { data } = await api.get(url, { params });
  return unwrap<T>(data);
}
