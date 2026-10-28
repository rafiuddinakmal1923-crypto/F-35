import { Lock } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { pollJob, post } from "../api.js";
import { t } from "../i18n.js";
import { KpiTile, ScoreRing, Sparkline } from "./ui.jsx";

export { fmt, pct } from "../lib/format.js";
export { ScoreRing, Sparkline };

const TAG_KEY = { ev_charging: "tagEv", solar: "tagSolar", vacancy: "tagVacancy" };

export function reasonLabel(r) {
  if (r.feature === "other") return r.reason_text === "Rounding" ? t("rounding") : t("otherEvidence");
  if (r.feature === "capped") return t("cappedLine");
  return r.reason_text;
}

// Reason bars: top three reasons plus "other" (and "capped" when clipping applies) add up to the score (FR-PS-07).
export function Reasons({ reasons, score }) {
  if (!reasons?.length) return <p className="muted">{t("noReasons")}</p>;
  const max = Math.max(...reasons.map((r) => Math.abs(r.contribution)), 1);
  const total = reasons.reduce((s, r) => s + r.contribution, 0);
  return (
    <div className="reasons">
      {reasons.map((r, i) => (
        <div className="reason" key={i}>
          <div className={`pts ${r.contribution < 0 ? "neg" : ""}`}>{r.contribution > 0 ? "+" : ""}{r.contribution.toFixed(1)}</div>
          <div>
            <div>{reasonLabel(r)}</div>
            <div className="track"><div className={`bar ${r.contribution < 0 ? "neg" : ""}`} style={{ width: `${(Math.abs(r.contribution) / max) * 100}%` }} /></div>
          </div>
        </div>
      ))}
      {score != null ? <small>{t("linesAddUp", { total: total.toFixed(1), score })}</small> : null}
    </div>
  );
}

export function Tags({ tags }) {
  return (tags || []).map((tag) => <span key={tag} className="chip ok">{TAG_KEY[tag] ? t(TAG_KEY[tag]) : tag.replace("_", " ")}</span>);
}

export function Confidence({ value }) {
  return value === "low" ? <span className="chip warn">{t("lowConfidence")}</span> : <span className="chip">{t("highConfidence")}</span>;
}

// Masked contact panel: a lock and a one-line reason (personal details only on an open case, for its people).
export function Masked({ note }) {
  return (
    <div className="masked"><Lock size={18} aria-hidden="true" />
      <span><b>{t("masked")}</b>{note || t("maskedReason")}</span></div>
  );
}

export function ErrorBox({ error }) {
  if (!error) return null;
  return <div className="notice error" role="alert">{error.message || String(error)}</div>;
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
      else setError(new Error(done.error?.split("\n")[0] || t("jobFailed")));
    } catch (e) {
      setError(e);
    }
  }
  const busy = job && (job.status === "queued" || job.status === "running");
  return (
    <div className="row">
      <button className={className} onClick={start} disabled={busy}>{label}</button>
      {job ? <small aria-live="polite">{t(`job_${job.status}`)}{job.progress ? `: ${job.progress}` : ""}</small> : null}
      {error ? <small style={{ color: "var(--theft-text)" }}>{error.message}</small> : null}
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

// Plain-language help next to a term or figure (hover, focus or tap shows it).
export function Help({ text }) {
  return <span className="help" tabIndex={0} role="note" aria-label={text} data-tip={text}>?</span>;
}

export function Tabs({ tabs, value, onChange }) {
  return (
    <div className="tabs-bar" role="tablist">
      {tabs.map((tb) => (
        <button key={tb.key} role="tab" aria-selected={value === tb.key} className={value === tb.key ? "active" : ""} onClick={() => onChange(tb.key)}>
          {tb.label}{tb.count != null ? <span className="count">{tb.count}</span> : null}
        </button>
      ))}
    </div>
  );
}

// Older pages' KPI card, now the design-system tile.
export function Kpi({ value, label, help, trend, goodWhenDown = true, onClick }) {
  return <KpiTile value={value} label={label} help={help} trend={trend} goodWhenDown={goodWhenDown} onClick={onClick} />;
}
