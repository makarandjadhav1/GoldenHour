"""HTTP routes. Each is thin: validate, call pure functions, return."""

import os

from fastapi import APIRouter, Header

from . import ai, builders, db, detect, extract, kb
from . import fields as fl
from .problem import problem
from .schemas import AskIn, ExplainIn, PackIn, ReportIn, TextIn, ValidateIn
from .text import normalize, redact

router = APIRouter(prefix="/v1")


def _clean(text: str):
    t, truncated = normalize(text)
    t, masked = redact(t)
    return t, masked, truncated


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "ai": bool(os.environ.get("ANTHROPIC_API_KEY")) and os.environ.get("AI_ENABLED", "true") != "false",
        "db": db.ping(),
    }


@router.post("/check")
def check(body: TextIn):
    t, masked, truncated = _clean(body.text)
    return detect.detect(t, body.lang) | {"redactedText": t, "maskedCount": masked, "truncated": truncated}


@router.post("/extract")
def extract_fields(body: TextIn):
    t, masked, truncated = _clean(body.text)
    inc = extract.extract_incident(t)
    f = fl.fields_from(inc)
    return {
        "incident": inc,
        "fields": f,
        "meta": _meta(f, auto=True),
        "missing": fl.missing_items(f),
        "maskedCount": masked,
        "truncated": truncated,
        "redactedText": t,
    }


def _meta(f: dict, auto: bool = False) -> dict:
    return {k: {"tier": fl.FIELDS[k], "warn": fl.validate(k, f[k]), "auto": auto and bool(f[k])} for k in fl.FIELDS}


@router.post("/validate")
def validate(body: ValidateIn):
    f = body.fields.model_dump()
    return {"meta": _meta(f), "missing": fl.missing_items(f)}


@router.post("/pack")
def pack(body: PackIn):
    f = body.fields.model_dump()
    minutes = fl.ELAPSED_MINUTES[body.elapsed]
    return {
        "mode": body.mode,
        "callScript": builders.call_script(f) if body.mode == "A" else None,
        "portalSheet": builders.portal_sheet(f) if body.mode == "B" else None,
        "portalVerified": builders.PORTAL["verifiedOn"] is not None,
        "complaint": builders.complaint(f),
        "bankLetter": builders.bank_letter(f),
        "checklist": builders.checklist(body.lang),
        "missing": fl.missing_items(f),
        "banner": fl.elapsed_banner(minutes),
        "packTxt": builders.pack_txt(f, body.mode, body.lang),
        "ics": builders.ics(minutes),
    }


@router.post("/ask")
def ask(body: AskIn):
    q, _ = redact(body.question)
    return kb.search(q, body.lang)


@router.post("/report-error", status_code=204)
def report_error(body: ReportIn):
    db.add_error_report(body.page, body.note)


@router.post("/ai/explain")
def ai_explain(body: ExplainIn, x_gh_ai_consent: str | None = Header(default=None)):
    if x_gh_ai_consent != "1":
        return problem(400, "consent_required", "Consent required", "AI features are opt-in.")
    if not ai.enabled():
        return problem(503, "ai_disabled", "AI is not available", "The extra opinion is switched off.")
    if not db.spend_tokens(ai.MAX_TOKENS + len(body.maskedText) // 3, int(os.environ.get("AI_DAILY_TOKEN_CAP", 500000))):
        return problem(503, "ai_budget_exhausted", "AI budget used up", "The extra opinion is unavailable today.")
    try:
        return ai.explain(body.maskedText, body.ruleLabels, body.language)
    except Exception:
        return problem(502, "ai_upstream_error", "AI unavailable", "The extra opinion could not be produced.")
