// Zone view (FR-UI-02; UI brief 2.2, the main demo screen): energy balance with the uncertainty band and a
// "gap opens" marker, hourly gap profile with a "flat 24/7" badge, the feeder schematic, and ranked suspects
// as cards. A card or a schematic node opens the premise in the right-hand drawer without leaving the zone.
import { BarChart3, Banknote, ExternalLink, Network, Users, Waves } from "lucide-react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { get, session } from "../api.js";
import { BarChart, LineChart } from "../components/Charts.jsx";
import { reasonLabel, Tags, useLoad } from "../components/Common.jsx";
import FeederSchematic from "../components/FeederSchematic.jsx";
import PremiseDetail from "../components/PremiseDetail.jsx";
import { Drawer, Panel, ScoreRing, StatusPill, zoneStatus } from "../components/ui.jsx";
import { t, useLang } from "../i18n.js";
import { fmt, int, pct, riskValue } from "../lib/format.js";

function decision(z, flatCv) {
  if (!z.balance_available) return t("decisionNoBalance");
  if (!z.flagged) return t("decisionNotFlagged", { pct: pct(z.gap_pct_recent) });
  const since = z.gap_start ? t("sinceDate", { date: z.gap_start }) : t("sinceStart");
  const flat = z.flatness_cv != null && z.flatness_cv < flatCv ? ` ${t("decisionFlat")}` : "";
  const large = z.priority === "large_load" ? ` ${t("decisionLarge")}` : "";
  return `${t("decisionFlagged", { pct: pct(z.gap_pct_recent), kwh: fmt(z.gap_kwh_recent, 0), since })}${flat}${large}`;
}

function SuspectCard({ s, topK, active, onOpen }) {
  const top = s.reasons.find((r) => !["other", "capped"].includes(r.feature));
  return (
    <button type="button" className={`suspect ${s.rank <= topK ? "top5" : ""} ${active ? "active" : ""}`} onClick={() => onOpen(s.premise_id)}
      aria-label={t("suspectAria", { rank: s.rank, id: s.premise_id, score: s.score })}>
      <span className="rank">{s.rank}</span>
      <ScoreRing score={s.score} size={46} />
      <span>
        <span className="pid">{s.premise_id}</span>
        {top ? <span className="why">{reasonLabel(top)}</span> : null}
        <span className="tags">
          {s.rank <= topK ? <StatusPill kind="flagged">{t("top5")}</StatusPill> : null}
          <Tags tags={s.tags} />
          {s.confidence === "low" ? <span className="chip warn">{t("lowConfidence")}</span> : null}
          {s.open_case_id ? <span className="chip info">{s.open_case_id}</span> : null}
        </span>
      </span>
    </button>
  );
}

