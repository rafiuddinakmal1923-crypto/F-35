"""Telegram dispatch bot (SRS 5.1-5.2, FR-AG-02): buttons, refusals, linking, and no customer details."""

from __future__ import annotations

import pytest

from tests.conftest import login
from voltguard.service import notify, telegram


def new_case(api, premise: str) -> str:
    """A manual NOR case on this premise, or on the next one along the street when it already has an open case."""
    zone, seq = premise.rsplit("-", 1)
    for n in range(int(seq), int(seq) + 40):
        r = api.post("/cases", json={"premise_id": f"{zone}-{n:03d}"}, headers=login(api, "analyst.nor"))
        if r.status_code == 200:
            return r.json()["case_id"]
    raise AssertionError(r.text)


def message(api, user: str, case_id: str, kind: str) -> dict:
    chats = api.get("/telegram/chats", headers=login(api, user)).json()
    return next(m for m in chats if m["case_id"] == case_id and m["kind"] == kind)


def test_FR_AG_02_supervisor_approves_and_team_answers_from_the_chat(api, pg):
    cid = new_case(api, "P-NOR-002-005")
    sup, insp = login(api, "supervisor.nor"), login(api, "inspector.c")
    suggestion = message(api, "supervisor.nor", cid, "suggestion")
    assert suggestion["can_answer"] and {b["action"] for b in suggestion["buttons"]} == {"approve", "reject"}
    # Only the addressed supervisor answers; an inspector cannot approve dispatch.
    assert api.post("/telegram/press", json={"notification_id": suggestion["notification_id"], "action": "approve"}, headers=insp).status_code in (400, 403)
    r = api.post("/telegram/press", json={"notification_id": suggestion["notification_id"], "action": "approve"}, headers=sup)
    assert r.status_code == 200, r.text
    case = api.get(f"/cases/{cid}", headers=sup).json()
    assert case["case"]["status"] == "assigned" and case["dispatch_suggestion"]["status"] == "approved"
    # A message is answered once.
    again = api.post("/telegram/press", json={"notification_id": suggestion["notification_id"], "action": "reject"}, headers=sup)
    assert again.status_code == 400 and "Already answered" in again.json()["message"]

    assignment = message(api, "inspector.c", cid, "assignment")
    assert assignment["can_answer"] and assignment["recipient"] == "T-NOR-C"
    assert api.post("/telegram/press", json={"notification_id": assignment["notification_id"], "action": "accept"},
                    headers=login(api, "inspector.a")).status_code in (400, 403)          # another team
    assert api.post("/telegram/press", json={"notification_id": assignment["notification_id"], "action": "accept"}, headers=insp).status_code == 200
    events = [e["event_type"] for e in api.get(f"/cases/{cid}", headers=sup).json()["events"]]
    assert "accepted" in events
    rows = api.get("/audit", params={"action": "telegram."}, headers=login(api, "auditor")).json()["rows"]
    assert {"telegram.action"} <= {r["action"] for r in rows}


def test_FR_AG_02_cannot_attend_tells_the_supervisor(api, pg):
    cid = new_case(api, "P-NOR-002-020")
    sup, insp = login(api, "supervisor.nor"), login(api, "inspector.c")
    api.post("/telegram/press", json={"notification_id": message(api, "supervisor.nor", cid, "suggestion")["notification_id"], "action": "approve"}, headers=sup)
    r = api.post("/telegram/press", json={"notification_id": message(api, "inspector.c", cid, "assignment")["notification_id"], "action": "decline"},
                 headers=insp)
    assert r.status_code == 200
    declined = message(api, "supervisor.nor", cid, "declined")
    assert "T-NOR-C cannot attend" in declined["text"] and not declined["buttons"]


def test_SRS_5_2_dispatch_messages_hold_no_customer_details(api, pg):
    from tests.test_cases import fake_names

    names = fake_names(pg[0])
    for user in ("supervisor.nor", "inspector.c", "supervisor.cen"):
        for m in api.get("/telegram/chats", headers=login(api, user)).json():
            assert "FAKE" not in m["text"] and not any(n in m["text"] for n in names), m["text"]


def test_FR_AG_02_real_bot_links_a_chat_and_answers_a_button(api, pg, monkeypatch):
    """The polling bot path, with Telegram's HTTP API replaced by a recorder."""
    sent = []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(notify, "telegram_call", lambda method, payload, timeout=8: (
        sent.append((method, payload)) or {"ok": True, "result": {"message_id": len(sent)}}))
    code = api.post("/telegram/link-code", headers=login(api, "supervisor.nor")).json()["code"]
    telegram.handle_update({"update_id": 1, "message": {"chat": {"id": 5551}, "text": f"/start {code}"}})
    assert "Linked to supervisor.nor" in sent[-1][1]["text"]
    assert api.get("/telegram/status", headers=login(api, "supervisor.nor")).json()["linked"]

    cid = new_case(api, "P-NOR-002-035")           # the suggestion now also goes to the linked chat, with buttons
    out = next(p for m, p in sent if m == "sendMessage" and cid in p.get("text", "") and "reply_markup" in p)
    button = out["reply_markup"]["inline_keyboard"][0][0]
    assert button["text"] == "Approve" and str(out["chat_id"]) == "5551"
    telegram.handle_update({"update_id": 2, "callback_query": {"id": "q1", "from": {"id": 5551}, "data": button["callback_data"]}})
    assert any(m == "answerCallbackQuery" and "approved" in p["text"] for m, p in sent)
    assert api.get(f"/cases/{cid}", headers=login(api, "supervisor.nor")).json()["case"]["status"] == "assigned"
    # An unlinked chat cannot press buttons.
    telegram.handle_update({"update_id": 3, "callback_query": {"id": "q2", "from": {"id": 999}, "data": button["callback_data"]}})
    assert "Link this chat first" in sent[-1][1]["text"]
    telegram.handle_update({"update_id": 4, "message": {"chat": {"id": 5551}, "text": "/unlink"}})
    assert not api.get("/telegram/status", headers=login(api, "supervisor.nor")).json()["linked"]


@pytest.mark.parametrize("user", ["analyst.nor", "manager.nor", "auditor"])
def test_FR_AD_01_chat_is_for_supervisors_and_inspectors(api, user):
    assert api.get("/telegram/chats", headers=login(api, user)).status_code == 403
