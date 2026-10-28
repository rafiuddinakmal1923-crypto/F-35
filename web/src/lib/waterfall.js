// Reason waterfall (UI brief 3.3): each reason's contribution as a step from the running total,
// legitimate-use penalties as negative steps, "other" and "capped" lines, ending exactly at the score.
// The API's reason lines already add up to the score (FR-PS-07); this only lays them out.

const ADJUST = new Set(["other", "capped"]);

export function waterfall(reasons, score) {
  let run = 0;
  const rows = (reasons || []).map((r) => {
    const c = Number(r.contribution) || 0;
    const start = run;
    run += c;
    const kind = ADJUST.has(r.feature) ? "adj" : c < 0 ? "neg" : "pos";
    return { ...r, contribution: c, start, end: run, kind };
  });
  const points = [0, score ?? 0, ...rows.flatMap((r) => [r.start, r.end])];
  const min = Math.min(0, ...points);
  const max = Math.max(1, ...points);
  return { rows, sum: run, min, max, exact: score == null || Math.abs(run - score) < 0.6 };
}

// Position of a value on the track, in percent of the track width.
export function at(v, { min, max }) {
  return ((v - min) / (max - min || 1)) * 100;
}

export function barStyle(row, domain) {
  const a = at(Math.min(row.start, row.end), domain);
  const b = at(Math.max(row.start, row.end), domain);
  return { left: `${a}%`, width: `${Math.max(b - a, 0.6)}%` };
}

// SHAP sub-reasons of the pattern model, scaled to the largest absolute value.
export function shapRows(shap) {
  const list = (shap || []).filter((s) => Number.isFinite(Number(s.shap)));
  const top = Math.max(...list.map((s) => Math.abs(s.shap)), 1e-9);
  return list.map((s) => ({ ...s, share: Math.abs(s.shap) / top, positive: s.shap > 0 }));
}
