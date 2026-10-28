// Number formatting and small derivations shared by pages (pure functions, tested in web/tests).

export const fmt = (v, digits = 1) => (v == null || Number.isNaN(Number(v)) ? "–" : Number(v).toFixed(digits));
export const pct = (v, digits = 1) => (v == null || Number.isNaN(Number(v)) ? "–" : `${(Number(v) * 100).toFixed(digits)}%`);

export function int(v, lang = "en") {
  if (v == null || Number.isNaN(Number(v))) return "–";
  return Math.round(Number(v)).toLocaleString(lang === "ms" ? "ms-MY" : "en-MY");
}

// Change of the last value against the one before (KPI tiles: "vs the day before").
export function change(series) {
  const v = (series || []).filter((x) => x != null && Number.isFinite(Number(x))).map(Number);
  if (v.length < 2) return null;
  const last = v[v.length - 1];
  const prev = v[v.length - 2];
  return { delta: last - prev, pct: prev ? (last - prev) / Math.abs(prev) : null };
}

// Value-at-risk label: RM when a tariff is set, otherwise kWh with the tariff placeholder. Never a guessed RM.
export function riskValue(value, tariff) {
  if (!value) return { kind: "none" };
  if (value.rm_per_month != null && tariff?.rm_per_kwh) return { kind: "rm", amount: value.rm_per_month, kwh: value.kwh_per_month };
  return { kind: "kwh", kwh: value.kwh_per_month, placeholder: tariff?.placeholder || "[TNB domestic tariff: to confirm]" };
}

export function hitRate(h) {
  return h && h.inspections ? h.confirmed_theft / h.inspections : null;
}

// Linear scale helper for SVG charts.
export function scale([d0, d1], [r0, r1]) {
  const span = d1 - d0 || 1;
  return (v) => r0 + ((v - d0) / span) * (r1 - r0);
}

export function daysBetween(a, b) {
  return Math.round((new Date(b) - new Date(a)) / 86400000);
}
