import { Lock, MapPin, ShieldCheck, Zap } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signIn } from "../api.js";
import { t } from "../i18n.js";

const HOME = { inspector: "/field", admin: "/data", auditor: "/audit", data_scientist: "/models", analyst: "/work", supervisor: "/work", pipeline: "/" };

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { user } = await signIn(username.trim(), password);
      navigate(HOME[user.role] || "/", { replace: true });
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <section className="login-brand">
        <span className="logo"><span className="logo-mark big"><Zap size={22} strokeWidth={2.5} /></span> VoltGuard AI</span>
        <h2>From a transformer's energy gap to a ranked, explained list of premises to inspect.</h2>
        <ul>
          <li><MapPin size={18} /> Zone energy balance with an uncertainty margin</li>
          <li><ShieldCheck size={18} /> Scores rank risk; people decide after inspection</li>
          <li><Lock size={18} /> Personal details only on an open case, and every view is logged</li>
        </ul>
        <small>R0 prototype · simulated data and fake personal details only</small>
      </section>
      <div className="login card">
      <h1>{t("signIn")}</h1>
      <p className="muted">Revenue-protection decision support for analysts, supervisors, managers and auditors. Inspectors: use the phone app at <a href="#/field">#/field</a>.</p>
      <form onSubmit={submit}>
        <label>{t("username")}<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
        <label>{t("password")}<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
        {error ? <div className="notice error">{error}</div> : null}
        <button className="primary" disabled={busy}>{t("signIn")}</button>
      </form>
      <p><small>Test accounts and passwords are printed by <code>make.ps1 demo</code>.</small></p>
      </div>
    </div>
  );
}
