"""Telegram dispatch bot (SRS 5.1-5.2, FR-AG-02): buttons on dispatch messages, chat linking, commands.

The same handler serves both the real bot (long polling, when TELEGRAM_BOT_TOKEN is set) and the
in-app chat simulator (POST /telegram/sim/press), so a demo without internet behaves the same way.

- Supervisor, on a dispatch suggestion: Approve / Reject -> the case service's decide_suggestion.
- Inspector team, on an assignment or reminder: Accept / On my way / Can't attend -> a case event;
  "Can't attend" also tells the supervisors to reassign.
- Commands: /start CODE (link this chat to a VoltGuard account), /mycases, /whoami, /unlink, /help.

Every action runs as the linked user on that user's own database connection (role and region
rules apply), is written to the case history and the audit log, and answers each message once.
Messages and replies carry case IDs and links only, never customer details.
"""

from __future__ import annotations

import logging
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone

import httpx

from voltguard import db
from voltguard.db import Caller
from voltguard.service import cases, notify

log = logging.getLogger("voltguard.telegram")
CODE_TTL = timedelta(minutes=15)
DONE = {"accept": "accepted", "enroute": "on the way", "decline": "cannot attend", "approve": "approved", "reject": "rejected"}
HELP = ("VoltGuard dispatch bot. Messages hold a case ID and a link, never customer details.\n"
        "/mycases - your open cases\n/whoami - the account linked to this chat\n/unlink - stop messages to this chat\n"
        "To link: in the VoltGuard web app open Dispatch chat -> Link Telegram, then send /start CODE here.")


class ActionRefused(Exception):
    pass


# --------------------------------------------------------------------------- linking

def new_link_code(user_id: str) -> dict:
    code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    expires = datetime.now(timezone.utc) + CODE_TTL
    with db.admin_connection() as conn:
        with conn.transaction():
            conn.execute("DELETE FROM telegram_link_code WHERE user_id = %s OR expires_at < now()", (user_id,))
            conn.execute("INSERT INTO telegram_link_code (code, user_id, expires_at) VALUES (%s, %s, %s)", (code, user_id, expires))
            db.audit(conn, user_id, "telegram.link_code", f"user:{user_id}", None)
    return {"code": code, "expires_at": expires.isoformat(), "bot_configured": bool(notify.token())}


def redeem(code: str, chat_id: str) -> dict | None:
    with db.admin_connection() as conn:
        with conn.transaction():
            row = conn.execute("DELETE FROM telegram_link_code WHERE code = %s AND expires_at > now() RETURNING user_id",
                               (code.strip().upper(),)).fetchone()
            if not row:
                return None
            # One account per chat: a chat linked before is moved to the new account.
            conn.execute("UPDATE app_user SET telegram_chat_id = NULL WHERE telegram_chat_id = %s", (chat_id,))
            user = conn.execute("UPDATE app_user SET telegram_chat_id = %s WHERE user_id = %s AND active "
                                "RETURNING user_id, role, region, team", (chat_id, row["user_id"])).fetchone()
            if user:
                db.audit(conn, user["user_id"], "telegram.link", f"user:{user['user_id']}", None)
            return user


def unlink(user_id: str) -> None:
    with db.admin_connection() as conn:
        with conn.transaction():
            conn.execute("UPDATE app_user SET telegram_chat_id = NULL WHERE user_id = %s", (user_id,))
            db.audit(conn, user_id, "telegram.unlink", f"user:{user_id}", None)


def user_for_chat(chat_id: str) -> dict | None:
    with db.admin_connection() as conn:
        return conn.execute("SELECT user_id, role, region, team FROM app_user WHERE telegram_chat_id = %s AND active",
                            (str(chat_id),)).fetchone()


def link_status(user_id: str) -> bool:
    with db.admin_connection() as conn:
        row = conn.execute("SELECT telegram_chat_id IS NOT NULL AS linked FROM app_user WHERE user_id = %s", (user_id,)).fetchone()
    return bool(row and row["linked"])


# --------------------------------------------------------------------------- buttons

def is_recipient(caller: Caller, recipient: str) -> bool:
    return recipient == caller.user_id or (caller.role == "inspector" and caller.team == recipient)


