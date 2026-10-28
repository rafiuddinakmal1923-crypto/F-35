// Design-system primitives (UI brief 1): panels with loading/empty/error states, KPI tiles with a
// sparkline and change, the amber score ring, status pills (icon + label, never colour alone) and the
// right-hand drawer. Colours only through CSS tokens.
import { AlertTriangle, ArrowDownRight, ArrowUpRight, CircleCheck, CircleDashed, Gauge, Inbox, Minus, ShieldAlert, TriangleAlert, X, Zap } from "lucide-react";
import { useEffect, useRef } from "react";
import { t } from "../i18n.js";
import { change as changeOf } from "../lib/format.js";

export function Skeleton({ lines = 3, block = false }) {
  return (
    <div className="skeleton" aria-busy="true" aria-label={t("loading")}>
      {block ? <span className="block" /> : null}
      {Array.from({ length: lines }, (_, i) => <span key={i} style={{ width: `${90 - i * 15}%` }} />)}
    </div>
  );
}

export function EmptyState({ children, icon: Icon = Inbox }) {
  return <div className="state"><Icon size={18} aria-hidden="true" /><span>{children || t("emptyDefault")}</span></div>;
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="state error" role="alert">
      <AlertTriangle size={18} aria-hidden="true" />
      <span><b>{t("loadError")}</b><br /><small>{error?.message || String(error || "")}</small></span>
      {onRetry ? <button type="button" onClick={onRetry}>{t("retry")}</button> : null}
    </div>
  );
}

// A panel shows its own state: skeleton while loading, an error with retry, an empty message, or its content.
export function Panel({ title, icon: Icon, actions, loading, error, empty, emptyText, onRetry, className = "", children, id, headingLevel = 2 }) {
  const H = `h${headingLevel}`;
  return (
    <section className={`panel ${className}`} aria-labelledby={id ? `${id}-title` : undefined}>
      {title || actions ? (
        <div className="panel-head">
          {title ? <H id={id ? `${id}-title` : undefined}>{Icon ? <Icon size={16} aria-hidden="true" /> : null}{title}</H> : <span />}
          {actions ? <div className="panel-actions">{actions}</div> : null}
        </div>
      ) : null}
      <div className="panel-body">
        {error ? <ErrorState error={error} onRetry={onRetry} /> : loading ? <Skeleton block /> : empty ? <EmptyState>{emptyText}</EmptyState> : children}
      </div>
    </section>
  );
}

export function Sparkline({ values, width = 96, height = 30, color = "var(--accent)", label }) {
  const v = (values || []).filter((x) => x != null && Number.isFinite(Number(x))).map(Number);
  if (v.length < 2) return null;
  const lo = Math.min(...v);
  const hi = Math.max(...v);
  const pts = v.map((x, i) => [(i / (v.length - 1)) * (width - 4) + 2, height - 3 - ((x - lo) / (hi - lo || 1)) * (height - 6)]);
  const last = pts[pts.length - 1];
  return (
    <svg className="sparkline" width={width} height={height} viewBox={`0 0 ${width} ${height}`} role={label ? "img" : undefined}
      aria-label={label} aria-hidden={label ? undefined : "true"}>
      <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={last[0]} cy={last[1]} r="2.5" fill={color} />
    </svg>
  );
}

