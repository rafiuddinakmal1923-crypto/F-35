// Network overview (FR-UI-01, FR-UI-04): zone-level figures only, no premise IDs or locations.
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { get, session } from "../api.js";
import { ErrorBox, fmt, JobButton, pct, useLoad } from "../components/Common.jsx";
import ZoneMap from "../components/ZoneMap.jsx";
import { t } from "../i18n.js";

export default function Overview() {
  const [district, setDistrict] = useState("");
  const [date, setDate] = useState("");
  const navigate = useNavigate();
  const { user } = session();
  const query = new URLSearchParams({ ...(district && { district }), ...(date && { date }) }).toString();
  const zones = useLoad(() => get(`/zones${query ? `?${query}` : ""}`), [query]);
  const data = zones.data;
  const canOpenZone = ["analyst", "supervisor", "manager"].includes(user?.role);

  return (
    <div className="stack overview">
      <header className="page-header">
        <div>
          <h1 className="page-title">{t("overview")}</h1>
          {data || (!zones.loading && !zones.error)
            ? <p className="page-context">{data?.run_date ? `Detection run of ${data.run_date}` : "No detection run yet"} · region {user?.region}</p>
            : zones.loading ? <span className="skeleton context-sk" aria-hidden="true" /> : null}
        </div>
        <div className="page-actions">
          {user?.role === "supervisor" ? <JobButton path="/jobs/create-cases" label={t("runCaseJob")} onDone={zones.reload} /> : null}
        </div>
      </header>
      <div className="toolbar filters">
        <label>{t("district")}
          <select value={district} onChange={(e) => setDistrict(e.target.value)}>
            <option value="">{t("allDistricts")}</option>
            {(data?.districts || []).map((d) => <option key={d}>{d}</option>)}
          </select>
        </label>
        <label>{t("date")}<input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label>
        {zones.loading && data ? <span className="loading" role="status"><span className="spinner" aria-hidden="true" />{t("loading")}</span> : null}
      </div>
      <ErrorBox error={zones.error} />
      {!data && zones.loading ? (
        <div className="overview-skeleton" role="status" aria-busy="true">
          <span className="visually-hidden">{t("loading")}</span>
          <div className="metric-strip">{[0, 1, 2, 3].map((i) => <div className="metric" key={i}><span className="skeleton metric-sk" /><span className="skeleton label-sk" /></div>)}</div>
          <div className="overview-grid">
            <div className="card"><span className="skeleton heading-sk" /><span className="skeleton block map-sk" /></div>
            <div className="card"><span className="skeleton heading-sk" />{[0, 1, 2, 3, 4, 5].map((i) => <span className="skeleton row-sk" key={i} />)}</div>
          </div>
        </div>
      ) : null}
      {data ? (
        <div className={`stack overview-data${zones.loading ? " is-updating" : ""}`} aria-busy={zones.loading}>
          <div className="metric-strip">
            <div className="metric"><div className="metric-value">{data.totals?.flagged ?? 0}</div><div className="metric-label">{t("flaggedZones")}</div></div>
            <div className="metric"><div className="metric-value">{fmt(data.totals?.gap_kwh_per_day, 0)}</div><div className="metric-label">{t("gapPerDay")}</div></div>
            <div className="metric"><div className="metric-value">{data.totals?.no_balance ?? 0}</div><div className="metric-label">{t("noBalance")}</div></div>
            <div className="metric"><div className="metric-value">{data.zones.reduce((s, z) => s + Number(z.open_cases || 0), 0)}</div><div className="metric-label">{t("openCases")}</div></div>
          </div>
          <div className="overview-grid">
            <section className="card dense map-panel">
              <div className="card-header"><h2>Zones by gap</h2></div>
              <ZoneMap zones={data.zones} onSelect={(z) => canOpenZone && navigate(`/zones/${z.transformer_id}`)} />
              {data.zones.length ? (
                <div className="legend map-legend">
                  <span className="lg-flagged">flagged</span><span className="lg-balanced">balanced</span>
                  <span className="lg-nometer">no transformer meter</span>
                  <span className="lg-size">{t("sizeIsGap")}</span>
                </div>
              ) : null}
            </section>
            <section className="card flush table-panel">
              <div className="card-header"><h2>{t("flaggedZones")}</h2><span className="count">{data.zones.length}</span></div>
              {data.zones.length ? (
                <div className="table-wrap">
                  <table className="sticky-first">
                    <thead><tr><th>{t("zone")}</th><th>{t("district")}</th><th className="num">{t("gap")}</th>
                      <th className="num">kWh/day</th><th className="num">± u</th><th>{t("gapStart")}</th><th><span className="visually-hidden">{t("tags")}</span></th></tr></thead>
                    <tbody>
                      {data.zones.map((z) => (
                        <tr key={z.transformer_id} className={z.flagged ? "flagged" : ""}>
                          <td>{canOpenZone ? <Link to={`/zones/${z.transformer_id}`}>{z.transformer_id}</Link> : z.transformer_id}</td>
                          <td>{z.district}</td>
                          <td className="num">{z.balance_available ? pct(z.gap_pct_recent) : "–"}</td>
                          <td className="num">{z.balance_available ? fmt(z.gap_kwh_recent, 0) : "–"}</td>
                          <td className="num">{z.balance_available ? fmt(z.uncertainty_kwh_recent, 0) : "–"}</td>
                          <td className="nowrap">{z.gap_start || (z.gap_since_start ? t("sinceStart") : "")}</td>
                          <td className="chips">
                            {z.flagged ? <span className="chip risk">flagged</span> : null}
                            {z.priority === "large_load" ? <span className="chip risk">{t("largeLoad")}</span> : null}
                            {z.flatness_cv != null && z.flatness_cv < 0.2 && z.flagged ? <span className="chip warn">flat 24/7</span> : null}
                            {!z.balance_available ? <span className="chip warn">no balance available</span> : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty in-panel">
                  <span className="empty-title">{t("noZones")}</span>
                  <span>{t("noZonesHint")}</span>
                </div>
              )}
            </section>
          </div>
          <p className="notice neutral footnote">{t("riskNote")}</p>
        </div>
      ) : null}
    </div>
  );
}