def handle_action(caller: Caller, notification_id: int, action: str) -> dict:
    """Run one button press as `caller`. Returns {"ok", "message", "notification"}; never raises for refusals."""
    try:
        with db.app_connection(caller) as conn:
            n = conn.execute("SELECT * FROM notification WHERE notification_id = %s FOR UPDATE", (notification_id,)).fetchone()
            if not n:
                raise ActionRefused("Message not found in your region")
            if not is_recipient(caller, n["recipient"]):
                raise ActionRefused("This message is not addressed to you")
            if action not in {b["action"] for b in n["buttons"] or []}:
                raise ActionRefused("This message has no such button")
            if n["answered_by"]:
                raise ActionRefused(f"Already answered: {DONE.get(n['answered_action'], n['answered_action'])} by {n['answered_by']}")
            _perform(conn, caller, n, action)
            answered = conn.execute("UPDATE notification SET answered_by = %s, answered_action = %s, answered_at = now() "
                                    "WHERE notification_id = %s RETURNING *", (caller.user_id, action, notification_id)).fetchone()
            db.audit(conn, caller.user_id, "telegram.action", f"case:{n['case_id']}",
                     {"notification_id": notification_id, "action": action, "channel": n["channel"]})
    except ActionRefused as exc:
        return {"ok": False, "message": str(exc)}
    except cases.CaseError as exc:
        return {"ok": False, "message": exc.message}
    _edit_telegram(answered)
    return {"ok": True, "message": f"Case {answered['case_id']}: {DONE[action]}.", "notification": answered}


def _perform(conn, caller: Caller, n: dict, action: str) -> None:
    case_id = n["case_id"]
    if action in ("approve", "reject"):
        cases.decide_suggestion(conn, caller, case_id, approve=action == "approve")
        return
    case = cases._case(conn, case_id, lock=True)
    cases._require_assigned_inspector(caller, case)
    if case["status"] != "assigned":
        raise ActionRefused(f"Case {case_id} is '{case['status']}', not waiting for a visit")
    cases._event(conn, case, caller.user_id, {"accept": "accepted", "enroute": "en_route", "decline": "declined"}[action],
                 {"via": "telegram" if n["channel"] == "telegram" else "telegram-sim"})
    if action == "decline":
        for sup in conn.execute("SELECT user_id FROM app_user WHERE role = 'supervisor' AND region = %s AND active",
                                (case["region"],)).fetchall():
            notify.send(conn, "declined", case_id, case["region"], sup["user_id"], f"Team {caller.team} cannot attend.", buttons=[])


def _edit_telegram(n: dict) -> None:
    """Replace the buttons of every copy of an answered message with who answered it."""
    if not notify.token():
        return
    for m in n.get("telegram_messages") or []:
        try:
            notify.telegram_call("editMessageText", {"chat_id": m["chat_id"], "message_id": m["message_id"],
                                                     "text": f"{n['text']}\n\n{DONE[n['answered_action']].capitalize()} by {n['answered_by']}."})
        except httpx.HTTPError as exc:
            log.warning("could not edit Telegram message %s: %s", m, exc.__class__.__name__)


# --------------------------------------------------------------------------- reading (in-app chat and /mycases)

