// Case page: status history, dispatch suggestion, assignment, outcomes, report and approvals.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { get, patch, post, request, session } from "../api.js";
import { ErrorBox, Masked, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

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
  return url ? <img className="thumb" src={url} alt="Inspection evidence" style={{ width: 96, height: 96, objectFit: "cover", borderRadius: 6 }} /> : null;
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
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>Report {report.report_id}</h2>
        <span className="chip info">{report.status.replace("_", " ")}</span>
      </div>
      <ErrorBox error={error || full.error} />
      {r ? (
        <>
          <p><small>Mode: {r.mode} · drafted by {r.created_by} · personal details are placeholders until export.</small></p>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: "0.9rem", background: "var(--surface-2)", padding: 12, borderRadius: 8 }}>{r.draft_text}</pre>
          <h3>Sources</h3>
          <ul>{(r.sources || []).map((s, i) => <li key={i}><small>{s.title}{s.section ? `, ${s.section}` : ""} ({s.source_ref || s.kind})</small></li>)}</ul>
        </>
      ) : null}
      <div className="row">
        {report.status === "draft" && user.role === "analyst" && caseData.case.assigned_analyst === user.user_id
          ? <button className="primary" onClick={() => act(`/reports/${report.report_id}/approve-content`)}>Approve content</button> : null}
        {report.status === "content_approved" && user.role === "manager"
          ? <button className="primary" onClick={() => act(`/reports/${report.report_id}/approve-export`)}>Approve export (second approval)</button> : null}
        {report.status === "export_approved" ? <button onClick={download}>Download PDF</button> : null}
      </div>
      <small>Content approval: {report.content_approved_by || "pending"} · Export approval: {report.export_approved_by || "pending"} (must be a different person)</small>
    </div>
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

  async function act(fn) {
    setError(null);
    try {
      await fn();
      detail.reload();
    } catch (e) {
      setError(e);
    }
  }

  return (
    <div className="stack">
      <ErrorBox error={detail.error || error} />
      {d ? (
        <>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <h1>{t("case")} {d.case.case_id}</h1>
              <small><Link to={`/premises/${d.case.premise_id}`}>{d.case.premise_id}</Link> · {d.case.transformer_id} · origin {d.case.origin}
                {d.case.score_at_creation != null ? ` · score ${d.case.score_at_creation} at creation` : ""}</small>
            </div>
            <span className="chip info" style={{ fontSize: "0.9rem" }}>{d.case.status}</span>
          </div>
          <div className="grid two">
            <div className="card stack">
              <h2>People</h2>
              <div>Analyst: {d.case.assigned_analyst || <span className="muted">unclaimed</span>}
                {user.role === "analyst" && !d.case.assigned_analyst && d.case.status !== "closed"
                  ? <button style={{ marginLeft: 8 }} onClick={() => act(() => post(`/cases/${id}/claim`))}>{t("claim")}</button> : null}</div>
              <div>Team: {d.case.assigned_team || "–"} {d.case.joint_operation ? <span className="chip risk">joint operation with police</span> : null}</div>
              {d.dispatch_suggestion ? (
                <div className="notice">
                  <b>Dispatch suggestion: {d.dispatch_suggestion.suggested_team}</b> ({d.dispatch_suggestion.distance_km} km) · {d.dispatch_suggestion.status}
                  <div><small>{d.dispatch_suggestion.rationale}</small></div>
                  {user.role === "supervisor" && d.dispatch_suggestion.status === "pending" ? (
                    <div className="row" style={{ marginTop: 8 }}>
                      <button className="primary" onClick={() => act(() => post(`/cases/${id}/dispatch-suggestion/approve`, { approve: true }))}>{t("approve")}</button>
                      <button onClick={() => act(() => post(`/cases/${id}/dispatch-suggestion/approve`, { approve: false }))}>{t("reject")}</button>
                    </div>
                  ) : null}
                </div>
              ) : null}
              {user.role === "supervisor" && ["new", "assigned"].includes(d.case.status) ? (
                <div className="row">
                  <select value={team} onChange={(e) => setTeam(e.target.value)}>
                    <option value="">{t("team")}…</option>
                    {(teams.data || []).map((tm) => <option key={tm.team_id} value={tm.team_id}>{tm.name} ({tm.team_id})</option>)}
                  </select>
                  <button disabled={!team} onClick={() => act(() => patch(`/cases/${id}/assign`, { team }))}>{t("assign")}</button>
                </div>
              ) : null}
            </div>
            <div className="card">
              <h2>Contact and location</h2>
              {d.contact ? (
                <div className="notice warn"><b>{d.contact.holder_name}</b><div>{d.contact.address}</div><div>{d.contact.contact}</div>
                  <small>Shown on an open case to its analyst, supervisor and assigned inspector; logged.</small></div>
              ) : <Masked note={d.case.status === "closed" ? "The case is closed." : "Only this case's analyst, the supervisor and the assigned inspector see them."} />}
            </div>
          </div>
          <div className="grid two">
            <div className="card">
              <h2>Status history</h2>
              <ul className="timeline">
                {d.events.map((e, i) => (
                  <li key={i}><small>{new Date(e.ts).toLocaleString()}</small><span><b>{e.event_type.replace("outcome:", "outcome: ")}</b> · {e.actor}</span></li>
                ))}
              </ul>
            </div>
            <div className="card">
              <h2>Inspection outcomes</h2>
              {d.outcomes.length ? d.outcomes.map((o) => (
                <div key={o.visit_no} style={{ marginBottom: 12 }}>
                  <div><b>Visit {o.visit_no}: {t(o.outcome)}</b> {o.reason_tag ? <span className="chip">{o.reason_tag}</span> : null}
                    <small> · {o.recorded_by} · {new Date(o.recorded_at).toLocaleString()}</small></div>
                  {o.notes_redacted ? <p style={{ margin: "4px 0" }}>{o.notes_redacted}</p> : null}
                  <div className="row">{(o.photo_keys || []).map((k) => <Photo key={k} caseId={id} photoKey={k} />)}</div>
                </div>
              )) : <p className="muted">No visit yet.</p>}
              <small>Notes are shown redacted; personal details typed into notes never leave the case service.</small>
            </div>
          </div>
          {similar.data?.similar ? (
            <div className="card">
              <h2>Similar past cases</h2>
              <table><thead><tr><th>Case</th><th>Outcome</th><th>Summary (redacted)</th><th className="num">Similarity</th></tr></thead>
                <tbody>{similar.data.similar.map((s) => (
                  <tr key={s.case_id}><td>{s.case_id}</td><td>{s.outcome.replace("_", " ")}</td><td><small>{s.summary}</small></td><td className="num">{s.similarity.toFixed(2)}</td></tr>
                ))}</tbody></table>
            </div>
          ) : null}
          {d.case.status === "reporting" && user.role === "analyst" && d.case.assigned_analyst === user.user_id && !d.reports.length ? (
            <button className="primary" onClick={() => act(() => post(`/agents/report/${id}`))}>Draft report</button>
          ) : null}
          {d.reports.map((r) => <Report key={r.report_id} report={r} caseData={d} onChange={detail.reload} />)}
        </>
      ) : null}
    </div>
  );
}
