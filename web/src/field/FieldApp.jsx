// Inspector app (FR-IW-02, NFR-13, NFR-16): assigned cases offline, outcome form with photos,
// sync when the connection returns, then the local copy is wiped.
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, request } from "../api.js";
import { setLang, t, useLang } from "../i18n.js";
import TelegramChat from "../components/TelegramChat.jsx";
import * as store from "./secureStore.js";

const OUTCOMES = ["confirmed_theft", "false_alarm", "inconclusive", "no_access"];

function newRef() {
  return `${Date.now().toString(36)}-${crypto.getRandomValues(new Uint32Array(2)).join("")}`;
}

async function call(token, path, options = {}) {
  return request(path, { ...options, tokenOverride: token });
}

function SignIn({ onSignedIn, notice }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  async function submit(e) {
    e.preventDefault();
    setError(null);
    try {
      const data = await request("/auth/token", { method: "POST", body: { username: username.trim(), password }, tokenOverride: "" });
      if (data.user.role !== "inspector") throw new Error("This app is for field inspectors");
      await store.put("session", { token: data.access_token, user: data.user, expiresAt: data.expires_at * 1000 });
      onSignedIn();
    } catch (err) {
      setError(err.message);
    }
  }
  return (
    <form className="card stack" onSubmit={submit}>
      <h1>VoltGuard · {t("field")}</h1>
      {notice ? <div className="notice warn">{notice}</div> : null}
      <label>{t("username")}<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
      <label>{t("password")}<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
      {error ? <div className="notice error">{error}</div> : null}
      <button className="primary">{t("signIn")}</button>
      <small>{t("wipeNotice")}</small>
    </form>
  );
}

function AskBox({ token }) {
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState(null);
  async function ask(e) {
    e.preventDefault();
    try {
      setAnswer(await call(token, "/agents/chat", { method: "POST", body: { agent: "field", message: q } }));
    } catch (err) {
      setAnswer({ answer: err instanceof TypeError ? "The assistant needs a connection." : err.message, sources: [] });
    }
  }
  return (
    <form className="card stack" onSubmit={ask}>
      <h2>{t("assistant")}</h2>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="What should I photograph at the meter board?" maxLength={1000} />
      <button type="submit" disabled={!q.trim()}>Ask</button>
      {answer ? (
        <div className="notice">{answer.answer}
          {answer.sources?.length ? <ol>{answer.sources.map((s, i) => <li key={i}><small>{s.title}{s.section ? `, ${s.section}` : ""}</small></li>)}</ol> : null}
        </div>
      ) : null}
    </form>
  );
}

function OutcomeForm({ item, onSaved }) {
  const [outcome, setOutcome] = useState(null);
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
    queue.push({ clientRef: newRef(), caseId: item.case_id, outcome, notes, photos: photos.map(({ id, type }) => ({ id, type })), savedAt: Date.now() });
    await store.put("queue", queue);
    photos.forEach((p) => URL.revokeObjectURL(p.preview));
    setBusy(false);
    onSaved();
  }

  return (
    <div className="card stack">
      <h2>{t("outcome")}</h2>
      <div className="outcomes">
        {OUTCOMES.map((o) => (
          <button key={o} className={outcome === o ? "selected primary" : ""} onClick={() => setOutcome(o)} type="button">{t(o)}</button>
        ))}
      </div>
      <label>{t("notes")}<textarea value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={4000} /></label>
      <label>{t("photo")}<input type="file" accept="image/*" capture="environment" onChange={addPhoto} /></label>
      <div className="row">{photos.map((p) => <img key={p.id} className="thumb" src={p.preview} alt="evidence" />)}</div>
      <button className="primary" disabled={!outcome || busy} onClick={save}>{t("submit")}</button>
    </div>
  );
}

