"""GoldenHour core: deterministic scam signals, incident extraction, response-pack builders.

No network access and no API key needed. Everything here is unit-tested (tests/test_core.py).
Claude (llm.py) is an optional layer on top; this module must stay useful on its own.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

# ----------------------------------------------------------------------------
# Redaction: mask secrets locally BEFORE analysis or anything is sent to an API
# ----------------------------------------------------------------------------
_CARD_RE = re.compile(r"(?<!\d)(?:\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{1,4}|\d{15,16})(?!\d)")
_AADHAAR_LABELLED_RE = re.compile(r"(?i)(aadh?aa?r|uid)(\D{0,15})(\d{4}\s?\d{4}\s?\d{4})(?!\d)")
_AADHAAR_SPACED_RE = re.compile(r"(?<!\d)\d{4} \d{4} \d{4}(?!\d)")
_OTP_AFTER_RE = re.compile(r"(?i)\b(otp|cvv|cvc|mpin|upi\s*pin|pin)\b(?!\s*code)(\D{0,20}?)(\d{3,8})(?!\d)")
_OTP_BEFORE_RE = re.compile(
    r"(?i)(?<!\d)(\d{4,8})(?!\d)(\s+is\s+(?:your|the)\s+(?:otp|one[- ]time\s+password|verification\s+code))"
)


def redact(text: str) -> tuple[str, int]:
    """Mask card numbers, Aadhaar numbers, OTP/PIN/CVV values. Returns (clean_text, n_masked)."""
    n = 0

    def sub(pattern: re.Pattern, repl, s: str) -> str:
        nonlocal n
        s, k = pattern.subn(repl, s)
        n += k
        return s

    text = sub(_CARD_RE, "[CARD-NO REDACTED]", text)
    text = sub(_AADHAAR_LABELLED_RE, lambda m: f"{m.group(1)}{m.group(2)}[AADHAAR REDACTED]", text)
    text = sub(_AADHAAR_SPACED_RE, "[AADHAAR-LIKE REDACTED]", text)
    text = sub(_OTP_AFTER_RE, lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
    text = sub(_OTP_BEFORE_RE, lambda m: f"[REDACTED]{m.group(2)}", text)
    return text, n


# ----------------------------------------------------------------------------
# Scam signal rules
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Rule:
    id: str
    label: str
    weight: int
    category: str
    why: str
    pattern: re.Pattern
    critical: bool = False
    unless_before: re.Pattern | None = None


def _r(id, label, weight, category, why, pattern, critical=False, unless=None) -> Rule:
    return Rule(id, label, weight, category, why, re.compile(pattern, re.I),
                critical, re.compile(unless, re.I) if unless else None)


_NEGATION_BEFORE = r"(?:\bnever|\bnot\b|n't|\bdont|\bno\s+one|\bnobody)[^.\n]{0,30}$"

RULES: list[Rule] = [
    _r("credential_request", "Asks you to share an OTP / PIN / CVV / password", 70, "credential",
       "No bank, government office or genuine company needs your OTP, PIN or CVV. Sharing it hands over your money.",
       r"\b(?:share|send|tell|give|provide|forward|read\s*out|enter|type|confirm)\b[^.\n]{0,40}?"
       r"\b(?:otp|pin|cvv|cvc|password|passcode|mpin)\b",
       critical=True, unless=_NEGATION_BEFORE),
    _r("remote_access", "Asks you to install a remote-access / screen-share app", 65, "malware",
       "Screen-sharing apps let the caller watch your screen and your OTPs and operate your banking apps.",
       r"\b(?:anydesk|teamviewer|quicksupport|rustdesk|airdroid|screen\s*shar\w*|remote\s*access)\b",
       critical=True),
    _r("apk_install", "Pushes an APK / unofficial app install", 60, "malware",
       "Apps installed from links (.apk) can read your SMS and OTPs. Genuine providers use the official Play Store/App Store.",
       r"\.apk\b|install\s+(?:this|the)\s+(?:app|apk)|download\s+(?:this|the)?\s*apk"),
    _r("digital_arrest", "'Digital arrest' / safe-account / arrest-warrant language", 75, "digital_arrest",
       "There is no 'digital arrest' in Indian law. Fake officers use it to scare victims into paying.",
       r"digital\s*arrest|arrest\s+warrant|money\s*launder\w*|safe\s*account|"
       r"rbi\s+(?:verification|safe|secure)\s+account|verification\s+account",
       critical=True),
    _r("isolation", "Tells you to stay on the call / not tell anyone", 45, "digital_arrest",
       "Isolating the victim ('don't tell your family', 'stay on video') is a core part of the scam script.",
       r"(?:do\s*not|don'?t|dont)\s+(?:disconnect|cut)\s+(?:the\s+)?(?:video\s+)?call|"
       r"stay\s+on\s+(?:the\s+)?(?:video\s+)?call|"
       r"(?:do\s*not|don'?t|dont)\s+(?:tell|inform)\s+(?:anyone|anybody|your\s+family|family)"),
    _r("parcel_drugs", "Parcel / courier linked to drugs or illegal items", 55, "digital_arrest",
       "A 'seized parcel in your name' is the standard opening of the fake-police scam.",
       r"(?:parcel|courier|consignment|package)[^.\n]{0,80}(?:drugs?|narcotics?|mdma|illegal|contraband|fake\s+passports?|seized)|"
       r"(?:drugs?|narcotics?|mdma|illegal|contraband)[^.\n]{0,80}(?:parcel|courier|consignment|package)"),
    _r("authority", "Claims to be police / CBI / customs / a regulator", 25, "digital_arrest",
       "Impersonating authority creates fear so you stop thinking. Verify by calling the office on its official number.",
       r"\b(?:cbi|enforcement\s+directorate|narcotics|ncb|customs|cyber\s*(?:crime|cell|police)|crime\s*branch|"
       r"trai|supreme\s*court|income\s*tax\s*(?:dept|department|officer)|fedex|dhl|inspector)\b"),
    _r("urgency", "Artificial urgency / deadline", 15, "generic",
       "Scammers rush you so you don't verify. Real institutions give written notice and time.",
       r"within\s+\d+\s*(?:hours?|hrs?|minutes?|mins?)|immediately|urgent(?:ly)?|last\s+warning|"
       r"expires?\s+(?:today|tonight)|final\s+notice|right\s+now|act\s+now|tonight|today\s+only"),
    _r("account_threat", "Threatens to block / suspend your account, SIM or service", 30, "generic",
       "Threats of blocking are used to force a quick click or call. Check the status in the official app instead.",
       r"\b(?:account|sim|number|card|services?|aadhaar|upi|pan)\b[^.\n]{0,40}?"
       r"\b(?:blocked|suspended|deactivated|disconnected|frozen|closed|terminated|cancelled)\b"),
    _r("kyc", "KYC / PAN update demand", 35, "kyc",
       "Banks do not ask you to update KYC through links or by sharing OTPs over SMS/WhatsApp.",
       r"kyc\s*(?:update|expir\w*|pending|verification|incomplete)|update\s+(?:your\s+)?(?:pan|kyc|aadhaar)|"
       r"pan\s+(?:card\s+)?(?:will\s+be\s+)?(?:blocked|suspended)"),
    _r("electricity", "Electricity-bill disconnection threat", 40, "electricity",
       "'Your power will be cut tonight' with a number to call is a widespread scam that often ends in an APK install.",
       r"electricity\s+(?:bill|connection|supply)|power\s+(?:supply|connection)\s+will\s+be\s+(?:cut|disconnected)|"
       r"(?:bill|electricity)[^.\n]{0,40}(?:disconnect\w*|tonight)"),
    _r("investment_promise", "Guaranteed / unrealistic investment returns", 45, "investment",
       "Guaranteed or very high returns do not exist in legitimate investing.",
       r"guaranteed\s+(?:returns?|profit)|double\s+your\s+money|assured\s+returns?|"
       r"\d+\s*%\s*(?:daily|per\s*day|weekly|guaranteed|returns?)|daily\s+(?:profit|income|returns?)|"
       r"risk[- ]free|100%\s*(?:profit|return)|sure[- ]shot|insider\s+tips?"),
    _r("group_lure", "VIP stock group / IPO-allotment / trading-tip lure", 25, "investment",
       "Invite-only groups with 'expert' tips are how investment scams recruit victims.",
       r"(?:vip|premium|exclusive)\s+(?:group|channel|club)|stock\s+(?:tips|signals)|ipo\s+allot\w*|"
       r"institutional\s+(?:account|trading)|(?:join|added)[^.\n]{0,30}(?:whatsapp|telegram)?\s*(?:group|channel)"),
    _r("task_job", "Part-time job / 'task' earning scheme", 40, "job_task",
       "Paid-per-task jobs that later ask for deposits are a known scam pattern.",
       r"part[- ]time\s+job|work\s+from\s+home|earn\s+(?:₹|rs\.?|inr)?\s?[\d,]+\s*(?:per|/|a)\s*(?:day|hour|week)|"
       r"like\s+(?:and|&)\s+subscribe|like\s+(?:youtube\s+)?videos|rate\s+(?:hotels?|products?|restaurants?)|"
       r"prepaid\s+task|task\s+complet\w+"),
    _r("upfront_fee", "Asks you to pay a fee/deposit to receive money or unlock earnings", 40, "generic",
       "Genuine prizes, loans, jobs and refunds do not require you to pay first.",
       r"(?:processing|registration|release|clearance|customs|insurance|refundable|security|verification)\s+"
       r"(?:fee|charges?|deposit|amount)|pay\s+(?:a\s+)?(?:small\s+)?(?:fee|deposit)\s+to\s+(?:receive|release|claim|withdraw)|"
       r"deposit\s+(?:₹|rs\.?|inr)\s?[\d,]+\s+to\s+(?:start|begin|activate)"),
    _r("lottery", "Prize / lottery you never entered", 45, "lottery",
       "You cannot win a lottery you did not enter. Fees to 'claim' prizes are the scam.",
       r"(?:won|winner|selected)\b[^.\n]{0,40}(?:lottery|prize|lucky\s*draw|kbc|iphone|gift|cash\s*prize|reward)|"
       r"kbc\s+lottery|claim\s+(?:your\s+)?(?:prize|reward|gift)"),
    _r("loan_app", "Instant-loan / loan-app lure", 35, "loan",
       "Predatory loan apps harvest contacts and photos and are linked to harassment.",
       r"instant\s+loan|loan\s+(?:approved|sanctioned)|pre[- ]approved\s+loan|no\s+cibil|"
       r"loan\s+without\s+(?:documents|kyc)|(?:contacts?|gallery|photos?)\s+access|loan\s+app"),
    _r("refund_trick", "Refund / 'sent by mistake' pretext", 45, "refund",
       "Refund pretexts are used to get you to approve a payment request or share credentials.",
       r"refund\s+(?:is\s+)?(?:pending|initiated|stuck|failed)|wrongly\s+(?:transferred|credited|sent)|"
       r"(?:amount|money)\s+(?:was\s+)?(?:sent|credited|transferred)\s+(?:by\s+mistake)"),
    _r("qr_receive", "Asks you to scan a QR / enter UPI PIN to RECEIVE money", 70, "refund",
       "You never need a PIN or QR scan to receive money. If a PIN is requested, money is leaving your account.",
       r"scan\s+(?:the\s+|this\s+)?qr[^.\n]{0,40}(?:receive|refund|claim)|"
       r"(?:enter|put)\s+(?:your\s+)?upi\s*pin\s+to\s+receive",
       critical=True),
    _r("family_emergency", "'Hi Mum/Dad, new number' or emergency money request", 40, "family",
       "Impersonating a relative from a 'new number' is a common WhatsApp scam.",
       r"(?:hi|hello|hey)\s+(?:mom|mum|dad|papa|mama|beta)\b[^.\n]{0,80}(?:new\s+number|lost|broke|changed)|"
       r"(?:emergency|hospital|accident)[^.\n]{0,60}(?:send|transfer|pay)\w*\s+(?:me\s+)?(?:money|₹|rs|\d)"),
]

# ----- URL checks ------------------------------------------------------------
_URL_RE = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s<>\"'`]+|"
    r"\b(?:bit\.ly|tinyurl\.com|t\.ly|cutt\.ly|rb\.gy|is\.gd|shorturl\.at)/[^\s<>\"'`]+"
)
SHORTENERS = {"bit.ly", "tinyurl.com", "t.ly", "cutt.ly", "rb.gy", "is.gd", "shorturl.at", "goo.gl", "ow.ly"}
SUSPICIOUS_TLDS = {"xyz", "top", "click", "icu", "site", "vip", "cc", "buzz", "link", "cyou", "sbs", "cfd",
                   "tk", "ml", "cf", "gq", "rest", "monster", "work"}
BRANDS: dict[str, tuple[str, ...]] = {
    "sbi": ("sbi.co.in", "onlinesbi.sbi", "sbi.bank.in", "sbicard.com", "sbilife.co.in"),
    "hdfc": ("hdfcbank.com", "hdfc.com", "hdfclife.com", "hdfcergo.com", "hdfcsec.com"),
    "icici": ("icicibank.com", "icici.com", "icicilombard.com", "iciciprulife.com", "icicisecurities.com"),
    "axis": ("axisbank.com",),
    "paytm": ("paytm.com", "paytmbank.com"),
    "phonepe": ("phonepe.com",),
    "npci": ("npci.org.in",),
    "uidai": ("uidai.gov.in",),
    "incometax": ("incometax.gov.in", "incometaxindia.gov.in"),
    "irctc": ("irctc.co.in",),
    "amazon": ("amazon.in", "amazon.com"),
    "flipkart": ("flipkart.com",),
    "fedex": ("fedex.com",),
    "dhl": ("dhl.com",),
    "indiapost": ("indiapost.gov.in",),
}
_ALL_OFFICIAL = tuple(d for ds in BRANDS.values() for d in ds)


def extract_urls(text: str) -> list[str]:
    seen: list[str] = []
    for m in _URL_RE.finditer(text):
        u = m.group(0).rstrip(".,;:!?)]}>")
        if u and u not in seen:
            seen.append(u)
    return seen


def _host(url: str) -> str:
    u = url if re.match(r"(?i)^https?://", url) else "http://" + url
    try:
        return (urlparse(u).hostname or "").lower()
    except ValueError:
        return ""


def _is_official(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in _ALL_OFFICIAL)


def analyze_url(url: str) -> list[tuple[str, str, int, str]]:
    """Return [(rule_id, label, weight, why)] for a single URL."""
    out: list[tuple[str, str, int, str]] = []
    host = _host(url)
    if not host:
        return out
    tokens = [t for t in re.split(r"[-_.\d]+", host) if t]
    if host in SHORTENERS:
        out.append(("url_shortener", f"Shortened link ({host}) hides the real destination", 25,
                    "Scammers use shorteners so you can't see where the link really goes."))
    if re.match(r"(?i)^http://", url):
        out.append(("url_http", "Link uses plain http:// (no encryption)", 12,
                    "Banks and government sites use https."))
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        out.append(("url_ip", "Link points to a raw IP address", 40, "Genuine services use domain names."))
    if "xn--" in host:
        out.append(("url_punycode", "Link uses look-alike (punycode) characters", 45,
                    "Homograph tricks imitate real domains with similar-looking letters."))
    if "@" in urlparse(url if "://" in url else "http://" + url).netloc:
        out.append(("url_userinfo", "Link hides its real host behind an '@'", 40,
                    "Everything before '@' is ignored by the browser; the real site is after it."))
    tld = host.rsplit(".", 1)[-1]
    if tld in SUSPICIOUS_TLDS:
        out.append(("url_tld", f"Link ends in .{tld}, a cheap domain often used for scam sites", 20,
                    "Not proof by itself, but banks and government sites don't use these."))
    if not _is_official(host):
        for brand in BRANDS:
            if brand in tokens or (len(brand) >= 5 and brand in host.replace("-", "")):
                out.append(("url_lookalike", f"'{host}' imitates {brand.upper()} but is not its real domain", 60,
                            "Real banks/services only use their own domains; look-alikes steal logins."))
                break
        else:
            if "gov" in tokens and not host.endswith((".gov.in", ".nic.in")):
                out.append(("url_lookalike", f"'{host}' pretends to be a government site", 60,
                            "Indian government sites end in .gov.in or .nic.in."))
    return out


# ----- Scam types and advice -------------------------------------------------
TYPE_ORDER = ["digital_arrest", "kyc", "electricity", "investment", "job_task",
              "lottery", "loan", "refund", "family"]

TYPE_NAMES = {
    "digital_arrest": "Digital-arrest / fake law-enforcement scam",
    "kyc": "Fake KYC / account-block scam",
    "electricity": "Electricity-bill disconnection scam",
    "investment": "Fake investment / trading-group scam",
    "job_task": "Part-time job / paid-task scam",
    "lottery": "Lottery / prize scam",
    "loan": "Predatory loan-app scam",
    "refund": "Refund / 'receive money' scam",
    "family": "Family-emergency impersonation",
    "malware": "Malicious app / remote-access scam",
    "credential": "Credential (OTP / PIN) phishing",
    "unclear": "No clear scam pattern",
}

ADVICE: dict[str, list[str]] = {
    "digital_arrest": [
        "Hang up. There is no 'digital arrest' in Indian law; police do not hold people on video calls or ask for money to 'verify' them.",
        "Do not transfer anything to any 'safe', 'RBI' or 'verification' account. No genuine agency asks for this.",
        "Tell a family member or friend right now. 'Don't tell anyone' is part of the script.",
        "If you already paid or shared details, call 1930 immediately and open the 'I already paid' tab.",
    ],
    "kyc": [
        "Don't tap the link and never share an OTP. Open your bank's official app, or call the number printed on your card or passbook, to see whether any KYC action is really pending.",
        "Report the sender number on Sanchar Saathi > Chakshu (sancharsaathi.gov.in).",
    ],
    "electricity": [
        "Don't call the number in the message and don't install anything. Check your bill on your electricity provider's official app/website or the number on a past paper bill.",
        "Never install an APK sent over SMS or WhatsApp.",
    ],
    "investment": [
        "Guaranteed or very high returns are a hallmark of fraud. Investment schemes were about 77% of reported cyber-fraud losses in 2025 (I4C data as reported by IANS).",
        "Check any adviser or broker on SEBI's official website before paying anyone.",
        "Never deposit more to 'unlock' withdrawals. Fake dashboards show fake profits.",
    ],
    "job_task": [
        "Genuine employers do not ask you to pay to start work or to 'unlock' task earnings.",
        "Small early payouts are bait to make you deposit larger amounts.",
    ],
    "lottery": ["You can't win a lottery you never entered. Never pay a fee to claim a prize."],
    "loan": ["Check that the lender is RBI-regulated before sharing documents, and don't install loan apps from links or grant contacts/gallery access."],
    "refund": ["You never need to enter a UPI PIN or scan a QR code to RECEIVE money. If it asks for a PIN, money is going out."],
    "family": ["Call the person on their old, known number before sending money. Ask something only they would know."],
    "malware": [
        "Don't install APKs or screen-share apps at someone's request.",
        "If you already installed one: go offline, uninstall it, call your bank to block cards/UPI, then open the 'I already paid' tab.",
    ],
    "credential": ["Never share an OTP, PIN, CVV or password with anyone, including people claiming to be bank staff."],
    "unclear": ["No strong scam markers found. Still verify the sender through an official channel before clicking, paying or sharing details."],
}

VERDICT_LABELS = {
    "scam": ("VERY LIKELY A SCAM", "बहुत संभव है कि यह स्कैम है"),
    "suspicious": ("SUSPICIOUS: verify before acting", "संदिग्ध: कोई कदम उठाने से पहले जाँचें"),
    "low": ("No strong scam signals (not a guarantee)", "कोई स्पष्ट स्कैम संकेत नहीं (गारंटी नहीं)"),
}


@dataclass
class Hit:
    rule_id: str
    label: str
    why: str
    weight: int
    evidence: str


@dataclass
class Detection:
    score: int
    verdict: str            # scam | suspicious | low
    scam_type: str
    hits: list[Hit] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    critical: bool = False

    @property
    def type_name(self) -> str:
        return TYPE_NAMES.get(self.scam_type, self.scam_type)


def _noisy_or(weights: list[int]) -> int:
    p = 1.0
    for w in weights:
        p *= 1 - w / 100
    return round(100 * (1 - p))


def detect(text: str) -> Detection:
    """Score a message. Each rule counts once; scores combine as noisy-OR; critical rules floor the score at 85."""
    hits: list[Hit] = []
    critical = False
    cat_weight: dict[str, int] = {}

    for rule in RULES:
        for m in rule.pattern.finditer(text):
            if rule.unless_before and rule.unless_before.search(text[max(0, m.start() - 40):m.start()]):
                continue
            ev = m.group(0).strip().replace("\n", " ")
            hits.append(Hit(rule.id, rule.label, rule.why, rule.weight, ev[:90]))
            critical = critical or rule.critical
            cat_weight[rule.category] = cat_weight.get(rule.category, 0) + rule.weight
            break

    urls = extract_urls(text)
    seen_url_rules: set[str] = set()
    for u in urls:
        for rid, label, weight, why in analyze_url(u):
            if rid in seen_url_rules:
                continue
            seen_url_rules.add(rid)
            hits.append(Hit(rid, label, why, weight, u[:90]))

    score = _noisy_or([h.weight for h in hits])
    if critical:
        score = max(score, 85)
    verdict = "scam" if score >= 60 else "suspicious" if score >= 30 else "low"

    scam_type = "unclear"
    primary = {c: w for c, w in cat_weight.items() if c in TYPE_ORDER}
    if primary:
        scam_type = max(primary, key=lambda c: primary[c])
    elif "malware" in cat_weight:
        scam_type = "malware"
    elif "credential" in cat_weight:
        scam_type = "credential"
    if verdict == "low":
        scam_type = "unclear"
    return Detection(score, verdict, scam_type, hits, urls, critical)


# ----------------------------------------------------------------------------
# Incident extraction (post-fraud)
# ----------------------------------------------------------------------------
BANK_ALIASES = {
    "SBI": r"sbi|state\s+bank(?:\s+of\s+india)?", "HDFC Bank": r"hdfc", "ICICI Bank": r"icici",
    "Axis Bank": r"axis", "Kotak": r"kotak", "Punjab National Bank": r"pnb|punjab\s+national",
    "Bank of Baroda": r"bank\s+of\s+baroda|bob", "Canara Bank": r"canara", "Union Bank": r"union\s+bank",
    "IDFC First": r"idfc", "Yes Bank": r"yes\s+bank", "IndusInd": r"indusind", "Federal Bank": r"federal\s+bank",
    "Bank of India": r"bank\s+of\s+india", "IDBI": r"idbi", "Indian Bank": r"indian\s+bank",
    "Bandhan": r"bandhan", "RBL": r"rbl", "Paytm Payments Bank": r"paytm\s+payments?\s+bank",
}
APP_ALIASES = {
    "Google Pay": r"google\s*pay|gpay|g\s*pay", "PhonePe": r"phone\s*pe", "Paytm": r"paytm",
    "BHIM": r"bhim", "Amazon Pay": r"amazon\s*pay",
}
_TIME_RE = re.compile(r"(?i)\b\d{1,2}[:.]\d{2}\s?(?:am|pm)\b")
_DATE_RE = re.compile(
    r"(?i)\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|"
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?(?:\s+\d{2,4})?\b|"
    r"\b(?:today|yesterday)\b"
)
_AMOUNT_RE = re.compile(
    r"(?i)(?:₹|\brs\.?|\binr)\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr\b)?"
)
_UTR_LABELLED_RE = re.compile(
    r"(?i)(?:\butr\b|\brrn\b|ref(?:erence)?(?:\s*(?:no\.?|number|id))?|txn(?:\s*(?:id|no\.?))?|"
    r"transaction\s*(?:id|no\.?|number|ref)?|upi\s*ref(?:erence)?(?:\s*(?:no\.?|id))?)"
    r"\W{0,12}(\d{12})(?!\d)"
)
_UTR_ALNUM_RE = re.compile(
    r"(?i)(?:\butr\b|\brrn\b|ref(?:erence)?(?:\s*(?:no\.?|number|id))?|txn(?:\s*(?:id|no\.?))?|"
    r"transaction\s*(?:id|no\.?|number)?)\W{0,12}([A-Z0-9]{13,22})\b"
)
_TWELVE_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\s-]?|91[\s-]|0)?([6-9]\d{4}[\s-]?\d{5})(?!\d)")
_UPI_RE = re.compile(r"(?<![\w.\-])([A-Za-z0-9][\w.\-]{1,48})@([A-Za-z][A-Za-z0-9]{1,20})\b(?!\.[A-Za-z])")
_ACCT_LAST4_RE = re.compile(r"(?i)\b(?:a/?c|acct|account|card)\b\D{0,12}?(?:x+|\*+)?\s?(\d{4})(?!\d)")


@dataclass
class Incident:
    amounts: list[str] = field(default_factory=list)
    utrs: list[str] = field(default_factory=list)
    possible_utrs: list[str] = field(default_factory=list)
    upi_ids: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    banks: list[str] = field(default_factory=list)
    apps: list[str] = field(default_factory=list)
    account_last4: list[str] = field(default_factory=list)
    when_hints: list[str] = field(default_factory=list)


def _uniq(items) -> list:
    out: list = []
    for i in items:
        if i not in out:
            out.append(i)
    return out


def _indian_group(n: int) -> str:
    """12345678 -> 1,23,45,678 (Indian digit grouping)."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def _fmt_amount(value: float) -> str:
    whole = int(value)
    if value == whole:
        return f"₹{_indian_group(whole)}"
    return f"₹{_indian_group(whole)}.{round((value - whole) * 100):02d}"


