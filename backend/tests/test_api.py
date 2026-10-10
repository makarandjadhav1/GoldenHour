import logging

import pytest
from fastapi.testclient import TestClient

from app import db, limits, main
from tests import samples


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def test_health(client):
    r = client.get("/v1/health").json()
    assert r["status"] == "ok" and r["db"] is True


def test_check(client):
    r = client.post("/v1/check", json={"text": samples.MESSAGES["Bank KYC SMS"], "lang": "en"}).json()
    assert r["verdict"] == "scam" and r["hits"] and "redactedText" in r and r["advice"]
    assert r["hits"][0]["end"] > r["hits"][0]["start"]


def test_check_masks_secrets(client):
    r = client.post("/v1/check", json={"text": "123456 is your OTP. Card 4111 1111 1111 1111"}).json()
    assert "123456" not in r["redactedText"] and "4111" not in r["redactedText"] and r["maskedCount"] >= 2


def test_extract_and_pack(client):
    t = samples.INCIDENTS["Electricity-bill APK, two UPI debits"]
    e = client.post("/v1/extract", json={"text": t}).json()
    assert e["fields"]["utrs"] == ["524587920123", "524587920456"] and e["meta"]["utrs"]["tier"] == 1
    f = e["fields"] | {"name": "Zed Qwerty", "location": "Kothrud"}
    p = client.post("/v1/pack", json={"fields": f, "mode": "A", "elapsed": "m30"}).json()
    assert "524587920123" in "\n".join(p["callScript"]) and "Zed Qwerty" not in "\n".join(p["callScript"])
    assert p["banner"]["zone"] == "first2h" and "BEGIN:VEVENT" in p["ics"] and p["portalSheet"] is None
    b = client.post("/v1/pack", json={"fields": f, "mode": "B"}).json()
    assert any(r["value"] == "Zed Qwerty" for r in b["portalSheet"]) and b["callScript"] is None


def test_extract_returns_redacted_text(client):
    r = client.post("/v1/extract", json={"text": "OTP 482913 paid Rs 500 UTR 524587920123"}).json()
    assert "482913" not in r["redactedText"] and r["maskedCount"] >= 1 and "524587920123" in r["redactedText"]


def test_validate(client):
    r = client.post("/v1/validate", json={"fields": {"utrs": ["12"], "mobile": "1"}}).json()
    assert r["meta"]["utrs"]["warn"] and r["meta"]["mobile"]["warn"]


def test_ask(client):
    r = client.post("/v1/ask", json={"question": "What is a UTR?"}).json()
    assert (
        not r["fallback"]
        and r["results"][0]["id"] == "what-is-utr"
        and r["results"][0]["sources"]
        and r["results"][0]["verifiedOn"]
    )
    r = client.post("/v1/ask", json={"question": "best pizza near me"}).json()
    assert r["fallback"] and r["results"] == []


def test_problems_dont_echo(client):
    r = client.post("/v1/check", json={"text": 5, "secretcanary": "CANARY-XYZ"})
    assert r.status_code == 400 and "CANARY" not in r.text and r.headers["content-type"].startswith("application/problem+json")
    r = client.post("/v1/check", content=b"x" * 20000, headers={"content-type": "application/json"})
    assert r.status_code == 413
    assert client.post("/v1/check", json={"text": "hi"}).headers["cache-control"] == "no-store"


def test_rate_limit(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_GENERAL", "3")
    limits._buckets.clear()
    codes = [client.post("/v1/ask", json={"question": "utr"}).status_code for _ in range(6)]
    assert 429 in codes and codes[0] == 200
    limits._buckets.clear()


def test_log_canary(client, caplog):
    caplog.set_level(logging.INFO)
    client.post("/v1/check", json={"text": "CANARY-LOGTEST-9981 paid to canary@okaxis 524587920123"})
    assert "CANARY" not in caplog.text and "524587920123" not in caplog.text


def test_report_error_stores_note_only(client):
    assert client.post("/v1/report-error", json={"page": "/ask", "note": "typo in answer"}).status_code == 204
    assert db._q("select count(*) c from error_reports", fetch="one")["c"] >= 1
