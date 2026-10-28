"""Model versions, retraining and monitoring alerts (FR-ML-01-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response

from voltguard import db
from voltguard.api.deps import connection, not_found, require
from voltguard.db import Caller
from voltguard.service import digest, jobs, learning, notify

router = APIRouter(tags=["models"])


@router.get("/models")
def models(c: Caller = Depends(require("manager", "data_scientist")), conn=Depends(connection)):
    """Each version with model-ranked and random-sample hit rates side by side (FR-ML-02)."""
    return {"versions": learning.versions(conn)}


@router.post("/models/retrain")
def retrain(wait: bool = False, c: Caller = Depends(require("data_scientist"))):
    return {"job_id": jobs.submit("retrain", c.user_id, lambda progress: learning.retrain(c.user_id, progress), wait=wait)}


@router.get("/alerts")
def alerts(c: Caller = Depends(require("data_scientist", "admin", "manager")), conn=Depends(connection)):
    return conn.execute("SELECT alert_id, ts, kind, severity, region, message, detail, acknowledged_by FROM alert "
                        "ORDER BY alert_id DESC LIMIT 100").fetchall()


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: int, c: Caller = Depends(require("data_scientist", "admin")), conn=Depends(connection)):
    row = conn.execute("UPDATE alert SET acknowledged_by = %s WHERE alert_id = %s RETURNING alert_id", (c.user_id, alert_id)).fetchone()
    if not row:
        raise not_found("No such alert")
    db.audit(conn, c.user_id, "alert.acknowledge", f"alert:{alert_id}", None)
    return row


LANGS = Query("en", pattern="^(en|ms)$", description="Report language: en or ms (Bahasa Melayu)")


@router.get("/weekly")
def weekly(lang: str = LANGS, c: Caller = Depends(require("manager", "supervisor")), conn=Depends(connection)):
    """Weekly summary of the caller's region: zone-level energy, cases, outcomes and hit rates (figures), plus the
    report's rule-based sentences in `lang` for the dashboard."""
    from voltguard.service import digest_render

    d = digest.build(conn, c)
    db.audit(conn, c.user_id, "digest.view", f"region:{c.region}", None)
    return {**d, "text": digest_render.dashboard_text(d, lang)}


@router.get("/weekly/html")
def weekly_html(lang: str = LANGS, c: Caller = Depends(require("manager", "supervisor")), conn=Depends(connection)):
    """The self-explanatory report page, as shown in the app and printed to PDF."""
    d = digest.build(conn, c)
    db.audit(conn, c.user_id, "digest.view", f"region:{c.region}", {"lang": lang})
    return HTMLResponse(digest.render_html(d, lang), headers={"Cache-Control": "no-store"})


@router.get("/weekly/pdf")
def weekly_pdf(lang: str = LANGS, c: Caller = Depends(require("manager", "supervisor")), conn=Depends(connection)):
    d = digest.build(conn, c)
    db.audit(conn, c.user_id, "digest.download", f"region:{c.region}", {"lang": lang})
    name = f"{d.get('report_id', 'voltguard-weekly')}{'-ms' if lang == 'ms' else ''}.pdf"
    return Response(digest.pdf_bytes(d, lang), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})


@router.post("/weekly/send")
def weekly_send(lang: str = LANGS, c: Caller = Depends(require("manager", "supervisor")), conn=Depends(connection)):
    """Send this week's summary to the caller now: headline and link, plus the PDF on Telegram when Settings
    allow it (weekly.send_pdf). Both pass the output check first."""
    from voltguard.service import digest_render, settings

    d = digest.build(conn, c)
    document = None
    if not d.get("empty") and int(settings.thresholds(conn).get("weekly", {}).get("send_pdf", 1)):
        data = digest_render.pdf_bytes(d, lang)
        digest_render.check_document(data)
        document = (f"{d['report_id']}.pdf", data)
    return notify.send(conn, "weekly", None, c.region, c.user_id, digest_render.headline(d, lang), buttons=[], document=document)
