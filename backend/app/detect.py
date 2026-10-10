"""Scam detection: rules from data, URL checks, noisy-OR scoring. Pure functions; rules are loaded once."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

DATA = Path(__file__).resolve().parent.parent / "data"
TYPE_ORDER = ["digital_arrest", "kyc", "electricity", "investment", "job_task", "lottery", "loan", "refund", "family"]
URL_RE = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s<>\"'`]+|"
    r"\b(?:bit\.ly|tinyurl\.com|t\.ly|cutt\.ly|rb\.gy|is\.gd|shorturl\.at)/[^\s<>\"'`]+"
)

RULES: list[dict] = []   # compiled rule dicts; set by load_rules()
BRANDS: dict = {}
ADVICE: dict = {}


def load_rules(rules: list[dict] | None = None) -> None:
    """Compile rules (from DB rows or the JSON file) once at startup."""
    rules = rules if rules is not None else json.loads((DATA / "rules.json").read_text())
    RULES[:] = [
        {**r, "re": re.compile(r["pattern"], re.I),
         "unless": re.compile(r["unlessBefore"], re.I) if r.get("unlessBefore") else None}
        for r in rules if r.get("enabled", True)
    ]
    BRANDS.update(json.loads((DATA / "brands.json").read_text()))
    ADVICE.update(json.loads((DATA / "advice.json").read_text()))


def _pick(d: dict, lang: str) -> str:
    return d.get(lang) or d["en"]


def extract_urls(text: str) -> list[str]:
    out: list[str] = []
    for m in URL_RE.finditer(text):
        u = m.group(0).rstrip(".,;:!?)]}>")
        if u and u not in out:
            out.append(u)
    return out


def _host(url: str) -> str:
    u = url if re.match(r"(?i)^https?://", url) else "http://" + url
    try:
        return (urlparse(u).hostname or "").lower()
    except ValueError:
        return ""


def _official(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for ds in BRANDS["brands"].values() for d in ds)


def analyze_url(url: str) -> list[tuple[str, str, int, str]]:
    """Lexical checks only. A user URL is never fetched. Returns [(rule_id, label, weight, why)]."""
    out = []
    host = _host(url)
    if not host:
        return out
    tokens = [t for t in re.split(r"[-_.\d]+", host) if t]
    if host in BRANDS["shorteners"] or host in {"goo.gl", "ow.ly"}:
        out.append(("url_shortener", f"Shortened link ({host}) hides the real destination", 25,
                    "Scammers use shorteners so you can't see where the link really goes."))
    if re.match(r"(?i)^http://", url):
        out.append(("url_http", "Link uses plain http:// (no encryption)", 12, "Banks and government sites use https."))
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        out.append(("url_ip", "Link points to a raw IP address", 40, "Genuine services use domain names."))
    if "xn--" in host:
        out.append(("url_punycode", "Link uses look-alike (punycode) characters", 45,
                    "Homograph tricks imitate real domains with similar-looking letters."))
    if "@" in urlparse(url if "://" in url else "http://" + url).netloc:
        out.append(("url_userinfo", "Link hides its real host behind an '@'", 40,
                    "Everything before '@' is ignored by the browser; the real site is after it."))
    tld = host.rsplit(".", 1)[-1]
    if tld in BRANDS["tlds"]:
        out.append(("url_tld", f"Link ends in .{tld}, a cheap domain often used for scam sites", 20,
                    "Not proof by itself, but banks and government sites don't use these."))
    if not _official(host):
        for brand in BRANDS["brands"]:
            if brand in tokens or (len(brand) >= 5 and brand in host.replace("-", "")):
                out.append(("url_lookalike", f"'{host}' imitates {brand.upper()} but is not its real domain", 60,
                            "Real banks/services only use their own domains; look-alikes steal logins."))
                break
        else:
            if "gov" in tokens and not host.endswith((".gov.in", ".nic.in")):
                out.append(("url_lookalike", f"'{host}' pretends to be a government site", 60,
                            "Indian government sites end in .gov.in or .nic.in."))
    return out


def noisy_or(weights: list[int]) -> int:
    p = 1.0
    for w in weights:
        p *= 1 - w / 100
    return round(100 * (1 - p))


def detect(text: str, lang: str = "en") -> dict:
    """Score already-normalised, already-redacted text."""
    hits, critical, cat_weight = [], False, {}
    for r in RULES:
        for m in r["re"].finditer(text):
            if r["unless"] and r["unless"].search(text[max(0, m.start() - 40):m.start()]):
                continue
            hits.append({"ruleId": r["id"], "label": _pick(r["label"], lang), "why": _pick(r["why"], lang),
                         "weight": r["weight"], "evidence": m.group(0).strip().replace("\n", " ")[:90],
                         "start": m.start(), "end": m.end(), "critical": r["critical"]})
            critical = critical or r["critical"]
            cat_weight[r["category"]] = cat_weight.get(r["category"], 0) + r["weight"]
            break

    urls = extract_urls(text)
    seen: set[str] = set()
    for u in urls:
        for rid, label, weight, why in analyze_url(u):
            if rid in seen:
                continue
            seen.add(rid)
            i = text.find(u)
            hits.append({"ruleId": rid, "label": label, "why": why, "weight": weight, "evidence": u[:90],
                         "start": i, "end": i + len(u), "critical": False})

    score = noisy_or([h["weight"] for h in hits])
    if critical:
        score = max(score, 85)
    verdict = "scam" if score >= 60 else "suspicious" if score >= 30 else "low"

    scam_type = "unclear"
    primary = {c: w for c, w in cat_weight.items() if c in TYPE_ORDER}
    if primary:
        scam_type = max(TYPE_ORDER, key=lambda c: primary.get(c, -1))
    elif "malware" in cat_weight:
        scam_type = "malware"
    elif "credential" in cat_weight:
        scam_type = "credential"
    if verdict == "low":
        scam_type = "unclear"
    advice = ADVICE["advice"].get(lang, ADVICE["advice"]["en"]).get(scam_type) or ADVICE["advice"]["en"][scam_type]
    return {"score": score, "verdict": verdict, "scamType": scam_type, "scamTypeName": ADVICE["typeNames"][scam_type],
            "critical": critical, "hits": hits, "urls": urls, "advice": advice}
