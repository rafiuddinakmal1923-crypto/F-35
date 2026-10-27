// Chat panel (SRS 5.1): the analyst chatbot (numeric questions, region-limited, query shown, FR-AG-03)
// and the field assistant (procedure questions from approved documents with citations, FR-AG-04).
// Chatbot answers draw the chart the query service names for their rows; the table and query stay one click away.
import { useEffect, useRef, useState } from "react";
import { post, session } from "../api.js";
import { QueryChart } from "../components/Charts.jsx";
import { t } from "../i18n.js";

const EXAMPLES = {
  analyst: ["Which zones had a gap above 10% this week?", "Show the gap trend for TX-CEN-001", "Daily gap of all zones as a chart",
    "Unexplained energy by district", "How many open cases are there?", "Hit rate model-ranked vs random sample", "Inspection outcomes so far"],
  field: ["What should I photograph at the meter board?", "What does a flat 24/7 gap mean?", "Should I disconnect the bypass cable?"],
};

function csv(rows) {
  const cols = Object.keys(rows[0] || {});
  const cell = (v) => (/[",\n]/.test(String(v ?? "")) ? `"${String(v).replaceAll('"', '""')}"` : String(v ?? ""));
  return [cols.join(","), ...rows.map((r) => cols.map((c) => cell(r[c])).join(","))].join("\n");
}

function Answer({ item }) {
  const [view, setView] = useState("chart");
  if (item.error) return <div className="notice error">{item.error}</div>;
  const r = item.result;
  const q = r.query;
  const hasChart = q?.chart && q.rows?.length;
  function download() {
    const url = URL.createObjectURL(new Blob([csv(q.rows)], { type: "text/csv" }));
    Object.assign(document.createElement("a"), { href: url, download: `${q.template}.csv` }).click();
    URL.revokeObjectURL(url);
  }
  return (
    <div className={`answer ${r.refused ? "refused" : ""}`}>
      <p className="answer-text">{r.answer}</p>
      {q ? (
        <>
          {q.rows.length ? (
            <div className="segmented" role="tablist">
              {hasChart ? <button className={view === "chart" ? "active" : ""} onClick={() => setView("chart")}>Chart</button> : null}
              <button className={view === "table" || !hasChart ? "active" : ""} onClick={() => setView("table")}>Table</button>
              <button className={view === "query" ? "active" : ""} onClick={() => setView("query")}>Query used</button>
              <button onClick={download} title="Download the rows as CSV">CSV</button>
            </div>
          ) : null}
          {view === "chart" && hasChart ? <QueryChart chart={q.chart} rows={q.rows} /> : null}
          {(view === "table" || (!hasChart && view === "chart")) && q.rows.length ? (
            <div className="table-wrap"><table>
              <thead><tr>{Object.keys(q.rows[0]).map((c) => <th key={c}>{c.replaceAll("_", " ")}</th>)}</tr></thead>
              <tbody>{q.rows.map((row, i) => <tr key={i}>{Object.values(row).map((v, j) => <td key={j}>{String(v ?? "")}</td>)}</tr>)}</tbody>
            </table></div>
          ) : null}
          {view === "query" || !q.rows.length ? (
            <pre className="query">{q.sql}{"\n"}{JSON.stringify(q.params)}</pre>
          ) : null}
        </>
      ) : null}
      {r.sources?.length ? (
        <ol className="sources">
          {r.sources.map((s, i) => <li key={i}><small>{s.title}{s.section ? `, ${s.section}` : ""} ({s.source_ref})</small></li>)}
        </ol>
      ) : null}
      <small className="muted">{q ? `Template ${q.template} · ` : ""}{r.mode ? `answered in ${r.mode} mode` : ""}</small>
    </div>
  );
}

export default function Assistant() {
  const { user } = session();
  const canAnalyst = ["manager", "analyst"].includes(user?.role);
  const [agent, setAgent] = useState(canAnalyst ? "analyst" : "field");
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [history.length, busy]);

  async function ask(text) {
    const q = (text ?? message).trim();
    if (!q || busy) return;
    setBusy(true);
    setMessage("");
    setHistory((h) => [...h, { q, agent, pending: true }]);
    let entry;
    try {
      entry = { q, agent, result: await post("/agents/chat", { agent, message: q }) };
    } catch (e) {
      entry = { q, agent, error: e.message };
    }
    setHistory((h) => [...h.slice(0, -1), entry]);
    setBusy(false);
  }

  return (
    <div className="assistant">
      <div className="assistant-head">
        <div>
          <h1>{t("assistant")}</h1>
          <small className="muted">Answers come only from your region's results or approved documents; agents never act on their own.</small>
        </div>
        {canAnalyst ? (
          <div className="segmented">
            <button className={agent === "analyst" ? "active" : ""} onClick={() => setAgent("analyst")}>Numbers and charts</button>
            <button className={agent === "field" ? "active" : ""} onClick={() => setAgent("field")}>Procedures</button>
          </div>
        ) : null}
      </div>
      <div className="chat-log">
        {!history.length ? (
          <div className="chat-empty">
            <p><b>{agent === "analyst" ? "Ask about zones, gaps, cases and hit rates." : "Ask about inspection procedures."}</b></p>
            <p className="muted">{agent === "analyst" ? "Try a trend or a breakdown: the answer comes with a chart, its table and the query used."
              : "Answers cite the approved document they come from, or say \"not found\"."}</p>
          </div>
        ) : null}
        {history.map((item, i) => (
          <div key={i} className="chat-turn">
            <div className="chat-q">{item.q}</div>
            {item.pending ? <div className="answer typing"><span /><span /><span /></div> : <Answer item={item} />}
          </div>
        ))}
        <div ref={end} style={{ scrollMarginBottom: 150 }} />
      </div>
      <div className="chat-input">
        <div className="chips">{EXAMPLES[agent].map((ex) => <button key={ex} type="button" onClick={() => ask(ex)} disabled={busy}>{ex}</button>)}</div>
        <form className="row" onSubmit={(e) => { e.preventDefault(); ask(); }}>
          <input style={{ flex: 1, minWidth: 220 }} value={message} onChange={(e) => setMessage(e.target.value)} maxLength={1000}
            placeholder={agent === "analyst" ? "e.g. Show the gap trend for TX-CEN-002 over 14 days" : "e.g. What should I photograph at the meter board?"}
            aria-label="Question" />
          <button className="primary" disabled={busy || !message.trim()}>Ask</button>
        </form>
      </div>
    </div>
  );
}
