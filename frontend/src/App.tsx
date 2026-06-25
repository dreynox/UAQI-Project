import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "@/components/Layout";
import OverviewPage from "@/pages/Overview";
import MapPage from "@/pages/Map";
import WardDetailPage from "@/pages/WardDetail";
import EnforcementPage from "@/pages/Enforcement";
import ComparePage from "@/pages/Compare";
import HealthOverlayPage from "@/pages/HealthOverlay";
import StoryPage from "@/pages/Story";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<OverviewPage />} />
        <Route path="/city/:code" element={<OverviewPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/map/:code" element={<MapPage />} />
        <Route path="/ward/:wardId" element={<WardDetailPage />} />
        <Route path="/enforcement" element={<EnforcementPage />} />
        <Route path="/enforcement/:code" element={<EnforcementPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/health" element={<HealthOverlayPage />} />
        <Route path="/health/:code" element={<HealthOverlayPage />} />
        <Route path="/story" element={<StoryPage />} />
        <Route path="/story/:code" element={<StoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
