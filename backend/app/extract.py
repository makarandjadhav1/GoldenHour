"""Incident extraction from a victim's own words. Pure functions over normalised, redacted text."""

import json
import re

from .detect import DATA, extract_urls

_BANKS = json.loads((DATA / "banks.json").read_text())
_TIME = re.compile(r"(?i)\b\d{1,2}[:.]\d{2}\s?(?:am|pm)\b")
_DATE = re.compile(
    r"(?i)\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|"
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?(?:\s+\d{2,4})?\b|"
    r"\b(?:today|yesterday)\b"
)
_AMOUNT = re.compile(r"(?i)(?:₹|\brs\.?|\binr)\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr\b)?")
_AMOUNT_HI = re.compile(r"([\d,]+(?:\.\d+)?)\s*(?:रुपये|रु\.?)")
_LABEL = (
    r"(?:\butr\b|\brrn\b|ref(?:erence)?(?:\s*(?:no\.?|number|id))?|txn(?:\s*(?:id|no\.?))?|"
    r"transaction\s*(?:id|no\.?|number|ref)?|upi\s*ref(?:erence)?(?:\s*(?:no\.?|id))?)"
)
_UTR = re.compile(r"(?i)" + _LABEL + r"\W{0,12}(\d{12})(?!\d)")
_UTR_ALNUM = re.compile(r"(?i)" + _LABEL + r"\W{0,12}([A-Z0-9]{13,22})\b")
_TWELVE = re.compile(r"(?<!\d)\d{12}(?!\d)")
_PHONE = re.compile(r"(?<!\d)(?:\+91[\s-]?|91[\s-]|0)?([6-9]\d{4}[\s-]?\d{5})(?!\d)")
_UPI = re.compile(r"(?<![\w.\-])([A-Za-z0-9][\w.\-]{1,48})@([A-Za-z][A-Za-z0-9]{1,20})\b(?!\.[A-Za-z])")
_LAST4 = re.compile(r"(?i)\b(?:a/?c|acct|account|card)\b\D{0,12}?(?:x+|\*+)?\s?(\d{4})(?!\d)")
_MINE = re.compile(r"(?i)(?:my\s+(?:number|mobile)|\bmine\b|मेरा\s+नंबर)\D{0,30}$")


def uniq(items) -> list:
    out: list = []
    for i in items:
        if i not in out:
            out.append(i)
    return out


def indian_group(n: int) -> str:
    """12345678 -> 1,23,45,678"""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail, parts = s[:-3], s[-3:], []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def fmt_amount(v: float) -> str:
    whole = int(v)
    return f"₹{indian_group(whole)}" if v == whole else f"₹{indian_group(whole)}.{round((v - whole) * 100):02d}"


def _amounts(text: str) -> list[str]:
    out = []
    for m in list(_AMOUNT.finditer(text)) + list(_AMOUNT_HI.finditer(text)):
        raw = m.group(1).replace(",", "").strip(".")
        try:
            val = float(raw)
        except ValueError:
            continue
        unit = (m.group(2) or "").lower() if m.re is _AMOUNT else ""
        val *= 1e5 if unit.startswith(("lakh", "lac")) else 1e7 if unit.startswith(("crore", "cr")) else 1
        out.append((m.start(), fmt_amount(val)))
    return uniq(a for _, a in sorted(out))


def extract_incident(text: str) -> dict:
    utrs = [m.group(1) for m in _UTR.finditer(text)]
    for m in _UTR_ALNUM.finditer(text):
        tok = m.group(1)
        if any(c.isdigit() for c in tok) and any(c.isalpha() for c in tok):
            utrs.append(tok.upper())
    utrs = uniq(utrs)

    possible = []
    for m in _TWELVE.finditer(text):
        tok = m.group(0)
        if tok in utrs or re.search(r"(?i)aadh?aa?r|uid", text[max(0, m.start() - 25) : m.start()]):
            continue
        if tok.startswith("91") and tok[2] in "6789":
            continue
        possible.append(tok)

    phones, victim = [], []
    for m in _PHONE.finditer(text):
        num = "+91" + re.sub(r"\D", "", m.group(1))
        (victim if _MINE.search(text[max(0, m.start() - 30) : m.start()]) else phones).append(num)

    low = text.lower()
    when = [
        m.group(0).strip().upper() if ":" in m.group(0) or "." in m.group(0) else m.group(0).strip() for m in _DATE.finditer(text)
    ] + [m.group(0).strip().upper() for m in _TIME.finditer(text)]
    return {
        "amounts": _amounts(text),
        "utrs": utrs,
        "possibleUtrs": uniq(possible),
        "upiIds": uniq(f"{m.group(1)}@{m.group(2)}" for m in _UPI.finditer(text)),
        "phones": uniq(phones),
        "victimPhones": uniq(victim),
        "urls": extract_urls(text),
        "banks": [n for n, p in _BANKS["banks"].items() if re.search(rf"\b(?:{p})\b", low)],
        "apps": [n for n, p in _BANKS["apps"].items() if re.search(rf"\b(?:{p})\b", low)],
        "accountLast4": uniq("XX" + m.group(1) for m in _LAST4.finditer(text)),
        "whenHints": uniq(when),
    }
