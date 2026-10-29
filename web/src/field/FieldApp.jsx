// Inspector app (FR-IW-02, NFR-13, NFR-16; UI brief 2.5): phone first, works offline. Today's cases in route
// order with distance, one-screen outcome form with big outcome buttons and a camera button, and a clear
// "saved offline / synced" banner. Outcomes are kept in the encrypted store until sync, then wiped.
import { Bot, Camera, CircleCheck, CircleHelp, ClipboardList, CloudOff, DoorClosed, MessageCircle, Navigation, RefreshCw, ShieldAlert,
  Sun, User, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiError, request } from "../api.js";
import { setLang, t, useLang } from "../i18n.js";
import TelegramChat from "../components/TelegramChat.jsx";
import { ThemeLangToggles } from "../pages/Login.jsx";
import * as store from "./secureStore.js";

const OUTCOMES = [
  { key: "confirmed_theft", Icon: ShieldAlert, cls: "theft" },
  { key: "false_alarm", Icon: CircleCheck, cls: "" },
  { key: "inconclusive", Icon: CircleHelp, cls: "" },
  { key: "no_access", Icon: DoorClosed, cls: "" },
];

function newRef() {
  return `${Date.now().toString(36)}-${crypto.getRandomValues(new Uint32Array(2)).join("")}`;
}

async function call(token, path, options = {}) {
  return request(path, { ...options, tokenOverride: token });
}

async function keepSession(data) {
  if (data.user.role !== "inspector") throw new Error(t("inspectorsOnly"));
  await store.put("session", { token: data.access_token, user: data.user, expiresAt: data.expires_at * 1000 });
}

function SignIn({ onSignedIn, notice }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  async function submit(e) {
    e.preventDefault();
    setError(null);
    try {
      await keepSession(await request("/auth/token", { method: "POST", body: { username: username.trim(), password }, tokenOverride: "" }));
      onSignedIn();
    } catch (err) {
      setError(err.message);
    }
  }
  return (
    <form className="card stack" onSubmit={submit}>
      <div className="row between"><h1>VoltGuard · {t("field")}</h1></div>
      {notice ? <div className="notice warn">{notice}</div> : null}
      <label>{t("username")}<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
      <label>{t("password")}<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
      {error ? <div className="notice error" role="alert">{error}</div> : null}
      <button className="primary" type="submit">{t("signIn")}</button>
      <small className="muted">{t("wipeNotice")}</small>
    </form>
  );
}

// The questions and answers live in FieldApp's memory, so they survive switching tabs; nothing is written to
// the phone, and they are gone after signing out or reloading.
function AskBox({ token, log, setLog }) {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  async function ask(e) {
    e.preventDefault();
    const question = q.trim();
    if (!question || busy) return;
    setBusy(true);
    let answer;
    try {
      answer = await call(token, "/agents/chat", { method: "POST", body: { agent: "field", message: question } });
    } catch (err) {
      answer = { answer: err instanceof TypeError ? t("assistantNeedsConnection") : err.message, sources: [] };
    }
    setLog((items) => [...items, { q: question, answer }].slice(-10));
    setQ("");
    setBusy(false);
  }
  return (
    <form className="card stack" onSubmit={ask}>
      <h2>{t("assistant")}</h2>
      {log.map((item, i) => (
        <div key={i} className="stack" style={{ gap: 4 }}>
          <b>{item.q}</b>
          <div className="notice"><span>{item.answer.answer}
            {item.answer.sources?.length ? <ol>{item.answer.sources.map((s, j) => <li key={j}><small>{s.title}{s.section ? `, ${s.section}` : ""}</small></li>)}</ol> : null}</span>
          </div>
        </div>
      ))}
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("askPlaceholder")} maxLength={1000} aria-label={t("assistant")} />
      <button type="submit" className="primary" disabled={!q.trim() || busy}>{busy ? "…" : t("ask")}</button>
    </form>
  );
}

function LinkTelegram({ token }) {
  const [code, setCode] = useState(null);
  const [error, setError] = useState(null);
  async function get() {
    setError(null);
    try {
      setCode(await call(token, "/telegram/link-code", { method: "POST" }));
    } catch (err) {
      setError(err.message);
    }
  }
  return (
    <div className="card stack">
      <small>{t("telegramLinkHint")}</small>
      <button type="button" onClick={get}>{t("linkTelegram")}</button>
      {code ? <div className="notice">{t("telegramSendCode", { code: code.code })}</div> : null}
      {error ? <div className="notice error">{error}</div> : null}
    </div>
  );
}

