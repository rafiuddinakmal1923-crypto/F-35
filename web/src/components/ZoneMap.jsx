// Map of zones (FR-UI-01): transformer positions only, never premise locations. Dots are sized by the
// recent gap (kWh/day) and coloured by status; large-load priority zones get a pulse ring. Offline, the
// map keeps a plain grid with the dots (BaseTiles reports that no tiles load).
import { CircleMarker, MapContainer, Tooltip } from "react-leaflet";
import { useState } from "react";
import "leaflet/dist/leaflet.css";
import BaseTiles from "./BaseTiles.jsx";
import { fmt, pct } from "../lib/format.js";
import { t } from "../i18n.js";
import { useTheme } from "../theme.js";

const COLOURS = {
  dark: { flagged: "#F2A33A", balanced: "#2DD4BF", none: "#7F93AE" },
  light: { flagged: "#B45F06", balanced: "#0F766E", none: "#64748B" },
};

export function dotRadius(gapKwh) {
  return 7 + Math.min(Math.sqrt(Math.max(Number(gapKwh) || 0, 0)) * 1.4, 22);
}

export default function ZoneMap({ zones, onSelect, hero = false }) {
  const [noTiles, setNoTiles] = useState(false);
  const theme = useTheme();
  const c = COLOURS[theme] || COLOURS.dark;
  const placed = zones.filter((z) => z.lat != null && z.lon != null);
  if (!placed.length) return <p className="muted">{t("noZonePositions")}</p>;
  const lat = placed.reduce((s, z) => s + z.lat, 0) / placed.length;
  const lon = placed.reduce((s, z) => s + z.lon, 0) / placed.length;
  const spread = Math.max(...placed.map((z) => Math.abs(z.lat - lat)), ...placed.map((z) => Math.abs(z.lon - lon)));
  const zoom = spread > 1 ? 7 : spread > 0.2 ? 10 : 12;
  const colour = (z) => (!z.balance_available ? c.none : z.flagged ? c.flagged : c.balanced);
  return (
    <div className={`map ${hero ? "hero" : ""}`}>
      <MapContainer center={[lat, lon]} zoom={zoom} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false} attributionControl>
        <BaseTiles onUnavailable={() => setNoTiles(true)} />
        {placed.filter((z) => z.priority === "large_load").map((z) => (
          <CircleMarker key={`${z.transformer_id}-pulse`} center={[z.lat, z.lon]} radius={dotRadius(z.gap_kwh_recent) + 4} interactive={false}
            pathOptions={{ color: colour(z), fill: false, weight: 2, className: "pulse-ring" }} />
        ))}
        {placed.map((z) => (
          <CircleMarker key={z.transformer_id} center={[z.lat, z.lon]} radius={dotRadius(z.balance_available ? z.gap_kwh_recent : 0)}
            pathOptions={{ color: colour(z), fillColor: colour(z), fillOpacity: 0.55, weight: 2 }}
            eventHandlers={{ click: () => onSelect?.(z) }}>
            <Tooltip>{`${z.transformer_id} · ${z.district} · ${z.balance_available ? `${t("gap")} ${pct(z.gap_pct_recent)} · ${fmt(z.gap_kwh_recent, 0)} kWh/${t("day")}` : t("pillNoBalance")}${z.flagged ? ` · ${t("pillFlagged")}` : ""}${z.priority === "large_load" ? ` · ${t("largeLoad")}` : ""}`}</Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
      <div className="map-legend" aria-hidden="true">
        <span><i style={{ background: c.flagged }} />{t("pillFlagged")}</span>
        <span><i style={{ background: c.balanced }} />{t("pillBalanced")}</span>
        <span><i style={{ background: c.none }} />{t("pillNoBalance")}</span>
        <span><i style={{ background: "transparent", border: `2px solid ${c.flagged}` }} />{t("largeLoad")}</span>
        <small>{t("dotSize")}</small>
      </div>
      {noTiles ? <small className="map-note">{t("mapOffline")}</small> : null}
    </div>
  );
}
