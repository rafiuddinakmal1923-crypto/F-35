// Audit log (FR-AD-02, NFR-12): every case view, assignment, outcome, export and agent action.
import { useState } from "react";
import { get } from "../api.js";
import { ErrorBox, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

export default function Audit() {
  const [user, setUser] = useState("");
  const [action, setAction] = useState("");
  const query = new URLSearchParams({ ...(user && { user }), ...(action && { action }), limit: 200 }).toString();
  const log = useLoad(() => get(`/audit?${query}`), [query]);
  const [verify, setVerify] = useState(null);
  const [error, setError] = useState(null);

  async function runVerify() {
    setError(null);
    try {
      setVerify(await get("/audit/verify"));
    } catch (e) {
      setError(e);
    }
  }

  return (
    <div className="stack">
      <h1>{t("audit")}</h1>
      <div className="row">
        <label>User<input value={user} onChange={(e) => setUser(e.target.value)} placeholder="analyst.cen" /></label>
        <label>Action starts with<input value={action} onChange={(e) => setAction(e.target.value)} placeholder="case." /></label>
        <button onClick={runVerify}>Verify hash chain</button>
      </div>
      <ErrorBox error={log.error || error} />
      {verify ? (
        <div className={`notice ${verify.ok ? "ok" : "error"}`}>
          {verify.ok ? `Chain intact: ${verify.rows} rows, ${verify.anchors_checked} daily anchor(s) outside the database match.`
            : `Tampering detected: ${verify.problems.map((p) => `row ${p.log_id}: ${p.problem}`).join("; ")}`}
        </div>
      ) : null}
      <div className="card table-wrap">
        <table><thead><tr><th>#</th><th>Time</th><th>User</th><th>Action</th><th>Object</th><th>Detail</th><th>Hash</th></tr></thead><tbody>
          {(log.data?.rows || []).map((r) => (
            <tr key={r.log_id}><td>{r.log_id}</td><td><small>{new Date(r.ts).toLocaleString()}</small></td><td>{r.user_id}</td><td>{r.action}</td>
              <td>{r.object_ref}</td><td><small>{r.detail ? JSON.stringify(r.detail) : ""}</small></td><td><code>{r.row_hash.slice(0, 10)}…</code></td></tr>
          ))}
        </tbody></table>
      </div>
    </div>
  );
}
