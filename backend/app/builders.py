"""Response-pack builders. Pure functions: (fields dict) -> text / structure. Missing values render as [placeholders]."""
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from .detect import DATA
from .fields import FIELDS, missing_items

CHECKLIST = json.loads((DATA / "checklist.json").read_text())
PORTAL = json.loads((DATA / "portal_sheet.json").read_text())
LABELS = {
    "name": "Your name", "mobile": "Your mobile", "location": "District / nearest police station",
    "when": "Date and time", "description": "What happened", "bank": "Bank / app", "account": "Account (last 4) or UPI ID",
    "amount": "Amount lost", "utrs": "Transaction ID(s) (UTR)", "scamPhones": "Scammer's phone number(s)",
    "scamUpi": "Scammer's UPI ID / account", "scamLinks": "Website / app / profile",
}


def _or(v, ph):
    return v.strip() if isinstance(v, str) and v.strip() else f"[{ph}]"


def _join(items, ph):
    return ", ".join(items) if items else f"[{ph}]"


def _amounts(f):
    return [a.strip() for a in re.split(r"[,\n;]+", f["amount"]) if a.strip()] if f["amount"] else []


def _transactions(f) -> list[str]:
    amts = _amounts(f)
    if f["utrs"] and len(amts) == len(f["utrs"]):
        return [f"UTR {u}: {a}" for u, a in zip(f["utrs"], amts)]
    lines = [f"UTR {u}" for u in f["utrs"]] or ["[UTR / transaction ID: find it in your bank or UPI app]"]
    if amts:
        lines.append("Amount(s): " + ", ".join(amts))
    return lines


def call_script(f: dict) -> list[str]:
    """Mode A. Tier 1 fields ONLY: never name, location or description."""
    tx = "; ".join(_transactions(f))
    return [
        'Say: "I want to report a financial cyber fraud."',
        f"Amount lost: {_or(f['amount'], 'amount')}",
        f"My mobile number: {_or(f['mobile'], 'your mobile number')}",
        f"Bank / app the money left from: {_or(f['bank'], 'bank or UPI app')}",
        f"Account (last 4) or UPI ID debited: {_or(f['account'], 'account last 4 or UPI ID')}",
        f"Transactions: {tx}",
        f"Date / time: {_or(f['when'], 'date and time')}",
        f"Fraudster's phone: {_join(f['scamPhones'], 'phone number(s)')}",
        f"Fraudster's UPI ID / account: {_join(f['scamUpi'], 'UPI ID or account')}",
        f"Fraudster's website / app / profile: {_join(f['scamLinks'], 'link, app or profile')}",
        'Ask: "Please give me the complaint reference number." Write it down.',
        "If you are asked for anything beyond this list, you can say you'll provide it on the portal.",
    ]


def portal_sheet(f: dict) -> list[dict]:
    rows = []
    for sec in PORTAL["sections"]:
        for k in sec["keys"]:
            v = f[k]
            rows.append({"section": sec["section"], "key": k, "label": LABELS[k], "tier": FIELDS[k],
                         "value": ", ".join(v) if isinstance(v, list) else v})
    return rows


def complaint(f: dict) -> str:
    tx = "\n".join(f"  - {t}" for t in _transactions(f))
    return f"""SUBJECT: Financial cyber fraud, online/UPI transaction(s) of {_or(f['amount'], 'amount')}

To: Cyber Crime Cell / National Cyber Crime Reporting Portal (cybercrime.gov.in)

COMPLAINANT: {_or(f['name'], 'your name')}, Mobile: {_or(f['mobile'], 'your mobile number')}, {_or(f['location'], 'district / nearest police station')}

INCIDENT DATE / TIME: {_or(f['when'], 'date and time')}

DESCRIPTION:
{_or(f['description'], 'what happened')}

TRANSACTION DETAILS:
  Bank / app: {_or(f['bank'], 'bank or UPI app')}   Account / UPI ID debited: {_or(f['account'], 'account last 4 or UPI ID')}
{tx}

FRAUDSTER DETAILS:
  Phone number(s): {_join(f['scamPhones'], 'phone number(s)')}
  UPI ID(s) / account(s): {_join(f['scamUpi'], 'UPI ID or account')}
  Website / app / profile: {_join(f['scamLinks'], 'link, app or profile')}

ACTION ALREADY TAKEN:
  Called 1930 on [date/time], reference number [____]. Informed my bank on [date/time], complaint number [____].

REQUEST:
  Please register this complaint, trace the beneficiary accounts and UPI IDs listed above, and place them on hold
  so the defrauded amount can be traced and frozen. Please advise on next steps.

EVIDENCE ATTACHED: screenshots of the transactions, the scammer's messages / call log / profile, and any app or link used.
"""


