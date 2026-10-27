// Zone view (FR-UI-02): energy balance over time, hourly gap profile, ranked suspects, voltage strip.
import { Link, useParams } from "react-router-dom";
import { get, session } from "../api.js";
import { BarChart, LineChart, VoltageStrip } from "../components/Charts.jsx";
import { Confidence, ErrorBox, fmt, pct, Tags, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

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

  return (
    <div className="stack">
      <div>
        <h1>{t("zone")} {id}</h1>
        {b ? (
          <div className="row">
            <span className="muted">{b.zone.district} · {b.zone.region}</span>
            {b.zone.flagged ? <span className="chip risk">flagged</span> : <span className="chip">not flagged</span>}
            {b.zone.priority === "large_load" ? <span className="chip risk">{t("largeLoad")}</span> : null}
            {!b.zone.balance_available ? <span className="chip warn">no balance available</span> : null}
            <span className="chip info">{t("gapStart")}: {b.zone.gap_start || (b.zone.gap_since_start ? t("sinceStart") : "–")}</span>
            <span className="chip info">{t("flatness")}: {fmt(b.zone.flatness_cv, 2)}</span>
          </div>
        ) : null}
      </div>
      <ErrorBox error={balance.error} />
      {b?.zone.notes?.length ? <div className="notice warn">{b.zone.notes.join(" ")}</div> : null}
      {b && b.zone.balance_available ? (
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
      {canSuspects ? (
        <div className="card table-wrap">
          <h2>{t("suspects")}</h2>
          <ErrorBox error={suspects.error} />
          {suspects.data ? (
            <table>
              <thead><tr><th>#</th><th>{t("premise")}</th><th className="num">{t("score")}</th><th>{t("reasons")}</th><th>{t("tags")}</th><th>{t("case")}</th></tr></thead>
              <tbody>
                {suspects.data.suspects.slice(0, 25).map((s) => (
                  <tr key={s.premise_id} className={s.rank <= suspects.data.top_k ? "flagged" : ""}>
                    <td>{s.rank}</td>
                    <td><Link to={`/premises/${s.premise_id}`}>{s.premise_id}</Link><br /><small>{s.premise_type} · phase {s.phase || "?"} · {s.feeder_branch || "?"}</small></td>
                    <td className="num"><b>{s.score}</b></td>
                    <td><small>{s.reasons.filter((r) => !["other", "capped"].includes(r.feature)).map((r) => r.reason_text).join(" · ")}</small></td>
                    <td><Tags tags={s.tags} /><Confidence value={s.confidence} /></td>
                    <td>{s.open_case_id ? <Link to={`/cases/${s.open_case_id}`}>{s.open_case_id}</Link> : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          <small>Top 5% of this zone: the first {suspects.data?.top_k} rows. {t("riskNote")}</small>
        </div>
      ) : null}
      {canSuspects && voltage.data ? (
        <div className="card">
          <h2>{t("voltageStrip")}</h2>
          <p className="muted">Method: {voltage.data.method} · confidence {voltage.data.confidence}. {(voltage.data.notes || []).join(" ")}</p>
          <VoltageStrip groups={voltage.data.groups} highlight={suspects.data?.suspects?.[0]?.premise_id} />
        </div>
      ) : null}
    </div>
  );
}