// Navigation opens the inspector's map app with coordinates only (no name or address is sent).
function NavigateLinks({ lat, lon }) {
  const ll = `${lat.toFixed(6)},${lon.toFixed(6)}`;
  return (
    <div className="row">
      <a className="button primary" href={`https://www.google.com/maps/dir/?api=1&destination=${ll}&travelmode=driving`} target="_blank" rel="noreferrer">
        <Navigation size={16} aria-hidden="true" />{t("navigate")} · Google Maps</a>
      <a className="button" href={`https://waze.com/ul?ll=${ll}&navigate=yes`} target="_blank" rel="noreferrer">Waze</a>
    </div>
  );
}

const stopOf = (route, caseId) => route?.stops?.find((s) => s.case_id === caseId);

function inRouteOrder(cases, route) {
  return [...cases].sort((a, b) => (stopOf(route, a.case_id)?.stop ?? 999) - (stopOf(route, b.case_id)?.stop ?? 999));
}

function SyncBanner({ online, queue, message, lastSync }) {
  if (!online) {
    return <div className="sync-banner offline" role="status"><CloudOff size={20} aria-hidden="true" />
      <span>{queue ? t("savedOfflineN", { n: queue }) : t("offline")}<small>{t("offlineBanner")}</small></span></div>;
  }
  if (queue) {
    return <div className="sync-banner pending" role="status"><RefreshCw size={20} aria-hidden="true" />
      <span>{t("waitingToSyncN", { n: queue })}<small>{message || t("syncSoon")}</small></span></div>;
  }
  return <div className="sync-banner synced" role="status"><Wifi size={20} aria-hidden="true" />
    <span>{lastSync ? t("syncedAt", { time: new Date(lastSync).toLocaleTimeString() }) : t("online")}<small>{message && !message.startsWith("Synced") ? message : t("wipeNotice")}</small></span></div>;
}

// Rooftop-solar homes (FR-PS-10): what to look at on site, with the generation the scorer expected so the
// inspector can compare it with the inverter's own total. Solar never rules out a bypass before the meter.
function SolarChecklist({ solar }) {
  return (
    <div className="card stack" style={{ gap: 6 }}>
      <h3 className="row" style={{ gap: 6 }}><Sun size={18} aria-hidden="true" />{t("solarVisitTitle")}</h3>
      <small className="muted">
        {solar.registered ? t("solarVisitRegistered", { kwp: solar.capacity_kwp ?? "?" }) : t("solarVisitUnregistered")}
        {solar.has_battery ? ` · ${t("solarVisitBattery")}` : ""}
      </small>
      <ul style={{ margin: 0 }}>
        {solar.checklist.map((key) => (
          <li key={key}><small>{key === "inverter_total_vs_expected" && solar.expected_kwh_per_day != null
            ? t("solarCheck_inverter_total_vs_expected_n", { kwh: solar.expected_kwh_per_day })
            : t(`solarCheck_${key}`)}</small></li>
        ))}
      </ul>
      {solar.psh_source === "assumed" ? <small className="muted">{t("solarPshAssumed")}</small> : null}
    </div>
  );
}

