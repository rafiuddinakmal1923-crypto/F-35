// Network overview (FR-UI-01, FR-UI-04; UI brief 2.1): full-height map of transformers as the hero, KPI
// strip and the "leaking zones" leaderboard. Zone-level figures only: no premise IDs or locations.
import { Banknote, ClipboardList, Crosshair, Gauge, Map as MapIcon, TriangleAlert, Trophy } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { get, session } from "../api.js";
import { JobButton, useLoad } from "../components/Common.jsx";
import { KpiTile, Panel, Sparkline, StatusPill, zoneStatus } from "../components/ui.jsx";
import ZoneMap from "../components/ZoneMap.jsx";
import { t, useLang } from "../i18n.js";
import { fmt, hitRate, int, pct, riskValue } from "../lib/format.js";

export function RiskValueKpi({ value, tariff, trend }) {
  const lang = useLang();
  const v = riskValue(value, tariff);
  if (v.kind === "rm") {
    return <KpiTile icon={Banknote} label={t("rmAtRisk")} estimate value={`RM ${int(v.amount, lang)}`} unit={t("perMonth")}
      note={t("rmBasis", { kwh: int(v.kwh, lang), rate: tariff.rm_per_kwh })} help={t("rmHelp")} trend={trend} />;
  }
  return <KpiTile icon={Banknote} label={t("rmAtRisk")} estimate placeholder={v.kind === "none" ? t("noneFlagged") : v.placeholder}
    note={v.kind === "kwh" ? t("kwhPerMonthAtRisk", { kwh: int(v.kwh, lang) }) : undefined} help={t("rmHelp")} />;
}

export default function Overview() {
  const lang = useLang();
  const [district, setDistrict] = useState("");
  const [date, setDate] = useState("");
  const navigate = useNavigate();
  const { user } = session();
  const query = new URLSearchParams({ ...(district && { district }), ...(date && { date }) }).toString();
  const zones = useLoad(() => get(`/zones${query ? `?${query}` : ""}`), [query]);
  const data = zones.data;
  const canOpenZone = ["analyst", "supervisor", "manager"].includes(user?.role);
  const trend = data?.trend || [];
  const hits = data?.totals?.hit_rates || {};
  const model = hitRate(hits.model_ranked);
  const random = hitRate(hits.random_sample);
  const ranked = (data?.zones || []).filter((z) => z.balance_available).sort((a, b) => (b.flagged - a.flagged) || ((b.gap_kwh_recent || 0) - (a.gap_kwh_recent || 0)));

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{t("overview")}</h1>
          <span className="sub">{data?.run_date ? t("runOf", { date: data.run_date }) : t("noRunYet")} · {t("region")} {user?.region}</span>
        </div>
        <div className="row">
          <label>{t("district")}
            <select value={district} onChange={(e) => setDistrict(e.target.value)}>
              <option value="">{t("allDistricts")}</option>
              {(data?.districts || []).map((d) => <option key={d}>{d}</option>)}
            </select>
          </label>
          <label>{t("date")}<input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label>
          {user?.role === "supervisor" ? <JobButton path="/jobs/create-cases" label={t("runCaseJob")} onDone={zones.reload} /> : null}
        </div>
      </div>

      <div className="kpi-strip" aria-busy={zones.loading}>
        <KpiTile icon={TriangleAlert} label={t("flaggedZones")} value={data ? data.totals?.flagged ?? 0 : "…"} trend={trend.map((p) => p.flagged)}
          help={t("helpFlagged")} />
        <KpiTile icon={Gauge} label={t("gapPerDay")} value={data ? int(data.totals?.gap_kwh_per_day, lang) : "…"} unit="kWh" trend={trend.map((p) => p.gap_kwh)}
          help={t("helpGap")} />
        {data ? <RiskValueKpi value={data.totals?.value?.zones ? data.totals.value : null} tariff={data.tariff} />
          : <KpiTile icon={Banknote} label={t("rmAtRisk")} estimate value="…" />}
        <KpiTile icon={ClipboardList} label={t("openCases")} value={data ? data.totals?.open_cases ?? 0 : "…"} onClick={() => navigate("/cases")} help={t("helpOpenCases")} />
        <KpiTile icon={Crosshair} label={t("hitRateKpi")} value={model != null ? pct(model, 0) : undefined}
          placeholder={model == null ? t("noOutcomesYet") : undefined}
          note={model != null ? t("vsRandom", { random: random != null ? pct(random, 0) : "–", n: hits.model_ranked?.inspections ?? 0, m: hits.random_sample?.inspections ?? 0 }) : undefined}
          help={t("helpHitRate")} />
      </div>

      <div className="overview-grid">
        <Panel title={t("mapTitle")} icon={MapIcon} loading={zones.loading && !data} error={zones.error} onRetry={zones.reload}
          empty={data && !data.zones.length} emptyText={t("noZones")}>
          {data ? <ZoneMap hero zones={data.zones} onSelect={(z) => canOpenZone && navigate(`/zones/${z.transformer_id}`)} /> : null}
          <p className="sr-only">{t("mapSummary", { n: data?.zones.length ?? 0, flagged: data?.totals?.flagged ?? 0 })}</p>
        </Panel>
        <Panel title={t("leaderboard")} icon={Trophy} loading={zones.loading && !data} error={zones.error} onRetry={zones.reload}
          empty={data && !ranked.length} emptyText={t("noZones")}>
          <ol className="leaderboard">
            {ranked.map((z, i) => (
              <li key={z.transformer_id}>
                <Link to={canOpenZone ? `/zones/${z.transformer_id}` : "#"} className={z.flagged ? "flagged" : ""}
                  aria-label={t("leaderAria", { zone: z.transformer_id, gap: fmt(z.gap_kwh_recent, 0), pct: pct(z.gap_pct_recent) })}>
                  <span className="pos">{i + 1}</span>
                  <span>
                    <span className="zid">{z.transformer_id}</span>
                    <small className="muted">{z.district}</small>
                    <span className="row" style={{ gap: 4, marginTop: 4 }}>
                      <StatusPill kind={zoneStatus(z)} />
                      {z.priority === "large_load" ? <StatusPill kind="largeLoad" /> : null}
                      {z.flagged && z.flatness_cv != null && z.flatness_cv < 0.2 ? <StatusPill kind="flat" /> : null}
                    </span>
                  </span>
                  <Sparkline values={z.spark} width={70} height={28} color={z.flagged ? "var(--accent)" : "var(--ok)"} label={t("sparkAria", { zone: z.transformer_id })} />
                  <span className="figs"><b>{fmt(z.gap_kwh_recent, 0)}</b>kWh/{t("day")}<br />{pct(z.gap_pct_recent)}
                    {z.value ? <><br /><span className="estimate-tag">{z.value.rm_per_month != null ? `RM ${int(z.value.rm_per_month, lang)}` : `${int(z.value.kwh_per_month, lang)} kWh`}/{t("monthShort")}</span></> : null}</span>
                </Link>
              </li>
            ))}
          </ol>
          {(data?.zones || []).filter((z) => !z.balance_available).map((z) => (
            <small key={z.transformer_id} className="muted">{t("zoneNoBalanceNote", { zone: z.transformer_id })}</small>
          ))}
        </Panel>
      </div>
      <p className="notice">{t("riskNote")}</p>
    </div>
  );
}