def extract_incident(text: str) -> Incident:
    inc = Incident()

    # amounts
    amts: list[str] = []
    for m in _AMOUNT_RE.finditer(text):
        raw = m.group(1).replace(",", "").strip(".")
        if not raw:
            continue
        try:
            val = float(raw)
        except ValueError:
            continue
        unit = (m.group(2) or "").lower()
        if unit.startswith(("lakh", "lac")):
            val *= 1e5
        elif unit.startswith(("crore", "cr")):
            val *= 1e7
        amts.append(_fmt_amount(val))
    inc.amounts = _uniq(amts)

    # UTRs: labelled first (high confidence)
    utrs = [m.group(1) for m in _UTR_LABELLED_RE.finditer(text)]
    for m in _UTR_ALNUM_RE.finditer(text):
        tok = m.group(1)
        if any(c.isdigit() for c in tok) and any(c.isalpha() for c in tok):
            utrs.append(tok.upper())
    inc.utrs = _uniq(utrs)

    # other 12-digit numbers -> "possible" (skip Aadhaar-labelled and 91+phone lookalikes)
    possible: list[str] = []
    for m in _TWELVE_RE.finditer(text):
        tok = m.group(0)
        if tok in inc.utrs:
            continue
        before = text[max(0, m.start() - 25):m.start()]
        if re.search(r"(?i)aadh?aa?r|uid", before):
            continue
        if tok.startswith("91") and tok[2] in "6789":
            continue
        possible.append(tok)
    inc.possible_utrs = _uniq(possible)

    inc.upi_ids = _uniq(f"{m.group(1)}@{m.group(2)}" for m in _UPI_RE.finditer(text))
    inc.phones = _uniq("+91" + re.sub(r"\D", "", m.group(1)) for m in _PHONE_RE.finditer(text))
    inc.urls = extract_urls(text)

    low = text.lower()
    inc.banks = [name for name, pat in BANK_ALIASES.items() if re.search(rf"\b(?:{pat})\b", low)]
    inc.apps = [name for name, pat in APP_ALIASES.items() if re.search(rf"\b(?:{pat})\b", low)]
    inc.account_last4 = _uniq("XX" + m.group(1) for m in _ACCT_LAST4_RE.finditer(text))
    inc.when_hints = _uniq([m.group(0).strip().upper() if ":" in m.group(0) or "." in m.group(0)
                            else m.group(0).strip() for m in _DATE_RE.finditer(text)] +
                           [m.group(0).strip().upper() for m in _TIME_RE.finditer(text)])
    return inc


