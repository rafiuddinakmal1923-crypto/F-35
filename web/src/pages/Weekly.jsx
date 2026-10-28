// Weekly summary (managers and supervisors): a dashboard of the region's week, in the interface language
// (English or Bahasa Melayu). Download PDF gives the full printed report (every chart, table, the glossary and
// the assumptions); Send puts it in Telegram or the in-app chat. Every figure comes from the database and every
// sentence from the same fixed rules as the PDF (GET /weekly?lang= returns both), never from the language model.
import { Activity, Banknote, ClipboardList, Clock, Crosshair, Database, Download, FileCheck, Info, ListChecks, Map as MapIcon,
  Send, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get, post, request } from "../api.js";
import { LineChart } from "../components/Charts.jsx";
import { ErrorBox } from "../components/Common.jsx";
import { KpiTile, Panel, Skeleton, StatusPill } from "../components/ui.jsx";
import { t, useLang } from "../i18n.js";
import { int } from "../lib/format.js";
import { LinkTelegram } from "./Dispatch.jsx";

const STATUSES = ["new", "assigned", "visited", "reporting", "closed"];
const OUTCOMES = ["confirmed_theft", "false_alarm", "inconclusive", "no_access"];

// "-2.6% vs last week" from the backend's change, or a plain note when there is nothing to compare with.
function vsLast(now, before, pctChange) {
  if (pctChange != null) return pctChange === 0 ? t("wkSameAsLast") : t("wkVsLast", { s: `${pctChange > 0 ? "+" : "−"}${Math.abs(pctChange)}%` });
  if (before == null) return t("wkNoPrev");
  const delta = (now ?? 0) - before;
  return delta === 0 ? t("wkSameAsLast") : t("wkVsLast", { s: `${delta > 0 ? "+" : "−"}${Math.abs(delta)}` });
}

// Same month names as the PDF ("24–30 Sep", "Ogo" in Bahasa Melayu).
const MONTHS = { en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  ms: ["Jan", "Feb", "Mac", "Apr", "Mei", "Jun", "Jul", "Ogo", "Sep", "Okt", "Nov", "Dis"] };

