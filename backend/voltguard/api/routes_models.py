"""Model versions, retraining and monitoring alerts (FR-ML-01-03)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response

from voltguard import db
from voltguard.api.deps import bad_request, connection, not_found, require
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


class Period:
    """?period=day|week|month|year|custom, with from and to (YYYY-MM-DD) for custom. Default: week."""

    def __init__(self, period: str, start: date | None, end: date | None):
        self.period, self.start, self.end = period, start, end

    def build(self, conn, c: Caller) -> dict:
        try:
            return digest.build(conn, c, period=self.period, start=self.start, end=self.end)
        except digest.PeriodError as exc:
            raise bad_request(str(exc)) from exc

    def detail(self, lang: str | None = None) -> dict:
        return {"period": self.period, "from": self.start and self.start.isoformat(), "to": self.end and self.end.isoformat(),
                **({"lang": lang} if lang else {})}


# A function, not the class itself, as the dependency: FastAPI resolves a function's annotations in this module,
# while a class's __init__ annotations stay unresolved strings under `from __future__ import annotations`.
def period_params(period: str = Query("week", pattern="^(day|week|month|year|custom)$",
                                      description="day, week (default), month, year, or custom with from and to"),
                  start: date | None = Query(None, alias="from", description="First day, for period=custom"),
                  end: date | None = Query(None, alias="to", description="Last day, for period=custom")) -> Period:
    return Period(period, start, end)


@router.get("/weekly")
def weekly(lang: str = LANGS, p: Period = Depends(period_params), c: Caller = Depends(require("manager", "supervisor")), conn=Depends(connection)):
    """Summary of the caller's region for the chosen period (a week by default): zone-level energy, cases,
    outcomes and hit rates (figures), plus the report's rule-based sentences in `lang` for the dashboard."""
    from voltguard.service import digest_render

    d = p.build(conn, c)
    db.audit(conn, c.user_id, "digest.view", f"region:{c.region}", p.detail())
    return {**d, "text": digest_render.dashboard_text(d, lang)}


@router.get("/weekly/html")
def weekly_html(lang: str = LANGS, p: Period = Depends(period_params), c: Caller = Depends(require("manager", "supervisor")),
                conn=Depends(connection)):
    """The self-explanatory report page, as shown in the app and printed to PDF."""
    d = p.build(conn, c)
    db.audit(conn, c.user_id, "digest.view", f"region:{c.region}", p.detail(lang))
    return HTMLResponse(digest.render_html(d, lang), headers={"Cache-Control": "no-store"})


@router.get("/weekly/pdf")
def weekly_pdf(lang: str = LANGS, p: Period = Depends(period_params), c: Caller = Depends(require("manager", "supervisor")),
               conn=Depends(connection)):
    d = p.build(conn, c)
    db.audit(conn, c.user_id, "digest.download", f"region:{c.region}", p.detail(lang))
    name = f"{d.get('report_id', 'voltguard-summary')}{'-ms' if lang == 'ms' else ''}.pdf"
    return Response(digest.pdf_bytes(d, lang), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})


@router.post("/weekly/send")
def weekly_send(lang: str = LANGS, p: Period = Depends(period_params), c: Caller = Depends(require("manager", "supervisor")),
                conn=Depends(connection)):
    """Send the chosen period's summary to the caller now: headline and link, plus the PDF on Telegram when
    Settings allow it (weekly.send_pdf). Both pass the output check first."""
    from voltguard.service import digest_render, settings

    d = p.build(conn, c)
    document = None
    if not d.get("empty") and int(settings.thresholds(conn).get("weekly", {}).get("send_pdf", 1)):
        data = digest_render.pdf_bytes(d, lang)
        digest_render.check_document(data)
        document = (f"{d['report_id']}.pdf", data)
    label = None if p.period == "week" else digest_render.message_label(d, lang)
    return notify.send(conn, "weekly", None, c.region, c.user_id, digest_render.headline(d, lang), buttons=[], document=document,
                       label=label, page=digest_render.page_link(d))
