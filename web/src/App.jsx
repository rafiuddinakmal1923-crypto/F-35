// App shell (UI brief 1): slim left rail with icons and labels, top bar with region, run date, data mode
// and mock badge, light/dark and language toggles; content pages are grids of panels. The guided demo
// panel appears only when the API reports DEMO_MODE on.
import { Activity, BrainCircuit, Briefcase, CalendarRange, ClipboardList, Database, FlaskConical, Lightbulb, LayoutDashboard, LogOut,
  MessageCircle, Search, Send, Settings as SettingsIcon, ShieldCheck, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { HashRouter, Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { get, onSessionChange, session, signOut } from "./api.js";
import DemoGuide from "./components/DemoGuide.jsx";
import FieldApp from "./field/FieldApp.jsx";
import { t, useLang } from "./i18n.js";
import { EXTRA_PAGES } from "./pages/extra.js";
import Audit from "./pages/Audit.jsx";
import Case from "./pages/Case.jsx";
import Cases from "./pages/Cases.jsx";
import DataManager from "./pages/DataManager.jsx";
import Login, { ThemeLangToggles } from "./pages/Login.jsx";
import Overview from "./pages/Overview.jsx";
import Premise from "./pages/Premise.jsx";
import Settings from "./pages/Settings.jsx";
import Work from "./pages/Work.jsx";
import Zone from "./pages/Zone.jsx";

const ICONS = { work: Briefcase, overview: LayoutDashboard, cases: ClipboardList, assistant: MessageCircle, weekly: CalendarRange,
  dispatch: Send, models: BrainCircuit, validation: FlaskConical, backtest: Activity, concept: Lightbulb, dataManager: Database,
  settings: SettingsIcon, audit: ShieldCheck };

// Which pages each role sees in the menu; the API enforces the same limits (FR-AD-01).
const NAV = [
  { to: "/work", key: "work", roles: ["analyst", "supervisor", "manager"], badge: "urgent" },
  { to: "/", key: "overview", roles: ["manager", "analyst", "supervisor"] },
  { to: "/cases", key: "cases", roles: ["manager", "analyst", "supervisor"] },
  ...EXTRA_PAGES.filter((p) => p.nav),
  { to: "/data", key: "dataManager", roles: ["admin"] },
  { to: "/settings", key: "settings", roles: ["admin", "analyst", "data_scientist", "manager", "supervisor"] },
  { to: "/audit", key: "audit", roles: ["auditor", "admin"] },
];
const ID_ROUTES = [
  { re: /^TX-[A-Z]{3}-\d{3}$/i, to: (id) => `/zones/${id}`, roles: ["manager", "analyst", "supervisor"] },
  { re: /^P-[A-Z]{3}-\d{3}-\d{3}$/i, to: (id) => `/premises/${id}`, roles: ["analyst", "supervisor"] },
  { re: /^C-\d{4}-\d{4}$/i, to: (id) => `/cases/${id}`, roles: ["manager", "analyst", "supervisor"] },
];

function useSession() {
  const [s, setS] = useState(session());
  useEffect(() => onSessionChange(setS), []);
  return s;
}

// Menu badges: next actions from /work, every minute.
function useBadges(user) {
  const [counts, setCounts] = useState({});
  useEffect(() => {
    if (!["analyst", "supervisor", "manager"].includes(user?.role)) return undefined;
    let live = true;
    const load = () => get("/work").then((w) => live && setCounts({ urgent: w.urgent, ...w.counts })).catch(() => {});
    load();
    const timer = setInterval(load, 60000);
    return () => { live = false; clearInterval(timer); };
  }, [user?.role]);
  return counts;
}

// Top-bar status: region, latest run, data mode and demo switch (GET /meta), refreshed every minute.
function useMeta(user) {
  const [meta, setMeta] = useState(null);
  useEffect(() => {
    if (!user) return undefined;
    let live = true;
    const load = () => get("/meta").then((m) => live && setMeta(m)).catch(() => {});
    load();
    const timer = setInterval(load, 60000);
    return () => { live = false; clearInterval(timer); };
  }, [user?.user_id]);  // eslint-disable-line react-hooks/exhaustive-deps
  return meta;
}

function SearchBox({ role }) {
  const [q, setQ] = useState("");
  const [miss, setMiss] = useState(false);
  const navigate = useNavigate();
  if (!["manager", "analyst", "supervisor"].includes(role)) return null;
  function go(e) {
    e.preventDefault();
    const id = q.trim().toUpperCase();
    const hit = ID_ROUTES.find((r) => r.re.test(id) && r.roles.includes(role));
    setMiss(!hit);
    if (hit) { navigate(hit.to(id)); setQ(""); }
  }
  return (
    <form className={`search ${miss ? "miss" : ""}`} onSubmit={go} role="search">
      <Search size={16} aria-hidden="true" />
      <input value={q} onChange={(e) => { setQ(e.target.value); setMiss(false); }} placeholder={t("searchPlaceholder")} aria-label={t("search")} />
      {miss ? <small className="search-miss" role="status">{t("searchMiss")}</small> : null}
    </form>
  );
}

function Shell({ children }) {
  const { user } = useSession();
  useLang();
  const badges = useBadges(user);
  const meta = useMeta(user);
  const items = NAV.filter((n) => n.roles.includes(user?.role) && (!n.demoOnly || meta?.demo));
  const badgeOf = (n) => (n.badge === "urgent" ? badges.urgent : n.key === "dispatch" ? badges.suggestions : null);
  return (
    <div className="app">
      <a className="skip-link" href="#main" onClick={(e) => { e.preventDefault(); document.getElementById("main")?.focus(); }}>{t("skipToContent")}</a>
      <header className="topbar">
        <span className="brand"><span className="logo-mark" title="VoltGuard AI"><Zap size={18} strokeWidth={2.5} aria-hidden="true" /></span></span>
        <span className="brand-name">VoltGuard <span>AI</span></span>
        <div className="status-chips">
          <span className="tchip keep">{t("region")} <b>{user?.region === "*" ? t("allRegions") : user?.region}</b>{meta?.region_name ? ` · ${meta.region_name}` : ""}</span>
          {meta?.run_date ? <span className="tchip hide-md">{t("runDate")} <b>{meta.run_date}</b></span> : null}
          {meta ? <span className={`tchip ${meta.data_mode === "simulated" ? "sim" : ""}`}>{meta.data_mode === "simulated" ? t("dataSimulated") : t("dataUpload")}</span> : null}
          {meta?.llm_mode === "mock" ? <span className="tchip mock" title={t("mockTitle")}>mock</span> : null}
        </div>
        <SearchBox role={user?.role} />
        <span className="spacer" />
        <ThemeLangToggles />
        <span className="who-chip" title={`${user?.role} · ${user?.region}`}>{user?.user_id}<small>{t(`role_${user?.role}`)}{user?.team ? ` · ${user.team}` : ""}</small></span>
        {user ? <button type="button" className="icon-btn" onClick={signOut} title={t("signOut")}><LogOut size={17} aria-hidden="true" /><span className="label">{t("signOut")}</span></button> : null}
      </header>
      <nav className="rail" aria-label={t("mainMenu")}>
        {items.map((n) => {
          const Icon = ICONS[n.key] || LayoutDashboard;
          const count = badgeOf(n);
          return (
            <NavLink key={n.to} to={n.to} end={n.to === "/"}>
              <Icon size={20} aria-hidden="true" /><span>{t(n.key)}</span>
              {count ? <span className="nav-badge" aria-label={t("waitingN", { n: count })}>{count}</span> : null}
            </NavLink>
          );
        })}
      </nav>
      <main id="main" tabIndex={-1}>{children}</main>
      {meta?.demo ? <DemoGuide /> : null}
    </div>
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
  useEffect(() => { document.documentElement.lang = lang === "ms" ? "ms" : "en"; }, [lang]);
  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/field/*" element={<FieldApp />} />
        <Route path="/" element={<Guarded><Overview /></Guarded>} />
        <Route path="/work" element={<Guarded><Work /></Guarded>} />
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
