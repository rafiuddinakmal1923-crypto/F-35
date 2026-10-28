// Telegram dispatch chat (SRS 5.1): the bot's messages with their buttons. Without a bot token this is
// the dispatch simulator; with one, the same messages also reach the linked Telegram chats and a press
// in either place answers the message once.
import { useEffect, useMemo, useRef, useState } from "react";
import { request } from "../api.js";

const TITLES = { assignment: "New inspection", reminder: "Reminder", escalation: "Escalation", suggestion: "Dispatch suggestion",
  no_access: "No access", declined: "Cannot attend", report: "Report" };
const DONE = { accept: "Accepted", enroute: "On the way", decline: "Cannot attend", approve: "Approved", reject: "Rejected",
  assigned: "Assigned directly", visited: "Visited" };

// The header already names the kind and case: show the rest of the text.
const body_ = (text) => text.replace(/^VoltGuard [^:]+: case [^.]+\.\s*/, "");

function linkify(text) {
  return text.split(/(https?:\/\/\S+)/g).map((part, i) => (part.startsWith("http")
    ? <a key={i} href={part.replace(/^https?:\/\/[^/]+/, "")}>{part.split("#")[1] || part}</a> : part));
}

export function useChats(token, refreshMs = 8000, enabled = true) {
  const [state, setState] = useState({ messages: [], error: null });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!enabled) return undefined;
    let live = true;
    request("/telegram/chats", { tokenOverride: token }).then((messages) => live && setState({ messages, error: null }),
      (error) => live && setState((s) => ({ ...s, error })));
    const timer = setTimeout(() => setTick((n) => n + 1), refreshMs);
    return () => { live = false; clearTimeout(timer); };
  }, [token, tick, refreshMs, enabled]);
  return { ...state, reload: () => setTick((n) => n + 1) };
}

export default function TelegramChat({ token, title = "VoltGuard Dispatch Bot", conversation, compact = false, links = true }) {
  const { messages, error, reload } = useChats(token);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(null);
  const body = useRef(null);
  const shown = useMemo(() => messages.filter((m) => !conversation || m.recipient === conversation).slice().reverse(), [messages, conversation]);

  // Newest message at the bottom, as in Telegram.
  const newest = shown.length ? shown[shown.length - 1].notification_id : null;
  useEffect(() => { if (body.current) body.current.scrollTop = body.current.scrollHeight; }, [newest, conversation]);
  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(null), 4000);
    return () => clearTimeout(timer);
  }, [notice]);

  async function press(m, action) {
    setBusy(`${m.notification_id}:${action}`);
    setNotice(null);
    try {
      const r = await request("/telegram/press", { method: "POST", body: { notification_id: m.notification_id, action }, tokenOverride: token });
      setNotice({ ok: true, text: r.message });
    } catch (e) {
      setNotice({ ok: false, text: e.message });
    } finally {
      setBusy(null);
      reload();
    }
  }

  return (
    <div className={`tg ${compact ? "compact" : ""}`}>
      <div className="tg-head">
        <div className="tg-avatar" aria-hidden="true">VG</div>
        <div><b>{title}</b><div><small>{conversation ? `to ${conversation}` : "all your dispatch messages"}</small></div></div>
      </div>
      <div className="tg-body" aria-live="polite" ref={body}>
        {error ? <div className="notice error">{error.message}</div> : null}
        {!shown.length ? <p className="tg-empty">No messages yet. Dispatch suggestions, assignments and reminders appear here.</p> : null}
        {shown.map((m) => (
          <div key={m.notification_id} className={`tg-msg kind-${m.kind}`}>
            <div className="tg-bubble">
              <div className="tg-kind">{TITLES[m.kind] || m.kind} · <span>{m.case_id}</span></div>
              <div className="tg-text">{links ? linkify(body_(m.text)) : body_(m.text).split("\nOpen:")[0]}</div>
              <div className="tg-meta">
                {m.channel === "telegram" ? "sent to Telegram" : "simulated"} · to {m.recipient} · {new Date(m.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </div>
            </div>
            {m.answered_by ? (
              <div className="tg-answer">✓ {DONE[m.answered_action] || m.answered_action} by {m.answered_by}</div>
            ) : m.buttons?.length ? (
              <div className="tg-buttons" style={{ gridTemplateColumns: `repeat(${Math.min(m.buttons.length, 3)}, 1fr)` }}>
                {m.buttons.map((b) => (
                  <button key={b.action} disabled={!m.can_answer || busy != null} onClick={() => press(m, b.action)}
                    title={m.can_answer ? "" : "Only the addressed person or team can answer"}>
                    {busy === `${m.notification_id}:${b.action}` ? "…" : b.label}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
      {notice ? <div className={`tg-toast ${notice.ok ? "ok" : "error"}`}>{notice.text}</div> : null}
    </div>
  );
}
