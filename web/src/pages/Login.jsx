import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signIn } from "../api.js";
import Logo from "../components/Logo.jsx";
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
    <main className="login-page">
      <div className="login">
        <header className="login-hero">
          <Logo size={44} />
          <h1 className="display">VoltGuard AI</h1>
          <p className="login-lede">Revenue-protection decision support.</p>
        </header>
        <div className="login-panel">
          <div className="login-aurora" aria-hidden="true" />
          <form className="login-form card glass" onSubmit={submit} aria-busy={busy}>
            <label>{t("username")}<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
            <label>{t("password")}<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
            {error ? <div className="notice error" role="alert">{error}</div> : null}
            <button className="primary large" disabled={busy}>
              {busy ? <><span className="spinner on-primary" aria-hidden="true" />{t("signingIn")}</> : t("signIn")}
            </button>
          </form>
        </div>
        <footer className="login-foot">
          <p className="login-note"><span className="status-dot warn" aria-hidden="true" />R0 prototype: simulated data and fake personal details only.</p>
          <p><small>Test accounts and passwords are printed by <code>make.ps1 demo</code>.</small></p>
        </footer>
      </div>
    </main>
  );
}
