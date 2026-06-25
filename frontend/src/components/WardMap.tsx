import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import L from "leaflet";
import { aqiColor, aqiLabel, formatNumber } from "@/lib/aqi";

interface Props {
  cityCode: string;
  geojson: GeoJSON.FeatureCollection;
  center: [number, number];
  zoom: number;
  layerOverlays: Record<string, GeoJSON.FeatureCollection | undefined>;
}

function FitBounds({ geojson }: { geojson: GeoJSON.FeatureCollection }) {
  const map = useMap();
  useEffect(() => {
    const layer = L.geoJSON(geojson as GeoJSON.GeoJsonObject);
    const b = layer.getBounds();
    if (b.isValid()) {
      map.fitBounds(b, { padding: [20, 20] });
    }
  }, [geojson, map]);
  return null;
}

const LAYER_COLOR: Record<string, string> = {
  institutions: "#7dd3fc",
  industry: "#a21caf",
  construction: "#eab308",
  thermal: "#ef4444",
};

export default function WardMap({ cityCode, geojson, center, zoom, layerOverlays }: Props) {
  // Style function for ward polygons
  const wardStyle = (feature?: GeoJSON.Feature) => {
    const aqi = (feature?.properties as { current_aqi?: number })?.current_aqi ?? 0;
    return {
      fillColor: aqiColor(aqi),
      fillOpacity: 0.55,
      color: "#0a0e1a",
      weight: 0.5,
    };
  };

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height: "100%", width: "100%" }}
      scrollWheelZoom
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />
      <FitBounds geojson={geojson} />
      <GeoJSON
        key={`wards-${cityCode}`}
        data={geojson as GeoJSON.GeoJsonObject}
        style={wardStyle}
        onEachFeature={(feature, layer) => {
          const p = feature.properties as {
            id: number;
            name: string;
            current_aqi: number;
            vulnerability_index: number;
            population: number;
          };
          layer.bindPopup(
            `<div style="min-width:180px">
              <div style="font-weight:600;font-size:13px">${p.name}</div>
              <div style="font-size:11px;color:#94a3b8">AQI: <b style="color:${aqiColor(
                p.current_aqi
              )}">${formatNumber(p.current_aqi)}</b> · ${aqiLabel(p.current_aqi)}</div>
              <div style="font-size:11px;color:#94a3b8">Vuln: ${formatNumber(
                p.vulnerability_index
              )} · Pop: ${formatNumber(p.population)}</div>
              <a href="/ward/${p.id}" style="color:#7dd3fc;font-size:11px">Open detail →</a>
            </div>`
          );
          layer.on({
            mouseover: (e) => {
              const target = e.target as L.Path;
              target.setStyle({ fillOpacity: 0.85, weight: 1.5 });
            },
            mouseout: (e) => {
              const target = e.target as L.Path;
              target.setStyle({ fillOpacity: 0.55, weight: 0.5 });
            },
          });
        }}
      />
      {Object.entries(layerOverlays).map(([key, gj]) => {
        if (!gj) return null;
        const color = LAYER_COLOR[key] || "#7dd3fc";
        return (
          <GeoJSON
            key={`layer-${key}`}
            data={gj as GeoJSON.GeoJsonObject}
            pointToLayer={(_feature, latlng) =>
              L.circleMarker(latlng, {
                radius: key === "thermal" ? 3 : 5,
                color,
                fillColor: color,
                fillOpacity: 0.6,
                weight: 0.5,
              })
            }
            onEachFeature={(feature, lyr) => {
              const props = feature.properties as Record<string, unknown>;
              const summary = Object.entries(props)
                .slice(0, 4)
                .map(([k, v]) => `${k}: ${v}`)
                .join("<br/>");
              lyr.bindPopup(`<div style="font-size:11px">${summary}</div>`);
            }}
          />
        );
      })}
    </MapContainer>
  );
}