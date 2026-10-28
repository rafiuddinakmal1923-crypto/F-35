// Rooftop-solar check wording (FR-PS-10; Solar brief 4): the premise panel says what the scorer saw,
// in English and Bahasa Melayu, and never turns missing data into a number.
import assert from "node:assert/strict";
import { test } from "node:test";
import { setLang } from "../src/i18n.js";
import { checkValue, stillSuspect, verdictText } from "../src/lib/solar.js";

const SUSPECT = { verdict: "night_unexplained", night_drop: 0.4, night_below_peers: 0.52, night_by: "drop" };

test("verdict: solar explains only part of the drop when night use fell", () => {
  setLang("en");
  assert.equal(verdictText(SUSPECT), "Solar explains only part of the drop: night use fell 40%, still a suspect.");
  assert.equal(verdictText({ verdict: "explained" }), "Daytime drop explained by solar; night use normal: not counted as theft.");
  assert.ok(stillSuspect(SUSPECT) && stillSuspect({ verdict: "over_budget" }) && !stillSuspect({ verdict: "explained" }));
});

test("verdict names the signal that decided: similar homes when night use did not fall", () => {
  setLang("en");
  assert.match(verdictText({ verdict: "night_unexplained", night_drop: 0.02, night_below_peers: 0.6, night_by: "peers" }),
    /60% below similar homes/);
});

test("energy budget shows the numbers, labels a default, and asks for kWp when missing", () => {
  setLang("en");
  const over = { check: "energy_budget", status: "against",
    values: { drop_kwh: 9.25, expected_kwh: 1.2, capacity_kwp: 0.2, psh_source: "weather" } };
  assert.equal(checkValue(over), "drop 9.3 kWh/day vs at most 1.2 kWh/day from 0.2 kWp");
  assert.match(checkValue({ ...over, values: { ...over.values, psh_source: "assumed" } }), /\[peak sun hours: to confirm\]$/);
  assert.equal(checkValue({ check: "energy_budget", status: "no_data", values: {} }), "needs the registered capacity (kWp)");
});

test("day vs night: drops show as minus, the battery marks low confidence", () => {
  setLang("en");
  const c = { check: "day_vs_night", status: "pass",
    values: { day_drop: 0.55, night_drop: -0.03, night_below_peers: -0.1, window: "00:00-07:00", confidence: "low" } };
  assert.equal(checkValue(c), "daytime use −55%, night use +3% (00:00-07:00) (low confidence: home battery)");
});

test("missing weather or voltage reads as no data, never as zero", () => {
  setLang("en");
  assert.equal(checkValue({ check: "rain_rebound", status: "no_data", values: { rebound: null } }), "needs district sunshine data");
  assert.equal(checkValue({ check: "voltage", status: "no_data", values: {} }), "voltage not available");
});

test("Bahasa Melayu wording", () => {
  setLang("ms");
  assert.equal(verdictText(SUSPECT), "Solar hanya menjelaskan sebahagian penurunan: penggunaan malam turun 40%, masih disyaki.");
  assert.equal(checkValue({ check: "registration", status: "pass", values: { date: "2026-09-02", capacity_kwp: 3.5, has_battery: true } }),
    "2026-09-02, 3.5 kWp, bateri rumah");
  setLang("en");
});
