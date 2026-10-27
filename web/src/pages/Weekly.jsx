// Weekly summary (managers and supervisors): zone-level energy, cases, outcomes and hit rates for the
// region, with week-on-week change; download as PDF or send the headline to Telegram / the in-app chat.
import { useState } from "react";
import { get, post, request } from "../api.js";
import { CategoryBars, LineChart } from "../components/Charts.jsx";
import { ErrorBox, Kpi, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";
import { LinkTelegram } from "./Dispatch.jsx";

export default function Weekly() {
  const weekly = useLoad(() => get("/weekly"), []);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const d = weekly.data;

  async function download() {
    setError(null);
    try {
      const res = await request("/weekly/pdf", { raw: true });
      const url = URL.createObjectURL(await res.blob());
      Object.assign(document.createElement("a"), { href: url, download: `voltguard-weekly-${d.region}.pdf` }).click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e);
    }
  }
  async function send() {
    setError(null);
    try {
      const r = await post("/weekly/send");
      setMessage(r.channel === "telegram" ? "Sent to your Telegram chat." : "Sent to your in-app chat (link Telegram to get it on your phone).");
    } catch (e) {
      setError(e);
    }
  }

  const k = d?.kpis;
  const weekStart = d ? d.daily_gap.findIndex((p) => p.date >= d.energy_window.from) : -1;
  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>{t("weekly")}</h1>
          {d && !d.empty ? <small className="muted">Region {d.region} · meter data {d.energy_window.from} to {d.energy_window.to} ·
            cases and visits {d.work_window.from} to {d.work_window.to}</small> : null}
        </div>
        <div className="row">
          <button onClick={send} disabled={!d || d.empty}>Send to my chat</button>
          <button className="primary" onClick={download} disabled={!d || d.empty}>Download PDF</button>
        </div>
      </div>
      <ErrorBox error={weekly.error || error} />
      {message ? <div className="notice ok">{message}</div> : null}
      {d?.empty ? <p className="muted">{d.message}</p> : null}
      {k ? (
        <>
          <div className="grid kpis">
            <Kpi value={k.flagged_zones} label={t("flaggedZones")} />
            <Kpi value={k.unexplained_kwh_per_day} label={t("gapPerDay")} change={k.unexplained_change_pct} />
            <Kpi value={`${k.cases_opened} / ${k.cases_closed}`} label="Cases opened / closed this week" />
            <Kpi value={k.cases_overdue} label="Overdue visits" />
            <Kpi value={k.reports_exported} label="Reports exported this week" />
            <Kpi value={k.open_alerts} label="Open data and model alerts" />
          </div>
          <div className="grid two">
            <div className="card">
              <h2>Unexplained energy, last 14 days</h2>
              <LineChart yLabel="kWh/day, whole region" xLabels={d.daily_gap.map((p) => p.date.slice(5))}
                series={[{ name: "Unexplained energy", values: d.daily_gap.map((p) => p.gap_kwh), color: "var(--series-1)" }]}
                markers={weekStart > 0 ? [{ index: weekStart, label: "this week" }] : []} />
              <small className="muted">About {k.unexplained_kwh_per_month?.toLocaleString()} kWh a month at this week's level. Value at risk: {k.value_at_risk}.</small>
            </div>
            <div className="card">
              <h2>Top zones this week</h2>
              <CategoryBars labels={d.top_zones.map((z) => `${z.transformer_id} · ${z.district}`)} values={d.top_zones.map((z) => z.gap_kwh_per_day)}
                unit="Unexplained energy, kWh/day" color="var(--risk)" />
            </div>
          </div>
          <div className="grid two">
            <div className="card">
              <h2>Inspection outcomes this week</h2>
              {Object.keys(d.outcomes_this_week).length
                ? <CategoryBars labels={Object.keys(d.outcomes_this_week).map((o) => t(o))} values={Object.values(d.outcomes_this_week)} unit="Visits" />
                : <p className="muted">No visit recorded this week.</p>}
            </div>
            <div className="card">
              <h2>Hit rate so far</h2>
              <CategoryBars labels={Object.keys(d.hit_rates).map((h) => h.replace("_", " "))}
                values={Object.values(d.hit_rates).map((h) => h.hit_rate_pct ?? 0)} unit="% of labelled inspections that found theft" color="var(--series-2)" />
              <small className="muted">Random-sample inspections are the unbiased reference for the model-ranked hit rate.</small>
            </div>
          </div>
          <p className="notice">{t("riskNote")} Zone-level figures only; no premise or personal details appear in this summary.
            The headline is sent every Monday at 07:45 to managers and supervisors.</p>
          <div style={{ maxWidth: 480 }}><LinkTelegram /></div>
        </>
      ) : null}
    </div>
  );
}
