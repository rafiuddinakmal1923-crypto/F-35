"""Notification service (SDD 3): assignments, reminders and escalations with a case link only.

Every message is recorded in `notification` and shown in the in-app Telegram chat (the dispatch
simulator), with its buttons. When TELEGRAM_BOT_TOKEN is set it is also sent to the recipients'
linked Telegram chats (app_user.telegram_chat_id, linked with /start CODE) and to any team or
user chat in TELEGRAM_CHAT_IDS. Buttons act through the case service (service/telegram.py).

Every message passes an output check first: anything that looks like a name, address, IC or
phone number blocks the message (SDD 8.4). Messages never carry customer names or addresses (SRS 5.2).
"""

from __future__ import annotations

import logging
import os

import httpx
import psycopg
from psycopg.types.json import Jsonb

from voltguard import config
from voltguard.agents import scrubber

log = logging.getLogger("voltguard.notify")

LABELS = {"assignment": "New inspection assigned", "reminder": "Reminder: inspection still open",
          "escalation": "Escalation: inspection overdue", "no_access": "No access recorded; revisit needed",
          "suggestion": "Dispatch suggestion waiting for approval", "report": "Report waiting for approval",
          "declined": "Team cannot attend; please reassign"}
# Buttons per message kind: the team answers field messages, the supervisor answers suggestions.
BUTTONS = {
    "assignment": [{"action": "accept", "label": "Accept"}, {"action": "enroute", "label": "On my way"},
                   {"action": "decline", "label": "Can't attend"}],
    "reminder": [{"action": "enroute", "label": "On my way"}, {"action": "decline", "label": "Can't attend"}],
    "suggestion": [{"action": "approve", "label": "Approve"}, {"action": "reject", "label": "Reject"}],
}


class BlockedMessage(Exception):
    pass


def case_link(case_id: str) -> str:
    return f"{config.public_base_url()}/#/cases/{case_id}"


def compose(kind: str, case_id: str, extra: str = "") -> str:
    text = f"VoltGuard {LABELS.get(kind, kind)}: case {case_id}. {extra}".strip()
    return f"{text}\nOpen: {case_link(case_id)}"


def output_check(text: str, extra: str = "") -> None:
    """Block names, addresses, IC and phone numbers in outgoing text (the case link itself is allowed).

    The whole message gets the pattern check; the free-text part also gets the full (Presidio) check.
    """
    found = {**scrubber.scrub(text.split("Open:")[0], presidio=False).found, **scrubber.scrub(extra).found}
    if found:
        raise BlockedMessage(f"message blocked: looks like personal details ({', '.join(found)})")


def _chat_ids() -> dict[str, str]:
    raw = os.environ.get("TELEGRAM_CHAT_IDS", "")
    return {k.strip(): v.strip() for k, v in (item.split("=", 1) for item in raw.split(",") if "=" in item)}


def token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def recipient_chats(conn: psycopg.Connection, recipient: str) -> list[str]:
    """Telegram chats for a team (its inspectors' linked chats) or a user, plus any configured chat."""
    rows = conn.execute("SELECT telegram_chat_id FROM app_user WHERE active AND telegram_chat_id IS NOT NULL "
                        "AND (user_id = %s OR (role = 'inspector' AND team = %s))", (recipient, recipient)).fetchall()
    chats = [r["telegram_chat_id"] for r in rows]
    extra = _chat_ids().get(recipient)
    return list(dict.fromkeys(chats + ([extra] if extra else [])))


def keyboard(notification_id: int, buttons: list[dict] | None, link: str | None = None) -> dict | None:
    rows = [[{"text": b["label"], "callback_data": f"{notification_id}:{b['action']}"} for b in buttons or []]]
    # Telegram refuses URL buttons that point at localhost; the link is in the text in that case.
    if link and link.startswith("https://"):
        rows.append([{"text": "Open case", "url": link}])
    rows = [r for r in rows if r]
    return {"inline_keyboard": rows} if rows else None


def telegram_call(method: str, payload: dict, timeout: float = 8) -> dict:
    r = httpx.post(f"https://api.telegram.org/bot{token()}/{method}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def send(conn: psycopg.Connection, kind: str, case_id: str, region: str, recipient: str, extra: str = "",
         buttons: list[dict] | None = None) -> dict:
    """Record one message (shown in the in-app chat) and send it to Telegram when a bot is configured.

    `recipient` is a team or user ID. `buttons` default to the kind's buttons (BUTTONS).
    """
    text = compose(kind, case_id, extra)
    output_check(text, extra)
    buttons = BUTTONS.get(kind) if buttons is None else buttons
    row = conn.execute("INSERT INTO notification (case_id, region, recipient, kind, channel, text, status, buttons) "
                       "VALUES (%s, %s, %s, %s, 'simulated', %s, 'sent', %s) RETURNING notification_id",
                       (case_id, region, recipient, kind, text, Jsonb(buttons) if buttons else None)).fetchone()
    nid = row["notification_id"]
    channel, status, sent = "simulated", "sent", []
    chats = recipient_chats(conn, recipient) if token() else []
    if chats:
        channel = "telegram"
        markup = keyboard(nid, buttons, case_link(case_id))
        for chat in chats:
            try:
                msg = telegram_call("sendMessage", {"chat_id": chat, "text": text, **({"reply_markup": markup} if markup else {})})
                sent.append({"chat_id": chat, "message_id": msg["result"]["message_id"]})
            except httpx.HTTPError as exc:
                status = f"failed: {exc.__class__.__name__}"
        conn.execute("UPDATE notification SET channel = %s, status = %s, telegram_messages = %s WHERE notification_id = %s",
                     (channel, status, Jsonb(sent), nid))
    log.info("[notify %s -> %s] %s", channel, recipient, text.replace("\n", " | "))
    return {"notification_id": nid, "channel": channel, "status": status, "text": text, "buttons": buttons}
