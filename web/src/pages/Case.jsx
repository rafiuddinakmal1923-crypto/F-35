// Case page (UI brief 2.4): status stepper New -> Assigned -> Visited -> Reporting -> Closed, people and dispatch,
// the masked contact panel, the audit trail as a vertical timeline, outcomes, similar cases, and the report in a
// paper-style frame with its two approvals as signature blocks (content approver, then a different export approver).
import { Camera, CircleCheck, CircleDot, CircleX, ClipboardList, Clock, Contact, FileCheck, FileSignature, FileText, Footprints, History,
  Hourglass, Navigation, PenLine, Send, Siren, TriangleAlert, UserCheck, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { get, patch, post, request, session } from "../api.js";
import { ErrorBox, Masked, useLoad } from "../components/Common.jsx";
import { Panel, Skeleton, StatusPill, ErrorState } from "../components/ui.jsx";
import { t } from "../i18n.js";

const STEPS = ["new", "assigned", "visited", "reporting", "closed"];
const EVENT_ICON = { created: ClipboardList, dispatch_suggested: Send, claimed: UserCheck, assigned: Navigation, accepted: CircleCheck,
  en_route: Footprints, declined: CircleX, reminded: Hourglass, escalated: Siren, photo_added: Camera, visited: CircleDot,
  report_drafted: FileText, note: FileText, dispatch_rejected: CircleX };
const eventIcon = (type) => EVENT_ICON[type] || (type.startsWith("outcome:") ? FileCheck : type.startsWith("report") ? FileText : Clock);

function ago(ts) {
  const m = Math.round((Date.now() - new Date(ts).getTime()) / 60000);
  if (m < 1) return t("justNow");
  if (m < 60) return t("minAgo", { n: m });
  if (m < 48 * 60) return t("hAgo", { n: Math.round(m / 60) });
  return new Date(ts).toLocaleDateString();
}

function Stepper({ status }) {
  const at = STEPS.indexOf(status);
  return (
    <ol className="stepper" aria-label={t("statusIs", { status: t(`status_${status}`) })}>
      {STEPS.map((s, i) => (
        <li key={s} className={i < at ? "done" : i === at ? "current" : ""} aria-current={i === at ? "step" : undefined}>
          <span>{i < at ? "✓" : i + 1}</span>{t(`status_${s}`)}
        </li>
      ))}
    </ol>
  );
}

function Photo({ caseId, photoKey }) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    let objectUrl;
    request(`/cases/${caseId}/photos/${photoKey}`, { raw: true }).then((res) => res.blob()).then((blob) => {
      objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
    }).catch(() => setUrl(null));
    return () => objectUrl && URL.revokeObjectURL(objectUrl);
  }, [caseId, photoKey]);
  return url ? <img className="thumb" src={url} alt={t("evidencePhoto")} style={{ width: 96, height: 96, objectFit: "cover", borderRadius: 6 }} /> : null;
}

function Signature({ step, title, who, at, waiting }) {
  return (
    <div className={`signature ${who ? "signed" : ""}`}>
      <span className="sig-step">{step}</span>
      <b>{title}</b>
      <span className="sig-line">{who ? <><PenLine size={16} aria-hidden="true" />{who}</> : <span className="muted">{waiting}</span>}</span>
      <small className="muted">{who ? t("signedAt", { at: at ? new Date(at).toLocaleString() : "–" }) : t("notSignedYet")}</small>
    </div>
  );
}

function Report({ report, caseData, onChange }) {
  const { user } = session();
  const [error, setError] = useState(null);
  const full = useLoad(() => get(`/reports/${report.report_id}`), [report.report_id, report.status]);
  async function act(path) {
    setError(null);
    try {
      await post(path);
      onChange();
    } catch (e) {
      setError(e);
    }
  }
  async function download() {
    const res = await request(`/reports/${report.report_id}/pdf`, { raw: true });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement("a"), { href: url, download: `${report.report_id}.pdf` });
    a.click();
    URL.revokeObjectURL(url);
  }
  const r = full.data;
  return (
    <Panel className="span-12" title={`${t("report")} ${report.report_id}`} icon={FileSignature} actions={<StatusPill kind="info">{t(`rstatus_${report.status}`)}</StatusPill>}>
      <ErrorBox error={error || full.error} />
      <div className="signatures">
        <Signature step={t("approvalOne")} title={t("contentApprover")} who={report.content_approved_by} at={report.content_approved_at}
          waiting={t("waitingFor", { who: caseData.case.assigned_analyst || t("theAnalyst") })} />
        <Signature step={t("approvalTwo")} title={t("exportApprover")} who={report.export_approved_by} at={report.export_approved_at}
          waiting={report.content_approved_by ? t("waitingForManager") : t("afterContent")} />
      </div>
      <small className="muted">{t("twoPeopleRule")}</small>
      <div className="row">
        {report.status === "draft" && user.role === "analyst" && caseData.case.assigned_analyst === user.user_id
          ? <button className="primary" onClick={() => act(`/reports/${report.report_id}/approve-content`)}>{t("approveContent")}</button> : null}
        {report.status === "content_approved" && user.role === "manager"
          ? <button className="primary" onClick={() => act(`/reports/${report.report_id}/approve-export`)}>{t("approveExport")}</button> : null}
        {report.status === "export_approved" ? <button onClick={download}>{t("downloadPdf")}</button> : null}
      </div>
      {r ? (
        <div className="paper" aria-label={t("reportPreview")}>
          <small>{t("reportMeta", { mode: r.mode, by: r.created_by })}</small>
          <pre style={{ marginTop: 10 }}>{r.draft_text}</pre>
          <h3 style={{ marginTop: 16 }}>{t("sources")}</h3>
          <ul>{(r.sources || []).map((s, i) => <li key={i}><small>{s.title}{s.section ? `, ${s.section}` : ""} ({s.source_ref || s.kind})</small></li>)}</ul>
        </div>
      ) : <Skeleton lines={6} />}
    </Panel>
  );
}

