// Model versions with model-ranked and random-sample hit rates side by side (FR-ML-01-02) and alerts (FR-ML-03).
import { get, post, session } from "../api.js";
import { ErrorBox, JobButton, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

const pct = (v) => (v == null ? "–" : `${(v * 100).toFixed(0)}%`);

export default function Models() {
  const { user } = session();
  const models = useLoad(() => get("/models"), []);
  const alerts = useLoad(() => get("/alerts"), []);
  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>{t("models")}</h1>
        {user?.role === "data_scientist" ? (
          <div className="row">
            <JobButton path="/jobs/run-detection" label={t("runDetection")} className="" />
            <JobButton path="/models/retrain" label="Retrain on new outcomes" onDone={models.reload} />
          </div>
        ) : null}
      </div>
      <p className="notice">On synthetic outcomes, retraining shows the mechanics of learning, not proof of improvement. Random-sample inspections
        are the unbiased reference for the hit rate of model-ranked inspections.</p>
      <ErrorBox error={models.error} />
      <div className="card table-wrap">
        <table>
          <thead>
            <tr><th>Version</th><th>Trained</th><th className="num">Labels</th>
              <th className="num">Model-ranked hit rate</th><th className="num">Random-sample hit rate</th>
              <th className="num">Precision at case threshold</th><th>Notes</th></tr>
          </thead>
          <tbody>
            {(models.data?.versions || []).map((v) => {
              const h = v.metrics.hit_rates || {};
              return (
                <tr key={v.version_id}>
                  <td><b>{v.version_id}</b> {v.active ? <span className="chip ok">active</span> : null}</td>
                  <td><small>{new Date(v.trained_at).toLocaleString()}</small></td>
                  <td className="num">{v.metrics.labels}</td>
                  <td className="num">{pct(h.model_ranked?.hit_rate)} <small>({h.model_ranked?.confirmed_theft}/{h.model_ranked?.inspections})</small></td>
                  <td className="num">{pct(h.random_sample?.hit_rate)} <small>({h.random_sample?.confirmed_theft}/{h.random_sample?.inspections})</small></td>
                  <td className="num">{pct(h.model_ranked?.precision_at_threshold)}</td>
                  <td><small>{v.metrics.skipped || (v.metrics.top_features ? `top features: ${v.metrics.top_features.join(", ")}` : "")}</small></td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {models.data && !models.data.versions.length ? <p className="muted">No version yet: retrain after outcomes are recorded.</p> : null}
      </div>
      <div className="card table-wrap">
        <h2>Alerts</h2>
        <ErrorBox error={alerts.error} />
        <table><thead><tr><th>Time</th><th>Kind</th><th>Message</th><th /></tr></thead><tbody>
          {(alerts.data || []).map((a) => (
            <tr key={a.alert_id}>
              <td><small>{new Date(a.ts).toLocaleString()}</small></td>
              <td><span className={`chip ${a.severity === "high" ? "risk" : "warn"}`}>{a.kind.replace("_", " ")}</span></td>
              <td>{a.message}</td>
              <td>{a.acknowledged_by ? <small>ack: {a.acknowledged_by}</small> : user?.role !== "manager"
                ? <button onClick={() => post(`/alerts/${a.alert_id}/acknowledge`).then(alerts.reload)}>Acknowledge</button> : null}</td>
            </tr>
          ))}
        </tbody></table>
      </div>
    </div>
  );
}
