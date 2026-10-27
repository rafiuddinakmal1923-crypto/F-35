// Small SVG charts with no chart library: line chart with an uncertainty band, bar chart,
// and the neighbour voltage strip. Colours come from CSS tokens so both themes work.

const W = 640;

function scale(domain, range) {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0 || 1;
  return (v) => r0 + ((v - d0) / span) * (r1 - r0);
}

function niceTicks(min, max, count = 4) {
  if (!isFinite(min) || !isFinite(max)) return [];
  if (min === max) return [min];
  const step = Math.pow(10, Math.floor(Math.log10((max - min) / count)));
  const err = ((max - min) / count) / step;
  const mult = err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1;
  const s = step * mult;
  const ticks = [];
  for (let v = Math.ceil(min / s) * s; v <= max + 1e-9; v += s) ticks.push(Number(v.toFixed(6)));
  return ticks;
}

export function LineChart({ series, height = 220, xLabels, yLabel, markers = [] }) {
  const pad = { l: 48, r: 12, t: 10, b: 26 };
  const n = Math.max(...series.map((s) => s.values.length), 1);
  const all = series.flatMap((s) => [...s.values, ...(s.band ? s.band.flat() : [])]).filter((v) => v != null && isFinite(v));
  const lo = Math.min(0, ...all);
  const hi = Math.max(...all, 1);
  const x = scale([0, n - 1], [pad.l, W - pad.r]);
  const y = scale([lo, hi], [height - pad.b, pad.t]);
  // Gaps (null values) break the line into separate segments instead of bridging them.
  const path = (vals) => {
    let d = "";
    let pen = "M";
    vals.forEach((v, i) => {
      if (v == null || !isFinite(v)) { pen = "M"; return; }
      d += `${pen}${x(i)},${y(v)} `;
      pen = "L";
    });
    return d.trim();
  };
  const every = Math.max(1, Math.ceil(n / 7));
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={yLabel}>
        <g className="axis">
          {niceTicks(lo, hi).map((tv) => (
            <g key={tv}>
              <line className="grid-line" x1={pad.l} x2={W - pad.r} y1={y(tv)} y2={y(tv)} />
              <text x={pad.l - 6} y={y(tv) + 3} textAnchor="end">{tv}</text>
            </g>
          ))}
          {xLabels?.map((label, i) => (i % every === 0 ? <text key={i} x={x(i)} y={height - 8} textAnchor="middle">{label}</text> : null))}
          {yLabel ? <text x={10} y={pad.t + 4} textAnchor="start">{yLabel}</text> : null}
        </g>
        {series.map((s) =>
          s.band ? (
            <path key={`${s.name}-band`} fill="var(--band)" stroke="none"
              d={`M${s.band.map(([l], i) => `${x(i)},${y(l)}`).join(" L")} L${s.band.map(([, h], i) => [i, h]).reverse().map(([i, h]) => `${x(i)},${y(h)}`).join(" L")} Z`} />
          ) : null,
        )}
        {markers.map((m) => (
          <g key={m.label}>
            <line x1={x(m.index)} x2={x(m.index)} y1={pad.t} y2={height - pad.b} stroke="var(--accent)" strokeDasharray="4 3" />
            <text x={x(m.index) + 4} y={pad.t + 10} fontSize="10" fill="var(--muted)">{m.label}</text>
          </g>
        ))}
        {series.map((s) => path(s.values) && (
          <path key={s.name} d={path(s.values)} fill="none" stroke={s.color} strokeWidth={s.width || 2}
            strokeDasharray={s.dashed ? "5 4" : undefined} />
        ))}
      </svg>
      <div className="legend">
        {series.map((s) => <span key={s.name} style={{ "--c": s.color }}>{s.name}</span>)}
      </div>
    </div>
  );
}

export function BarChart({ values, labels, height = 160, color = "var(--series-4)", yLabel }) {
  const pad = { l: 40, r: 8, t: 10, b: 22 };
  const hi = Math.max(...values.map((v) => v ?? 0), 0.001);
  const lo = Math.min(0, ...values.map((v) => v ?? 0));
  const y = scale([lo, hi], [height - pad.b, pad.t]);
  const bw = (W - pad.l - pad.r) / values.length;
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={yLabel}>
        <g className="axis">
          {niceTicks(lo, hi, 3).map((tv) => (
            <g key={tv}>
              <line className="grid-line" x1={pad.l} x2={W - pad.r} y1={y(tv)} y2={y(tv)} />
              <text x={pad.l - 6} y={y(tv) + 3} textAnchor="end">{tv}</text>
            </g>
          ))}
          {labels.map((l, i) => (i % 3 === 0 ? <text key={i} x={pad.l + bw * i + bw / 2} y={height - 6} textAnchor="middle">{l}</text> : null))}
        </g>
        {values.map((v, i) => (
          <rect key={i} x={pad.l + bw * i + 1} width={Math.max(bw - 2, 1)} y={Math.min(y(v ?? 0), y(0))}
            height={Math.abs(y(v ?? 0) - y(0))} fill={color} rx="2" />
        ))}
      </svg>
    </div>
  );
}

// Unexplained voltage drop along each phase/branch; the fitted tap position is marked.
export function VoltageStrip({ groups, highlight, minDropV = 0.4 }) {
  if (!groups?.length) return <p className="muted">No voltage result for this zone.</p>;
  const rowH = 54;
  const pad = { l: 70, r: 12 };
  const maxPos = Math.max(...groups.flatMap((g) => g.positions), 1);
  const minSig = Math.min(...groups.flatMap((g) => g.signal_v), -0.5);
  const x = scale([0, maxPos], [pad.l, W - pad.r]);
  const height = rowH * groups.length + 20;
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label="Neighbour voltage strip">
        {groups.map((g, gi) => {
          const top = 10 + gi * rowH;
          const yv = scale([0, minSig], [top + 6, top + rowH - 8]);
          return (
            <g key={g.group}>
              <text x={4} y={top + 20} fontSize="11" fill="var(--muted)">{g.group}</text>
              <line x1={pad.l} x2={W - pad.r} y1={yv(0)} y2={yv(0)} stroke="var(--border)" />
              {/* A fitted position is only a located tap when its drop is above the noise level. */}
              {g.fitted_drop_v >= minDropV ? (
                <line x1={x(g.tap_position)} x2={x(g.tap_position)} y1={top + 2} y2={top + rowH - 4} stroke="var(--accent)" strokeDasharray="3 3" />
              ) : null}
              {g.positions.map((p, i) => {
                const pid = g.premises[i];
                const hot = pid === highlight;
                return (
                  <g key={pid}>
                    <line x1={x(p)} x2={x(p)} y1={yv(0)} y2={yv(Math.min(g.signal_v[i], 0))} stroke={hot ? "var(--risk)" : "var(--series-1)"} strokeWidth={hot ? 4 : 2} />
                    <circle cx={x(p)} cy={yv(Math.min(g.signal_v[i], 0))} r={hot ? 4 : 2.5} fill={hot ? "var(--risk)" : "var(--series-1)"} />
                    <title>{`${pid}: ${g.signal_v[i]} V`}</title>
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      <div className="legend">
        <span style={{ "--c": "var(--series-1)" }}>Unexplained voltage drop (V) by distance from the transformer</span>
        <span style={{ "--c": "var(--accent)" }}>Estimated hidden-load position</span>
      </div>
    </div>
  );
}