def auto_summary(det: Detection, redacted_text: str) -> str:
    snippet = " ".join(redacted_text.split())[:350]
    kind = det.type_name if det.verdict != "low" else "online fraud"
    return f"Type of fraud (auto-detected, please correct if wrong): {kind}. What happened, in my words: {snippet}"


# ----------------------------------------------------------------------------
# Response pack
# ----------------------------------------------------------------------------
STEPS = [
    ("Call 1930 now", "अभी 1930 पर कॉल करें",
     "The National Cyber Crime Helpline for financial fraud. Read the call script below, top to bottom, and ask for the complaint reference number."),
    ("Alert your bank and block", "अपने बैंक को सूचित करें और ब्लॉक करवाएँ",
     "Use the number on your card or the bank's app. Report the unauthorised transaction, ask them to block cards/UPI/net-banking as needed, and note the complaint number."),
    ("Preserve the evidence", "सबूत सुरक्षित रखें",
     "Don't delete chats, call logs, SMS or the app. Screenshot every transaction page and the scammer's number, profile and links."),
    ("File the formal complaint within 24 hours", "24 घंटे के भीतर औपचारिक शिकायत दर्ज करें",
     "On cybercrime.gov.in, using the complaint text below. After your 1930 call you receive an SMS with a reference number and a link to the portal."),
    ("Secure your accounts", "अपने खाते सुरक्षित करें",
     "Change passwords and UPI PIN. If you installed an APK or screen-share app, uninstall it and check your other bank accounts and apps."),
    ("Beware of 'recovery' offers", "'रिकवरी' के झूठे प्रस्तावों से सावधान",
     "Anyone who contacts you promising to recover your money for a fee is very likely a second scam."),
    ("Follow up", "फॉलो-अप करें",
     "Track the complaint on cybercrime.gov.in and keep printouts to take to your bank branch or cyber cell."),
]


