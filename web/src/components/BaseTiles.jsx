// Map background with automatic fallback, no API key needed, following the app theme (dark tiles in
// the dark theme). CARTO's basemaps now answer with "API KEY REQUIRED" pictures that load without an
// error (so no fallback could catch them), hence Esri's canvas basemaps first, then OpenStreetMap
// (its servers refuse many requests from localhost), then Esri streets. When a provider's tiles keep
// failing, the next one is used; when none load (offline), the map keeps its plain grid and the
// transformer dots, and a short note says why.
import { useEffect, useMemo, useState } from "react";
import { TileLayer } from "react-leaflet";
import { useTheme } from "../theme.js";

export function providers(theme) {
  return [
    { name: "Esri Canvas", maxNativeZoom: 16,
      url: `https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/${theme === "dark" ? "World_Dark_Gray_Base" : "World_Light_Gray_Base"}/MapServer/tile/{z}/{y}/{x}`,
      attribution: "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors" },
    { name: "OpenStreetMap", url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' },
    { name: "Esri", url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
      attribution: "Tiles &copy; Esri" },
  ];
}
export const PROVIDERS = providers("dark");
const KEY = "vg_tiles2";  // new key so browsers that saved the old CARTO choice start again
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
  const theme = useTheme();
  const list = useMemo(() => providers(theme), [theme]);
  const [index, setIndex] = useState(startIndex);
  const [counts, setCounts] = useState({ ok: 0, failed: 0 });
  const provider = list[index];

  useEffect(() => {
    if (counts.failed < MAX_ERRORS || counts.ok > 0) return;
    if (index + 1 < list.length) {
      try { sessionStorage.setItem(KEY, String(index + 1)); } catch { /* storage may be blocked */ }
      setIndex(index + 1);
      setCounts({ ok: 0, failed: 0 });
    } else {
      onUnavailable?.();
    }
  }, [counts, index, list.length, onUnavailable]);

  const handlers = useMemo(() => ({
    tileload: () => setCounts((c) => ({ ...c, ok: c.ok + 1 })),
    tileerror: () => setCounts((c) => ({ ...c, failed: c.failed + 1 })),
  }), []);

  return (
    <TileLayer key={`${provider.name}-${theme}`} url={provider.url} attribution={provider.attribution} subdomains={provider.subdomains || "abc"}
      referrerPolicy="strict-origin" eventHandlers={handlers} maxNativeZoom={provider.maxNativeZoom || 19} maxZoom={19} />
  );
}