export default function Zone() {
  const { id } = useParams();
  const lang = useLang();
  const [params, setParams] = useSearchParams();
  const openPremise = params.get("premise");
  const { user } = session();
  const balance = useLoad(() => get(`/zones/${id}/balance`), [id]);
  const canSuspects = ["analyst", "supervisor"].includes(user?.role);
  const suspects = useLoad(() => (canSuspects ? get(`/zones/${id}/suspects?limit=500`) : Promise.resolve(null)), [id]);
  const voltage = useLoad(() => (canSuspects ? get(`/zones/${id}/voltage`) : Promise.resolve(null)), [id]);
  const b = balance.data;
  const z = b?.zone;
  const days = b?.days || [];
  const startIdx = z?.gap_start ? days.findIndex((d) => d.date === z.gap_start) : -1;
  const flatCv = b?.flat_cv ?? 0.2;
  const flat = z?.flatness_cv != null && z.flatness_cv < flatCv;
  const list = suspects.data?.suspects || [];
  const open = (pid) => setParams(pid ? { premise: pid } : {});
  const v = riskValue(b?.value, b?.tariff);
  const markers = startIdx >= 0 ? [{ index: startIdx, label: t("gapOpens") }] : [];
  const gapMax = days.reduce((m, d) => Math.max(m, d.gap_kwh ?? 0), 0);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{t("zone")} {id}</h1>
          {z ? <p className="decision">{decision(z, flatCv)}</p> : null}
          {z ? (
            <div className="row" style={{ gap: 6, marginTop: 6 }}>
              <span className="muted">{z.district} · {z.region}</span>
              <StatusPill kind={zoneStatus(z)} />
              {z.priority === "large_load" ? <StatusPill kind="largeLoad" /> : null}
              {z.flagged && flat ? <StatusPill kind="flat" /> : null}
              <StatusPill kind="info">{t("gapStart")}: {z.gap_start || (z.gap_since_start ? t("sinceStart") : "–")}</StatusPill>
              {v.kind === "rm" ? <StatusPill kind="flagged"><Banknote size={13} aria-hidden="true" />RM {int(v.amount, lang)}/{t("monthShort")} · {t("estimate")}</StatusPill> : null}
              {v.kind === "kwh" ? <StatusPill kind="flagged"><Banknote size={13} aria-hidden="true" />{int(v.kwh, lang)} kWh/{t("monthShort")} · {t("estimate")} · {v.placeholder}</StatusPill> : null}
            </div>
          ) : null}
        </div>
        <Link className="button" to="/">{t("backToOverview")}</Link>
      </div>
      {z?.notes?.length ? <div className="notice warn">{z.notes.join(" ")}</div> : null}

      <div className="zone-grid">
        <Panel title={t("energyBalance")} icon={Waves} loading={balance.loading && !b} error={balance.error} onRetry={balance.reload}
          empty={b && !z.balance_available} emptyText={t("noBalanceExplain")}>
          {b && z.balance_available ? (
            <>
              <LineChart yLabel="kWh/day" height={190} xLabels={days.map((d) => d.date.slice(5))} markers={markers}
                summary={t("balanceSummary", { days: days.length, start: z.gap_start || t("sinceStart") })}
                series={[
                  { name: t("supplied"), values: days.map((d) => d.supplied_kwh), color: "var(--series-supply)" },
                  { name: t("explained"), color: "var(--series-explained)", dashed: true,
                    values: days.map((d) => (d.metered_kwh ?? 0) + (d.estimated_kwh ?? 0) + (d.tech_loss_kwh ?? 0)) },
                ]} />
              <LineChart yLabel={t("gapKwhDay")} height={150} xLabels={days.map((d) => d.date.slice(5))} markers={markers}
                summary={t("gapSummary", { max: fmt(gapMax, 0), u: fmt(z.uncertainty_kwh_recent, 0) })}
                series={[{ name: t("gapBand"), values: days.map((d) => d.gap_kwh), color: "var(--series-gap)",
                  band: days.map((d) => [d.gap_kwh - d.uncertainty_kwh, d.gap_kwh + d.uncertainty_kwh]) }]} />
            </>
          ) : null}
        </Panel>

        <Panel title={t("hourlyGap")} icon={BarChart3} loading={balance.loading && !b} error={balance.error} onRetry={balance.reload}
          empty={b && !z.balance_available} emptyText={t("noBalanceExplain")}
          actions={z?.flagged && flat ? <StatusPill kind="flat" /> : null}>
          {b && z.balance_available ? (
            <>
              <BarChart values={b.hourly_gap_kwh || []} labels={[...Array(24).keys()].map((h) => `${h}h`)} yLabel={t("kwhPerHour")} height={190}
                summary={t("hourlySummary", { cv: fmt(z.flatness_cv, 2) })} />
              <p className="muted" style={{ margin: 0 }}>{t("flatnessLine", { cv: fmt(z.flatness_cv, 2) })} {flat ? t("flatMeaning") : ""}</p>
            </>
          ) : null}
        </Panel>

        <div className="suspects-col" style={{ display: "flex" }}>
          <Panel title={t("suspects")} icon={Users} className="" loading={canSuspects && suspects.loading && !suspects.data} error={suspects.error}
            onRetry={suspects.reload} empty={!canSuspects || (suspects.data && !list.length)}
            emptyText={!canSuspects ? t("managerZoneOnly") : t("noSuspects")}
            actions={list.length ? <small className="muted">{t("topKNote", { k: suspects.data.top_k })}</small> : null}>
            <div className="suspect-list">
              {list.slice(0, 30).map((s) => <SuspectCard key={s.premise_id} s={s} topK={suspects.data.top_k} active={s.premise_id === openPremise} onOpen={open} />)}
            </div>
            {list.length > 30 ? <small className="muted">{t("moreInSchematic", { n: list.length - 30 })}</small> : null}
            <small className="muted">{t("riskNote")}</small>
          </Panel>
        </div>

        <Panel className="schematic-panel" title={t("feederSchematic")} icon={Network} loading={canSuspects && (suspects.loading || voltage.loading) && !suspects.data}
          error={suspects.error || voltage.error} empty={!canSuspects} emptyText={t("managerZoneOnly")}
          actions={voltage.data ? <small className="muted">{t("voltageMethod", { method: voltage.data.method, confidence: voltage.data.confidence })}</small> : null}>
          {canSuspects && suspects.data ? (
            <FeederSchematic zone={id} suspects={list} voltage={voltage.data} minDropV={voltage.data?.min_drop_v} onOpen={open} highlight={openPremise} />
          ) : null}
        </Panel>
      </div>

      {openPremise && canSuspects ? (
        <Drawer title={`${t("premise")} ${openPremise}`} onClose={() => open(null)}
          actions={<Link className="button" to={`/premises/${openPremise}`}><ExternalLink size={15} aria-hidden="true" />{t("openFullPage")}</Link>}>
          <PremiseDetail id={openPremise} compact />
        </Drawer>
      ) : null}
    </div>
  );
}
