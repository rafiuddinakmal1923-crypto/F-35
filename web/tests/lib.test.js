// Pure helpers behind the new components: reason waterfall, feeder schematic, value-at-risk labels.
import assert from "node:assert/strict";
import { test } from "node:test";
import { change, riskValue } from "../src/lib/format.js";
import { layoutSchematic, riskMix, schematicSummary } from "../src/lib/schematic.js";
import { shapRows, waterfall } from "../src/lib/waterfall.js";

const REASONS = [
  { feature: "voltage_proximity", contribution: 40.2, reason_text: "Neighbours show a drop" },
  { feature: "gap_from_similar", contribution: 30.1, reason_text: "Use is 60% below similar homes" },
  { feature: "tag:solar", contribution: -10.0, reason_text: "Drop explained by rooftop solar" },
  { feature: "other", contribution: 12.7, reason_text: "Other evidence" },
];

test("3.3 waterfall: running steps end exactly at the score, penalties step down", () => {
  const wf = waterfall(REASONS, 73);
  assert.equal(wf.rows.length, 4);
  assert.ok(Math.abs(wf.sum - 73) < 1e-9 && wf.exact);
  assert.equal(wf.rows[2].kind, "neg");
  assert.ok(Math.abs(wf.rows[2].start - 70.3) < 1e-9);
  assert.equal(wf.rows[3].kind, "adj");
  for (let i = 1; i < wf.rows.length; i += 1) assert.equal(wf.rows[i].start, wf.rows[i - 1].end);
  assert.ok(wf.min <= 0 && wf.max >= 73);
});

test("3.3 waterfall flags lines that do not add up", () => {
  assert.equal(waterfall(REASONS, 80).exact, false);
});

test("3.3 SHAP sub-reasons scale to the largest absolute value and keep their sign", () => {
  const rows = shapRows([{ feature: "trend", shap: 0.8 }, { feature: "cv", shap: -0.4 }]);
  assert.deepEqual(rows.map((r) => [r.share, r.positive]), [[1, true], [0.5, false]]);
});

const SUSPECTS = [
  { premise_id: "P-1", rank: 1, score: 94, phase: "B", feeder_branch: "B2", street_seq: 7 },
  { premise_id: "P-2", rank: 2, score: 23, phase: "B", feeder_branch: "B2", street_seq: 3 },
  { premise_id: "P-3", rank: 3, score: 12, phase: "A", feeder_branch: "B1", street_seq: 1 },
  { premise_id: "P-4", rank: 4, score: 5, phase: null, feeder_branch: null, street_seq: 2 },
];
const VOLTAGE = { available: true, groups: [
  { group: "B2/B", premises: ["P-2", "P-1"], positions: [40, 120], signal_v: [-0.3, -1.4], tap_position: 118, fitted_drop_v: 1.4 },
] };

test("3.2 schematic: a lane per phase, branches as lines, premises in street order", () => {
  const s = layoutSchematic({ suspects: SUSPECTS, voltage: VOLTAGE, minDropV: 0.4 });
  assert.deepEqual(s.lanes.map((l) => l.phase), ["A", "B", "?"]);
  const b2 = s.lanes[1].branches[0];
  assert.deepEqual(b2.nodes.map((n) => n.id), ["P-2", "P-1"]);          // street order, not rank order
  assert.ok(b2.nodes[0].x < b2.nodes[1].x);
  assert.equal(b2.tap.x, b2.nodes[1].x);                                  // fitted tap marked at the nearest node
  assert.ok(b2.dip.every((d) => d.depth >= 0 && d.depth <= 1));
  assert.equal(s.top.id, "P-1");
  assert.equal(schematicSummary(s).deepest.id, "P-1");
  assert.ok(s.nodes.every((n) => !("lat" in n) && !("lon" in n)));       // no locations
});

test("3.2 schematic without voltage data has no overlay and no tap", () => {
  const s = layoutSchematic({ suspects: SUSPECTS, voltage: { available: false, groups: [] } });
  assert.equal(s.overlay, false);
  assert.ok(s.lanes.every((l) => l.branches.every((b) => b.tap === null && b.dip === null)));
});

test("3.2 a fitted drop below the noise level marks no tap", () => {
  const s = layoutSchematic({ suspects: SUSPECTS, voltage: VOLTAGE, minDropV: 2 });
  assert.equal(s.lanes[1].branches[0].tap, null);
  assert.equal(riskMix(120), 1);
  assert.equal(riskMix(0), 0);
});

test("3.1 value at risk: RM only with a tariff, otherwise kWh and the placeholder", () => {
  const value = { kwh_per_month: 3000, rm_per_month: null, estimate: true };
  const noTariff = riskValue(value, { rm_per_kwh: null, placeholder: "[TNB domestic tariff: to confirm]" });
  assert.deepEqual(noTariff, { kind: "kwh", kwh: 3000, placeholder: "[TNB domestic tariff: to confirm]" });
  assert.equal(riskValue({ ...value, rm_per_month: 1500 }, { rm_per_kwh: 0.5 }).amount, 1500);
  assert.equal(riskValue(null, {}).kind, "none");
});

test("KPI change compares the last value with the one before", () => {
  assert.deepEqual(change([10, null, 8, 12]), { delta: 4, pct: 0.5 });
  assert.equal(change([5]), null);
});
