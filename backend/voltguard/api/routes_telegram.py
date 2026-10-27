"""Telegram dispatch bot endpoints: the in-app chat (simulator), its buttons, and chat linking."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from voltguard.api.deps import bad_request, require
from voltguard.db import Caller
from voltguard.service import notify, telegram

router = APIRouter(tags=["telegram"])
CHAT_ROLES = ("supervisor", "inspector")


class Press(BaseModel):
    notification_id: int
    action: str


@router.get("/telegram/status")
def status(c: Caller = Depends(require(*CHAT_ROLES))):
    return {"bot_configured": bool(notify.token()), "linked": telegram.link_status(c.user_id)}


@router.get("/telegram/chats")
def chats(limit: int = Query(100, le=300), c: Caller = Depends(require(*CHAT_ROLES))):
    """Messages addressed to the caller (or the caller's team), newest first, with their buttons."""
    return telegram.chats_for(c, limit)


@router.post("/telegram/press")
def press(body: Press, c: Caller = Depends(require(*CHAT_ROLES))):
    """Press a message button from the in-app chat: the same handler the real bot uses."""
    result = telegram.handle_action(c, body.notification_id, body.action)
    if not result["ok"]:
        raise bad_request(result["message"], code="refused")
    return result


@router.post("/telegram/link-code")
def link_code(c: Caller = Depends(require(*CHAT_ROLES))):
    """A one-time code to send to the bot as /start CODE (valid 15 minutes)."""
    return telegram.new_link_code(c.user_id)


@router.post("/telegram/unlink")
def unlink(c: Caller = Depends(require(*CHAT_ROLES))):
    telegram.unlink(c.user_id)
    return {"linked": False}