def elapsed_banner(minutes: int) -> tuple[str, str]:
    """Returns (level, message). level in red|orange|yellow."""
    if minutes <= 120:
        return "red", "First two hours: the money may still be moving through the banking chain. Call 1930 before anything else."
    if minutes <= 1440:
        return "orange", "Call 1930 now, then file the formal complaint on cybercrime.gov.in within 24 hours of the incident."
    return "yellow", ("It's later than ideal, but report anyway: call 1930, file on cybercrime.gov.in and inform your bank "
                      "in writing. Reports also help block the scammers' accounts.")


@dataclass
class Fields:
    name: str = ""
    mobile: str = ""
    location: str = ""
    bank: str = ""
    account: str = ""
    amount: str = ""
    utrs: list[str] = field(default_factory=list)
    when: str = ""
    scam_phones: list[str] = field(default_factory=list)
    scam_upi: list[str] = field(default_factory=list)
    scam_links: list[str] = field(default_factory=list)
    description: str = ""


def split_csv(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,\n;]+", s) if p.strip()]


def missing_items(f: Fields) -> list[str]:
    miss = []
    if not f.utrs:
        miss.append("UTR / transaction ID. Open your bank or UPI app > transaction history > the debit, and screenshot it. "
                    "It may be called UPI Ref No. or RRN; in Google Pay it is the 'UPI transaction ID'.")
    if not f.amount:
        miss.append("Amount lost.")
    if not f.bank:
        miss.append("Bank / wallet / UPI app the money left from.")
    if not f.account:
        miss.append("Your account number (last 4 is enough to start) or UPI ID that was debited.")
    if not f.when:
        miss.append("Date and approximate time of each transaction.")
    if not f.mobile:
        miss.append("Your mobile number.")
    if not (f.scam_phones or f.scam_upi or f.scam_links):
        miss.append("Any scammer identifier: phone number, UPI ID / bank account, website, app name or social profile.")
    return miss


