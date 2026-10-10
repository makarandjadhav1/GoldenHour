"""Fields, data tiers, validation, missing items, elapsed-time guidance. Pure functions.

Tier 1 = shared on the 1930 call. Tier 2 = typed into the portal by the victim. Tier 3 (OTP, PIN, CVV,
password, card no., Aadhaar) has NO field here by design.
"""
import re

LIST_KEYS = {"utrs", "scamPhones", "scamUpi", "scamLinks"}
# key: (tier, in_call_script)
FIELDS = {
    "amount": 1, "utrs": 1, "bank": 1, "account": 1, "when": 1, "mobile": 1,
    "scamPhones": 1, "scamUpi": 1, "scamLinks": 1,
    "description": 2, "name": 2, "location": 2,
}
QUICK = ["amount", "utrs", "bank", "when", "mobile"]
ELAPSED_MINUTES = {"lt15": 10, "m30": 30, "h1to2": 90, "sameDay": 360, "earlier": 2000}

HOW_TO_FIND = {
    "utrs": "Open your bank or UPI app > transaction history > the debit, and screenshot it. It may be called UPI Ref No. "
            "or RRN; in Google Pay it is the 'UPI transaction ID'.",
    "amount": "Amount lost.",
    "bank": "Bank / wallet / UPI app the money left from.",
    "account": "Your account number (last 4 is enough to start) or UPI ID that was debited.",
    "when": "Date and approximate time of each transaction.",
    "mobile": "Your mobile number.",
    "scammer": "Any scammer identifier: phone number, UPI ID / bank account, website, app name or social profile.",
}


def empty_fields() -> dict:
    return {k: ([] if k in LIST_KEYS else "") for k in FIELDS}


def fields_from(inc: dict) -> dict:
    f = empty_fields()
    f.update(
        amount=", ".join(inc["amounts"]), utrs=list(inc["utrs"]), bank=(inc["banks"] or inc["apps"] or [""])[0],
        account=(inc["accountLast4"] or [""])[0], when=", ".join(inc["whenHints"]),
        mobile=(inc["victimPhones"] or [""])[0], scamPhones=list(inc["phones"]),
        scamUpi=list(inc["upiIds"]), scamLinks=list(inc["urls"]),
    )
    return f


def validate(key: str, v) -> str | None:
    """Return a gentle warning or None. Never blocks."""
    if key == "utrs":
        bad = [u for u in v if not (re.fullmatch(r"\d{12}", u) or re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9]{13,22}", u))]
        return "That doesn't look like a 12-digit transaction ID. Check your bank app?" if bad else None
    if key == "mobile" and v:
        d = re.sub(r"[\s-]", "", v).removeprefix("+91")
        return None if re.fullmatch(r"[6-9]\d{9}", d) else "A mobile number has 10 digits."
    if key == "account" and re.search(r"\d{5,}", v or ""):
        return "Last 4 digits is enough to start. You don't need to share the full number on a call."
    if key == "description" and len(v or "") > 1500:
        return "Please keep it under 1500 characters."
    return None


def missing_items(f: dict) -> list[dict]:
    miss = [k for k in ("utrs", "amount", "bank", "account", "when", "mobile") if not f.get(k)]
    if not (f["scamPhones"] or f["scamUpi"] or f["scamLinks"]):
        miss.append("scammer")
    return [{"key": k, "howToFind": HOW_TO_FIND[k]} for k in miss]


def elapsed_banner(minutes: int) -> dict:
    """level is a calm Sun-Clock zone: first2h | day | later."""
    if minutes <= 120:
        return {"zone": "first2h", "message": "First two hours: the money may still be moving through the banking chain. Call 1930 before anything else."}
    if minutes <= 1440:
        return {"zone": "day", "message": "Call 1930 now, then file the formal complaint on cybercrime.gov.in within 24 hours of the incident."}
    return {"zone": "later", "message": "It's later than ideal, but report anyway: call 1930, file on cybercrime.gov.in and inform your bank in writing."}
