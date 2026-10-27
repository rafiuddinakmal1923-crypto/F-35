// Zone view (FR-UI-02): energy balance over time, hourly gap profile, ranked suspects, voltage strip.
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { get, session } from "../api.js";
import { BarChart, LineChart, VoltageStrip } from "../components/Charts.jsx";
import { Confidence, ErrorBox, fmt, Help, pct, ScoreRing, Tabs, Tags, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

// Decision first (design brief 2.1): one sentence that says what the page is about.
function decision(z) {
  if (!z.balance_available) return "No energy balance here: premises are ranked on usage patterns only.";
  if (!z.flagged) return `Not flagged: the recent gap (${pct(z.gap_pct_recent)} of supply) stays inside the flag rule.`;
  const since = z.gap_start ? `since ${z.gap_start}` : "since data start";
  const flat = z.flatness_cv != null && z.flatness_cv < 0.2 ? " The hidden load runs flat 24/7, typical of mining rigs." : "";
  const large = z.priority === "large_load" ? " Large-load priority." : "";
  return `Flagged: ${pct(z.gap_pct_recent)} of supply (about ${fmt(z.gap_kwh_recent, 0)} kWh/day) is unexplained ${since}.${flat}${large}`;
}

export default function Zone() {
  const { id } = useParams();
  const { user } = session();
  const balance = useLoad(() => get(`/zones/${id}/balance`), [id]);
  const canSuspects = ["analyst", "supervisor"].includes(user?.role);
  const suspects = useLoad(() => (canSuspects ? get(`/zones/${id}/suspects`) : Promise.resolve(null)), [id]);
  const voltage = useLoad(() => (canSuspects ? get(`/zones/${id}/voltage`) : Promise.resolve(null)), [id]);
  const b = balance.data;
  const days = b?.days || [];
  const startIdx = b?.zone.gap_start ? days.findIndex((d) => d.date === b.zone.gap_start) : -1;
  const [tab, setTab] = useState(null);
  const [showAll, setShowAll] = useState(false);
  const current = tab || (canSuspects ? "suspects" : "evidence");
  const list = suspects.data?.suspects || [];

  return (
    <div className="stack">
      <div>
        <h1>{t("zone")} {id}</h1>
        {b ? <p className="decision">{decision(b.zone)}</p> : null}
        {b ? (
          <div className="row">
            <span className="muted">{b.zone.district} · {b.zone.region}</span>
            {b.zone.flagged ? <span className="chip risk">flagged</span> : <span className="chip">not flagged</span>}
            {b.zone.priority === "large_load" ? <span className="chip risk">{t("largeLoad")}</span> : null}
            {!b.zone.balance_available ? <span className="chip warn">no balance available</span> : null}
            <span className="chip info">{t("gapStart")}: {b.zone.gap_start || (b.zone.gap_since_start ? t("sinceStart") : "–")}</span>
            <span className="chip info">{t("flatness")}: {fmt(b.zone.flatness_cv, 2)}<Help text="Coefficient of variation of the hourly gap. Below 0.2 the hidden load runs flat 24/7, typical of crypto-mining rigs." /></span>
          </div>
        ) : null}
      </div>
      <ErrorBox error={balance.error} />
      {b?.zone.notes?.length ? <div className="notice warn">{b.zone.notes.join(" ")}</div> : null}
      <Tabs value={current} onChange={setTab} tabs={[
        { key: "evidence", label: "Evidence" },
        ...(canSuspects ? [{ key: "suspects", label: t("suspects"), count: list.length || null }, { key: "voltage", label: t("voltageStrip") }] : []),
      ]} />
      {current === "evidence" && b && !b.zone.balance_available ? (
        <p className="notice warn">No transformer meter in this zone: there is no energy balance, and premises are ranked on usage patterns only (low confidence).</p>
      ) : null}
      {current === "evidence" && b && b.zone.balance_available ? (
        <div className="grid two">
          <div className="card">
            <h2>{t("energyBalance")}</h2>
            <LineChart
              yLabel="kWh/day"
              xLabels={days.map((d) => d.date.slice(5))}
              markers={startIdx >= 0 ? [{ index: startIdx, label: "gap opens" }] : []}
              series={[
                { name: "Supplied", values: days.map((d) => d.supplied_kwh), color: "var(--series-1)" },
                { name: "Metered + estimated + technical loss", color: "var(--series-2)",
                  values: days.map((d) => (d.metered_kwh ?? 0) + (d.estimated_kwh ?? 0) + (d.tech_loss_kwh ?? 0)) },
              ]}
            />
            <LineChart
              yLabel="gap kWh/day"
              xLabels={days.map((d) => d.date.slice(5))}
              height={170}
              markers={startIdx >= 0 ? [{ index: startIdx, label: "gap opens" }] : []}
              series={[{ name: "Gap ± uncertainty u", values: days.map((d) => d.gap_kwh), color: "var(--series-4)",
                band: days.map((d) => [d.gap_kwh - d.uncertainty_kwh, d.gap_kwh + d.uncertainty_kwh]) }]}
            />
          </div>
          <div className="card">
            <h2>{t("hourlyGap")}</h2>
            <BarChart values={b.hourly_gap_kwh || []} labels={[...Array(24).keys()].map((h) => `${h}h`)} yLabel="kWh per hour" />
            <p className="muted">
              Flatness (coefficient of variation) {fmt(b.zone.flatness_cv, 2)}
              {b.zone.flatness_cv != null && b.zone.flatness_cv < 0.2 ? ": a constant 24/7 load, typical of mining rigs." : "."}
            </p>
          </div>
        </div>
      ) : null}
      {!canSuspects ? (
        <p className="notice">Premise rankings are shown to analysts and supervisors. Managers see zone-level figures only (SRS 2.2).</p>
      ) : null}
      {canSuspects && current === "suspects" ? (
        <div className="card table-wrap">
          <h2>{t("suspects")}</h2>
          <ErrorBox error={suspects.error} />
          {suspects.data ? (
            <table>
              <thead><tr><th>#</th><th>{t("premise")}</th><th className="num">{t("score")}</th><th>{t("reasons")}</th><th>{t("tags")}</th><th>{t("case")}</th></tr></thead>
              <tbody>
                {list.slice(0, showAll ? list.length : 10).map((s) => (
                  <tr key={s.premise_id} className={s.rank <= suspects.data.top_k ? "flagged" : ""}>
                    <td>{s.rank}</td>
                    <td><Link to={`/premises/${s.premise_id}`}>{s.premise_id}</Link><br /><small>{s.premise_type} · phase {s.phase || "?"} · {s.feeder_branch || "?"}</small></td>
                    <td className="num"><ScoreRing score={s.score} size={40} /></td>
                    <td><small>{s.reasons.find((r) => !["other", "capped"].includes(r.feature))?.reason_text}</small>
                      {s.reasons.filter((r) => !["other", "capped"].includes(r.feature)).length > 1
                        ? <small className="muted"> · +{s.reasons.filter((r) => !["other", "capped"].includes(r.feature)).length - 1} more on the premise page</small> : null}</td>
                    <td><Tags tags={s.tags} /><Confidence value={s.confidence} /></td>
                    <td>{s.open_case_id ? <Link to={`/cases/${s.open_case_id}`}>{s.open_case_id}</Link> : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          {list.length > 10 ? (
            <button className="show-more" onClick={() => setShowAll((v) => !v)}>{showAll ? "Show the top 10" : `Show all ${list.length}`}</button>
          ) : null}
          <p><small>Top 5% of this zone: the first {suspects.data?.top_k} rows (orange edge). {t("riskNote")}</small></p>
        </div>
      ) : null}
      {canSuspects && current === "voltage" && voltage.data ? (
        <div className="card">
          <h2>{t("voltageStrip")}</h2>
          <p className="muted">Method: {voltage.data.method} · confidence {voltage.data.confidence}. {(voltage.data.notes || []).join(" ")}</p>
          <VoltageStrip groups={voltage.data.groups} highlight={suspects.data?.suspects?.[0]?.premise_id} minDropV={voltage.data.min_drop_v} />
        </div>
      ) : null}
    </div>
  );
}
