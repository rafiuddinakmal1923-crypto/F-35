// Evidence timeline (UI brief 3.4): one time axis per premise with the zone's gap start, the premise's
// own change point, tenancy change, solar registration and case events. Dates come from the premise view.
import { CalendarClock, ClipboardList, Home, Sun, TrendingDown, Zap } from "lucide-react";
import { t } from "../i18n.js";

const KINDS = {
  gap: { Icon: Zap, colour: "var(--accent)" },
  change: { Icon: TrendingDown, colour: "var(--accent)" },
  tenancy: { Icon: Home, colour: "var(--info)" },
  solar: { Icon: Sun, colour: "var(--ok)" },
  case: { Icon: ClipboardList, colour: "var(--neutral)" },
};

export function timelineEvents(p) {
  const out = [];
  const days = p.usage?.days || [];
  if (p.zone?.gap_start) out.push({ kind: "gap", date: p.zone.gap_start, label: t("evGapStart") });
  else if (p.zone?.gap_since_start && days.length) out.push({ kind: "gap", date: String(days[0].date), label: t("evGapSinceStart") });
  if (p.details?.own_change_day) out.push({ kind: "change", date: p.details.own_change_day, label: t("evChangePoint") });
  for (const e of p.account_events || []) {
    if (e.event_type === "change_of_tenancy" || e.event_type === "holder_change") out.push({ kind: "tenancy", date: String(e.event_date), label: t("evTenancy") });
    if (e.event_type === "solar_registration") out.push({ kind: "solar", date: String(e.event_date), label: t("evSolar") });
  }
  for (const e of p.case_events || []) {
    out.push({ kind: "case", date: String(e.ts).slice(0, 10), label: `${t("evCase")}: ${e.event_type.replace("outcome:", "").replaceAll("_", " ")}` });
  }
  return out.sort((a, b) => a.date.localeCompare(b.date));
}

export default function EvidenceTimeline({ premise }) {
  const events = timelineEvents(premise);
  const days = (premise.usage?.days || []).map((d) => String(d.date));
  const dates = [...days, ...events.map((e) => e.date)].sort();
  if (!events.length) return <p className="muted">{t("noTimelineEvents")}</p>;
  const first = new Date(dates[0]);
  const last = new Date(dates[dates.length - 1]);
  const span = Math.max(last - first, 86400000);
  const W = 640;
  const x = (d) => 20 + ((new Date(d) - first) / span) * (W - 40);
  const lanes = {};
  return (
    <div className="ev-axis">
      <svg viewBox={`0 0 ${W} 84`} role="img" aria-label={t("timelineSummary", { list: events.map((e) => `${e.date} ${e.label}`).join("; ") })}>
        <line className="axis-line" x1="20" x2={W - 20} y1="52" y2="52" />
        <text x="20" y="76">{dates[0]}</text>
        <text x={W - 20} y="76" textAnchor="end">{dates[dates.length - 1]}</text>
        {events.map((e, i) => {
          const px = x(e.date);
          const slot = Object.keys(lanes).filter((k) => Math.abs(k - px) < 24).length;
          lanes[px + i / 1000] = true;
          const { Icon, colour } = KINDS[e.kind];
          const y = 36 - slot * 22;
          return (
            <g key={i}>
              <line x1={px} x2={px} y1={y + 8} y2="52" stroke={colour} strokeWidth="1.5" />
              <circle cx={px} cy="52" r="4" fill={colour} />
              <circle cx={px} cy={y} r="10" fill={colour} />
              <Icon x={px - 6} y={y - 6} width="12" height="12" color="#1B2433" aria-hidden="true" />
            </g>
          );
        })}
      </svg>
      <ul className="ev-list">
        {events.map((e, i) => {
          const { Icon, colour } = KINDS[e.kind];
          return (
            <li key={i}><span className="ev-dot" style={{ background: colour }}><Icon size={12} aria-hidden="true" /></span>
              <span><b className="tabular">{e.date}</b> · {e.label}</span></li>
          );
        })}
      </ul>
      {!events.some((e) => e.kind === "case") ? <small className="muted"><CalendarClock size={12} aria-hidden="true" /> {t("noCaseEventsYet")}</small> : null}
    </div>
  );
}
