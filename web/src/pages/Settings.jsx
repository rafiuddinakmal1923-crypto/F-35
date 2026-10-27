// Thresholds and weights (FR-AD-03): admins change them without code changes; the next run uses them.
import { useState } from "react";
import { get, put, session } from "../api.js";
import { ErrorBox, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

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
    <div className="stack">
      <h1>{t("settings")}</h1>
      <p className="muted">Defaults come from <code>config/thresholds.yaml</code> and the tuned weights; values saved here override them and are logged.</p>
      <ErrorBox error={settings.error || error} />
      {message ? <div className="notice ok">{message}</div> : null}
      <div className="grid two">
        {Object.entries(eff).map(([section, values]) => (
          <div className="card" key={section}>
            <h2>{section}</h2>
            <table><tbody>
              {Object.entries(values).map(([key, value]) => (
                <tr key={key}><td>{key}</td><td className="num">{String(value)}</td>
                  <td>{canEdit ? <input type="number" step="any" min="0" style={{ width: 110 }} value={draft[section]?.[key] ?? ""}
                    onChange={(e) => change(section, key, e.target.value)} placeholder="new value" /> : null}</td></tr>
              ))}
            </tbody></table>
          </div>
        ))}
      </div>
      {canEdit ? <button className="primary" onClick={save} disabled={!Object.keys(draft).length}>Save changes</button> : null}
    </div>
  );
}
