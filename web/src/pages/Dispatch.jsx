// Dispatch (FR-AG-02, SRS 5.1, NFR-16): the Telegram dispatch chat per conversation, linking a real
// Telegram chat, and remote sign-out of a lost inspector phone.
import { useMemo, useState } from "react";
import { get, post, session } from "../api.js";
import { ErrorBox, useLoad } from "../components/Common.jsx";
import TelegramChat, { useChats } from "../components/TelegramChat.jsx";

function LinkTelegram() {
  const status = useLoad(() => get("/telegram/status"), []);
  const [code, setCode] = useState(null);
  const [error, setError] = useState(null);
  async function newCode() {
    setError(null);
    try {
      setCode(await post("/telegram/link-code"));
    } catch (e) {
      setError(e);
    }
  }
  const s = status.data;
  return (
    <div className="card stack">
      <h2>Telegram</h2>
      <ErrorBox error={status.error || error} />
      {s ? (
        <div className="row">
          <span className={`chip ${s.bot_configured ? "ok" : "warn"}`}>{s.bot_configured ? "bot connected" : "simulated in the app"}</span>
          <span className={`chip ${s.linked ? "ok" : ""}`}>{s.linked ? "your chat is linked" : "your chat is not linked"}</span>
        </div>
      ) : null}
      <small>
        {s?.bot_configured
          ? "Messages also go to linked Telegram chats; a button pressed there or here answers the message once."
          : "No bot token is set (TELEGRAM_BOT_TOKEN in .env), so the bot runs inside the app: messages and buttons appear here."}
      </small>
      <button onClick={newCode}>Link Telegram</button>
      {code ? (
        <div className="notice">
          Send <code>/start {code.code}</code> to the bot within 15 minutes.
          {!code.bot_configured ? <div><small>The code works once a bot token is set and the API restarted.</small></div> : null}
        </div>
      ) : null}
    </div>
  );
}

function Devices() {
  const { user } = session();
  const users = useLoad(() => get("/users"), []);
  const [done, setDone] = useState({});
  const [error, setError] = useState(null);
  const inspectors = (users.data || []).filter((u) => u.role === "inspector" && (user.region === "*" || u.region === user.region));
  async function signOutPhone(id) {
    if (!window.confirm(`Sign out every device of ${id}? Their phone wipes its case data at the next connection.`)) return;
    setError(null);
    try {
      await post(`/users/${id}/sign-out`);
      setDone((d) => ({ ...d, [id]: true }));
    } catch (e) {
      setError(e);
    }
  }
  return (
    <div className="card stack">
      <h2>Inspector phones</h2>
      <small>Lost or stolen phone: sign the inspector out everywhere. The app wipes its encrypted case data at the next connection (NFR-16).</small>
      <ErrorBox error={users.error || error} />
      <table><tbody>
        {inspectors.map((u) => (
          <tr key={u.user_id}><td>{u.user_id}</td><td><small>{u.team} · {u.region}</small></td>
            <td className="num">{done[u.user_id] ? <span className="chip ok">signed out</span>
              : <button className="danger" onClick={() => signOutPhone(u.user_id)}>Sign out phone</button>}</td></tr>
        ))}
      </tbody></table>
    </div>
  );
}

export default function Dispatch() {
  const { user } = session();
  const isSupervisor = user?.role === "supervisor";
  const { messages } = useChats(undefined, 8000, isSupervisor);
  const conversations = useMemo(() => {
    const seen = new Map([[user.user_id, 0]]);
    messages.forEach((m) => seen.set(m.recipient, (seen.get(m.recipient) || 0) + (m.can_answer ? 1 : 0)));
    return [...seen.entries()];
  }, [messages, user.user_id]);
  const [conversation, setConversation] = useState(user.user_id);

  return (
    <div className="stack">
      <div>
        <h1>Dispatch</h1>
        <small>Dispatch suggestions, assignments, reminders and escalations, as the Telegram bot sends them. Messages hold a case ID and link only.</small>
      </div>
      <div className="dispatch-grid">
        {isSupervisor ? (
          <>
            <div className="card tg-list">
              {conversations.map(([who, waiting]) => (
                <button key={who} className={conversation === who ? "active" : ""} onClick={() => setConversation(who)}>
                  <span>{who === user.user_id ? `You (${who})` : `Team ${who}`}</span>
                  {waiting ? <span className="chip risk">{waiting}</span> : null}
                </button>
              ))}
              <small style={{ padding: "8px 10px" }}>Team chats are read-only here: the inspectors answer them.</small>
            </div>
            <TelegramChat conversation={conversation} />
          </>
        ) : null}
        <div className="stack">
          {isSupervisor ? <LinkTelegram /> : null}
          <Devices />
        </div>
      </div>
    </div>
  );
}
