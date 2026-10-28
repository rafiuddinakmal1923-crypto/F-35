// Validation (UI brief 3.6): held-out results, where detection breaks, model-ranked vs random-sample hit
// rate per model version, and the limits. Numbers come only from reports/simulation_summary.json and the
// database; a missing result says "not run yet", never a placeholder number.
import { AlertTriangle, Crosshair, FlaskConical, Info, ListChecks, TrendingDown } from "lucide-react";
import { get } from "../api.js";
import { LineChart } from "../components/Charts.jsx";
import { useLoad } from "../components/Common.jsx";
import { EmptyState, Panel } from "../components/ui.jsx";
import { t } from "../i18n.js";
import { fmt, hitRate, pct } from "../lib/format.js";

function Compare({ rows, unit = "" }) {
  const max = Math.max(...rows.map((r) => r.value ?? 0), 1e-9);
  return (
    <div className="compare-bars">
      {rows.map((r) => (
        <div key={r.label} className="compare-bar">
          <span>{r.label}</span>
          <span className="track" aria-hidden="true"><span className={`fill ${r.ref ? "ref" : ""}`} style={{ width: `${((r.value ?? 0) / max) * 100}%`, display: "block" }} /></span>
          <span className="val">{r.value == null ? "–" : `${r.text ?? r.value}${unit}`}</span>
        </div>
      ))}
    </div>
  );
}

export default function Validation() {
  const data = useLoad(() => get("/validation/summary"), []);
  const sim = data.data?.simulation;
  const held = sim?.heldout;
  const noise = sim?.noise_sweep || [];
  const monthly = sim?.monthly_read_sweep || [];
  const versions = data.data?.model_versions || [];
  const notRun = <EmptyState icon={FlaskConical}>{t("notRunYet")}</EmptyState>;
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{t("validation")}</h1>
          <span className="sub">{sim ? t("validationFrom", { file: data.data.file, date: sim.generated }) : t("validationIntro")}</span>
        </div>
      </div>
      <div className="panels">
        <Panel className="span-6" title={t("heldOut")} icon={Crosshair} loading={data.loading} error={data.error} onRetry={data.reload}>
          {held ? (
            <>
              <div className="row" style={{ alignItems: "flex-end", gap: 18 }}>
                <div><div className="big-figure">{pct(held.share_ranked_thefts_in_top5, 0)}</div>
                  <small className="muted">{t("heldRanked", { found: held.thefts_in_top5, of: held.thefts_ranked })}</small></div>
                <div><div className="big-figure" style={{ fontSize: "1.6rem" }}>{pct(held.share_all_thefts_in_top5, 0)}</div>
                  <small className="muted">{t("heldAll", { found: held.thefts_in_top5, of: held.thefts })}</small></div>
              </div>
              <h3 style={{ marginTop: 6 }}>{t("inspectionsPerTheft")}</h3>
              <Compare rows={[
                { label: t("modelOrder"), value: held.inspections_per_theft_model, text: fmt(held.inspections_per_theft_model, 1) },
                { label: t("randomOrder"), value: held.inspections_per_theft_random, text: fmt(held.inspections_per_theft_random, 1), ref: true },
              ]} />
              <small className="muted">{t("heldFoot", { clean: held.clean_zone_false_flags, zones: held.clean_zones, missed: pct(held.largest_missed_share, 1) })}</small>
            </>
          ) : notRun}
        </Panel>

        <Panel className="span-6" title={t("hitRatesByVersion")} icon={ListChecks} loading={data.loading} error={data.error}
          empty={data.data && !versions.length} emptyText={t("noModelVersions")}>
          {versions.map((v) => {
            const m = hitRate(v.model_ranked);
            const r = hitRate(v.random_sample);
            return (
              <div key={v.version_id} className="stack" style={{ gap: 6 }}>
                <b className="display">{v.version_id}{v.active ? <span className="chip ok" style={{ marginLeft: 6 }}>{t("active")}</span> : null}</b>
                <Compare rows={[
                  { label: t("modelRanked"), value: m, text: m != null ? `${pct(m, 0)} (${v.model_ranked.confirmed_theft}/${v.model_ranked.inspections})` : null },
                  { label: t("randomSample"), value: r, text: r != null ? `${pct(r, 0)} (${v.random_sample.confirmed_theft}/${v.random_sample.inspections})` : null, ref: true },
                ]} />
              </div>
            );
          })}
          <small className="muted">{t("hitRateNote")}</small>
        </Panel>

        <Panel className="span-6" title={t("breaksNoise")} icon={TrendingDown} loading={data.loading} error={data.error}>
          {noise.length ? (
            <>
              <LineChart height={180} yLabel={t("shareOfSupply")} xLabels={noise.map((n) => fmt(n.noise, 2))}
                summary={t("noiseSummary", { list: noise.map((n) => `${fmt(n.noise, 2)}: ${pct(n.smallest_flagged_share, 1)}`).join("; ") })}
                series={[
                  { name: t("smallestFlagged"), values: noise.map((n) => (n.smallest_flagged_share == null ? null : n.smallest_flagged_share * 100)), color: "var(--series-gap)" },
                  { name: t("thefts5"), values: noise.map((n) => (n.share_all_thefts_in_top5 == null ? null : n.share_all_thefts_in_top5 * 100)), color: "var(--series-supply)", dashed: true },
                ]} />
              <small className="muted">{t("noiseNote")}</small>
            </>
          ) : notRun}
        </Panel>

        <Panel className="span-6" title={t("breaksMonthly")} icon={AlertTriangle} loading={data.loading} error={data.error}>
          {monthly.length ? (
            <>
              <LineChart height={180} yLabel="%" xLabels={monthly.map((m) => pct(m.monthly_read_share, 0))}
                summary={t("monthlySummary", { list: monthly.map((m) => `${pct(m.monthly_read_share, 0)}: ${pct(m.theft_zone_flag_rate, 0)}`).join("; ") })}
                series={[
                  { name: t("theftZonesFlagged"), values: monthly.map((m) => (m.theft_zone_flag_rate == null ? null : m.theft_zone_flag_rate * 100)), color: "var(--series-gap)" },
                  { name: t("thefts5"), values: monthly.map((m) => (m.share_all_thefts_in_top5 == null ? null : m.share_all_thefts_in_top5 * 100)), color: "var(--series-supply)", dashed: true },
                ]} />
              <small className="muted">{t("monthlyNote")}</small>
            </>
          ) : notRun}
        </Panel>

        <Panel className="span-12" title={t("limits")} icon={Info}>
          <ul className="limits">
            {["limitVoltage", "limitSgcc", "limitSimulation", "limitPilot"].map((k) => <li key={k}><AlertTriangle size={16} aria-hidden="true" />{t(k)}</li>)}
          </ul>
        </Panel>
      </div>
    </div>
  );
}
