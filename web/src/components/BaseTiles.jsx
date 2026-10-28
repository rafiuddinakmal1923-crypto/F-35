// Map background with automatic fallback. OpenStreetMap's own tile servers refuse many requests
// from apps on localhost (they answer with an "Access blocked" picture), so CARTO's free basemap
// is tried first, then OpenStreetMap, then Esri. When a provider's tiles keep failing, the next one
// is used; when none load (no internet), the zones still show and a short note says why.
import { useEffect, useMemo, useState } from "react";
import { TileLayer } from "react-leaflet";

const dark = () => typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches;

export const PROVIDERS = [
  { name: "CARTO", url: `https://{s}.basemaps.cartocdn.com/${dark() ? "dark_all" : "rastertiles/voyager"}/{z}/{x}/{y}{r}.png`, subdomains: "abcd",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>' },
  { name: "OpenStreetMap", url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", referrerPolicy: "strict-origin",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' },
  { name: "Esri", url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: "Tiles &copy; Esri" },
];
const KEY = "vg_tiles";
const MAX_ERRORS = 4;

function startIndex() {
  try {
    const i = Number(sessionStorage.getItem(KEY));
    return Number.isInteger(i) && i >= 0 && i < PROVIDERS.length ? i : 0;
  } catch {
    return 0;
  }
}

export default function BaseTiles({ onUnavailable }) {
  const [index, setIndex] = useState(startIndex);
  const [counts, setCounts] = useState({ ok: 0, failed: 0 });
  const provider = PROVIDERS[index];

  useEffect(() => {
    if (counts.failed < MAX_ERRORS || counts.ok > 0) return;
    if (index + 1 < PROVIDERS.length) {
      try { sessionStorage.setItem(KEY, String(index + 1)); } catch { /* storage may be blocked */ }
      setIndex(index + 1);
      setCounts({ ok: 0, failed: 0 });
    } else {
      onUnavailable?.();
    }
  }, [counts, index, onUnavailable]);

  const handlers = useMemo(() => ({
    tileload: () => setCounts((c) => ({ ...c, ok: c.ok + 1 })),
    tileerror: () => setCounts((c) => ({ ...c, failed: c.failed + 1 })),
  }), []);

  return (
    <TileLayer key={provider.name} url={provider.url} attribution={provider.attribution} subdomains={provider.subdomains || "abc"}
      referrerPolicy={provider.referrerPolicy || "strict-origin"} eventHandlers={handlers} maxZoom={19} />
  );
}
