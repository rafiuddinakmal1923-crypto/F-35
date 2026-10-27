"""Notification service (SDD 3): assignments, reminders and escalations with a case link only.

Telegram when TELEGRAM_BOT_TOKEN is set (chat IDs per team or user from TELEGRAM_CHAT_IDS or
app_user.telegram_chat_id), otherwise a console notifier that logs the message. Every message
passes an output check first: anything that looks like a name, address, IC or phone number
blocks the message (SDD 8.4). Messages never carry customer names or addresses (SRS 5.2).
"""

from __future__ import annotations

import logging
import os

import httpx
import psycopg

from voltguard import config
from voltguard.agents import scrubber

log = logging.getLogger("voltguard.notify")


class BlockedMessage(Exception):
    pass


def case_link(case_id: str) -> str:
    return f"{config.public_base_url()}/#/cases/{case_id}"


def compose(kind: str, case_id: str, extra: str = "") -> str:
    labels = {"assignment": "New inspection assigned", "reminder": "Reminder: inspection still open",
              "escalation": "Escalation: inspection overdue", "no_access": "No access recorded; revisit needed",
              "suggestion": "Dispatch suggestion waiting for approval", "report": "Report waiting for approval"}
    text = f"VoltGuard {labels.get(kind, kind)}: case {case_id}. {extra}".strip()
    return f"{text}\nOpen: {case_link(case_id)}"


def output_check(text: str) -> None:
    """Block names, addresses, IC and phone numbers in outgoing text (the case link itself is allowed)."""
    without_link = text.split("Open:")[0]
    result = scrubber.scrub(without_link)
    if result.changed:
        raise BlockedMessage(f"message blocked: looks like personal details ({', '.join(result.found)})")


def _chat_ids() -> dict[str, str]:
    raw = os.environ.get("TELEGRAM_CHAT_IDS", "")
    return {k.strip(): v.strip() for k, v in (item.split("=", 1) for item in raw.split(",") if "=" in item)}


def send(conn: psycopg.Connection, kind: str, case_id: str, region: str, recipient: str, extra: str = "") -> dict:
    """Send (or log) one message and record it in `notification`. `recipient` is a team or user ID."""
    text = compose(kind, case_id, extra)
    output_check(text)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel, status = "console", "sent"
    chat = _chat_ids().get(recipient)
    if token and chat:
        try:
            httpx.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat, "text": text}, timeout=10).raise_for_status()
            channel = "telegram"
        except httpx.HTTPError as exc:
            channel, status = "telegram", f"failed: {exc.__class__.__name__}"
    if channel == "console":
        log.info("[notify -> %s] %s", recipient, text.replace("\n", " | "))
    row = conn.execute("INSERT INTO notification (case_id, region, recipient, kind, channel, text, status) "
                       "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING notification_id",
                       (case_id, region, recipient, kind, channel, text, status)).fetchone()
    return {"notification_id": row["notification_id"], "channel": channel, "status": status, "text": text}