// KPI tile: big number, label, sparkline and change against the previous value of the same series.
export function KpiTile({ icon: Icon = Gauge, label, value, unit, trend, goodWhenDown = true, estimate, help, placeholder, onClick, note }) {
  const c = changeOf(trend);
  const dir = !c || Math.abs(c.delta) < 1e-9 ? "flat" : c.delta > 0 ? "up" : "down";
  const good = dir === "flat" ? "" : (dir === "down") === goodWhenDown ? "good" : "bad";
  const Arrow = dir === "up" ? ArrowUpRight : dir === "down" ? ArrowDownRight : Minus;
  const interactive = onClick ? { role: "button", tabIndex: 0, onClick, onKeyDown: (e) => (e.key === "Enter" || e.key === " ") && onClick() } : {};
  return (
    <div className={`card kpi ${onClick ? "clickable" : ""}`} {...interactive}>
      <div className="kpi-label"><Icon size={14} aria-hidden="true" />{label}{estimate ? <span className="estimate-tag">{t("estimate")}</span> : null}
        {help ? <span className="help" tabIndex={0} role="note" aria-label={help} data-tip={help}>?</span> : null}</div>
      <div className="kpi-top">
        {placeholder ? <div className="kpi-value placeholder">{placeholder}</div>
          : <div className="kpi-value">{value ?? "–"}{unit ? <small>{unit}</small> : null}</div>}
        <Sparkline values={trend} color={good === "bad" ? "var(--accent)" : "var(--ok)"} />
      </div>
      {c ? (
        <span className={`change ${good}`}><Arrow size={13} aria-hidden="true" />
          {c.pct != null ? `${Math.abs(c.pct * 100).toFixed(0)}%` : Math.abs(c.delta).toFixed(0)} {t("vsDayBefore")}</span>
      ) : note ? <span className="change">{note}</span> : null}
    </div>
  );
}

// Risk score 0-100 as a ring with an amber fill (the number is in the middle and in the label).
export function ScoreRing({ score, size = 44 }) {
  const s = Math.min(Math.max(Number(score) || 0, 0), 100);
  const stroke = size >= 60 ? 6 : 4.5;
  const r = size / 2 - stroke;
  const c = 2 * Math.PI * r;
  return (
    <svg className="score-ring" width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={t("scoreOf", { score: s })}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--panel-2)" strokeWidth={stroke} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={s >= 20 ? "var(--accent)" : "var(--neutral)"} strokeWidth={stroke} strokeLinecap="round"
        strokeDasharray={`${(s / 100) * c} ${c}`} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" fontSize={size * 0.34} fontWeight="600" fill="var(--text)">{s}</text>
    </svg>
  );
}

const PILL = {
  flagged: { cls: "risk", Icon: TriangleAlert, key: "pillFlagged" },
  balanced: { cls: "ok", Icon: CircleCheck, key: "pillBalanced" },
  noBalance: { cls: "neutral", Icon: CircleDashed, key: "pillNoBalance" },
  largeLoad: { cls: "risk", Icon: Zap, key: "largeLoad" },
  flat: { cls: "risk", Icon: Minus, key: "pillFlat" },
  theft: { cls: "theft", Icon: ShieldAlert, key: "confirmed_theft" },
  cleared: { cls: "ok", Icon: CircleCheck, key: "pillCleared" },
  info: { cls: "info", Icon: null, key: null },
};

export function StatusPill({ kind, children, title }) {
  const p = PILL[kind] || PILL.info;
  return <span className={`pill ${p.cls}`} title={title}>{p.Icon ? <p.Icon size={13} aria-hidden="true" /> : null}{children || (p.key ? t(p.key) : null)}</span>;
}

export function zoneStatus(z) {
  if (!z.balance_available) return "noBalance";
  return z.flagged ? "flagged" : "balanced";
}

// Right-hand drawer: opens premises and cases without leaving the zone. Escape closes; focus returns.
export function Drawer({ title, onClose, children, actions }) {
  const closeRef = useRef(null);
  useEffect(() => {
    const before = document.activeElement;
    closeRef.current?.focus();
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("keydown", onKey); before?.focus?.(); };
  }, [onClose]);
  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={title}>
        <div className="drawer-head">
          <h2>{title}</h2>
          <div className="row">{actions}<button ref={closeRef} type="button" className="icon-btn" onClick={onClose} aria-label={t("close")}><X size={18} /></button></div>
        </div>
        <div className="drawer-body">{children}</div>
      </aside>
    </>
  );
}

export function SrSummary({ children }) {
  return <p className="sr-only">{children}</p>;
}
