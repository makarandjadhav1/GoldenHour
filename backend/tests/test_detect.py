import json
import pytest
from app import detect
from app.text import normalize, redact
from tests import samples

RULES = json.loads((detect.DATA / "rules.json").read_text())


def run(text):
    t, _ = normalize(text)
    t, _ = redact(t)
    return detect.detect(t)


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r["id"])
def test_rule_examples(rule):
    assert len(rule["examples"]) >= 2 and len(rule["counterExamples"]) >= 2
    for ex in rule["examples"]:
        assert rule["id"] in {h["ruleId"] for h in run(ex)["hits"]}, ex
    for cx in rule["counterExamples"]:
        assert rule["id"] not in {h["ruleId"] for h in run(cx)["hits"]}, cx


def test_twenty_rules():
    assert len(RULES) == 20


def test_digital_arrest():
    d = run(samples.MESSAGES["Fake police video call ('digital arrest')"])
    assert d["verdict"] == "scam" and d["score"] >= 85 and d["critical"] and d["scamType"] == "digital_arrest"


def test_kyc_sms():
    d = run(samples.MESSAGES["Bank KYC SMS"])
    assert {"credential_request", "kyc", "url_lookalike", "url_tld"} <= {h["ruleId"] for h in d["hits"]}
    assert d["verdict"] == "scam" and d["scamType"] == "kyc"


def test_electricity():
    d = run(samples.MESSAGES["Electricity bill threat"])
    assert d["verdict"] == "scam" and d["scamType"] == "electricity"
    assert "apk_install" in {h["ruleId"] for h in d["hits"]}


def test_investment_and_task():
    assert run(samples.MESSAGES["Stock-tip WhatsApp group"])["scamType"] == "investment"
    assert run(samples.MESSAGES["Part-time task job"])["scamType"] == "job_task"


def test_genuine_stay_low():
    for k in ("GENUINE bank OTP (should stay low)", "GENUINE delivery update (should stay low)"):
        d = run(samples.MESSAGES[k])
        assert d["verdict"] == "low" and not d["critical"]


def test_negation():
    assert not run("Never share your OTP with anyone.")["critical"]
    assert not run("We will never ask you to share your OTP or PIN.")["critical"]
    assert run("Please share the OTP you just received to confirm.")["critical"]


def test_spans_point_at_evidence():
    t = "Please share the OTP now"
    h = detect.detect(t)["hits"][0]
    assert t[h["start"]:h["end"]].startswith("share")


def test_urls():
    assert detect.analyze_url("https://www.onlinesbi.sbi/login") == []
    ids = {r[0] for r in detect.analyze_url("http://hdfc-netbanking-secure.click/login")}
    assert {"url_lookalike", "url_tld", "url_http"} <= ids
    assert "url_shortener" in {r[0] for r in detect.analyze_url("https://bit.ly/abc")}
    assert "url_ip" in {r[0] for r in detect.analyze_url("http://192.168.4.5/pay")}


def test_empty():
    d = run("")
    assert d["score"] == 0 and d["verdict"] == "low"


def test_redact_vectors():
    out, n = redact("Card 4111 1111 1111 1111, aadhaar 1234 5678 9012, OTP 482913, 123456 is your OTP, UTR 524587920123")
    assert "4111" not in out and "1234 5678" not in out and "482913" not in out and "123456" not in out
    assert "524587920123" in out and n >= 4


def test_normalize_devanagari_and_cap():
    assert normalize("UTR ५२४५८७९२०१२३")[0] == "UTR 524587920123"
    t, trunc = normalize("a" * 6000)
    assert len(t) == 5000 and trunc


def test_redact_idempotent_and_fast():
    s = "OTP 123456 card 4111 1111 1111 1111 " * 100
    once, _ = redact(s)
    assert redact(once)[0] == once
