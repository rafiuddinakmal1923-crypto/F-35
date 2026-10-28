// Feeder schematic layout (UI brief 3.2): transformer at the left, each phase a lane, each branch a line,
// premises as nodes in street order. Uses only the ranked suspects (phase, branch, street order, score)
// and the voltage groups (residual per premise): no coordinates and no exact locations.

const PHASES = ["A", "B", "C"];

export function riskMix(score) {
  // 0 (grey) .. 1 (amber): node colour as a mix of the neutral and accent tokens.
  return Math.max(0, Math.min(1, (Number(score) || 0) / 60));
}

export function layoutSchematic({ suspects, voltage, width = 760, minDropV = 0.4 }) {
  const list = suspects || [];
  const groups = voltage?.available === false ? [] : voltage?.groups || [];
  const residual = new Map();
  const tapByGroup = new Map();
  for (const g of groups) {
    g.premises.forEach((p, i) => residual.set(p, g.signal_v[i]));
    if (g.fitted_drop_v >= minDropV) tapByGroup.set(g.group, g);
  }
  const lanesBy = new Map();
  for (const s of list) {
    const phase = PHASES.includes(s.phase) ? s.phase : "?";
    if (!lanesBy.has(phase)) lanesBy.set(phase, new Map());
    const branch = s.feeder_branch || "?";
    const br = lanesBy.get(phase);
    if (!br.has(branch)) br.set(branch, []);
    br.get(branch).push(s);
  }
  const left = 96;
  const right = 18;
  const branchH = 34;
  const lanePad = 14;
  const order = [...PHASES, "?"].filter((p) => lanesBy.has(p));
  let y = 10;
  const lanes = [];
  let maxDip = 0.0001;
  for (const v of residual.values()) if (v < 0) maxDip = Math.max(maxDip, -v);
  for (const phase of order) {
    const branches = [...lanesBy.get(phase).entries()].sort(([a], [b]) => String(a).localeCompare(String(b)));
    const top = y;
    const rows = branches.map(([name, members], bi) => {
      const by = top + lanePad + bi * branchH + branchH / 2;
      const sorted = [...members].sort((a, b) => (a.street_seq ?? 0) - (b.street_seq ?? 0) || String(a.premise_id).localeCompare(b.premise_id));
      const n = sorted.length;
      const span = width - left - right - 30;
      const nodes = sorted.map((s, i) => ({
        id: s.premise_id, rank: s.rank, score: s.score, x: left + 30 + (n === 1 ? span / 2 : (i / (n - 1)) * span), y: by,
        residual: residual.has(s.premise_id) ? residual.get(s.premise_id) : null, mix: riskMix(s.score),
      }));
      const tapGroup = tapByGroup.get(`${name}/${phase}`);
      let tap = null;
      if (tapGroup && nodes.length) {
        // The fitted tap sits at a feeder distance; mark the node nearest to it in street order.
        const nearest = tapGroup.premises.reduce((best, p, i) => {
          const d = Math.abs(tapGroup.positions[i] - tapGroup.tap_position);
          return d < best.d ? { d, p } : best;
        }, { d: Infinity, p: null });
        const node = nodes.find((nd) => nd.id === nearest.p);
        if (node) tap = { x: node.x, dropV: tapGroup.fitted_drop_v };
      }
      // Dip overlay: residual below zero drawn as a shaded profile under the branch line.
      const withV = nodes.filter((nd) => nd.residual != null);
      const dip = withV.length >= 2 ? withV.map((nd) => ({ x: nd.x, depth: Math.max(-nd.residual, 0) / maxDip })) : null;
      return { name, y: by, nodes, tap, dip };
    });
    const h = lanePad * 2 + rows.length * branchH;
    lanes.push({ phase, top, height: h, branches: rows });
    y += h + 8;
  }
  const nodes = lanes.flatMap((l) => l.branches.flatMap((b) => b.nodes));
  const topNode = nodes.reduce((best, nd) => (best == null || nd.rank < best.rank ? nd : best), null);
  return { width, height: Math.max(y, 80), left, lanes, nodes, top: topNode, overlay: groups.length > 0, maxDipV: maxDip };
}

export function schematicSummary(layout) {
  const branches = layout.lanes.reduce((s, l) => s + l.branches.length, 0);
  const deepest = layout.nodes.reduce((best, nd) => (nd.residual != null && (best == null || nd.residual < best.residual) ? nd : best), null);
  return { phases: layout.lanes.length, branches, premises: layout.nodes.length, top: layout.top, deepest };
}