function OutcomeForm({ item, onSaved }) {
  const [outcome, setOutcome] = useState(null);
  const [reasonTag, setReasonTag] = useState(null);
  const [notes, setNotes] = useState("");
  const [photos, setPhotos] = useState([]);
  const [busy, setBusy] = useState(false);

  async function addPhoto(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    const buffer = await file.arrayBuffer();
    const id = newRef();
    await store.put(`photo:${id}`, buffer);   // encrypted at once; the file object is dropped
    setPhotos((p) => [...p, { id, type: file.type || "image/jpeg", preview: URL.createObjectURL(new Blob([buffer], { type: file.type })) }]);
  }

  async function save() {
    setBusy(true);
    const queue = (await store.get("queue")) || [];
    queue.push({ clientRef: newRef(), caseId: item.case_id, outcome, reasonTag, notes, photos: photos.map(({ id, type }) => ({ id, type })),
      savedAt: Date.now() });
    await store.put("queue", queue);
    photos.forEach((p) => URL.revokeObjectURL(p.preview));
    setBusy(false);
    onSaved();
  }

  return (
    <div className="card stack">
      <h2>{t("outcome")}</h2>
      <div className="outcomes" role="radiogroup" aria-label={t("outcome")}>
        {OUTCOMES.map(({ key, Icon, cls }) => (
          <button key={key} type="button" role="radio" aria-checked={outcome === key} className={`${cls} ${outcome === key ? "selected" : ""}`}
            onClick={() => { setOutcome(key); setReasonTag(null); }}>
            <Icon size={26} aria-hidden="true" />{t(key)}
          </button>
        ))}
      </div>
      {item.solar && item.solar.reason_tags?.[outcome] ? (
        <label className="row" style={{ gap: 8, minHeight: 44 }}>
          <input type="checkbox" checked={reasonTag === item.solar.reason_tags[outcome]}
            onChange={(e) => setReasonTag(e.target.checked ? item.solar.reason_tags[outcome] : null)} />
          {t(`reason_${item.solar.reason_tags[outcome]}`)}
        </label>
      ) : null}
      <label className="camera-btn"><Camera size={24} aria-hidden="true" />{photos.length ? t("photoAnother", { n: photos.length }) : t("takePhoto")}
        <input type="file" accept="image/*" capture="environment" onChange={addPhoto} aria-label={t("takePhoto")} /></label>
      {photos.length ? <div className="row">{photos.map((p) => <img key={p.id} className="thumb" src={p.preview} alt={t("evidencePhoto")} />)}</div> : null}
      <label>{t("notes")}<textarea value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={4000} /></label>
      <button className="primary" type="button" disabled={!outcome || busy} onClick={save}>{t("submit")}</button>
      <small className="muted">{t("submitOfflineNote")}</small>
    </div>
  );
}

