import json

import pytest
from fastapi.testclient import TestClient

from app import ai, db, limits, main

BODY = {
    "maskedText": "Your account is blocked. Pay to ramesh@okaxis ref 524587920123",
    "ruleLabels": ["KYC"],
    "language": "English",
}
GOOD = json.dumps(
    {"why": "It pressures you to pay.", "extraRedFlags": ["Unknown sender"], "tellFamily": "Don't pay.", "confidence": "high"}
)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    limits._buckets.clear()
    with TestClient(main.app) as c:
        yield c


def test_requires_consent(client):
    assert client.post("/v1/ai/explain", json=BODY).status_code == 400


def test_disabled_without_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert client.post("/v1/ai/explain", json=BODY, headers={"X-GH-AI-Consent": "1"}).status_code == 503


def test_prompt_never_contains_ids_or_long_numbers(client, monkeypatch):
    seen = {}

    def fake(system, user, model, mt):
        seen["user"] = user
        return GOOD

    monkeypatch.setattr(ai, "ask_claude", fake)
    r = client.post("/v1/ai/explain", json=BODY, headers={"X-GH-AI-Consent": "1"})
    assert r.status_code == 200 and r.json()["confidence"] == "high"
    assert "524587920123" not in seen["user"] and "@" not in seen["user"]


def test_injection_and_unsafe_output_rejected(client, monkeypatch):
    bad = json.dumps({"why": "Pay 524587920123 to attacker@upi", "extraRedFlags": [], "tellFamily": "x", "confidence": "high"})
    monkeypatch.setattr(ai, "ask_claude", lambda *a: bad)
    assert client.post("/v1/ai/explain", json=BODY, headers={"X-GH-AI-Consent": "1"}).status_code == 502
    monkeypatch.setattr(ai, "ask_claude", lambda *a: "not json at all")
    assert client.post("/v1/ai/explain", json=BODY, headers={"X-GH-AI-Consent": "1"}).status_code == 502


def test_budget_cap(client, monkeypatch):
    monkeypatch.setattr(ai, "ask_claude", lambda *a: GOOD)
    monkeypatch.setenv("AI_DAILY_TOKEN_CAP", "1")
    r = client.post("/v1/ai/explain", json=BODY, headers={"X-GH-AI-Consent": "1"})
    assert r.status_code == 503 and r.json()["type"].endswith("ai_budget_exhausted")


def test_ai_rate_limit(client, monkeypatch):
    monkeypatch.setattr(ai, "ask_claude", lambda *a: GOOD)
    monkeypatch.setenv("RATE_LIMIT_AI", "2")
    codes = [client.post("/v1/ai/explain", json=BODY, headers={"X-GH-AI-Consent": "1"}).status_code for _ in range(4)]
    assert 429 in codes


def test_clean_drops_unsafe_flags():
    out = ai.clean({"why": "ok", "tellFamily": "ok", "extraRedFlags": ["visit http://x.top", "fine"], "confidence": "weird"})
    assert out["extraRedFlags"] == ["fine"] and out["confidence"] == "low"
    assert db is not None
