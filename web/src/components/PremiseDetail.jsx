// Premise detail (UI brief 2.3), shown in the zone's right-hand drawer and on the premise page:
// score ring and reason waterfall, evidence timeline, use vs similar homes, "why cleared" for tagged
// homes, and the masked contact panel. Personal details and the exact location appear only when the
// API returns them: an open case, for that case's people (FR-UI-03).
import { Activity, CalendarRange, ClipboardList, Contact, ListTree, ShieldCheck, Sun, Zap } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { get, post, session } from "../api.js";
import { t } from "../i18n.js";
import { LineChart, VoltageStrip } from "./Charts.jsx";
import { Confidence, Masked, Tags, useLoad } from "./Common.jsx";
import EvidenceTimeline from "./EvidenceTimeline.jsx";
import { ErrorState, Panel, ScoreRing, Skeleton, StatusPill } from "./ui.jsx";
import Waterfall from "./Waterfall.jsx";
import SolarCheck from "./SolarCheck.jsx";
import WhyCleared from "./WhyCleared.jsx";

export default function PremiseDetail({ id, compact = false }) {
  const { user } = session();
  const navigate = useNavigate();
  const premise = useLoad(() => get(`/premises/${id}`), [id]);
  const [error, setError] = useState(null);
  const p = premise.data;
  if (premise.error) return <ErrorState error={premise.error} onRetry={premise.reload} />;
  if (!p) return <Skeleton lines={6} block />;

  async function openCase() {
    setError(null);
    try {
      const created = await post("/cases", { premise_id: id, reason: "Opened from the premise view" });
      navigate(`/cases/${created.case_id}`);
    } catch (e) {
      setError(e);
    }
  }
  const usage = p.usage.days;
  const span = compact ? "span-12" : "span-6";
  return (
    <div className="stack">
      <div className="row between">
        <div>
          <small><Link to={`/zones/${p.premise.transformer_id}`}>{p.premise.transformer_id}</Link> · {p.premise.premise_type} · {p.premise.tariff} ·
            {" "}{t("phase")} {p.premise.phase || "?"} · {t("branch")} {p.premise.feeder_branch || "?"}</small>
        </div>
        {p.case ? <Link className="button" to={`/cases/${p.case.case_id}`}><ClipboardList size={16} aria-hidden="true" />{t("case")} {p.case.case_id} · {t(`status_${p.case.status}`)}</Link>
          : ["analyst", "supervisor"].includes(user?.role) ? <button type="button" onClick={openCase}>{t("openManualCase")}</button> : null}
      </div>
      {error ? <ErrorState error={error} /> : null}
      <div className="panels">
        <Panel className={compact ? "span-12" : "span-7"} title={t("whyRanked")} icon={ListTree}>
          {p.score ? (
            <>
              <div className="row">
                <ScoreRing score={p.score.score} size={72} />
                <div className="stack" style={{ gap: 4 }}>
                  <span className="display" style={{ fontSize: "1.05rem" }}>{t("rankInZone", { rank: p.score.rank })}</span>
                  <div className="row" style={{ gap: 4 }}><Confidence value={p.score.confidence} /><Tags tags={p.score.tags} /></div>
                </div>
              </div>
              <Waterfall reasons={p.reasons} score={p.score.score} shap={p.details?.pattern_shap} />
            </>
          ) : <p className="muted">{t("notScored")}</p>}
          <small className="muted">{t("riskNote")}</small>
        </Panel>
        <div className={`${compact ? "span-12" : "span-5"} stack`}>
          {p.solar_check ? <Panel title={t("solarCheck")} icon={Sun}><SolarCheck check={p.solar_check} /></Panel> : null}
          {p.why_cleared?.length ? (
            <Panel title={t("whyCleared")} icon={ShieldCheck}><WhyCleared items={p.why_cleared} /></Panel>
          ) : null}
          <Panel title={t("contactLocation")} icon={Contact}>
            {p.contact ? (
              <div className="notice warn">
                <span><b>{p.contact.holder_name}</b><br />{p.contact.address}<br />{p.contact.contact}<br />
                  <small>{t("contactShown", { case: p.case.case_id, lat: p.contact.lat?.toFixed(5), lon: p.contact.lon?.toFixed(5) })}</small></span>
              </div>
            ) : <Masked note={t("maskedReason")} />}
          </Panel>
        </div>
        <Panel className="span-12" title={t("evidenceTimeline")} icon={CalendarRange}><EvidenceTimeline premise={p} /></Panel>
        <Panel className={span} title={t("usage")} icon={Activity} empty={!usage.length} emptyText={t("noUsage")}>
          {!p.usage.interval_data ? <p className="notice">{t("monthlyMeterNote")}</p> : null}
          <LineChart yLabel="kWh/day" xLabels={usage.map((d) => String(d.date).slice(5))} height={200}
            summary={t("usageSummary", { type: p.usage.premise_type, days: usage.length })}
            series={[
              { name: t("thisPremise"), values: usage.map((d) => d.kwh), color: "var(--accent)" },
              { name: t("similarMedian", { type: p.usage.premise_type }), values: usage.map((d) => d.similar_median_kwh), color: "var(--series-supply)", dashed: true },
            ]} />
        </Panel>
        <Panel className={span} title={t("voltageStrip")} icon={Zap} empty={!p.neighbour_voltage} emptyText={t("noVoltageEvidence")}>
          {p.neighbour_voltage ? <VoltageStrip groups={[p.neighbour_voltage]} highlight={p.premise.premise_id} minDropV={p.voltage_min_drop_v} /> : null}
        </Panel>
      </div>
      {p.account_events?.length ? (
        <div className="row" style={{ gap: 6 }}>
          <small className="muted">{t("accountEvents")}:</small>
          {p.account_events.map((e, i) => <StatusPill key={i} kind="info">{String(e.event_date)} · {t(`event_${e.event_type}`)}</StatusPill>)}
        </div>
      ) : null}
    </div>
  );
}
