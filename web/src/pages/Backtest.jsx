// Back-test replay (UI brief 3.7, the demo of the pilot ask): pick a zone with a known case and drag the
// day slider; the zone balance, flag state and suspect ranking replay day by day, as the nightly run would
// have seen them. A marker shows the first day the known case entered the top 5% ("time to detection").
// Data: scripts/backtest.py --replay through GET /backtest/{zone}. Managers see zone-level figures only.
import { Activity, Pause, Play, Timer, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { get } from "../api.js";
import { LineChart } from "../components/Charts.jsx";
import { useLoad } from "../components/Common.jsx";
import { Panel, StatusPill } from "../components/ui.jsx";
import { t } from "../i18n.js";

export default function Backtest() {
  const list = useLoad(() => get("/backtest"), []);
  const zones = list.data?.zones || [];
  const [zone, setZone] = useState(null);
  const current = zone || zones.find((z) => z.detected)?.zone || zones[0]?.zone;
  const replay = useLoad(() => (current ? get(`/backtest/${current}`) : Promise.resolve(null)), [current]);
  const r = replay.data;
  const frames = r?.frames || [];
  const [idx, setIdx] = useState(null);
  const [playing, setPlaying] = useState(false);
  useEffect(() => { setIdx(null); setPlaying(false); }, [current]);
  const at = idx == null ? Math.max(frames.length - 1, 0) : idx;
  const frame = frames[at];
  useEffect(() => {
    if (!playing) return undefined;
    const timer = setInterval(() => setIdx((i) => {
      const n = (i ?? -1) + 1;
      if (n >= frames.length - 1) setPlaying(false);
      return Math.min(n, frames.length - 1);
    }), 450);
    return () => clearInterval(timer);
  }, [playing, frames.length]);

  const days = frame ? frame.day : 0;
  const bal = r?.balance;
  const cut = (arr) => (arr || []).map((v, i) => (i < days ? v : null));
  const known = r?.known_cases || [];
  const detectDays = known.map((k) => k.first_top5_day).filter(Boolean);
  const frameIndexOfDay = (d) => frames.findIndex((f) => f.day === d);
  const knownIds = new Set(known.map((k) => k.premise_id));
  const markers = known.filter((k) => k.first_top5_day).map((k) => ({ index: k.first_top5_day - 1, label: t("detectedDay", { day: k.first_top5_day }) }));

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{t("backtest")}</h1>
          <span className="sub">{t("backtestIntro")}</span>
        </div>
        <label>{t("zone")}
          <select value={current || ""} onChange={(e) => setZone(e.target.value)}>
            {zones.map((z) => <option key={z.zone} value={z.zone}>{z.zone} · {t("knownCasesN", { n: z.known_cases })}</option>)}
          </select>
        </label>
      </div>
      <Panel title={t("replay")} icon={Timer} loading={list.loading || replay.loading} error={list.error || replay.error}
        onRetry={replay.reload} empty={list.data && !zones.length} emptyText={t("noReplay")}>
        {frame ? (
          <>
            <div className="slider-row">
              <button type="button" className="icon-btn" onClick={() => { if (at >= frames.length - 1) setIdx(0); setPlaying((p) => !p); }}
                aria-label={playing ? t("pause") : t("play")}>{playing ? <Pause size={16} /> : <Play size={16} />}</button>
              <input type="range" min={0} max={frames.length - 1} value={at} onChange={(e) => { setPlaying(false); setIdx(Number(e.target.value)); }}
                aria-label={t("replayDay")} aria-valuetext={t("dayOf", { day: frame.day, date: frame.date })} />
              <span className="display tabular" style={{ minWidth: 150 }}>{t("dayOf", { day: frame.day, date: frame.date })}</span>
            </div>
            <div className="slider-marks" aria-hidden="true">
              {detectDays.map((d) => {
                const i = frameIndexOfDay(d);
                return i >= 0 ? <span key={d} style={{ left: `${(i / Math.max(frames.length - 1, 1)) * 100}%` }}>▲ {t("detectedDay", { day: d })}</span> : null;
              })}
            </div>
            <div className="row" style={{ gap: 6 }}>
              <StatusPill kind={frame.flagged ? "flagged" : r.balance_available ? "balanced" : "noBalance"} />
              {frame.over_threshold ? <StatusPill kind="info">{t("overThresholdToday")}</StatusPill> : null}
              <StatusPill kind="info">{t("gapStart")}: {frame.gap_start || (frame.gap_since_start ? t("sinceStart") : "–")}</StatusPill>
              <small className="muted">{t("replaySource", { source: r.source, step: r.step_days, generated: r.generated })}</small>
            </div>
          </>
        ) : null}
      </Panel>
      {r && frame ? (
        <div className="panels">
          <Panel className="span-8" title={t("energyBalance")} icon={Activity}>
            <LineChart yLabel="kWh/day" height={230} xLabels={bal.dates.map((d) => d.slice(5))} markers={markers}
              summary={t("replaySummary", { day: frame.day, flagged: frame.flagged ? t("pillFlagged") : t("pillBalanced") })}
              series={[
                { name: t("supplied"), values: cut(bal.supplied_kwh), color: "var(--series-supply)" },
                { name: t("explained"), values: cut(bal.explained_kwh), color: "var(--series-explained)", dashed: true },
                { name: t("gapBand"), values: cut(bal.gap_kwh), color: "var(--series-gap)",
                  band: bal.gap_kwh.map((g, i) => (i < days && g != null ? [g - bal.uncertainty_kwh[i], g + bal.uncertainty_kwh[i]] : [null, null])) },
              ]} />
          </Panel>
          <Panel className="span-4" title={t("knownCases")} icon={Timer}>
            {known.map((k, i) => (
              <div key={i} className="stack" style={{ gap: 2 }}>
                <b className="display">{k.premise_id || t("knownCaseN", { n: i + 1 })}</b>
                <small className="muted">{t(`kind_${k.kind}`)} · {t("theftStarts", { date: k.theft_starts })}</small>
                {k.first_top5_day ? (
                  <StatusPill kind={frame.day >= k.first_top5_day ? "flagged" : "info"}>
                    {t("timeToDetection", { days: k.days_to_detection, day: k.first_top5_day })}</StatusPill>
                ) : <StatusPill kind="noBalance">{t("notDetected")}</StatusPill>}
              </div>
            ))}
            <small className="muted">{t("backtestNote")}</small>
          </Panel>
          {!r.premise_ids_hidden ? (
            <Panel className="span-12" title={t("rankingOnDay", { day: frame.day })} icon={Users} empty={!frame.ranked} emptyText={t("notRankedYet")}>
              <ol className="rank-list">
                {frame.top.map((p) => (
                  <li key={p.premise_id} className={`${knownIds.has(p.premise_id) ? "known" : ""} ${p.rank === frame.top_k ? "cut" : ""}`}>
                    <span className="display">{p.rank}</span>
                    <span>{p.premise_id}{knownIds.has(p.premise_id) ? ` · ${t("knownCase")}` : ""}</span>
                    <span className="num display">{p.score}</span>
                  </li>
                ))}
              </ol>
              <small className="muted">{t("top5Line", { k: frame.top_k })}</small>
            </Panel>
          ) : <p className="notice">{t("managerZoneOnly")}</p>}
        </div>
      ) : null}
    </div>
  );
}