def bank_letter(f: dict) -> str:
    tx = "\n".join(f"  - {t}" for t in _transactions(f))
    return f"""Subject: Unauthorised/fraudulent transaction(s). Please block and record complaint

Dear Sir/Madam,

I am {_or(f['name'], 'your name')}, holder of account/UPI ID {_or(f['account'], 'account last 4 or UPI ID')} with {_or(f['bank'], 'bank')}
(registered mobile {_or(f['mobile'], 'your mobile number')}).

I was the victim of an online fraud on {_or(f['when'], 'date and time')}. The following transaction(s) were made:
{tx}

The money was sent to: {_join(f['scamUpi'], 'beneficiary UPI ID / account')}.

I have reported this to the National Cyber Crime Helpline (1930) on [date/time], reference number [____], and will file/have filed a
complaint on cybercrime.gov.in.

I request you to: (1) block further debits through my cards, UPI and net banking as appropriate, (2) record this fraud complaint and
give me a written complaint number, (3) coordinate with the beneficiary bank/app to hold the credited amount, and (4) tell me in
writing what further documents you need.

Yours faithfully,
{_or(f['name'], 'your name')}
"""


def checklist(lang: str = "en") -> list[dict]:
    return [{"id": s["id"], "title": s["title"].get(lang) or s["title"]["en"], "detail": s["detail"]["en"], "done": False}
            for s in CHECKLIST]


def pack_txt(f: dict, mode: str, lang: str = "en") -> str:
    miss = missing_items(f)
    miss_txt = "\n".join(f"  [ ] {m['howToFind']}" for m in miss) or "  Nothing. You have everything the helpline usually asks for."
    steps = "\n".join(f"{i}. {s['title']}: {s['detail']}" for i, s in enumerate(checklist(lang), 1))
    if mode == "A":
        mid = "1930 CALL SCRIPT (Tier 1 details only; read top to bottom)\n\n" + "\n".join(f"{i}. {l}" for i, l in enumerate(call_script(f), 1))
    else:
        sheet = portal_sheet(f)
        mid = "PORTAL SHEET (type these into cybercrime.gov.in yourself)\n\n" + "\n".join(
            f"[{r['section']}] {r['label']}: {_or(r['value'], 'fill in')}" for r in sheet)
    bar = "=" * 70
    return (f"GOLDENHOUR RESPONSE PACK\nReporting channels: call 1930 and file at cybercrime.gov.in\n{bar}\n\n"
            f"WHAT TO DO, IN ORDER\n{steps}\n\nSTILL MISSING\n{miss_txt}\n\n{bar}\n{mid}\n\n{bar}\n\n"
            f"COMPLAINT TEXT (paste into cybercrime.gov.in)\n\n{complaint(f)}\n{bar}\n\nLETTER / EMAIL TO YOUR BANK\n\n{bank_letter(f)}\n"
            "GoldenHour only prepares this. You submit it yourself. Check every detail first. This is not legal advice.\n"
            "Delete this file from shared devices.\n")


def ics(elapsed_minutes: int, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    due = now + max(timedelta(minutes=15), timedelta(hours=24) - timedelta(minutes=elapsed_minutes))
    fmt = "%Y%m%dT%H%M%SZ"
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GoldenHour//EN", "BEGIN:VEVENT", f"UID:{uuid.uuid4()}",
        f"DTSTAMP:{now.strftime(fmt)}", f"DTSTART:{due.strftime(fmt)}", f"DTEND:{(due + timedelta(minutes=15)).strftime(fmt)}",
        "SUMMARY:File your formal complaint on cybercrime.gov.in", "END:VEVENT", "END:VCALENDAR", ""])
