import { Kanban, List } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { get, session } from "../api.js";
import { ErrorBox, JobButton, ScoreRing, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

const STATUSES = ["new", "assigned", "visited", "reporting", "closed"];
const FILTERS = { all: () => true, mine: (c, u) => c.assigned_analyst === u.user_id, unclaimed: (c) => !c.assigned_analyst && c.status !== "closed",
  random: (c) => c.origin === "random_sample", joint: (c) => c.joint_operation };
const FILTER_LABEL = { all: "All", mine: "Mine", unclaimed: "Unclaimed", random: "Random sample", joint: "Joint operation" };

function Board({ cases }) {
  return (
    <div className="board">
      {STATUSES.map((s) => {
        const col = cases.filter((c) => c.status === s);
        return (
          <div key={s} className="board-col">
            <h3>{s}<span className="count-pill">{col.length}</span></h3>
            {col.map((c) => (
              <Link key={c.case_id} to={`/cases/${c.case_id}`} className="board-card">
                <div className="row" style={{ justifyContent: "space-between", flexWrap: "nowrap" }}>
                  <b>{c.case_id}</b>{c.score_at_creation != null ? <ScoreRing score={c.score_at_creation} size={30} /> : null}
                </div>
                <small>{c.premise_id} · {c.transformer_id}</small>
                <div>{c.origin === "random_sample" ? <span className="chip">random sample</span> : null}
                  {c.joint_operation ? <span className="chip risk">joint op</span> : null}
                  {c.assigned_team ? <span className="chip info">{c.assigned_team}</span> : null}
                  {!c.assigned_analyst && s !== "closed" ? <span className="chip warn">unclaimed</span> : null}</div>
              </Link>
            ))}
          </div>
        );
      })}
    </div>
  );
}

export default function Cases() {
  const [status, setStatus] = useState("");
  const [filter, setFilter] = useState("all");
  const [view, setView] = useState(() => {
    try { return localStorage.getItem("vg_cases_view") || "table"; } catch { return "table"; }
  });
  const { user } = session();
  const cases = useLoad(() => get(`/cases${status && view === "table" ? `?status=${status}` : ""}`), [status, view], 10000);
  const shown = (cases.data?.cases || []).filter((c) => FILTERS[filter](c, user));
  function pick(v) {
    setView(v);
    try { localStorage.setItem("vg_cases_view", v); } catch { /* storage may be blocked */ }
  }
  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>{t("cases")}</h1>
        {user?.role === "supervisor" ? <JobButton path="/jobs/create-cases" label={t("runCaseJob")} onDone={cases.reload} /> : null}
      </div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row">
          <div className="segmented" role="group" aria-label="Filter">
            {Object.keys(FILTERS).filter((f) => f !== "mine" || user?.role === "analyst").map((f) => (
              <button key={f} className={filter === f ? "active" : ""} onClick={() => setFilter(f)}>{FILTER_LABEL[f]}</button>
            ))}
          </div>
          {view === "table" ? (
            <label style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>{t("status")}
              <select value={status} onChange={(e) => setStatus(e.target.value)}>{["", ...STATUSES].map((s) => <option key={s} value={s}>{s || "all"}</option>)}</select>
            </label>
          ) : null}
        </div>
        <div className="segmented" role="group" aria-label="View">
          <button className={view === "table" ? "active" : ""} onClick={() => pick("table")}><List size={15} style={{ verticalAlign: -2 }} /> Table</button>
          <button className={view === "board" ? "active" : ""} onClick={() => pick("board")}><Kanban size={15} style={{ verticalAlign: -2 }} /> Board</button>
        </div>
      </div>
      <ErrorBox error={cases.error} />
      {view === "board" ? <Board cases={shown} /> : (
        <div className="card table-wrap">
          <table>
            <thead><tr><th>{t("case")}</th><th>{t("premise")}</th><th>{t("status")}</th><th>{t("origin")}</th><th className="num">{t("score")}</th>
              <th>Analyst</th><th>{t("team")}</th><th>Dispatch suggestion</th></tr></thead>
            <tbody>
              {shown.map((c) => (
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
          {cases.data && !shown.length ? <p className="muted">No cases here.{user?.role === "supervisor" ? " Run the case job to create cases from the latest scores." : ""}</p> : null}
        </div>
      )}
    </div>
  );
}
