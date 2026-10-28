// Every label the web app uses exists in English and Bahasa Melayu, with the same placeholders (UI brief 0).
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { KEYS, t } from "../src/i18n.js";
import { CHECK_NAMES, MARKS, VERDICTS } from "../src/lib/solar.js";

const SRC = fileURLToPath(new URL("../src/", import.meta.url));

function files(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : /\.(jsx?|mjs)$/.test(name) ? [path] : [];
  });
}

// Keys built at run time, such as t(`status_${s}`), with every value they can take.
const DYNAMIC = {
  status_: ["new", "assigned", "visited", "reporting", "closed"],
  rstatus_: ["draft", "content_approved", "export_approved"],
  origin_: ["model", "random_sample", "manual"],
  role_: ["manager", "analyst", "supervisor", "inspector", "data_scientist", "admin", "auditor", "pipeline"],
  job_: ["queued", "running", "done", "failed"],
  cleared_: ["solar", "ev_charging", "metered_mining", "vacancy"],
  event_: ["change_of_tenancy", "holder_change", "solar_registration"],
  fallback_: ["AS2", "AS3", "AS7", "AS8", "AS9"],
  kind_: ["full_bypass_mining", "partial_bypass", "confirmed_theft"],
  guide: [1, 2, 3, 4, 5, 6, 7].flatMap((n) => [`${n}Title`, `${n}Say`, `${n}Pass`]),
  reason_: ["solar_confirmed_no_theft", "solar_plus_bypass"],
};
// Keys referenced through maps (menu items, pills, tags, SHAP texts, limits, concept rules).
const INDIRECT = ["work", "overview", "cases", "assistant", "weekly", "dispatch", "models", "validation", "backtest", "concept", "dataManager",
  "settings", "audit", "pillFlagged", "pillBalanced", "pillNoBalance", "pillFlat", "pillCleared", "largeLoad", "confirmed_theft", "false_alarm",
  "inconclusive", "no_access", "tagEv", "tagSolar", "tagVacancy", "limitVoltage", "limitSgcc", "limitSimulation", "limitPilot",
  "conceptRule1", "conceptRule2", "conceptRule3", "conceptRule4", "conceptRule5",
  ...["cv", "min_ratio", "max_ratio", "zero_day_share", "trend", "half_ratio", "max_drop", "weekly_autocorr", "low_day_share",
    "last_first_week_ratio", "level_vs_peers"].map((f) => `shap_${f}`),
  // Rooftop-solar check (camel-case families the pattern above does not pick up).
  ...CHECK_NAMES.map((c) => `solarCheckName_${c}`), ...MARKS.map((m) => `solarMark_${m}`), ...VERDICTS.map((v) => `solarVerdict_${v}`),
  ...["panels_inverter_seen", "inverter_total_vs_expected", "registration_seen", "wiring_before_meter"].map((k) => `solarCheck_${k}`)];

function usedKeys() {
  const keys = new Set(INDIRECT);
  for (const path of files(SRC)) {
    const text = readFileSync(path, "utf8");
    for (const m of text.matchAll(/\bt\("([A-Za-z0-9_]+)"/g)) keys.add(m[1]);
    for (const m of text.matchAll(/\bt\(`([a-z]+_?)\$\{/g)) {
      assert.ok(DYNAMIC[m[1]], `label family "${m[1]}" in ${path} must be listed in this test`);
      DYNAMIC[m[1]].forEach((v) => keys.add(m[1] + v));
    }
  }
  return keys;
}

const placeholders = (s) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(",");

test("every used label exists in English and Bahasa Melayu", () => {
  const missing = [...usedKeys()].filter((k) => !KEYS.en[k] || !KEYS.ms[k]);
  assert.deepEqual(missing, []);
});

test("both languages have the same keys and the same placeholders", () => {
  assert.deepEqual(Object.keys(KEYS.ms).sort(), Object.keys(KEYS.en).sort());
  const differ = Object.keys(KEYS.en).filter((k) => placeholders(KEYS.en[k]) !== placeholders(KEYS.ms[k]));
  assert.deepEqual(differ, []);
});

test("placeholders are filled, unknown ones stay visible", () => {
  assert.equal(t("runOf", { date: "2026-09-30" }), "Detection run of 2026-09-30");
  assert.equal(t("visitN", { n: 0 }), "Visit 0");
  assert.equal(t("visitN"), "Visit {n}");
});
