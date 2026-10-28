// Data manager (admin only, prompt 3.4): data health per table (UI brief 3.9), upload CSV or Parquet, pick the
// table, validate, preview, activate; in demo mode, "Reset demo" reseeds the rehearsal data.
import { Database, HeartPulse, History, RotateCcw, Upload } from "lucide-react";
import { useState } from "react";
import { get, pollJob, post, request } from "../api.js";
import { ErrorBox, JobButton, useLoad } from "../components/Common.jsx";
import { Panel, StatusPill } from "../components/ui.jsx";
import { t, useLang } from "../i18n.js";
import { int, pct } from "../lib/format.js";

function HealthCard({ card, lang }) {
  const upload = card.upload_report;
  return (
    <div className="health-card">
      <span className="t">{card.table}</span>
      <span className="rows">{int(card.rows, lang)} <small className="muted">{t("rows")}</small></span>
      <span><StatusPill kind={card.source === "simulated" ? "info" : "balanced"}>{card.source}</StatusPill></span>
      <dl>
        <dt>{t("duplicatesRemoved")}</dt><dd>{upload ? int(card.duplicates_removed || 0, lang) : t("notApplicable")}</dd>
        <dt>{t("timezoneFixes")}</dt><dd>{upload ? int(card.timezone_fixes || 0, lang) : t("notApplicable")}</dd>
      </dl>
    </div>
  );
}

function ResetDemo() {
  const [state, setState] = useState(null);
  async function reset() {
    setState({ busy: true });
    const started = Date.now();
    try {
      const job = await pollJob((await post("/admin/demo/reset")).job_id, () => {}, 1000);
      if (job.status !== "done") throw new Error(job.error?.split("\n")[0] || t("jobFailed"));
      setState({ ok: t("resetDone", { s: ((Date.now() - started) / 1000).toFixed(0) }) });
    } catch (e) {
      setState({ error: e });
    }
  }
  return (
    <Panel title={t("resetDemo")} icon={RotateCcw}>
      <p className="muted" style={{ margin: 0 }}>{t("resetExplain")}</p>
      <div className="row"><button type="button" className="primary" onClick={reset} disabled={state?.busy}>{state?.busy ? t("resetting") : t("resetDemo")}</button>
        {state?.ok ? <span className="pill ok">{state.ok}</span> : null}</div>
      <ErrorBox error={state?.error} />
    </Panel>
  );
}

