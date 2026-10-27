import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signIn } from "../api.js";
import { t } from "../i18n.js";

const HOME = { inspector: "/field", admin: "/data", auditor: "/audit", data_scientist: "/models", pipeline: "/" };

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
    <div className="login card">
      <h1>VoltGuard AI</h1>
      <p className="muted">Revenue-protection decision support. R0 prototype: simulated data and fake personal details only.</p>
      <form onSubmit={submit}>
        <label>{t("username")}<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
        <label>{t("password")}<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
        {error ? <div className="notice error">{error}</div> : null}
        <button className="primary" disabled={busy}>{t("signIn")}</button>
      </form>
      <p><small>Test accounts and passwords are printed by <code>make.ps1 demo</code>.</small></p>
    </div>
  );
}
