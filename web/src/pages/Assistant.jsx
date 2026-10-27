// Chat panel (SRS 5.1): the analyst chatbot (numeric questions, region-limited, query shown, FR-AG-03)
// and the field assistant (procedure questions from approved documents with citations, FR-AG-04).
import { useState } from "react";
import { post, session } from "../api.js";
import { t } from "../i18n.js";

const EXAMPLES = {
  analyst: ["Which zones had a gap above 10% this week?", "How many open cases are there?", "Hit rate model-ranked vs random sample", "Top 3 zones"],
  field: ["What should I photograph at the meter board?", "What does a flat 24/7 gap mean?", "Should I disconnect the bypass cable?"],
};

function Answer({ item }) {
  if (item.error) return <div className="notice error">{item.error}</div>;
  const r = item.result;
  return (
    <div className={`notice ${r.refused ? "warn" : ""}`}>
      <div>{r.answer}</div>
      {r.query ? (
        <details open style={{ marginTop: 8 }}>
          <summary><small>Query used ({r.query.template})</small></summary>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.8rem" }}>{r.query.sql}{"\n"}{JSON.stringify(r.query.params)}</pre>
          {r.query.rows.length ? (
            <div className="table-wrap"><table>
              <thead><tr>{Object.keys(r.query.rows[0]).map((c) => <th key={c}>{c}</th>)}</tr></thead>
              <tbody>{r.query.rows.map((row, i) => <tr key={i}>{Object.values(row).map((v, j) => <td key={j}>{String(v ?? "")}</td>)}</tr>)}</tbody>
            </table></div>
          ) : null}
        </details>
      ) : null}
      {r.sources?.length ? (
        <ol style={{ margin: "8px 0 0", paddingLeft: 20 }}>
          {r.sources.map((s, i) => <li key={i}><small>{s.title}{s.section ? `, ${s.section}` : ""} ({s.source_ref})</small></li>)}
        </ol>
      ) : null}
      {r.mode ? <small className="muted">answered in {r.mode} mode</small> : null}
    </div>
  );
}

export default function Assistant() {
  const { user } = session();
  const [agent, setAgent] = useState(["manager", "analyst"].includes(user?.role) ? "analyst" : "field");
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);

  async function ask(text) {
    const q = (text ?? message).trim();
    if (!q) return;
    setBusy(true);
    setMessage("");
    try {
      const result = await post("/agents/chat", { agent, message: q });
      setHistory((h) => [{ q, agent, result }, ...h]);
    } catch (e) {
      setHistory((h) => [{ q, agent, error: e.message }, ...h]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack" style={{ maxWidth: 900 }}>
      <h1>{t("assistant")}</h1>
      <div className="row">
        {["manager", "analyst"].includes(user?.role) ? (
          <label>Agent
            <select value={agent} onChange={(e) => setAgent(e.target.value)}>
              <option value="analyst">Analyst chatbot (numbers, your region)</option>
              <option value="field">Field assistant (approved documents)</option>
            </select>
          </label>
        ) : null}
      </div>
      <form className="row" onSubmit={(e) => { e.preventDefault(); ask(); }}>
        <input style={{ flex: 1, minWidth: 240 }} value={message} onChange={(e) => setMessage(e.target.value)} maxLength={1000}
          placeholder={EXAMPLES[agent][0]} />
        <button className="primary" disabled={busy}>Ask</button>
      </form>
      <div className="row">{EXAMPLES[agent].map((ex) => <button key={ex} type="button" onClick={() => ask(ex)}><small>{ex}</small></button>)}</div>
      <p className="muted"><small>Agents only read results and approved documents. They never disconnect supply or contact anyone, and they cite their source or say "not found".</small></p>
      {history.map((item, i) => (
        <div key={i} className="card stack">
          <b>{item.q}</b>
          <Answer item={item} />
        </div>
      ))}
    </div>
  );
}
