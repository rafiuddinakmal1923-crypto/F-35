"""FastAPI application: the only way clients and agents reach the data (SDD 7).

Served behind the proxy at /api (the proxy strips the prefix). JSON over HTTPS, dates in ISO
8601 (Asia/Kuala_Lumpur), errors as {"code", "message"}.
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from voltguard import __version__, config, db
from voltguard.api import routes_admin, routes_auth, routes_zones
from voltguard.service import scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
OPTIONAL_ROUTERS = ("routes_cases", "routes_agents", "routes_models", "routes_telegram")
_requests: Counter = Counter()
_latency: Counter = Counter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from voltguard.agents import dispatch

    from voltguard.service import digest, monitoring, telegram

    scheduler.register("dispatch_reminders", dispatch.run_reminders, minutes=1)
    scheduler.register("unusual_access", monitoring.check_unusual_access, minutes=15)
    scheduler.register("weekly_summary", digest.send_weekly, cron={"day_of_week": "mon", "hour": 7, "minute": 45})
    scheduler.start()
    telegram.start_polling()            # only when TELEGRAM_BOT_TOKEN is set
    yield
    telegram.stop_polling()
    scheduler.stop()
    db.close_pools()


def create_app() -> FastAPI:
    app = FastAPI(title="VoltGuard AI", version=__version__, lifespan=lifespan,
                  description="R0 prototype API. Scores are risk rankings, not findings of theft.")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:8080"],
                       allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "error", "message": str(exc.detail)}
        return JSONResponse(detail, status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse({"code": "invalid_request", "message": "; ".join(e.get("msg", "") for e in exc.errors())[:500]},
                            status_code=422)

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        _requests[(request.method, path, response.status_code)] += 1
        _latency[(request.method, path)] += time.perf_counter() - started
        return response

    app.include_router(routes_auth.router)
    app.include_router(routes_zones.router)
    app.include_router(routes_admin.router)
    for module in OPTIONAL_ROUTERS:
        try:
            mod = __import__(f"voltguard.api.{module}", fromlist=["router"])
            app.include_router(mod.router)
        except ModuleNotFoundError:
            pass

    @app.get("/health", tags=["ops"])
    def health():
        with db.admin_connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "version": __version__, "llm_mode": config.llm_mode(), "report_mode": config.report_mode()}

    @app.get("/metrics", tags=["ops"], response_class=PlainTextResponse)
    def metrics():
        lines = ["# TYPE voltguard_requests_total counter"]
        for (method, path, code), n in sorted(_requests.items()):
            lines.append(f'voltguard_requests_total{{method="{method}",path="{path}",status="{code}"}} {n}')
        lines.append("# TYPE voltguard_request_seconds_total counter")
        for (method, path), s in sorted(_latency.items()):
            lines.append(f'voltguard_request_seconds_total{{method="{method}",path="{path}"}} {s:.4f}')
        return "\n".join(lines) + "\n"

    return app


app = create_app()
