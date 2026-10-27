// Premise view (FR-UI-03): reasons, use vs similar homes, neighbour voltage, account context.
// Personal details and exact location appear only on an open case, for that case's people.
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { get, post, session } from "../api.js";
import { LineChart, VoltageStrip } from "../components/Charts.jsx";
import { Confidence, ErrorBox, Masked, Reasons, Tags, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

export default function Premise() {
  const { id } = useParams();
  const { user } = session();
  const navigate = useNavigate();
  const premise = useLoad(() => get(`/premises/${id}`), [id]);
  const [error, setError] = useState(null);
  const p = premise.data;

  async function openCase() {
    setError(null);
    try {
      const created = await post("/cases", { premise_id: id, reason: "Opened from the premise view" });
      navigate(`/cases/${created.case_id}`);
    } catch (e) {
      setError(e);
    }
  }

  return (
    <div className="stack">
      <ErrorBox error={premise.error || error} />
      {p ? (
        <>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <h1>{t("premise")} {p.premise.premise_id}</h1>
              <small><Link to={`/zones/${p.premise.transformer_id}`}>{p.premise.transformer_id}</Link> · {p.premise.premise_type} · {p.premise.tariff} ·
                phase {p.premise.phase || "?"} · branch {p.premise.feeder_branch || "?"} · {p.premise.distance_m ?? "?"} m</small>
            </div>
            {p.case ? <Link className="button" to={`/cases/${p.case.case_id}`}>{t("case")} {p.case.case_id} ({p.case.status})</Link>
              : ["analyst", "supervisor"].includes(user?.role) ? <button onClick={openCase}>Open a manual case</button> : null}
          </div>
          <div className="grid two">
            <div className="card">
              <h2>{t("score")}</h2>
              {p.score ? (
                <>
                  <div className="row"><span className="score-big">{p.score.score}</span>
                    <span>rank {p.score.rank} in zone</span><Confidence value={p.score.confidence} /><Tags tags={p.score.tags} /></div>
                  <Reasons reasons={p.reasons} score={p.score.score} />
                </>
              ) : <p className="muted">Not scored in the latest run (zone not flagged).</p>}
              <p><small>{t("riskNote")}</small></p>
            </div>
            <div className="card">
              <h2>Contact and location</h2>
              {p.contact ? (
                <div className="notice warn">
                  <div><b>{p.contact.holder_name}</b></div>
                  <div>{p.contact.address}</div>
                  <div>{p.contact.contact}</div>
                  <small>Location {p.contact.lat?.toFixed(5)}, {p.contact.lon?.toFixed(5)} · shown because you work on open case {p.case.case_id}; this view is logged.</small>
                </div>
              ) : <Masked note={p.masking_note} />}
              <h3 style={{ marginTop: 14 }}>{t("accountEvents")}</h3>
              {p.account_events.length ? (
                <ul>{p.account_events.map((e, i) => <li key={i}>{e.event_date}: {e.event_type.replaceAll("_", " ")}</li>)}</ul>
              ) : <p className="muted">None recorded.</p>}
            </div>
          </div>
          <div className="grid two">
            <div className="card">
              <h2>{t("usage")}</h2>
              {!p.usage.interval_data ? <p className="muted">Monthly-read meter: no daily readings, so only similar homes are shown.</p> : null}
              <LineChart yLabel="kWh/day" xLabels={p.usage.days.map((d) => String(d.date).slice(5))}
                series={[
                  { name: "This premise", values: p.usage.days.map((d) => d.kwh), color: "var(--series-4)" },
                  { name: `Median of similar ${p.usage.premise_type} homes`, values: p.usage.days.map((d) => d.similar_median_kwh), color: "var(--series-1)", dashed: true },
                ]} />
            </div>
            <div className="card">
              <h2>{t("voltageStrip")}</h2>
              {p.neighbour_voltage ? <VoltageStrip groups={[p.neighbour_voltage]} highlight={p.premise.premise_id} minDropV={p.voltage_min_drop_v} />
                : <p className="muted">No voltage evidence for this premise (no voltage data, no phase data, or zone not located).</p>}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
