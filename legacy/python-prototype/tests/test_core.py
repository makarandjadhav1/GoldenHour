import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import llm  # noqa: E402
import samples  # noqa: E402
import scamcore as sc  # noqa: E402


# ---------- detection ----------
def test_digital_arrest_is_flagged_critical():
    d = sc.detect(samples.MESSAGES["Fake police video call ('digital arrest')"])
    assert d.verdict == "scam" and d.score >= 85 and d.critical
    assert d.scam_type == "digital_arrest"


def test_kyc_sms_flags_lookalike_and_otp():
    d = sc.detect(samples.MESSAGES["Bank KYC SMS"])
    ids = {h.rule_id for h in d.hits}
    assert {"credential_request", "kyc", "url_lookalike", "url_tld"} <= ids
    assert d.verdict == "scam" and d.scam_type == "kyc"


def test_electricity_apk():
    d = sc.detect(samples.MESSAGES["Electricity bill threat"])
    assert d.verdict == "scam" and d.scam_type == "electricity"
    assert "apk_install" in {h.rule_id for h in d.hits}


def test_investment_and_task_types():
    assert sc.detect(samples.MESSAGES["Stock-tip WhatsApp group"]).scam_type == "investment"
    assert sc.detect(samples.MESSAGES["Part-time task job"]).scam_type == "job_task"


def test_genuine_otp_sms_is_not_flagged():
    d = sc.detect(samples.MESSAGES["GENUINE bank OTP (should stay low)"])
    assert d.verdict == "low" and not d.critical


def test_genuine_delivery_is_not_flagged():
    d = sc.detect(samples.MESSAGES["GENUINE delivery update (should stay low)"])
    assert d.verdict == "low"


def test_negated_otp_warning_not_flagged_but_request_is():
    assert not sc.detect("Never share your OTP with anyone.").critical
    assert not sc.detect("We will never ask you to share your OTP or PIN.").critical
    assert sc.detect("Please share the OTP you just received to confirm.").critical


def test_official_domains_not_flagged():
    assert sc.analyze_url("https://www.onlinesbi.sbi/login") == []
    assert sc.analyze_url("https://www.hdfcbank.com/") == []


def test_lookalike_and_shortener_and_ip():
    ids = {r[0] for r in sc.analyze_url("http://hdfc-netbanking-secure.click/login")}
    assert "url_lookalike" in ids and "url_tld" in ids and "url_http" in ids
    assert "url_shortener" in {r[0] for r in sc.analyze_url("https://bit.ly/abc")}
    assert "url_ip" in {r[0] for r in sc.analyze_url("http://192.168.4.5/pay")}


def test_empty_text():
    d = sc.detect("")
    assert d.score == 0 and d.verdict == "low"


# ---------- redaction ----------
def test_redaction_masks_secrets_but_keeps_utr():
    t = ("Card 4111 1111 1111 1111, aadhaar 1234 5678 9012, OTP 482913, "
         "123456 is your OTP, UTR 524587920123")
    out, n = sc.redact(t)
    assert "4111" not in out and "1234 5678" not in out and "482913" not in out and "123456" not in out
    assert "524587920123" in out and n >= 4


# ---------- extraction ----------
def test_extraction_on_sample():
    inc = sc.extract_incident(samples.INCIDENTS["Electricity-bill APK, two UPI debits"])
    assert inc.amounts == ["₹49,999", "₹25,000"]
    assert inc.utrs == ["524587920123", "524587920456"]
    assert inc.upi_ids == ["rajesh.kumar77@okaxis"]
    assert "+919876543210" in inc.phones and "+919123456789" in inc.phones
    assert inc.banks == ["SBI"] and inc.account_last4 == ["XX2234"]
    assert any("mseb-bill-update.xyz" in u for u in inc.urls)
    assert "4:10 PM" in inc.when_hints


def test_utr_not_confused_with_aadhaar_or_phone():
    inc = sc.extract_incident("Aadhaar 123456789012 was misused. Call 919876543210. UTR: 524587920123.")
    assert inc.utrs == ["524587920123"]
    assert "123456789012" not in inc.possible_utrs
    assert "919876543210" not in inc.possible_utrs


def test_unlabelled_12_digit_is_only_possible():
    inc = sc.extract_incident("paid 524587920123 yesterday")
    assert inc.utrs == [] and inc.possible_utrs == ["524587920123"]


def test_emails_are_not_upi_ids_and_lakh_amounts():
    inc = sc.extract_incident("mail me at john@gmail.com; paid Rs. 2.5 lakh to shop@oksbi.")
    assert inc.upi_ids == ["shop@oksbi"]
    assert inc.amounts == ["₹2,50,000"]


def test_second_sample_extraction():
    inc = sc.extract_incident(samples.INCIDENTS["Fake trading group, card + IMPS"])
    assert inc.utrs == ["612345678901"] and inc.amounts == ["₹1,20,000"]
    assert inc.upi_ids == ["tradedesk@ybl"] and inc.banks == ["HDFC Bank"] and inc.account_last4 == ["XX8841"]


# ---------- builders ----------
def test_pack_contains_facts_and_flags_missing():
    f = sc.Fields(name="A Tester", amount="₹49,999", utrs=["524587920123"], bank="SBI")
    pack = sc.build_pack(f)
    assert "524587920123" in pack and "1930" in pack and "cybercrime.gov.in" in pack
    miss = sc.missing_items(f)
    assert any("Date and approximate time" in m for m in miss)
    assert any("scammer identifier" in m.lower() for m in miss)


def test_missing_utr_gives_actionable_hint():
    assert "UPI Ref No." in sc.missing_items(sc.Fields())[0]


def test_transactions_paired_when_counts_match():
    f = sc.Fields(amount="₹100, ₹200", utrs=["111111111111", "222222222222"])
    assert "UTR 111111111111: ₹100" in sc.build_call_script(f)


def test_elapsed_banner_levels():
    assert sc.elapsed_banner(30)[0] == "red"
    assert sc.elapsed_banner(600)[0] == "orange"
    assert sc.elapsed_banner(3000)[0] == "yellow"


# ---------- LLM guard rails (no network) ----------
def test_polish_guard_rejects_invented_numbers_and_ids():
    draft = "Paid ₹49,999 via UTR 524587920123 to rajesh@okaxis."
    assert llm.numbers_ok(draft, "I paid ₹49,999 (UTR 524587920123) to rajesh@okaxis within 24 hours.")
    assert not llm.numbers_ok(draft, "I paid ₹59,999 (UTR 524587920123) to rajesh@okaxis.")
    assert not llm.numbers_ok(draft, "I paid ₹49,999 (UTR 524587920123) to other@okaxis.")


def test_parse_json_handles_fences_and_garbage():
    assert llm.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.parse_json('Sure! {"a": 2} hope that helps') == {"a": 2}
    try:
        llm.parse_json("no json here")
        assert False
    except llm.LLMError:
        pass


def test_no_key_means_demo_mode(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert llm.get_client() is None
