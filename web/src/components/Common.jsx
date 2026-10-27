import { useEffect, useRef, useState } from "react";
import { pollJob, post } from "../api.js";
import { t } from "../i18n.js";

// Top three reasons plus "other" (and "capped" when clipping applies): they add up to the score (FR-PS-07).
export function Reasons({ reasons, score }) {
  if (!reasons?.length) return <p className="muted">No reasons recorded.</p>;
  const max = Math.max(...reasons.map((r) => Math.abs(r.contribution)), 1);
  const total = reasons.reduce((s, r) => s + r.contribution, 0);
  return (
    <div className="reasons">
      {reasons.map((r, i) => (
        <div className="reason" key={i}>
          <div className={`pts ${r.contribution < 0 ? "neg" : ""}`}>{r.contribution > 0 ? "+" : ""}{r.contribution.toFixed(1)}</div>
          <div>
            <div>{r.feature === "other" ? "Other evidence" : r.feature === "capped" ? "Capped at 0-100" : r.reason_text}</div>
            <div className={`bar ${r.contribution < 0 ? "neg" : ""}`} style={{ width: `${(Math.abs(r.contribution) / max) * 100}%` }} />
          </div>
        </div>
      ))}
      {score != null ? <small>Lines add up to {total.toFixed(1)} = score {score}</small> : null}
    </div>
  );
}

export function Tags({ tags }) {
  return (tags || []).map((tag) => <span key={tag} className="chip ok">{tag.replace("_", " ")}</span>);
}

export function Confidence({ value }) {
  return value === "low" ? <span className="chip warn">low confidence</span> : <span className="chip">high confidence</span>;
}

export function Masked({ note }) {
  return <div className="masked">{t("masked")}. {note}</div>;
}

export function ErrorBox({ error }) {
  if (!error) return null;
  return <div className="notice error">{error.message || String(error)}</div>;
}

// Start a job and poll its status; one heavy job at a time, so a second click shows "queued".
export function JobButton({ path, label, onDone, className = "primary" }) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);
  async function start() {
    setError(null);
    try {
      const started = await post(path.includes("?") ? path : `${path}?wait=false`);
      const done = await pollJob(started.job_id, (j) => alive.current && setJob(j));
      if (done.status === "done") onDone?.(done.result);
      else setError(new Error(done.error?.split("\n")[0] || "Job failed"));
    } catch (e) {
      setError(e);
    }
  }
  const busy = job && (job.status === "queued" || job.status === "running");
  return (
    <div className="row">
      <button className={className} onClick={start} disabled={busy}>{label}</button>
      {job ? <small>{job.status}{job.progress ? `: ${job.progress}` : ""}</small> : null}
      {error ? <small style={{ color: "var(--risk)" }}>{error.message}</small> : null}
    </div>
  );
}

export function useLoad(loader, deps, refreshMs = 0) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [tick, setTick] = useState(0);
  // Optional polling: pages two people work on at once (case pages) pick up each other's changes.
  useEffect(() => {
    if (!refreshMs) return undefined;
    const timer = setInterval(() => setTick((n) => n + 1), refreshMs);
    return () => clearInterval(timer);
  }, [refreshMs]);
  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true }));
    loader().then((data) => live && setState({ data, error: null, loading: false }),
      (error) => live && setState({ data: null, error, loading: false }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { ...state, reload: () => setTick((n) => n + 1) };
}

export const fmt = (v, digits = 1) => (v == null || Number.isNaN(v) ? "–" : Number(v).toFixed(digits));
export const pct = (v) => (v == null ? "–" : `${(v * 100).toFixed(1)}%`);
