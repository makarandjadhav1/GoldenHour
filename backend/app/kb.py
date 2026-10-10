"""Ask: keyword search over the cached knowledge base. Pure functions; no guessing below the threshold."""

import re

KB: list[dict] = []
THRESHOLD = 0.3
STOP = set(
    [
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "i",
        "me",
        "my",
        "to",
        "do",
        "of",
        "in",
        "on",
        "it",
        "and",
        "or",
        "for",
        "what",
        "how",
        "can",
        "if",
        "does",
        "should",
        "this",
        "that",
        "with",
        "at",
        "be",
    ]
)
FALLBACK = "I don't have a verified answer for that. The best next step is calling 1930 or checking cybercrime.gov.in."


def load_kb(entries: list[dict]) -> None:
    KB[:] = entries


def _tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[\w]+", s.lower().replace("'", "")) if t not in STOP}


def _pick(d: dict, lang: str) -> str:
    return d.get(lang) or d["en"]


def search(question: str, lang: str = "en", top: int = 3) -> dict:
    qt = _tokens(question)
    if not qt:
        return {"fallback": True, "message": FALLBACK, "results": []}
    scored = []
    for e in KB:
        qtext, atext = _tokens(_pick(e["q"], lang) + " " + e["q"]["en"]), _tokens(_pick(e["a"], lang))
        kw = {t for k in e["keywords"] for t in _tokens(k)}
        kw_phrase = sum(1 for k in e["keywords"] if k.lower() in question.lower())
        score = (3 * len(qt & qtext) + 2 * len(qt & kw) + len(qt & atext) + 2 * kw_phrase) / (3 * len(qt))
        score += len(qt & qtext) / max(len(qtext), 1)  # prefer entries whose title the question covers
        scored.append((score, e))
    scored.sort(key=lambda x: -x[0])
    results = [
        {
            "id": e["id"],
            "q": _pick(e["q"], lang),
            "a": _pick(e["a"], lang),
            "sources": e["sources"],
            "verifiedOn": e["verifiedOn"],
            "score": round(s, 2),
            "translationPending": lang not in e["a"],
        }
        for s, e in scored[:top]
        if s >= THRESHOLD
    ]
    if not results:
        return {"fallback": True, "message": FALLBACK, "results": []}
    return {"fallback": False, "message": None, "results": results}