export default function Case() {
  const { id } = useParams();
  const { user } = session();
  const detail = useLoad(() => get(`/cases/${id}`), [id]);
  // Another person may act on this case meanwhile (claim, approval, outcome): poll a cheap change
  // marker and reload the full page only when it changes (each full load is an audited view).
  const version = useLoad(() => get(`/cases/${id}/version`), [id], 10000);
  const marker = version.data ? JSON.stringify(version.data) : null;
  const [seen, setSeen] = useState(null);
  useEffect(() => {
    if (marker && seen && marker !== seen) detail.reload();
    if (marker) setSeen(marker);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marker]);
  const similar = useLoad(() => (["analyst", "inspector"].includes(user?.role) ? get(`/cases/${id}/similar`).catch(() => null) : Promise.resolve(null)), [id]);
  const teams = useLoad(() => (user?.role === "supervisor" ? get("/teams") : Promise.resolve([])), [id]);
  const [team, setTeam] = useState("");
  const [error, setError] = useState(null);
  const d = detail.data;
  // Managers see evidence photos only for the export (second) approval; the API enforces the same rule.
  const showPhotos = user?.role !== "manager" || (d?.reports || []).some((r) => ["content_approved", "export_approved"].includes(r.status));

  async function act(fn) {
    setError(null);
    try {
      await fn();
      detail.reload();
    } catch (e) {
      setError(e);
    }
  }

  if (detail.error) return <div className="page"><ErrorState error={detail.error} onRetry={detail.reload} /></div>;
  if (!d) return <div className="page"><Skeleton lines={8} block /></div>;
  const theft = d.outcomes.some((o) => o.outcome === "confirmed_theft");
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{t("case")} {d.case.case_id}</h1>
          <span className="sub"><Link to={`/premises/${d.case.premise_id}`}>{d.case.premise_id}</Link> · <Link to={`/zones/${d.case.transformer_id}`}>{d.case.transformer_id}</Link>
            {" "}· {t("origin")} {t(`origin_${d.case.origin}`)}{d.case.score_at_creation != null ? ` · ${t("scoreAtCreation", { score: d.case.score_at_creation })}` : ""}</span>
        </div>
        <div className="row">{theft ? <StatusPill kind="theft" /> : null}<StatusPill kind="info">{t(`status_${d.case.status}`)}</StatusPill></div>
      </div>
      <div className="card"><Stepper status={d.case.status} /></div>
      <ErrorBox error={error} />
      {d.case.joint_operation ? <div className="notice error"><TriangleAlert size={16} aria-hidden="true" />{t("jointOperation")}</div> : null}
      <div className="panels">
        <Panel className="span-6" title={t("people")} icon={Users}>
          <div>{t("analyst")}: {d.case.assigned_analyst || <span className="muted">{t("unclaimed")}</span>}
            {user.role === "analyst" && !d.case.assigned_analyst && d.case.status !== "closed"
              ? <button className="primary" style={{ marginLeft: 8 }} onClick={() => act(() => post(`/cases/${id}/claim`))}>{t("claim")}</button> : null}</div>
          <div>{t("team")}: {d.case.assigned_team || "–"}</div>
          {d.dispatch_suggestion ? (
            <div className="notice">
              <Send size={16} aria-hidden="true" />
              <span><b>{t("dispatchSuggestion", { team: d.dispatch_suggestion.suggested_team, km: d.dispatch_suggestion.distance_km })}</b> · {d.dispatch_suggestion.status}
                <br /><small>{d.dispatch_suggestion.rationale}</small>
                {user.role === "supervisor" && d.dispatch_suggestion.status === "pending" ? (
                  <span className="row" style={{ marginTop: 8 }}>
                    <button className="primary" onClick={() => act(() => post(`/cases/${id}/dispatch-suggestion/approve`, { approve: true }))}>{t("approve")}</button>
                    <button onClick={() => act(() => post(`/cases/${id}/dispatch-suggestion/approve`, { approve: false }))}>{t("reject")}</button>
                  </span>
                ) : null}</span>
            </div>
          ) : null}
          {user.role === "supervisor" && ["new", "assigned"].includes(d.case.status) ? (
            <div className="row">
              <select value={team} onChange={(e) => setTeam(e.target.value)} aria-label={t("team")}>
                <option value="">{t("team")}…</option>
                {(teams.data || []).map((tm) => <option key={tm.team_id} value={tm.team_id}>{tm.name} ({tm.team_id})</option>)}
              </select>
              <button disabled={!team} onClick={() => act(() => patch(`/cases/${id}/assign`, { team }))}>{t("assign")}</button>
            </div>
          ) : null}
        </Panel>
        <Panel className="span-6" title={t("contactLocation")} icon={Contact}>
          {d.contact ? (
            <div className="notice warn"><span><b>{d.contact.holder_name}</b><br />{d.contact.address}<br />{d.contact.contact}<br />
              <small>{t("contactOnCase")}</small></span></div>
          ) : <Masked note={d.case.status === "closed" ? t("caseClosedMasked") : t("maskedCaseReason")} />}
        </Panel>
        <Panel className="span-6" title={t("auditTrail")} icon={History} empty={!d.events.length}>
          <ol className="timeline vertical">
            {d.events.map((e, i) => {
              const Icon = eventIcon(e.event_type);
              const via = e.detail?.via ? ` · ${t("via")} ${e.detail.via}` : "";
              return (
                <li key={i} className={`ev-${e.event_type.split(":")[0]}`}>
                  <span className="ev-icon"><Icon size={15} aria-hidden="true" /></span>
                  <span><b>{e.event_type.replace("outcome:", `${t("outcome")}: `).replaceAll("_", " ")}</b> · {e.actor}{via}
                    <br /><small title={new Date(e.ts).toLocaleString()}>{ago(e.ts)}</small></span>
                </li>
              );
            })}
          </ol>
        </Panel>
        <Panel className="span-6" title={t("inspectionOutcomes")} icon={FileCheck} empty={!d.outcomes.length} emptyText={t("noVisitYet")}>
          {d.outcomes.map((o) => (
            <div key={o.visit_no} className="stack" style={{ gap: 4 }}>
              <div className="row" style={{ gap: 6 }}><b>{t("visitN", { n: o.visit_no })}</b>
                <StatusPill kind={o.outcome === "confirmed_theft" ? "theft" : o.outcome === "false_alarm" ? "cleared" : "info"}>{t(o.outcome)}</StatusPill>
                {o.reason_tag ? <span className="chip">{o.reason_tag}</span> : null}
                <small className="muted">{o.recorded_by} · {new Date(o.recorded_at).toLocaleString()}</small></div>
              {o.notes_redacted ? <p style={{ margin: 0 }}>{o.notes_redacted}</p> : null}
              {showPhotos ? <div className="row">{(o.photo_keys || []).map((k) => <Photo key={k} caseId={id} photoKey={k} />)}</div>
                : o.photo_keys?.length ? <small className="muted">{t("photosForExport", { n: o.photo_keys.length })}</small> : null}
            </div>
          ))}
          <small className="muted">{t("notesRedacted")}</small>
        </Panel>
        {similar.data?.similar ? (
          <Panel className="span-12" title={t("similarCases")} icon={ClipboardList}>
            <div className="table-wrap"><table><thead><tr><th>{t("case")}</th><th>{t("outcome")}</th><th>{t("summaryRedacted")}</th><th className="num">{t("similarity")}</th></tr></thead>
              <tbody>{similar.data.similar.map((s) => (
                <tr key={s.case_id}><td>{s.case_id}</td><td>{t(s.outcome) || s.outcome}</td><td><small>{s.summary}</small></td><td className="num">{s.similarity.toFixed(2)}</td></tr>
              ))}</tbody></table></div>
          </Panel>
        ) : null}
        {d.case.status === "reporting" && user.role === "analyst" && d.case.assigned_analyst === user.user_id && !d.reports.length ? (
          <div className="span-12"><button className="primary" onClick={() => act(() => post(`/agents/report/${id}`))}>{t("draftReport")}</button></div>
        ) : null}
        {d.reports.map((r) => <Report key={r.report_id} report={r} caseData={d} onChange={detail.reload} />)}
      </div>
    </div>
  );
}