def chats_for(caller: Caller, limit: int = 100) -> list[dict]:
    """Messages the caller receives; supervisors also see their region's team chats (read-only)."""
    with db.app_connection(caller) as conn:
        if caller.role == "supervisor":
            rows = conn.execute("SELECT * FROM notification WHERE recipient = %s OR recipient IN (SELECT team_id FROM team) "
                                "ORDER BY notification_id DESC LIMIT %s", (caller.user_id, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM notification WHERE recipient = %s OR recipient = %s ORDER BY notification_id DESC LIMIT %s",
                                (caller.user_id, caller.team or "", limit)).fetchall()
    for r in rows:
        r["can_answer"] = bool(r["buttons"]) and not r["answered_by"] and is_recipient(caller, r["recipient"])
    return rows


def my_cases_text(user: dict) -> str:
    caller = Caller(user["user_id"], user["role"], user["region"], user["team"])
    with db.app_connection(caller) as conn:
        if caller.role == "inspector":
            rows = conn.execute("SELECT case_id, status, joint_operation FROM inspection_case WHERE status = 'assigned' "
                                "ORDER BY assigned_at").fetchall()
            lines = [f"{r['case_id']} ({'joint operation' if r['joint_operation'] else r['status']}) {notify.case_link(r['case_id'])}"
                     for r in rows]
        elif caller.role == "supervisor":
            rows = conn.execute("SELECT s.case_id, s.suggested_team FROM dispatch_suggestion s JOIN inspection_case c USING (case_id) "
                                "WHERE s.status = 'pending' AND c.status = 'new' ORDER BY s.case_id").fetchall()
            lines = [f"{r['case_id']}: suggestion {r['suggested_team']} waiting {notify.case_link(r['case_id'])}" for r in rows]
        else:
            return "Case lists in this chat are for inspectors and supervisors."
    return "\n".join(lines) if lines else "No open items."


# --------------------------------------------------------------------------- long polling (real bot)

def handle_update(update: dict) -> None:
    if "callback_query" in update:
        q = update["callback_query"]
        user = user_for_chat(str(q["from"]["id"]))
        text = "Link this chat first: send /start CODE (code from the VoltGuard web app)."
        if user:
            try:
                nid, action = q.get("data", "").split(":", 1)
                result = handle_action(Caller(user["user_id"], user["role"], user["region"], user["team"]), int(nid), action)
                text = result["message"]
            except ValueError:
                text = "Unknown button"
        notify.telegram_call("answerCallbackQuery", {"callback_query_id": q["id"], "text": text[:190], "show_alert": False})
        return
    message = update.get("message") or {}
    chat_id, text = str(message.get("chat", {}).get("id", "")), (message.get("text") or "").strip()
    if not chat_id or not text.startswith("/"):
        return
    command, _, arg = text.partition(" ")
    command = command.split("@")[0].lower()
    user = user_for_chat(chat_id)
    if command == "/start" and arg:
        linked = redeem(arg, chat_id)
        reply = (f"Linked to {linked['user_id']} ({linked['role']}). You will get dispatch messages here." if linked
                 else "That code is unknown or expired. Get a new one in the web app (Dispatch chat -> Link Telegram).")
    elif command in ("/start", "/help"):
        reply = HELP
    elif not user:
        reply = "This chat is not linked. " + HELP
    elif command == "/whoami":
        reply = f"{user['user_id']} · {user['role']} · {user['region']}" + (f" · {user['team']}" if user["team"] else "")
    elif command == "/mycases":
        reply = my_cases_text(user)
    elif command == "/unlink":
        unlink(user["user_id"])
        reply = "Unlinked. No more messages to this chat."
    else:
        reply = HELP
    notify.telegram_call("sendMessage", {"chat_id": chat_id, "text": reply})


def _offset() -> int:
    with db.admin_connection() as conn:
        row = conn.execute("SELECT value FROM telegram_state WHERE key = 'offset'").fetchone()
    return int(row["value"]) if row else 0


def _save_offset(offset: int) -> None:
    with db.admin_connection() as conn:
        conn.execute("INSERT INTO telegram_state (key, value) VALUES ('offset', %s) ON CONFLICT (key) DO UPDATE SET value = excluded.value",
                     (str(offset),))


def poll_once(timeout: int = 25) -> int:
    offset = _offset()
    updates = notify.telegram_call("getUpdates", {"offset": offset, "timeout": timeout,
                                                  "allowed_updates": ["message", "callback_query"]}, timeout=timeout + 10)["result"]
    for update in updates:
        try:
            handle_update(update)
        except Exception:  # one bad update must not stop the bot
            log.exception("Telegram update %s failed", update.get("update_id"))
        _save_offset(update["update_id"] + 1)
    return len(updates)


_stop = threading.Event()
_thread: threading.Thread | None = None


def start_polling() -> bool:
    """Start the bot in a background thread (API process) when a token is set and polling is not off."""
    global _thread
    if not notify.token() or os.environ.get("TELEGRAM_POLL", "on").lower() == "off" or (_thread and _thread.is_alive()):
        return False
    _stop.clear()

    def loop() -> None:
        log.info("Telegram bot polling started")
        while not _stop.is_set():
            try:
                poll_once()
            except Exception as exc:  # network or token problems: log and retry, the API keeps working
                log.warning("Telegram polling failed (%s); retrying in 10 s", exc.__class__.__name__)
                _stop.wait(10)

    _thread = threading.Thread(target=loop, name="telegram-bot", daemon=True)
    _thread.start()
    return True


def stop_polling() -> None:
    _stop.set()
