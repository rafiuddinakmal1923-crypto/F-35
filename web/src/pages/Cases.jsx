import { useState } from "react";
import { Link } from "react-router-dom";
import { get, session } from "../api.js";
import { ErrorBox, JobButton, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

const STATUSES = ["", "new", "assigned", "visited", "reporting", "closed"];

export default function Cases() {
  const [status, setStatus] = useState("");
  const { user } = session();
  const cases = useLoad(() => get(`/cases${status ? `?status=${status}` : ""}`), [status], 10000);
  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>{t("cases")}</h1>
        {user?.role === "supervisor" ? <JobButton path="/jobs/create-cases" label={t("runCaseJob")} onDone={cases.reload} /> : null}
      </div>
      <label style={{ maxWidth: 200 }}>{t("status")}
        <select value={status} onChange={(e) => setStatus(e.target.value)}>{STATUSES.map((s) => <option key={s} value={s}>{s || "all"}</option>)}</select>
      </label>
      <ErrorBox error={cases.error} />
      <div className="card table-wrap">
        <table>
          <thead><tr><th>{t("case")}</th><th>{t("premise")}</th><th>{t("status")}</th><th>{t("origin")}</th><th className="num">{t("score")}</th>
            <th>Analyst</th><th>{t("team")}</th><th>Dispatch suggestion</th></tr></thead>
          <tbody>
            {(cases.data?.cases || []).map((c) => (
              <tr key={c.case_id}>
                <td><Link to={`/cases/${c.case_id}`}>{c.case_id}</Link></td>
                <td>{c.premise_id}<br /><small>{c.transformer_id}</small></td>
                <td><span className={`chip ${c.status === "closed" ? "" : "info"}`}>{c.status}</span></td>
                <td>{c.origin === "random_sample" ? <span className="chip">random sample</span> : c.origin}</td>
                <td className="num">{c.score_at_creation ?? "–"}</td>
                <td>{c.assigned_analyst || <span className="muted">unclaimed</span>}</td>
                <td>{c.assigned_team || "–"}{c.joint_operation ? <span className="chip risk">joint op</span> : null}</td>
                <td>{c.suggested_team ? `${c.suggested_team} (${c.suggestion_status})` : "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {cases.data && !cases.data.cases.length ? <p className="muted">No cases.</p> : null}
      </div>
    </div>
  );
}