export default function DataManager() {
  const lang = useLang();
  const datasets = useLoad(() => get("/admin/datasets"), []);
  const health = useLoad(() => get("/admin/data-health"), []);
  const meta = useLoad(() => get("/meta"), []);
  const [dataset, setDataset] = useState("");
  const [table, setTable] = useState("meter_reading");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function upload(event) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append("dataset", dataset);
      form.append("table", table);
      form.append("file", file);
      setResult(await request("/admin/datasets", { method: "POST", form }));
      datasets.reload();
      health.reload();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  async function activate(name, version) {
    setError(null);
    try {
      await post(`/admin/datasets/${name}/versions/${version}/activate`);
      datasets.reload();
      health.reload();
    } catch (e) {
      setError(e);
    }
  }

  async function openReport(name, version) {
    const res = await request(`/admin/datasets/${name}/versions/${version}/report`, { raw: true });
    const url = URL.createObjectURL(new Blob([await res.text()], { type: "text/html" }));
    window.open(url, "_blank", "noopener");
  }

  async function revert(tableName) {
    const form = new FormData();
    form.append("source", "simulated");
    await request(`/admin/sources/${tableName}`, { method: "POST", form });
    datasets.reload();
    health.reload();
  }

  const d = datasets.data;
  const h = health.data;
  return (
    <div className="page">
      <div className="page-head">
        <div><h1>{t("dataManager")}</h1>
          <span className="sub">{t("dataManagerIntro")}</span></div>
        <JobButton path="/jobs/run-detection" label={t("runDetection")} className="" />
      </div>
      <ErrorBox error={error} />
      <Panel title={t("dataHealth")} icon={HeartPulse} loading={health.loading && !h} error={health.error} onRetry={health.reload}>
        {h ? (
          <>
            <div className="row" style={{ gap: 18 }}>
              <div><div className="big-figure" style={{ fontSize: "1.8rem" }}>{pct(h.completeness.complete_share, 1)}</div>
                <small className="muted">{t("completenessLine", { short: int(h.completeness.short_meter_days, lang), total: int(h.completeness.meter_days, lang), min: pct(h.completeness.threshold, 0) })}</small></div>
              <div className="stack" style={{ gap: 4 }}>
                <b>{t("fallbacksActive")}</b>
                <div className="row" style={{ gap: 6 }}>
                  {h.fallbacks.length ? h.fallbacks.map((f) => (
                    <StatusPill key={f.code} kind="flagged" title={f.zones?.join(", ")}>{f.code} · {t(`fallback_${f.code.replace("-", "")}`)}{f.zones?.length ? ` (${f.zones.length})` : ""}</StatusPill>
                  )) : <StatusPill kind="cleared">{t("noFallbacks")}</StatusPill>}
                </div>
              </div>
            </div>
            <div className="health-grid">{h.tables.map((c) => <HealthCard key={c.table} card={c} lang={lang} />)}</div>
            <small className="muted">{h.data_mode === "simulated" ? t("healthSimulatedNote") : t("healthUploadNote")}</small>
          </>
        ) : null}
      </Panel>
      <div className="panels">
        <form className="panel span-6" onSubmit={upload}>
          <div className="panel-head"><h2><Upload size={16} aria-hidden="true" />{t("upload")}</h2></div>
          <label>{t("datasetName")}<input value={dataset} onChange={(e) => setDataset(e.target.value)} pattern="[A-Za-z0-9_.\-]{1,64}" placeholder="tnb_extract_2026_10" required /></label>
          <label>{t("targetTable")}<select value={table} onChange={(e) => setTable(e.target.value)}>{(d?.tables || []).map((x) => <option key={x}>{x}</option>)}</select></label>
          <label>{t("fileCsvParquet")}<input type="file" accept=".csv,.parquet" onChange={(e) => setFile(e.target.files[0])} required /></label>
          <button className="primary" disabled={busy || !file}>{busy ? t("validating") : t("uploadValidate")}</button>
        </form>
        <Panel className="span-6" title={t("activeSources")} icon={Database} loading={datasets.loading && !d} error={datasets.error}>
          <div className="table-wrap"><table><tbody>
            {Object.entries(d?.active_sources || {}).map(([tbl, src]) => (
              <tr key={tbl}><td>{tbl}</td><td><code>{src}</code></td>
                <td>{src !== "simulated" ? <button onClick={() => revert(tbl)}>{t("backToSimulated")}</button> : null}</td></tr>
            ))}
          </tbody></table></div>
        </Panel>
      </div>
      {result ? (
        <Panel title={`${result.dataset} ${result.version}: ${result.report.status}`}>
          <p>{t("uploadResult", { errors: result.report.errors, warnings: result.report.warnings, short: result.report.flagged_meter_days })}</p>
          <div className="table-wrap"><table><thead><tr><th>{t("level")}</th><th>{t("table")}</th><th>{t("check")}</th><th>{t("message")}</th></tr></thead><tbody>
            {result.report.issues.map((i, k) => <tr key={k}><td><span className={`chip ${i.level === "error" ? "theft" : "warn"}`}>{i.level}</span></td><td>{i.table}.{i.column || "-"}</td><td>{i.check}</td><td>{i.message}</td></tr>)}
          </tbody></table></div>
          {Object.entries(result.preview || {}).map(([tbl, rows]) => (
            <div key={tbl} className="table-wrap"><h3>{t("preview")}: {tbl}</h3>
              <table><thead><tr>{Object.keys(rows[0] || {}).map((c) => <th key={c}>{c}</th>)}</tr></thead>
                <tbody>{rows.map((r, i) => <tr key={i}>{Object.values(r).map((v, j) => <td key={j}>{String(v ?? "")}</td>)}</tr>)}</tbody></table></div>
          ))}
        </Panel>
      ) : null}
      <Panel title={t("datasetsVersions")} icon={History} empty={d && !d.datasets.length} emptyText={t("noUploadsYet")}>
        <div className="table-wrap"><table><thead><tr><th>{t("dataset")}</th><th>{t("version")}</th><th>{t("status")}</th><th>{t("tables")}</th><th>{t("created")}</th><th /></tr></thead><tbody>
          {(d?.datasets || []).flatMap((ds) => ds.versions.map((v) => (
            <tr key={`${ds.dataset}-${v.version}`}>
              <td>{ds.dataset}</td><td>{v.version}</td>
              <td><span className={`chip ${v.status === "accepted" ? "ok" : "theft"}`}>{v.status}</span>{v.activated ? <span className="chip info">{t("activated")}</span> : null}</td>
              <td><small>{Object.entries(v.tables).map(([k, n]) => `${k} (${n})`).join(", ")}</small></td>
              <td><small>{v.created_at} · {v.created_by}</small></td>
              <td className="row"><button onClick={() => openReport(ds.dataset, v.version)}>{t("report")}</button>
                {v.status === "accepted" ? <button onClick={() => activate(ds.dataset, v.version)}>{t("activate")}</button> : null}</td>
            </tr>
          )))}
        </tbody></table></div>
      </Panel>
      {meta.data?.demo ? <ResetDemo /> : null}
    </div>
  );
}
