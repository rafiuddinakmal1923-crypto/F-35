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
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>{t("overview")}</h1>
          <small>{data?.run_date ? `Detection run of ${data.run_date}` : "No detection run yet"} · region {user?.region}</small>
        </div>
        <div className="row">
          {user?.role === "supervisor" ? <JobButton path="/jobs/create-cases" label={t("runCaseJob")} onDone={zones.reload} /> : null}
        </div>
      </div>
      <div className="row">
        <label>{t("district")}
          <select value={district} onChange={(e) => setDistrict(e.target.value)}>
            <option value="">{t("allDistricts")}</option>
            {(data?.districts || []).map((d) => <option key={d}>{d}</option>)}
          </select>
        </label>
        <label>{t("date")}<input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label>
      </div>
      <ErrorBox error={zones.error} />
      {data ? (
        <>
          <div className="grid kpis">
            <div className="card kpi"><div className="value">{data.totals?.flagged ?? 0}</div><div className="label">{t("flaggedZones")}</div></div>
            <div className="card kpi"><div className="value">{fmt(data.totals?.gap_kwh_per_day, 0)}</div><div className="label">{t("gapPerDay")}</div></div>
            <div className="card kpi"><div className="value">{data.totals?.no_balance ?? 0}</div><div className="label">{t("noBalance")}</div></div>
            <div className="card kpi"><div className="value">{data.zones.reduce((s, z) => s + Number(z.open_cases || 0), 0)}</div><div className="label">{t("openCases")}</div></div>
          </div>
          <div className="grid two">
            <div className="card">
              <h2>Zones by gap</h2>
              <ZoneMap zones={data.zones} onSelect={(z) => canOpenZone && navigate(`/zones/${z.transformer_id}`)} />
              <div className="legend" style={{ marginTop: 6 }}>
                <span style={{ "--c": "#c2410c" }}>flagged</span><span style={{ "--c": "#2563eb" }}>balanced</span>
                <span style={{ "--c": "#9a6700" }}>no transformer meter</span>
              </div>
            </div>
            <div className="card table-wrap">
              <h2>{t("flaggedZones")}</h2>
              <table>
                <thead><tr><th>{t("zone")}</th><th>{t("district")}</th><th className="num">{t("gap")}</th>
                  <th className="num">kWh/day</th><th className="num">± u</th><th>{t("gapStart")}</th><th /></tr></thead>
                <tbody>
                  {data.zones.map((z) => (
                    <tr key={z.transformer_id} className={z.flagged ? "flagged" : ""}>
                      <td>{canOpenZone ? <Link to={`/zones/${z.transformer_id}`}>{z.transformer_id}</Link> : z.transformer_id}</td>
                      <td>{z.district}</td>
                      <td className="num">{z.balance_available ? pct(z.gap_pct_recent) : "–"}</td>
                      <td className="num">{z.balance_available ? fmt(z.gap_kwh_recent, 0) : "–"}</td>
                      <td className="num">{z.balance_available ? fmt(z.uncertainty_kwh_recent, 0) : "–"}</td>
                      <td>{z.gap_start || (z.gap_since_start ? t("sinceStart") : "")}</td>
                      <td>
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
          </div>
          <p className="notice">{t("riskNote")}</p>
        </>
      ) : null}
    </div>
  );
}
