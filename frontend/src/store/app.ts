/**
 * Global UI state (lightweight, persisted in memory only).
 * Backend data lives in React Query — this is for selected city + theme.
 */

import { create } from "zustand";

export type CityCode = "DEL" | "BLR" | "BOM";

interface AppState {
  selectedCity: CityCode;
  setSelectedCity: (code: CityCode) => void;

  // Side panel for ward drilldown
  selectedWardId: number | null;
  setSelectedWardId: (id: number | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedCity: "DEL",
  setSelectedCity: (code) => set({ selectedCity: code, selectedWardId: null }),

  selectedWardId: null,
  setSelectedWardId: (id) => set({ selectedWardId: id }),
}));