export default function FieldApp() {
  useLang();
  const [session, setSession] = useState(undefined);
  const [cases, setCases] = useState([]);
  const [queue, setQueue] = useState([]);
  const [open, setOpen] = useState(null);
  const [online, setOnline] = useState(navigator.onLine);
  const [message, setMessage] = useState(null);
  const [notice, setNotice] = useState(null);
  const [tab, setTab] = useState("cases");
  const syncing = useRef(false);

  const loadLocal = useCallback(async () => {
    if (await store.enforceMaxAge()) setNotice("Local case data was older than 24 hours and has been wiped. Sign in again.");
    const s = await store.get("session").catch(() => null);
    setSession(s && s.expiresAt > Date.now() ? s : null);
    setCases((await store.get("cases").catch(() => null)) || []);
    setQueue((await store.get("queue").catch(() => null)) || []);
  }, []);

  const handleAuthError = useCallback(async (err) => {
    if (err instanceof ApiError && err.status === 401) {
      await store.wipeAll();
      setSession(null);
      setCases([]);
      setQueue([]);
      setNotice(err.code === "signed_out" ? "This phone was signed out remotely. All case data on it has been wiped." : "Please sign in again.");
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
    setMessage("Syncing…");
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
          body: { outcome: item.outcome, notes: item.notes || null, photo_keys: keys, client_ref: item.clientRef } });
        for (const photo of item.photos) await store.remove(`photo:${photo.id}`);
        pending = pending.filter((q) => q.clientRef !== item.clientRef);
        await store.put("queue", pending);
      }
      // Fresh list of assigned cases; synced cases drop off the phone.
      const list = (await call(s.token, "/cases")).cases;
      await store.put("cases", list);
      await store.put("meta", { downloadedAt: Date.now() });
      setMessage(`Synced at ${new Date().toLocaleTimeString()}`);
    } catch (err) {
      if (await handleAuthError(err)) {
        setMessage(null);
      } else if (err instanceof TypeError) {
        setOnline(false);
        setMessage("No connection: outcomes stay encrypted on this phone until the next sync.");
      } else {
        setMessage(`Sync failed: ${err.message}`);
      }
    } finally {
      syncing.current = false;
    }
    await loadLocal();
  }, [handleAuthError, loadLocal]);

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

  if (session === undefined) return <div className="field"><p className="muted">Loading…</p></div>;
  if (!session) return <div className="field"><SignIn notice={notice} onSignedIn={() => { setNotice(null); loadLocal(); }} /></div>;

  const queuedFor = (id) => queue.filter((q) => q.caseId === id).length;
  const item = open && cases.find((c) => c.case_id === open);

  return (
    <div className="field">
      <div className="status-line">
        <b>{session.user.user_id} · {session.user.team}</b>
        <span className={`chip ${online ? "ok" : "warn"}`}>{online ? t("online") : t("offline")}</span>
        <select value={localStorage.getItem("vg_lang") || "en"} onChange={(e) => setLang(e.target.value)}><option value="en">EN</option><option value="ms">BM</option></select>
      </div>
      {notice ? <div className="notice warn">{notice}</div> : null}
      <div className="row" style={{ marginBottom: 10 }}>
        <button onClick={sync}>{t("sync")}</button>
        {queue.length ? <span className="chip warn">{queue.length} {t("pending")}</span> : null}
        {message ? <small>{message}</small> : null}
        <button onClick={async () => { await store.wipeAll(); loadLocal(); }}>{t("signOut")}</button>
      </div>
      {!item ? (
        <div className="tabs">
          <button className={tab === "cases" ? "active" : ""} onClick={() => setTab("cases")}>{t("myCases")}</button>
          <button className={tab === "messages" ? "active" : ""} onClick={() => setTab("messages")}>{t("messages")}</button>
        </div>
      ) : null}
      {!item && tab === "messages" ? (
        online ? <TelegramChat token={session.token} compact links={false} title="VoltGuard Dispatch Bot" />
          : <p className="muted">Messages need a connection.</p>
      ) : item ? (
        <div className="stack">
          <button onClick={() => setOpen(null)}>← {t("myCases")}</button>
          <div className="card">
            <h2>{item.label === "Routine meter check" ? t("routine") : `${t("case")} ${item.case_id}`}</h2>
            <small>{item.case_id} · {item.premise_id}</small>
            {item.joint_operation ? <div className="notice error" style={{ marginTop: 8 }}>Joint operation with police: do not visit alone.</div> : null}
            <h3 style={{ marginTop: 10 }}>{t("address")}</h3>
            {item.contact ? <p>{item.contact.address}<br /><small>{item.contact.holder_name} · {item.contact.contact}</small></p> : <p className="muted">Not available</p>}
            {item.reasons?.length ? (
              <><h3>{t("reasons")}</h3><ol>{item.reasons.map((r, i) => <li key={i}>{r.reason_text}</li>)}</ol></>
            ) : null}
            <h3>{t("safety")}</h3>
            <ul>{item.safety_checklist.map((s, i) => <li key={i}><small>{s}</small></li>)}</ul>
          </div>
          {queuedFor(item.case_id) ? <div className="notice">Outcome saved on this phone (encrypted); it syncs when online.</div>
            : <OutcomeForm item={item} onSaved={async () => { await loadLocal(); sync(); }} />}
        </div>
      ) : (
        <div>
          <h2>{t("myCases")}</h2>
          {cases.length ? cases.map((c) => (
            <a key={c.case_id} className="card case-card" href="#/field" onClick={(e) => { e.preventDefault(); setOpen(c.case_id); }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <b>{c.label === "Routine meter check" ? t("routine") : c.case_id}</b>
                {queuedFor(c.case_id) ? <span className="chip warn">{t("pending")}</span> : <span className="chip info">{c.status}</span>}
              </div>
              <small>{c.contact?.address || c.premise_id}</small>
            </a>
          )) : <p className="muted">No assigned cases on this phone.</p>}
          <p><small>{t("wipeNotice")}</small></p>
          <AskBox token={session.token} />
        </div>
      )}
    </div>
  );
}
