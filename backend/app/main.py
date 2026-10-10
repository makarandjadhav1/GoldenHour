"""App wiring: startup data load, middleware (limits, headers, logging), RFC 7807 errors."""

import json
import logging
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import db, detect, kb, limits
from .routes import router

log = logging.getLogger("goldenhour")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(message)s")
MAX_BODY = 16 * 1024
_loaded_version = ""


def problem(status: int, code: str, title: str, detail: str, req_id: str = "") -> JSONResponse:
    """RFC 7807. The detail never echoes user input."""
    return JSONResponse(
        {
            "type": f"https://goldenhour.example/errors/{code}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": req_id,
        },
        status_code=status,
        media_type="application/problem+json",
    )


def load_data(force: bool = False) -> None:
    """Load rules and KB from Postgres (or the repo JSON if the DB is down). Cheap version check keeps it fresh."""
    global _loaded_version
    try:
        v = db.version()
        if v == _loaded_version and not force:
            return
        detect.load_rules(db.load_rules() or None)
        kb.load_kb(db.load_kb() or json.loads((detect.DATA / "kb.json").read_text()))
        _loaded_version = v
    except Exception:
        if not detect.RULES:
            detect.load_rules()
            kb.load_kb(json.loads((detect.DATA / "kb.json").read_text()))


def _refresher():
    while True:
        time.sleep(60)
        load_data()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db.open_pool()
    except Exception:
        log.warning('{"level":"warn","msg":"db unavailable, using bundled data"}')
    load_data(force=True)
    threading.Thread(target=_refresher, daemon=True).start()
    yield
    db.close_pool()


app = FastAPI(title="GoldenHour API", lifespan=lifespan, docs_url=None, redoc_url=None)
if os.environ.get("WEB_ORIGIN"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.environ["WEB_ORIGIN"]],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-GH-AI-Consent"],
    )
app.include_router(router)


@app.middleware("http")
async def guard(request: Request, call_next):
    rid, t0 = "req_" + uuid.uuid4().hex[:8], time.perf_counter()
    path = request.url.path
    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() if os.environ.get("TRUST_PROXY") else "") or (
        request.client.host if request.client else "?"
    )
    if request.method == "POST":
        n = request.headers.get("content-length")
        if n is None:
            resp = problem(411, "length_required", "Length required", "Send a Content-Length header.", rid)
        elif int(n) > MAX_BODY:
            resp = problem(413, "too_large", "Request too large", "Please send less text.", rid)
        else:
            resp = None
    else:
        resp = None
    if resp is None and path != "/v1/health" and not limits.allow(ip, "ai" if path.startswith("/v1/ai/") else "general"):
        resp = problem(429, "rate_limited", "Too many requests", "Try again in a little while.", rid)
    resp = resp or await call_next(request)
    resp.headers.update(
        {
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
            "Strict-Transport-Security": "max-age=31536000",
            "X-Request-Id": rid,
        }
    )
    log.info(
        json.dumps(
            {
                "ts": int(time.time()),
                "reqId": rid,
                "route": path,
                "status": resp.status_code,
                "ms": round((time.perf_counter() - t0) * 1000),
            }
        )
    )
    return resp


@app.exception_handler(RequestValidationError)
async def invalid(request: Request, exc: RequestValidationError):
    return problem(400, "invalid_request", "Invalid request", "The request was not in the expected format.")