def _or(v: str, placeholder: str) -> str:
    return v.strip() if v and v.strip() else f"[{placeholder}]"


def _join(items: list[str], placeholder: str) -> str:
    return ", ".join(items) if items else f"[{placeholder}]"


def _transactions(f: Fields) -> list[str]:
    amounts = split_csv(f.amount) if f.amount else []
    if f.utrs and len(amounts) == len(f.utrs):
        return [f"UTR {u}: {a}" for u, a in zip(f.utrs, amounts)]
    lines = [f"UTR {u}" for u in f.utrs]
    if not lines:
        lines = ["[UTR / transaction ID: find it in your bank or UPI app]"]
    if amounts:
        lines.append("Amount(s): " + ", ".join(amounts))
    return lines


def build_call_script(f: Fields) -> str:
    tx = "\n".join(f"     - {t}" for t in _transactions(f))
    return f"""1930 CALL SCRIPT (read top to bottom; keep your bank app open)

1. Say: "I want to report a financial cyber fraud."
2. Amount lost: {_or(f.amount, 'amount')}
3. Your name: {_or(f.name, 'your name')}   Mobile: {_or(f.mobile, 'your mobile number')}
4. Your district / nearest police station: {_or(f.location, 'district, police station')}
5. Bank / wallet / app the money left from: {_or(f.bank, 'bank or UPI app')}
   Account / UPI ID debited: {_or(f.account, 'account last 4 or UPI ID')}
6. Transactions (one by one):
{tx}
   Date / time: {_or(f.when, 'date and time')}
7. Fraudster details:
   Phone: {_join(f.scam_phones, 'phone number(s)')}
   UPI ID / account: {_join(f.scam_upi, 'UPI ID or account')}
   Website / app / profile: {_join(f.scam_links, 'link, app or profile')}
8. What happened (one or two sentences): {_or(f.description, 'what happened')}
9. Ask: "Please give me the complaint reference number." Write it down.
"""


