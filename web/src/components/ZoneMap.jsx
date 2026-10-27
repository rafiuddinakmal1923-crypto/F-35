// Map of zones by gap (FR-UI-01): transformer positions only, never premise locations.
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { pct } from "./Common.jsx";

export default function ZoneMap({ zones, onSelect }) {
  const placed = zones.filter((z) => z.lat != null && z.lon != null);
  if (!placed.length) return <p className="muted">No zone positions recorded.</p>;
  const lat = placed.reduce((s, z) => s + z.lat, 0) / placed.length;
  const lon = placed.reduce((s, z) => s + z.lon, 0) / placed.length;
  const spread = Math.max(...placed.map((z) => Math.abs(z.lat - lat)), ...placed.map((z) => Math.abs(z.lon - lon)));
  const zoom = spread > 1 ? 7 : spread > 0.2 ? 10 : 12;
  return (
    <div className="map">
      <MapContainer center={[lat, lon]} zoom={zoom} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
        {/* Tiles need internet; without it the circles still show on a blank map. OpenStreetMap refuses
            tiles without a Referer, and the site sends none (Caddyfile), so tiles alone send the origin. */}
        <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors"
          referrerPolicy="strict-origin" />
        {placed.map((z) => (
          <CircleMarker key={z.transformer_id} center={[z.lat, z.lon]}
            radius={6 + Math.min(Math.max((z.gap_pct_recent || 0) * 100, 0), 25)}
            pathOptions={{ color: z.flagged ? "#c2410c" : z.balance_available ? "#2563eb" : "#9a6700", fillOpacity: 0.45 }}
            eventHandlers={{ click: () => onSelect?.(z) }}>
            <Tooltip>{`${z.transformer_id} · ${z.district} · gap ${pct(z.gap_pct_recent)}${z.flagged ? " · flagged" : ""}`}</Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
