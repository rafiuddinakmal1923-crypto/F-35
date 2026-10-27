// Network overview (FR-UI-01, FR-UI-04): zone-level figures only, no premise IDs or locations.
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { get, session } from "../api.js";
import { ErrorBox, fmt, Help, JobButton, Kpi, pct, useLoad } from "../components/Common.jsx";
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
            <Kpi value={data.totals?.flagged ?? 0} label={t("flaggedZones")} trend={(data.trend || []).map((p) => p.flagged)}
              help="Transformer zones whose unexplained energy stayed above the flag rule (share of supply, minimum kWh and uncertainty) for several days." />
            <Kpi value={fmt(data.totals?.gap_kwh_per_day, 0)} label={t("gapPerDay")} trend={(data.trend || []).map((p) => p.gap_kwh)}
              help="Energy supplied by the transformers that no meter, estimate or technical loss explains, per day, in the flagged zones. Trend: last 14 days." />
            <Kpi value={data.totals?.no_balance ?? 0} label={t("noBalance")}
              help="Zones without a transformer meter: their premises are ranked on usage patterns only, with low confidence." />
            <Kpi value={data.zones.reduce((s, z) => s + Number(z.open_cases || 0), 0)} label={t("openCases")} onClick={() => navigate("/cases")}
              help="Inspection cases not yet closed in these zones. Click to open the case list." />
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
                <thead><tr><th>{t("zone")}</th><th>{t("district")}</th><th className="num">{t("gap")}<Help text="Unexplained energy as a share of what the transformer supplied, recent days." /></th>
                  <th className="num">kWh/day</th><th className="num">± u<Help text="Uncertainty margin: meter, estimate and loss-model error. A gap inside it is not flagged." /></th>
                  <th>{t("gapStart")}</th><th /></tr></thead>
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