def build_complaint(f: Fields) -> str:
    tx = "\n".join(f"  - {t}" for t in _transactions(f))
    return f"""SUBJECT: Financial cyber fraud, online/UPI transaction(s) of {_or(f.amount, 'amount')}

To: Cyber Crime Cell / National Cyber Crime Reporting Portal (cybercrime.gov.in)

COMPLAINANT: {_or(f.name, 'your name')}, Mobile: {_or(f.mobile, 'your mobile number')}, {_or(f.location, 'district / nearest police station')}

INCIDENT DATE / TIME: {_or(f.when, 'date and time')}

DESCRIPTION:
{_or(f.description, 'what happened')}

TRANSACTION DETAILS:
  Bank / app: {_or(f.bank, 'bank or UPI app')}   Account / UPI ID debited: {_or(f.account, 'account last 4 or UPI ID')}
{tx}

FRAUDSTER DETAILS:
  Phone number(s): {_join(f.scam_phones, 'phone number(s)')}
  UPI ID(s) / account(s): {_join(f.scam_upi, 'UPI ID or account')}
  Website / app / profile: {_join(f.scam_links, 'link, app or profile')}

ACTION ALREADY TAKEN:
  Called 1930 on [date/time], reference number [____]. Informed my bank on [date/time], complaint number [____].

REQUEST:
  Please register this complaint, trace the beneficiary accounts and UPI IDs listed above, and place them on hold
  so the defrauded amount can be traced and frozen. Please advise on next steps.

EVIDENCE ATTACHED: screenshots of the transactions, the scammer's messages / call log / profile, and any app or link used.
"""