export default function FieldApp() {
  useLang();
  const location = useLocation();
  const navigate = useNavigate();
  const [session, setSession] = useState(undefined);
  const [cases, setCases] = useState([]);
  const [route, setRoute] = useState(null);
  const [queue, setQueue] = useState([]);
  const [meta, setMeta] = useState(null);
  const [open, setOpen] = useState(null);
  const [online, setOnline] = useState(navigator.onLine);
  const [message, setMessage] = useState(null);
  const [notice, setNotice] = useState(null);
  const [tab, setTab] = useState("cases");
  const [askLog, setAskLog] = useState([]);
  const syncing = useRef(false);
  useEffect(() => { if (!session) setAskLog([]); }, [session]);

  const loadLocal = useCallback(async () => {
    if (await store.enforceMaxAge()) setNotice(t("wipedOld"));
    const s = await store.get("session").catch(() => null);
    setSession(s && s.expiresAt > Date.now() ? s : null);
    setCases((await store.get("cases").catch(() => null)) || []);
    setRoute(await store.get("route").catch(() => null));
    setQueue((await store.get("queue").catch(() => null)) || []);
    setMeta(await store.get("meta").catch(() => null));
  }, []);

  const handleAuthError = useCallback(async (err) => {
    if (err instanceof ApiError && err.status === 401) {
      await store.wipeAll();
      setSession(null);
      setCases([]);
      setRoute(null);
      setQueue([]);
      setNotice(err.code === "signed_out" ? t("remoteWiped") : t("signInAgain"));
      return true;
    }
    return false;
  }, []);

  const sync = useCallback(async () => {
    // One sync at a time; navigator.onLine is only a hint, so just try and treat a network error as offline.
    if (syncing.current) return;
    const s = await store.get("session").catch(() => null);
    if (!s) return;
    syncing.current = true;
    setMessage(t("syncing"));
    try {
      let pending = (await store.get("queue")) || [];
      for (const item of [...pending]) {
        const keys = [];
        for (const photo of item.photos) {
          const buffer = await store.get(`photo:${photo.id}`);
          if (!buffer) continue;
          const form = new FormData();
          form.append("file", new Blob([buffer], { type: photo.type }), "photo");
          keys.push((await call(s.token, `/cases/${item.caseId}/photos`, { method: "POST", form })).photo_key);
        }
        await call(s.token, `/cases/${item.caseId}/outcome`, { method: "POST",
          body: { outcome: item.outcome, reason_tag: item.reasonTag || null, notes: item.notes || null, photo_keys: keys, client_ref: item.clientRef } });
        for (const photo of item.photos) await store.remove(`photo:${photo.id}`);
        pending = pending.filter((q) => q.clientRef !== item.clientRef);
        await store.put("queue", pending);
      }
      // Fresh list of assigned cases; synced cases drop off the phone.
      const list = (await call(s.token, "/cases")).cases;
      await store.put("cases", list);
      // Today's visiting order, kept encrypted with the cases so it works offline.
      await store.put("route", await call(s.token, "/route").catch(() => null));
      await store.put("meta", { downloadedAt: Date.now() });
      setOnline(true);
      setMessage(null);
    } catch (err) {
      if (await handleAuthError(err)) {
        setMessage(null);
      } else if (err instanceof TypeError) {
        setOnline(false);
        setMessage(t("noConnectionKept"));
      } else {
        setMessage(t("syncFailed", { error: err.message }));
      }
    } finally {
      syncing.current = false;
    }
    await loadLocal();
  }, [handleAuthError, loadLocal]);

  // Demo role card (DEMO_MODE on): /field?demo=inspector.b signs in once, then the URL is cleaned.
  useEffect(() => {
    const demoUser = new URLSearchParams(location.search).get("demo");
    if (!demoUser) return;
    request("/auth/demo-token", { method: "POST", body: { username: demoUser }, tokenOverride: "" })
      .then(keepSession).then(() => { setNotice(null); return loadLocal(); })
      .catch((e) => setNotice(e.message))
      .finally(() => navigate("/field", { replace: true }));
  }, [location.search]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadLocal();
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
    const up = () => { setOnline(true); sync(); };
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    const timer = setInterval(() => store.enforceMaxAge().then((wiped) => wiped && loadLocal()), 60_000);
    return () => { window.removeEventListener("online", up); window.removeEventListener("offline", down); clearInterval(timer); };
  }, [loadLocal, sync]);

  useEffect(() => { if (session) sync(); }, [session?.token]); // eslint-disable-line react-hooks/exhaustive-deps

  if (session === undefined) return <div className="field"><p className="muted">{t("loading")}</p></div>;
  if (!session) {
    return (
      <div className="field">
        <div className="field-top"><span className="who">VoltGuard</span><span className="row"><ThemeLangToggles /></span></div>
        <SignIn notice={notice} onSignedIn={() => { setNotice(null); loadLocal(); }} />
      </div>
    );
  }

  const queuedFor = (id) => queue.filter((q) => q.caseId === id).length;
  const item = open && cases.find((c) => c.case_id === open);
  const tabs = [
    { key: "cases", label: t("myCases"), Icon: ClipboardList, badge: queue.length || null },
    { key: "messages", label: t("messages"), Icon: MessageCircle },
    { key: "assistant", label: t("assistant"), Icon: Bot },
    { key: "me", label: t("me"), Icon: User },
  ];
  const ordered = inRouteOrder(cases, route);

  return (
    <div className="field">
      <div className="field-top">
        <span className="who">{session.user.user_id} · {session.user.team}</span>
        <span className="row" style={{ gap: 6 }}>
          <span className={`pill ${online ? "ok" : "risk"}`}>{online ? <Wifi size={13} aria-hidden="true" /> : <WifiOff size={13} aria-hidden="true" />}{online ? t("online") : t("offline")}</span>
          <button type="button" className="icon-btn" onClick={sync} aria-label={t("sync")}><RefreshCw size={16} aria-hidden="true" /><span className="label">{t("sync")}</span></button>
        </span>
      </div>
      <SyncBanner online={online} queue={queue.length} message={message} lastSync={meta?.downloadedAt} />
      {notice ? <div className="notice warn">{notice}</div> : null}
      {!item ? (
        <nav className="tabs field-tabs" aria-label={t("field")}>
          {tabs.map(({ key, label, Icon, badge }) => (
            <button key={key} type="button" className={tab === key ? "active" : ""} onClick={() => setTab(key)} aria-current={tab === key ? "page" : undefined}>
              <Icon size={22} aria-hidden="true" /><span>{label}</span>{badge ? <span className="nav-badge">{badge}</span> : null}
            </button>
          ))}
        </nav>
      ) : null}
      {!item && tab === "messages" ? (
        online ? (
          <>
            <TelegramChat token={session.token} compact links={false} title="VoltGuard Dispatch Bot" />
            <LinkTelegram token={session.token} />
          </>
        ) : <p className="muted">{t("messagesNeedConnection")}</p>
      ) : !item && tab === "assistant" ? (
        <AskBox token={session.token} log={askLog} setLog={setAskLog} />
      ) : !item && tab === "me" ? (
        <div className="card stack">
          <h2>{session.user.user_id}</h2>
          <small>{t(`role_${session.user.role}`)} · {session.user.team} · {session.user.region}</small>
          <label>{t("language")}
            <select value={localStorage.getItem("vg_lang") || "en"} onChange={(e) => setLang(e.target.value)}><option value="ms">Bahasa Melayu</option><option value="en">English</option></select>
          </label>
          <div className="row"><ThemeLangToggles /></div>
          <p><small>{t("wipeNotice")}</small></p>
          <button className="danger" onClick={async () => { await store.wipeAll(); loadLocal(); }}>{t("signOut")}</button>
        </div>
      ) : item ? (
        <div className="stack">
          <button type="button" className="back" onClick={() => setOpen(null)}>← {t("myCases")}</button>
          <div className="card stack" style={{ gap: 8 }}>
            <h2>{item.label === "Routine meter check" ? t("routine") : `${t("case")} ${item.case_id}`}</h2>
            <small>{item.case_id} · {item.premise_id}{stopOf(route, item.case_id) ? ` · ${t("kmFromBase", { km: stopOf(route, item.case_id).base_km })}` : ""}</small>
            {item.joint_operation ? <div className="notice error">{t("jointOperationField")}</div> : null}
            <h3>{t("address")}</h3>
            {item.contact ? <p style={{ margin: 0 }}>{item.contact.address}<br /><small>{item.contact.holder_name} · {item.contact.contact}</small></p> : <p className="muted">{t("notAvailable")}</p>}
            {item.contact?.lat != null ? <NavigateLinks lat={item.contact.lat} lon={item.contact.lon} /> : null}
            {item.reasons?.length ? <><h3>{t("reasons")}</h3><ol style={{ margin: 0 }}>{item.reasons.map((r, i) => <li key={i}>{r.reason_text}</li>)}</ol></> : null}
            <h3>{t("safety")}</h3>
            <ul style={{ margin: 0 }}>{item.safety_checklist.map((s, i) => <li key={i}><small>{s}</small></li>)}</ul>
          </div>
          {item.solar ? <SolarChecklist solar={item.solar} /> : null}
          {queuedFor(item.case_id) ? <div className="sync-banner pending"><CloudOff size={20} aria-hidden="true" /><span>{t("outcomeSavedOffline")}</span></div>
            : <OutcomeForm item={item} onSaved={async () => { await loadLocal(); sync(); }} />}
        </div>
      ) : (
        <>
          <div className="row between">
            <h2>{t("todaysCases")}</h2>
            {route?.stops?.length ? <small className="muted">{t("routeTotals", { n: route.stops.length, km: route.total_km })}</small> : null}
          </div>
          {ordered.length ? ordered.map((c) => {
            const stop = stopOf(route, c.case_id);
            return (
              <a key={c.case_id} className="card case-card" href="#/field" onClick={(e) => { e.preventDefault(); setOpen(c.case_id); }}>
                {stop ? <span className="stop-no">{stop.stop}</span> : <span className="stop-no" style={{ background: "var(--panel-2)", color: "var(--muted)" }}>–</span>}
                <span>
                  <b>{c.label === "Routine meter check" ? t("routine") : c.case_id}</b>{c.joint_operation ? <span className="chip theft" style={{ marginLeft: 6 }}>{t("joint")}</span> : null}<br />
                  <small className="muted">{c.contact?.address || c.premise_id}</small><br />
                  {queuedFor(c.case_id) ? <span className="chip warn">{t("pending")}</span> : <span className="chip info">{t(`status_${c.status}`)}</span>}
                </span>
                <span className="km">{stop ? `${stop.base_km ?? stop.total_km} km` : "–"}<small>{stop ? t("fromBaseStraight") : t("noLocation")}</small></span>
              </a>
            );
          }) : <p className="muted">{t("noCasesOnPhone")}</p>}
          {route?.assumptions ? <small className="muted">{t("routeOrderNote")}</small> : null}
          {route?.full_route_url ? <a className="button" href={route.full_route_url} target="_blank" rel="noreferrer">{t("openRoute")}</a> : null}
        </>
      )}
    </div>
  );
}
