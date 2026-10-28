import { useEffect, useState } from "react";
import { HashRouter, Navigate, NavLink, Route, Routes, useLocation } from "react-router-dom";
import { get, onSessionChange, session, signOut } from "./api.js";
import FieldApp from "./field/FieldApp.jsx";
import { setLang, t, useLang } from "./i18n.js";
import { EXTRA_PAGES } from "./pages/extra.js";
import Audit from "./pages/Audit.jsx";
import Case from "./pages/Case.jsx";
import Cases from "./pages/Cases.jsx";
import DataManager from "./pages/DataManager.jsx";
import Login from "./pages/Login.jsx";
import Overview from "./pages/Overview.jsx";
import Premise from "./pages/Premise.jsx";
import Settings from "./pages/Settings.jsx";
import Zone from "./pages/Zone.jsx";

// Which pages each role sees in the menu; the API enforces the same limits (FR-AD-01).
const NAV = [
  { to: "/", key: "overview", roles: ["manager", "analyst", "supervisor"] },
  { to: "/cases", key: "cases", roles: ["manager", "analyst", "supervisor"] },
  ...EXTRA_PAGES.filter((p) => p.nav),
  { to: "/data", key: "dataManager", roles: ["admin"] },
  { to: "/settings", key: "settings", roles: ["admin", "analyst", "data_scientist", "manager", "supervisor"] },
  { to: "/audit", key: "audit", roles: ["auditor", "admin"] },
];

function useSession() {
  const [s, setS] = useState(session());
  useEffect(() => onSessionChange(setS), []);
  return s;
}

function Shell({ children }) {
  const { user } = useSession();
  const lang = useLang();
  const [health, setHealth] = useState(null);
  useEffect(() => { get("/health").then(setHealth).catch(() => setHealth(null)); }, []);
  return (
    <>
      <header className="topbar">
        <span className="logo"><img src="/icon.svg" alt="" width="24" height="24" /> VoltGuard AI</span>
        <span className="env-badges">
          {health?.llm_mode === "mock" ? <span className="badge badge-mode" title={t("mockModeHint")}>{t("mockMode")}</span> : null}
          <span className="badge">{t("envSimulated")}</span>
        </span>
        <span className="spacer" />
        <select value={lang} onChange={(e) => setLang(e.target.value)} aria-label={t("language")}>
          {/* Language names stay in their own language so each reader can find theirs. */}
          <option value="en">English</option><option value="ms">Bahasa Melayu</option>
        </select>
        {user ? <button onClick={signOut}>{t("signOut")}</button> : null}
      </header>
      <div className="layout">
        <nav className="nav" aria-label={t("mainNavigation")}>
          <div className="who">
            <span className="who-id">{user?.user_id}</span>
            <span className="who-meta">{user?.role} · {user?.region}{user?.team ? ` · ${user.team}` : ""}</span>
          </div>
          <div className="nav-links">
            {NAV.filter((n) => n.roles.includes(user?.role)).map((n) => (
              <NavLink key={n.to} to={n.to} end={n.to === "/"}>{t(n.key)}</NavLink>
            ))}
          </div>
        </nav>
        <main id="main">{children}</main>
      </div>
    </>
  );
}

function Guarded({ children }) {
  const { user } = useSession();
  const location = useLocation();
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return <Shell>{children}</Shell>;
}

export default function App() {
  const lang = useLang();
  useEffect(() => { document.documentElement.lang = lang; }, [lang]); // approved exception: screen readers read the chosen language
  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/field/*" element={<FieldApp />} />
        <Route path="/" element={<Guarded><Overview /></Guarded>} />
        <Route path="/zones/:id" element={<Guarded><Zone /></Guarded>} />
        <Route path="/premises/:id" element={<Guarded><Premise /></Guarded>} />
        <Route path="/cases" element={<Guarded><Cases /></Guarded>} />
        <Route path="/cases/:id" element={<Guarded><Case /></Guarded>} />
        <Route path="/data" element={<Guarded><DataManager /></Guarded>} />
        <Route path="/settings" element={<Guarded><Settings /></Guarded>} />
        <Route path="/audit" element={<Guarded><Audit /></Guarded>} />
        {EXTRA_PAGES.map((p) => <Route key={p.to} path={p.to} element={<Guarded><p.Component /></Guarded>} />)}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
