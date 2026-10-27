"""Job scheduler inside the API (lite profile for Celery + Redis; SDD 3 "Job scheduler").

* daily: copy the latest audit hash outside the database (NFR-12)
* every minute: dispatch reminders and escalations (FR-AG-02), registered by the dispatch agent
"""

from __future__ import annotations

import logging
import os
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

log = logging.getLogger("voltguard.scheduler")
_scheduler: BackgroundScheduler | None = None
_extra: list[tuple[str, Callable[[], None], dict]] = []


def register(name: str, fn: Callable[[], None], **trigger) -> None:
    """Modules add their periodic jobs here (e.g. register('reminders', fn, minutes=1), or a calendar
    time with register('weekly', fn, cron={'day_of_week': 'mon', 'hour': 8})); one job per name."""
    _extra[:] = [e for e in _extra if e[0] != name]
    _extra.append((name, fn, trigger))


def _safe(name: str, fn: Callable[[], None]) -> Callable[[], None]:
    def run() -> None:
        try:
            fn()
        except Exception:  # a failing periodic job must not stop the scheduler; it is logged
            log.exception("scheduled job %s failed", name)
    return run


def start() -> BackgroundScheduler | None:
    global _scheduler
    if _scheduler is not None or os.environ.get("SCHEDULER", "on") == "off":
        return _scheduler
    from voltguard import audit

    _scheduler = BackgroundScheduler(timezone="Asia/Kuala_Lumpur")
    _scheduler.add_job(_safe("audit_anchor", audit.write_anchor), "cron", hour=23, minute=55, id="audit_anchor")
    _scheduler.add_job(_safe("audit_anchor_startup", audit.write_anchor), "date", id="audit_anchor_startup")
    for name, fn, trigger in _extra:
        if "cron" in trigger:
            _scheduler.add_job(_safe(name, fn), "cron", id=name, **trigger["cron"])
        else:
            _scheduler.add_job(_safe(name, fn), "interval", id=name, **trigger)
    _scheduler.start()
    return _scheduler


def stop() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