def build_bank_letter(f: Fields) -> str:
    tx = "\n".join(f"  - {t}" for t in _transactions(f))
    return f"""Subject: URGENT: Unauthorised/fraudulent transaction(s). Please block and record complaint

Dear Sir/Madam,

I am {_or(f.name, 'your name')}, holder of account/UPI ID {_or(f.account, 'account last 4 or UPI ID')} with {_or(f.bank, 'bank')}
(registered mobile {_or(f.mobile, 'your mobile number')}).

I was the victim of an online fraud on {_or(f.when, 'date and time')}. The following transaction(s) were made:
{tx}

The money was sent to: {_join(f.scam_upi, 'beneficiary UPI ID / account')}.

I have reported this to the National Cyber Crime Helpline (1930) on [date/time], reference number [____], and will file/have filed a
complaint on cybercrime.gov.in.

I request you to: (1) block further debits through my cards, UPI and net banking as appropriate, (2) record this fraud complaint and
give me a written complaint number, (3) coordinate with the beneficiary bank/app to hold the credited amount, and (4) tell me in
writing what further documents you need.

Yours faithfully,
{_or(f.name, 'your name')}
"""


def build_pack(f: Fields) -> str:
    miss = missing_items(f)
    miss_txt = "\n".join(f"  [ ] {m}" for m in miss) if miss else "  None. You have everything the helpline usually asks for."
    steps = "\n".join(f"{i}. {t}: {d}" for i, (t, _hi, d) in enumerate(STEPS, 1))
    return (
        "GOLDENHOUR RESPONSE PACK\n"
        "Reporting channels: call 1930 (financial cyber fraud helpline) and file at cybercrime.gov.in\n"
        "=" * 70 + "\n\nWHAT TO DO, IN ORDER\n" + steps +
        "\n\nSTILL MISSING\n" + miss_txt +
        "\n\n" + "=" * 70 + "\n" + build_call_script(f) +
        "\n" + "=" * 70 + "\n\nCOMPLAINT TEXT (paste into cybercrime.gov.in)\n\n" + build_complaint(f) +
        "\n" + "=" * 70 + "\n\nLETTER / EMAIL TO YOUR BANK\n\n" + build_bank_letter(f) +
        "\nGenerated locally by GoldenHour. Check every detail before submitting. This is not legal advice.\n"
    )
