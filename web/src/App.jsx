import { BrainCircuit, CalendarRange, ClipboardList, Database, LayoutDashboard, LogOut, MessageCircle, Search, Send, Settings as SettingsIcon,
  ShieldCheck, Briefcase, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { HashRouter, Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
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
import Work from "./pages/Work.jsx";
import Zone from "./pages/Zone.jsx";

const ICONS = { work: Briefcase, overview: LayoutDashboard, cases: ClipboardList, assistant: MessageCircle, weekly: CalendarRange,
  dispatch: Send, models: BrainCircuit, dataManager: Database, settings: SettingsIcon, audit: ShieldCheck };

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
      {miss ? <small className="search-miss">{t("searchMiss")}</small> : null}
    </form>
  );
}

function Shell({ children }) {
  const { user } = useSession();
  const lang = useLang();
  const [health, setHealth] = useState(null);
  const badges = useBadges(user);
  useEffect(() => { get("/health").then(setHealth).catch(() => setHealth(null)); }, []);
  const items = NAV.filter((n) => n.roles.includes(user?.role));
  const badgeOf = (n) => (n.badge === "urgent" ? badges.urgent : n.key === "dispatch" ? badges.suggestions : null);
  return (
    <>
      <header className="topbar">
        <span className="logo"><span className="logo-mark"><Zap size={16} strokeWidth={2.5} /></span> VoltGuard AI</span>
        {health?.llm_mode === "mock" ? <span className="badge-mode" title="Agents use deterministic templates">mock</span> : null}
        <span className="badge-mode outline">R0 · simulated data</span>
        <SearchBox role={user?.role} />
        <span className="spacer" />
        <span className="who-chip" title={`${user?.role} · ${user?.region}`}>{user?.user_id}<small>{user?.role} · {user?.region}{user?.team ? ` · ${user.team}` : ""}</small></span>
        <select value={lang} onChange={(e) => setLang(e.target.value)} aria-label="Language">
          <option value="en">EN</option><option value="ms">BM</option>
        </select>
        {user ? <button className="icon-btn sign-out" onClick={signOut} title={t("signOut")}><LogOut size={18} aria-hidden="true" /><span>{t("signOut")}</span></button> : null}
      </header>
      <div className="layout">
        <nav className="nav" aria-label="Main">
          {items.map((n) => {
            const Icon = ICONS[n.key] || LayoutDashboard;
            const count = badgeOf(n);
            return (
              <NavLink key={n.to} to={n.to} end={n.to === "/"}>
                <Icon size={18} aria-hidden="true" /><span className="nav-label">{t(n.key)}</span>
                {count ? <span className="nav-badge" aria-label={`${count} waiting`}>{count}</span> : null}
              </NavLink>
            );
          })}
        </nav>
        <main>{children}</main>
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
