// Wording of the rooftop-solar check (FR-PS-10; Solar brief 4). Pure functions over the API's `solar_check`
// facts, so the web unit tests can check them without a browser. Nothing is computed or guessed here.
import { t } from "../i18n.js";
import { fmt } from "./format.js";

// A drop shows as minus. A home that exports at midday reads below zero, so a daytime drop can pass 100%.
const pc = (v) => (v == null ? "–" : v > 1.005 ? t("dropNetExport") : `${v < 0 ? "+" : "−"}${Math.round(Math.abs(v) * 100)}%`);
const share = (v) => (v == null ? "–" : `${Math.round(Math.abs(v) * 100)}%`);

export const CHECK_NAMES = ["registration", "export", "day_vs_night", "sun_shape", "rain_rebound", "energy_budget", "voltage", "timing"];
export const MARKS = ["pass", "against", "not_seen", "no_data"];
export const VERDICTS = ["explained", "night_unexplained", "over_budget", "not_tagged"];

/** The value text for one check, in the interface language. */
export function checkValue(c) {
  const v = c.values || {};
  switch (c.check) {
    case "registration":
      if (c.status !== "pass") return t("solarVal_unregistered");
      return t(v.has_battery ? "solarVal_registeredBattery" : "solarVal_registered", { date: v.date || "?", kwp: v.capacity_kwp ?? "?" });
    case "export":
      return c.status === "pass" ? t("solarVal_export") : c.status === "no_data" ? t("solarMark_no_data") : t("solarVal_noExport");
    case "day_vs_night": {
      if (c.status === "no_data") return t("solarMark_no_data");
      let s = t("solarVal_dayNight", { day: pc(v.day_drop), night: pc(v.night_drop), window: v.window || "19:00-07:00" });
      if (v.night_below_peers != null && v.night_below_peers > 0) s += t("solarVal_dayNightPeers", { peers: share(v.night_below_peers) });
      if (v.confidence === "low") s += t("solarVal_lowConf");
      return s;
    }
    case "sun_shape": {
      if (c.status === "no_data") return t("solarMark_no_data");
      const s = t("solarVal_sun", { shape: fmt(v.shape_corr, 2), sun: fmt(v.sun_corr, 2) });
      // A system that covers all midday use leaves no day-to-day variation: the zeroed midday is the sign then.
      return v.midday_zero_share != null && v.midday_zero_share >= 0.5 ? s + t("solarVal_middayZero", { share: share(v.midday_zero_share) }) : s;
    }
    case "rain_rebound":
      return v.rebound == null ? t("solarVal_reboundNone") : t("solarVal_rebound", { v: share(v.rebound) });
    case "energy_budget":
      if (c.status === "no_data") return t("solarVal_budgetNone");
      return t("solarVal_budget", { drop: fmt(v.drop_kwh, 1), expected: fmt(v.expected_kwh, 1), kwp: v.capacity_kwp ?? "?" })
        + (v.psh_source === "assumed" ? t("solarVal_budgetAssumed") : "");
    case "voltage":
      return c.status === "no_data" ? t("solarVal_voltageNone") : t("solarVal_voltage", { rise: fmt(v.midday_rise_v, 1), dip: fmt(v.night_dip_v, 1) });
    case "timing":
      return t(v.kind === "before_registration" ? "solarVal_timingBefore" : "solarVal_timingGap", { days: v.days ?? "?" });
    default:
      return "";
  }
}

/** The verdict sentence, e.g. "Solar explains only part of the drop: night use fell 40%, still a suspect." */
export function verdictText(sc) {
  if (sc.verdict === "night_unexplained") {
    // Name the night-time signal that decided (the API says which: its own history or similar homes).
    return sc.night_by === "peers"
      ? t("solarVerdict_night_unexplainedPeers", { peers: share(sc.night_below_peers) })
      : t("solarVerdict_night_unexplained", { night: share(sc.night_drop) });
  }
  return t(`solarVerdict_${VERDICTS.includes(sc.verdict) ? sc.verdict : "not_tagged"}`);
}

/** Still a suspect after the solar check (the penalty was not applied). */
export const stillSuspect = (sc) => ["night_unexplained", "over_budget"].includes(sc?.verdict);
