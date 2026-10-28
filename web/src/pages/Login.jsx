// Sign-in (UI brief 2.6). With DEMO_MODE on, the test accounts appear as role cards so judges can switch
// roles in one click (simulated data and fake personal details only); the password form stays below.
import { BrainCircuit, ClipboardCheck, Database, Lock, MapPin, Moon, ScrollText, ShieldCheck, Smartphone, Sun, UserCog, Users, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { request, signIn, signInDemo } from "../api.js";
import { setLang, t, useLang } from "../i18n.js";
import { setTheme, useTheme } from "../theme.js";

export const HOME = { inspector: "/field", admin: "/data", auditor: "/audit", data_scientist: "/models", analyst: "/work", supervisor: "/work", pipeline: "/" };
const ROLE_ICON = { manager: Users, analyst: ClipboardCheck, supervisor: UserCog, inspector: Smartphone, data_scientist: BrainCircuit, admin: Database, auditor: ScrollText };

export function ThemeLangToggles() {
  const lang = useLang();
  const theme = useTheme();
  return (
    <>
      <button type="button" className="icon-btn" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        aria-label={theme === "dark" ? t("toLight") : t("toDark")} title={theme === "dark" ? t("toLight") : t("toDark")}>
        {theme === "dark" ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}<span className="label">{theme === "dark" ? t("light") : t("dark")}</span>
      </button>
      <select className="lang-select" value={lang} onChange={(e) => setLang(e.target.value)} aria-label={t("language")}>
        <option value="en">EN</option><option value="ms">BM</option>
      </select>
    </>
  );
}

export default function Login() {
  useLang();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [accounts, setAccounts] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    request("/demo/accounts", { tokenOverride: "" }).then((r) => setAccounts(r.accounts)).catch(() => setAccounts([]));
  }, []);

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

  async function pick(account) {
    setError(null);
    if (account.role === "inspector") {
      navigate(`/field?demo=${encodeURIComponent(account.user_id)}`);
      return;
    }
    try {
      const { user } = await signInDemo(account.user_id);
      navigate(HOME[user.role] || "/", { replace: true });
    } catch (e) {
      setError(e.message);
    }
  }

  const demo = accounts?.length > 0;
  const formOpen = !demo || showForm;
  return (
    <div className="login-page">
      <section className="login-brand">
        <span className="logo"><span className="logo-mark big"><Zap size={24} strokeWidth={2.5} aria-hidden="true" /></span> VoltGuard AI</span>
        <h2>{t("loginTagline")}</h2>
        <ul>
          <li><MapPin size={18} aria-hidden="true" /> {t("loginPoint1")}</li>
          <li><ShieldCheck size={18} aria-hidden="true" /> {t("loginPoint2")}</li>
          <li><Lock size={18} aria-hidden="true" /> {t("loginPoint3")}</li>
        </ul>
        <small className="muted">{t("loginR0")}</small>
      </section>
      <div className="login-side">
        <div className="login-tools"><ThemeLangToggles /></div>
        <h1>{t("signIn")}</h1>
        {demo ? (
          <>
            <p className="muted" style={{ margin: 0 }}>{t("demoPickRole")}</p>
            <div className="role-cards">
              {accounts.map((a) => {
                const Icon = ROLE_ICON[a.role] || Users;
                return (
                  <button key={a.user_id} type="button" className="role-card" onClick={() => pick(a)} data-account={a.user_id}>
                    <b><Icon size={16} aria-hidden="true" />{t(`role_${a.role}`)}</b>
                    <small>{a.user_id} · {a.region === "*" ? t("allRegions") : a.region}{a.team ? ` · ${a.team}` : ""}</small>
                  </button>
                );
              })}
            </div>
            <small className="muted">{t("demoCardsNote")}</small>
            {!showForm ? <button type="button" className="ghost" data-manual-sign-in onClick={() => setShowForm(true)}>{t("signInWithPassword")}</button> : null}
          </>
        ) : <p className="muted">{t("loginIntro")} <a href="#/field">#/field</a>.</p>}
        {formOpen ? (
          <form onSubmit={submit}>
            <label>{t("username")}<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
            <label>{t("password")}<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
            <button className="primary" type="submit" disabled={busy}>{t("signIn")}</button>
          </form>
        ) : null}
        {error ? <div className="notice error" role="alert">{error}</div> : null}
        {!demo ? <small className="muted">{t("loginAccountsHint")}</small> : null}
      </div>
    </div>
  );
}
