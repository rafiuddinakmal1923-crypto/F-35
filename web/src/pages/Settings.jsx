// Thresholds and weights (FR-AD-03): admins change them without code changes; the next run uses them.
// The tariff for value-at-risk estimates (UI brief 3.1) is set here too: empty means the labelled placeholder.
import { Banknote, SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { get, put, session } from "../api.js";
import { ErrorBox, useLoad } from "../components/Common.jsx";
import { Panel } from "../components/ui.jsx";
import { t } from "../i18n.js";

function TariffPanel({ canEdit }) {
  const tariff = useLoad(() => get("/settings/tariff"), []);
  const [rate, setRate] = useState("");
  const [source, setSource] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    if (tariff.data) {
      setRate(tariff.data.rm_per_kwh ?? "");
      setSource(tariff.data.source ?? "");
    }
  }, [tariff.data]);
  async function save(e) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await put("/settings/tariff", { rm_per_kwh: rate === "" ? null : Number(rate), source: source || null });
      setMessage(t("tariffSaved"));
      tariff.reload();
    } catch (err) {
      setError(err);
    }
  }
  const d = tariff.data;
  return (
    <Panel title={t("tariffTitle")} icon={Banknote} loading={tariff.loading && !d} error={tariff.error}>
      <p className="muted" style={{ margin: 0 }}>{t("tariffExplain", { days: d?.days_per_month ?? 30, file: d?.file ?? "config/tariffs.yaml" })}</p>
      <p style={{ margin: 0 }}><b>{t("tariffCurrent")}:</b> {d?.rm_per_kwh != null ? `RM ${d.rm_per_kwh}/kWh${d.source ? ` (${d.source})` : ""}` : <span className="estimate-tag">{d?.placeholder}</span>}</p>
      {canEdit ? (
        <form className="row" onSubmit={save}>
          <label>{t("tariffRate")}<input type="number" step="0.0001" min="0" max="10" value={rate} onChange={(e) => setRate(e.target.value)} placeholder={t("tariffEmpty")} /></label>
          <label style={{ flex: 1, minWidth: 200 }}>{t("tariffSource")}<input value={source} onChange={(e) => setSource(e.target.value)} placeholder={t("tariffSourceHint")} maxLength={200} /></label>
          <button className="primary" type="submit" style={{ alignSelf: "flex-end" }}>{t("save")}</button>
        </form>
      ) : null}
      {message ? <div className="notice ok">{message}</div> : null}
      <ErrorBox error={error} />
    </Panel>
  );
}

export default function Settings() {
  const { user } = session();
  const settings = useLoad(() => get("/settings/thresholds"), []);
  const [draft, setDraft] = useState({});
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const canEdit = user?.role === "admin";

  function change(section, key, value) {
    setDraft((d) => ({ ...d, [section]: { ...(d[section] || {}), [key]: value === "" ? undefined : Number(value) } }));
  }

  async function save() {
    setError(null);
    setMessage(null);
    const clean = Object.fromEntries(Object.entries(draft).map(([s, v]) => [s, Object.fromEntries(Object.entries(v).filter(([, x]) => x !== undefined))]));
    try {
      const r = await put("/settings/thresholds", clean);
      setMessage(r.next);
      setDraft({});
      settings.reload();
    } catch (e) {
      setError(e);
    }
  }

  const eff = settings.data?.effective || {};
  return (
    <div className="page">
      <div className="page-head">
        <div><h1>{t("settings")}</h1><span className="sub">{t("settingsIntro")}</span></div>
        {canEdit ? <button className="primary" onClick={save} disabled={!Object.keys(draft).length}>{t("saveChanges")}</button> : null}
      </div>
      <ErrorBox error={settings.error || error} />
      {message ? <div className="notice ok">{message}</div> : null}
      {user?.role !== "auditor" ? <TariffPanel canEdit={canEdit} /> : null}
      <div className="grid two">
        {Object.entries(eff).map(([section, values]) => (
          <Panel key={section} title={section} icon={SlidersHorizontal}>
            <div className="table-wrap"><table><tbody>
              {Object.entries(values).map(([key, value]) => (
                <tr key={key}><td>{key}</td><td className="num">{String(value)}</td>
                  <td>{canEdit ? <input type="number" step="any" min="0" style={{ width: 110 }} value={draft[section]?.[key] ?? ""}
                    onChange={(e) => change(section, key, e.target.value)} placeholder={t("newValue")} aria-label={`${section}.${key}`} /> : null}</td></tr>
              ))}
            </tbody></table></div>
          </Panel>
        ))}
      </div>
    </div>
  );
}
