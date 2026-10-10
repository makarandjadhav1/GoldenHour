from app.extract import extract_incident as ex, indian_group
from app.text import normalize, redact
from tests import samples


def run(t):
    return ex(redact(normalize(t)[0])[0])


def test_e1():
    i = run(samples.INCIDENTS["Electricity-bill APK, two UPI debits"])
    assert i["amounts"] == ["₹49,999", "₹25,000"] and i["utrs"] == ["524587920123", "524587920456"]
    assert i["upiIds"] == ["rajesh.kumar77@okaxis"] and i["banks"] == ["SBI"] and i["accountLast4"] == ["XX2234"]
    assert "+919876543210" in i["phones"] and i["victimPhones"] == ["+919123456789"]
    assert "4:10 PM" in i["whenHints"]


def test_e2_aadhaar_phone_not_utr():
    i = run("Aadhaar 123456789012 was misused. Call 919876543210. UTR: 524587920123.")
    assert i["utrs"] == ["524587920123"] and i["possibleUtrs"] == []


def test_e3_unlabelled():
    i = run("paid 524587920123 yesterday")
    assert i["utrs"] == [] and i["possibleUtrs"] == ["524587920123"]


def test_e4_email_and_lakh():
    i = run("mail me at john@gmail.com; paid Rs. 2.5 lakh to shop@oksbi.")
    assert i["upiIds"] == ["shop@oksbi"] and i["amounts"] == ["₹2,50,000"]


def test_e5():
    i = run(samples.INCIDENTS["Fake trading group, card + IMPS"])
    assert i["utrs"] == ["612345678901"] and i["amounts"] == ["₹1,20,000"] and i["upiIds"] == ["tradedesk@ybl"]
    assert i["banks"] == ["HDFC Bank"] and i["accountLast4"] == ["XX8841"]


def test_hindi():
    i = run("मैंने 5,000 रुपये भेजे। UTR ५२४५८७९२०१२३")
    assert i["amounts"] == ["₹5,000"] and i["utrs"] == ["524587920123"]


def test_group():
    assert indian_group(12345678) == "1,23,45,678"
