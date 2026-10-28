"""Agent endpoints (SDD 7-8): report drafts and approvals, chat, query service, similar cases.

Every agent runs with the identity of the user it acts for, so roles, region limits and audit
apply exactly as for that user (SDD 8.4).
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field

from voltguard import config
from voltguard.agents import chatbot, embed, guardrails, llm, rag, report
from voltguard.api.deps import ApiError, bad_request, connection, forbidden, require
from voltguard.db import Caller
from voltguard.service import cases

router = APIRouter(tags=["agents"])


def _call(fn, *args):
    try:
        return fn(*args)
    except report.ReportError as exc:
        raise ApiError(exc.status, exc.code, exc.message) from exc
    except (guardrails.OutputBlocked, llm.PromptBlocked) as exc:
        raise ApiError(422, "blocked", str(exc)) from exc


class Chat(BaseModel):
    agent: Literal["analyst", "field"]
    message: str = Field(..., min_length=1, max_length=1000)


class Query(BaseModel):
    template: str
    params: dict = {}


@router.get("/agents/status")
def agent_status(c: Caller = Depends(require("manager", "analyst", "supervisor", "inspector", "admin", "data_scientist"))):
    return {"llm_mode": config.llm_mode(), "llm_available": llm.available(), "report_mode": config.report_mode(),
            "embedding_model": embed.model_name(), "tools": guardrails.TOOLS}


@router.post("/agents/report/{case_id}")
def draft_report(case_id: str, c: Caller = Depends(require("analyst")), conn=Depends(connection)):
    return _call(report.draft_for_case, conn, c, case_id)


@router.get("/reports/{report_id}")
def get_report(report_id: str, c: Caller = Depends(require("analyst", "manager", "supervisor")), conn=Depends(connection)):
    return _call(report.get_report, conn, c, report_id)


@router.post("/reports/{report_id}/approve-content")
def approve_content(report_id: str, c: Caller = Depends(require("analyst")), conn=Depends(connection)):
    return _call(report.approve_content, conn, c, report_id)


@router.post("/reports/{report_id}/approve-export")
def approve_export(report_id: str, c: Caller = Depends(require("manager")), conn=Depends(connection)):
    return _call(report.approve_export, conn, c, report_id)


@router.get("/reports/{report_id}/pdf")
def report_pdf(report_id: str, c: Caller = Depends(require("analyst", "manager")), conn=Depends(connection)):
    data = _call(report.get_pdf, conn, c, report_id)
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{report_id}.pdf"',
                                                                 "Cache-Control": "no-store"})


@router.post("/agents/chat")
def chat(body: Chat, c: Caller = Depends(require("manager", "analyst", "inspector", "supervisor")), conn=Depends(connection)):
    if body.agent == "analyst":
        if c.role not in ("manager", "analyst"):
            raise forbidden("The analyst chatbot answers managers and analysts")
        result = _call(chatbot.ask, conn, c, body.message)
        if result.get("query") or result.get("refused"):
            return result
        # Not a numeric question ("What does Act 447 say about meter tampering?"): try the approved documents,
        # through the document assistant and its own checks. Keep the chatbot's reply when they hold nothing.
        docs = _call(rag.answer, conn, c, body.message, "field_assistant")
        return {**docs, "answered_by": "documents"} if docs["sources"] else result
    return _call(rag.answer, conn, c, body.message, "field_assistant")


@router.get("/query/templates")
def query_templates(c: Caller = Depends(require("manager", "analyst"))):
    return {k: {"description": t.description, "params": dict(zip(t.params, t.defaults))} for k, t in chatbot.TEMPLATES.items()}


@router.post("/query")
def query(body: Query, c: Caller = Depends(require("manager", "analyst")), conn=Depends(connection)):
    """Read-only query on results views, limited by row-level security to the caller's region."""
    try:
        return chatbot.run_query(conn, c, body.template, body.params)
    except (chatbot.QueryError, ValueError, TypeError) as exc:
        raise bad_request(str(exc)) from exc


@router.get("/cases/{case_id}/similar")
def similar(case_id: str, c: Caller = Depends(require("analyst", "inspector", "supervisor")), conn=Depends(connection)):
    try:
        cases.case_detail(conn, c, case_id)       # same access rule as opening the case
    except cases.CaseError as exc:
        raise ApiError(exc.status, exc.code, exc.message) from exc
    return {"case_id": case_id, "similar": rag.similar_cases(conn, c, case_id)}
