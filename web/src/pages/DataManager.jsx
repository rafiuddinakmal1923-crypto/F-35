// Data manager (admin only, prompt 3.4): upload CSV or Parquet, pick the table, validate, preview, activate.
import { useState } from "react";
import { get, post, request } from "../api.js";
import { ErrorBox, JobButton, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

export default function DataManager() {
  const datasets = useLoad(() => get("/admin/datasets"), []);
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
  }

  const d = datasets.data;
  return (
    <div className="stack">
      <h1>{t("dataManager")}</h1>
      <p className="muted">Upload a new dataset here, or drop files into <code>DATA_ROOT/uploads/&lt;dataset&gt;/</code> and run
        <code> make.ps1 ingest</code>. Templates and the schema are in <code>data/uploads/</code>. Uploads are validated and versioned;
        activation points <code>config/data_sources.yaml</code> at the version.</p>
      <ErrorBox error={datasets.error || error} />
      <div className="grid two">
        <form className="card stack" onSubmit={upload}>
          <h2>Upload</h2>
          <label>Dataset name<input value={dataset} onChange={(e) => setDataset(e.target.value)} pattern="[A-Za-z0-9_.\-]{1,64}" placeholder="tnb_extract_2026_10" required /></label>
          <label>Target table<select value={table} onChange={(e) => setTable(e.target.value)}>{(d?.tables || []).map((x) => <option key={x}>{x}</option>)}</select></label>
          <label>File (CSV or Parquet)<input type="file" accept=".csv,.parquet" onChange={(e) => setFile(e.target.files[0])} required /></label>
          <button className="primary" disabled={busy || !file}>{busy ? "Validating…" : "Upload and validate"}</button>
        </form>
        <div className="card">
          <h2>Active source per table</h2>
          <table><tbody>
            {Object.entries(d?.active_sources || {}).map(([tbl, src]) => (
              <tr key={tbl}><td>{tbl}</td><td><code>{src}</code></td>
                <td>{src !== "simulated" ? <button onClick={() => revert(tbl)}>back to simulated</button> : null}</td></tr>
            ))}
          </tbody></table>
          <div style={{ marginTop: 10 }}><JobButton path="/jobs/run-detection" label={t("runDetection")} className="" /></div>
        </div>
      </div>
      {result ? (
        <div className="card">
          <h2>{result.dataset} {result.version}: {result.report.status}</h2>
          <p>{result.report.errors} error(s), {result.report.warnings} warning(s), {result.report.flagged_meter_days} meter-day(s) under 90% complete.</p>
          <div className="table-wrap"><table><thead><tr><th>Level</th><th>Table</th><th>Check</th><th>Message</th></tr></thead><tbody>
            {result.report.issues.map((i, k) => <tr key={k}><td><span className={`chip ${i.level === "error" ? "risk" : "warn"}`}>{i.level}</span></td><td>{i.table}.{i.column || "-"}</td><td>{i.check}</td><td>{i.message}</td></tr>)}
          </tbody></table></div>
          {Object.entries(result.preview || {}).map(([tbl, rows]) => (
            <div key={tbl} className="table-wrap"><h3>Preview: {tbl}</h3>
              <table><thead><tr>{Object.keys(rows[0] || {}).map((c) => <th key={c}>{c}</th>)}</tr></thead>
                <tbody>{rows.map((r, i) => <tr key={i}>{Object.values(r).map((v, j) => <td key={j}>{String(v ?? "")}</td>)}</tr>)}</tbody></table></div>
          ))}
        </div>
      ) : null}
      <div className="card table-wrap">
        <h2>Datasets and versions</h2>
        <table><thead><tr><th>Dataset</th><th>Version</th><th>Status</th><th>Tables</th><th>Created</th><th /></tr></thead><tbody>
          {(d?.datasets || []).flatMap((ds) => ds.versions.map((v) => (
            <tr key={`${ds.dataset}-${v.version}`}>
              <td>{ds.dataset}</td><td>{v.version}</td>
              <td><span className={`chip ${v.status === "accepted" ? "ok" : "risk"}`}>{v.status}</span>{v.activated ? <span className="chip info">activated</span> : null}</td>
              <td><small>{Object.entries(v.tables).map(([k, n]) => `${k} (${n})`).join(", ")}</small></td>
              <td><small>{v.created_at} · {v.created_by}</small></td>
              <td className="row"><button onClick={() => openReport(ds.dataset, v.version)}>Report</button>
                {v.status === "accepted" ? <button onClick={() => activate(ds.dataset, v.version)}>Activate</button> : null}</td>
            </tr>
          )))}
        </tbody></table>
      </div>
    </div>
  );
}