function day(iso, lang) {
  const [, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[lang === "ms" ? "ms" : "en"][m - 1]}`;
}

function span(a, b, lang) {
  return a.slice(0, 7) === b.slice(0, 7) ? `${Number(a.slice(8))}–${day(b, lang)}` : `${day(a, lang)} – ${day(b, lang)}`;
}

// Each zone: unexplained kWh/day as a bar (amber when flagged), the margin of error as a whisker and the zone's
// own threshold as a tick, so the flag can be read without colour.
function ZoneBars({ zones, lang }) {
  const hi = Math.max(...zones.map((z) => Math.max(z.gap_kwh_per_day + z.margin_kwh, z.threshold_kwh)), 1) * 1.08;
  const at = (v) => `${(Math.max(v, 0) / hi) * 100}%`;
  return (
    <ul className="wk-zones">
      {zones.map((z) => (
        <li key={z.transformer_id}>
          <div className="wk-zone-name">
            <Link to={`/zones/${z.transformer_id}`} className="zid">{z.transformer_id}</Link>
            <small className="muted">{z.district}</small>
          </div>
          <div className="wk-track" role="img" aria-label={t("wkZoneAria", { zone: z.transformer_id, g: int(z.gap_kwh_per_day, lang), m: int(z.margin_kwh, lang), th: int(z.threshold_kwh, lang) })}>
            <span className={`wk-bar ${z.flagged ? "risk" : "ok"}`} style={{ width: at(z.gap_kwh_per_day) }} />
            <span className="wk-whisker" style={{ left: at(z.gap_kwh_per_day - z.margin_kwh), width: `calc(${at(z.gap_kwh_per_day + z.margin_kwh)} - ${at(z.gap_kwh_per_day - z.margin_kwh)})` }} />
            <span className="wk-threshold" style={{ left: at(z.threshold_kwh) }} title={`${t("wkThresholdMark")} ${int(z.threshold_kwh, lang)} kWh`} />
          </div>
          <div className="wk-zone-figs">
            <b>{int(z.gap_kwh_per_day, lang)}</b> kWh/{t("day")}
            <small className="muted">{z.gap_pct}% · {t("wkThresholdMark")} {int(z.threshold_kwh, lang)}</small>
          </div>
          <div className="row wk-zone-tags">
            <StatusPill kind={z.flagged ? "flagged" : "balanced"} />
            {z.priority === "large_load" ? <StatusPill kind="largeLoad" /> : null}
            {z.open_cases ? <StatusPill kind="info">{t("wkOpenCasesN", { n: z.open_cases })}</StatusPill> : null}
            {z.flagged && z.suspects_without_case ? <StatusPill kind="info">{t("wkWaiting", { n: z.suspects_without_case })}</StatusPill> : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

// Hit rates with their 95% Wilson range: the gap between the two rows is the model's value.
function HitRates({ rates }) {
  const rows = [["model_ranked", t("wkModel")], ["random_sample", t("wkRandom")]].filter(([k]) => rates[k]);
  if (!rows.length) return <p className="muted">{t("wkNoHits")}</p>;
  return (
    <ul className="wk-hits">
      {rows.map(([key, label]) => {
        const h = rates[key];
        return (
          <li key={key}>
            <span>{label}<small className="muted">{t("wkOfN", { a: h.confirmed_theft, n: h.inspections })}</small></span>
            <div className="wk-track" role="img" aria-label={`${label}: ${h.hit_rate_pct}%, ${t("wkRange", { lo: h.ci_low_pct, hi: h.ci_high_pct })}`}>
              {h.ci_low_pct != null ? <span className="wk-range" style={{ left: `${h.ci_low_pct}%`, width: `${h.ci_high_pct - h.ci_low_pct}%` }} /> : null}
              <span className={`wk-dot ${key === "model_ranked" ? "risk" : "neutral"}`} style={{ left: `${h.hit_rate_pct ?? 0}%` }} />
            </div>
            <span className="wk-hit-figs"><b>{h.hit_rate_pct ?? "–"}%</b>
              {h.ci_low_pct != null ? <small className="muted">{t("wkRange", { lo: h.ci_low_pct, hi: h.ci_high_pct })}</small> : null}</span>
          </li>
        );
      })}
    </ul>
  );
}

function Takeaway({ children }) {
  return children ? <p className="wk-takeaway"><Info size={14} aria-hidden="true" />{children}</p> : null;
}

export default function Weekly() {
  const lang = useLang();
  const [d, setD] = useState(null);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let live = true;
    setError(null);
    get(`/weekly?lang=${lang}`).then((r) => live && setD(r)).catch((e) => live && setError(e));
    return () => { live = false; };
  }, [lang, tick]);

  async function download() {
    setError(null);
    setBusy(true);
    try {
      const res = await request(`/weekly/pdf?lang=${lang}`, { raw: true });
      const name = (res.headers.get("content-disposition") || "").match(/filename="([^"]+)"/)?.[1] || "voltguard-weekly.pdf";
      const url = URL.createObjectURL(await res.blob());
      Object.assign(document.createElement("a"), { href: url, download: name }).click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  async function send() {
    setError(null);
    try {
      const r = await post(`/weekly/send?lang=${lang}`);
      setMessage(r.channel === "telegram" ? t("weeklySentTelegram") : t("weeklySentApp"));
    } catch (e) {
      setError(e);
    }
  }

  const text = d?.text || {};
  const k = d?.kpis;
  const ready = d && !d.empty;
  const loading = !d && !error;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{t("weekly")}{ready ? <small className="muted wk-id"> · {d.report_id}</small> : null}</h1>
          <span className="sub">{t("weeklyNote")}</span>
          {ready ? (
            <span className="sub wk-windows">
              {t("wkMeterWeek")}: <b>{span(d.energy_window.from, d.energy_window.to, lang)}</b> · {t("wkFieldWeek")}: <b>{span(d.work_window.from, d.work_window.to, lang)}</b>
              <span className="help" tabIndex={0} role="note" aria-label={text.why_two_dates} data-tip={text.why_two_dates}>?</span>
            </span>
          ) : null}
        </div>
        <div className="row">
          <button onClick={send} disabled={!ready}><Send size={15} aria-hidden="true" />{t("weeklySend")}</button>
          <button className="primary" onClick={download} disabled={!ready || busy}><Download size={15} aria-hidden="true" />{busy ? t("wkPreparing") : t("weeklyDownload")}</button>
        </div>
      </div>
      <ErrorBox error={error} />
      {message ? <div className="notice ok">{message}</div> : null}
      {text.banner ? <div className="notice warn"><TriangleAlert size={15} aria-hidden="true" />{text.banner}</div> : null}
      {loading ? <Skeleton lines={8} block /> : null}
      {d?.empty ? <Panel empty emptyText={text.empty} /> : null}

      {ready ? (
        <>
          <section className="panel wk-summary" aria-labelledby="wk-summary-title">
            <h2 id="wk-summary-title">{t("wkThisWeek")}</h2>
            <p>{text.summary.join(" ")}</p>
            {text.actions.length ? (
              <ol>{text.actions.map((a, i) => <li key={i}><b>{t("wkAction", { n: i + 1 })}:</b> {a}</li>)}</ol>
            ) : null}
            <small className="muted">{t("wkRuleNote")}</small>
          </section>

          <div className="grid wk-kpis">
            <KpiTile icon={TriangleAlert} label={t("wkFlagged")} value={k.flagged_zones} unit={` ${t("wkFlaggedOf", { n: k.zones_with_balance })}`}
              note={vsLast(k.flagged_zones, k.flagged_zones_prev)} help={t("wkHelpFlagged", { k: d.thresholds.consecutive_days })} />
            <KpiTile icon={Activity} label={t("wkUnexplained")} value={int(k.unexplained_kwh_per_day, lang)} unit=" kWh/d"
              note={vsLast(k.unexplained_kwh_per_day, k.unexplained_kwh_per_day_prev, k.unexplained_change_pct)} help={t("wkHelpUnexplained")} />
            <KpiTile icon={Banknote} label={t("wkMonth")} estimate value={k.unexplained_kwh_per_month != null ? `~${int(k.unexplained_kwh_per_month, lang)}` : null}
              unit=" kWh" note={d.value.rm_per_kwh ? k.value_at_risk : t("wkTariffUnset")} help={text.value} />
            <KpiTile icon={ClipboardList} label={t("wkCases")} value={`${k.cases_opened} / ${k.cases_closed}`}
              note={t("wkClosedTotal", { n: k.cases_closed_total })} help={t("wkHelpCases")} />
            <KpiTile icon={Clock} label={t("wkOverdue")} value={k.cases_overdue} note={t("wkOverdueHelp", { h: d.thresholds.escalation_hours })} />
            <KpiTile icon={FileCheck} label={t("wkReportsAlerts")} value={`${k.reports_exported} · ${k.open_alerts}`}
              note={t("wkAlertsWeek", { n: k.alerts_this_week })} help={t("wkHelpReports")} />
          </div>

          <div className="grid two">
            <Panel title={t("wkEnergyTitle")} icon={Activity} empty={d.daily_gap.length < 2} emptyText={text.energy}>
              <EnergyChart d={d} lang={lang} />
              <Takeaway>{text.energy}</Takeaway>
            </Panel>
            <Panel title={t("wkZonesTitle")} icon={MapIcon} empty={!d.zones.length} emptyText={text.zones}>
              <ZoneBars zones={d.zones} lang={lang} />
              <small className="muted">{t("wkLegendZones")}</small>
              {d.no_balance_zones.length ? <small className="muted wk-block">{t("wkNoDtm", { zones: d.no_balance_zones.map((z) => z.transformer_id).join(", ") })}</small> : null}
              <Takeaway>{text.zones}</Takeaway>
            </Panel>
            <Panel title={t("wkHitsTitle")} icon={Crosshair}>
              <HitRates rates={d.hit_rates} />
              <Takeaway>{text.hits}</Takeaway>
            </Panel>
            <Panel title={t("wkWorkTitle")} icon={ClipboardList}>
              <table className="wk-table">
                <thead><tr><th>{t("wkByStatus")}</th><th className="num">{t("wkCount")}</th></tr></thead>
                <tbody>{STATUSES.map((s) => <tr key={s}><td>{t(`status_${s}`)}</td><td className="num">{d.cases_by_status[s] ?? 0}</td></tr>)}</tbody>
              </table>
              <table className="wk-table">
                <thead><tr><th>{t("wkOutcomes")}</th><th className="num">{t("wkThisWeekCol")}</th><th className="num">{t("wkAllTime")}</th></tr></thead>
                <tbody>{OUTCOMES.map((o) => (
                  <tr key={o}><td>{t(o)}{o === "no_access" ? <small className="muted"> · {t("wkNotLearned")}</small> : null}</td>
                    <td className="num">{d.outcomes_this_week[o] ?? 0}</td><td className="num">{d.outcomes_all_time[o] ?? 0}</td></tr>
                ))}</tbody>
              </table>
            </Panel>
            <Panel title={t("wkStepsTitle")} icon={ListChecks} empty={!text.next_steps.length} emptyText={t("wkNoSteps")}>
              <ol className="wk-steps">{text.next_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
              <small className="muted">{t("wkRuleNote")}</small>
            </Panel>
            <Panel title={t("wkTrustTitle")} icon={Database}>
              <dl className="wk-facts">
                <dt>{t("wkComplete")}</dt><dd>{d.quality.meter_days_complete_pct != null ? `${d.quality.meter_days_complete_pct}%` : "–"}</dd>
                <dt>{t("wkMonthlyRead")}</dt><dd>{d.quality.monthly_read_pct != null ? `${d.quality.monthly_read_pct}%` : "–"}</dd>
                <dt>{t("wkFallbacks")}</dt><dd>{d.quality.fallbacks.length ? d.quality.fallbacks.join(", ") : t("wkNone")}</dd>
                <dt>{t("wkScoring")}</dt><dd>{d.model.scoring || "–"}</dd>
                <dt>{t("wkRetrained")}</dt><dd>{d.model.retrained ? `${d.model.retrained} (${d.model.retrained_at.slice(0, 10)})` : t("wkNone")}</dd>
                <dt>{t("wkFlagRule")}</dt><dd>{t("wkFlagRuleText", { p: `${Math.round(d.thresholds.share_of_supply * 100)}%`, g: d.thresholds.min_gap_kwh_per_day, k: d.thresholds.consecutive_days })}</dd>
              </dl>
            </Panel>
          </div>
          <p className="notice"><Download size={15} aria-hidden="true" />{t("wkFullReport")}</p>
        </>
      ) : null}
      {error && !d ? <button onClick={() => setTick((n) => n + 1)}>{t("retry")}</button> : null}
      <div style={{ maxWidth: 480 }}><LinkTelegram /></div>
    </div>
  );
}

function EnergyChart({ d, lang }) {
  const pts = d.daily_gap;
  const start = Math.max(pts.findIndex((p) => p.date >= d.energy_window.from), 0);
  const avg = pts.map((_, i) => (i < start ? d.week_average.prev : d.week_average.this));
  const summary = t("wkEnergyAria", { avg: int(d.week_average.this, lang), prev: d.week_average.prev != null ? int(d.week_average.prev, lang) : "–" });
  return (
    <LineChart height={230} yLabel="kWh/day" summary={summary} xLabels={pts.map((p) => day(p.date, lang))}
      markers={start > 0 ? [{ index: start, label: t("wkWeekStarts") }] : []}
      series={[
        { name: t("wkBand"), values: [], band: pts.map((p) => [p.gap_kwh - p.margin_kwh, p.gap_kwh + p.margin_kwh]) },
        { name: t("wkGapSeries"), values: pts.map((p) => p.gap_kwh), color: "var(--series-gap)" },
        { name: t("wkAvgSeries"), values: avg, color: "var(--neutral)", dashed: true, width: 1.5 },
      ]} />
  );
}
