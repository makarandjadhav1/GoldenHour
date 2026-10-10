"""Optional Claude second opinion. Opt-in, masked input only, output sanitised. Scores and verdicts always come from rules."""

import json
import os
import re
from pathlib import Path

PROMPT = (Path(__file__).parent / "prompts" / "explain.md").read_text()
MAX_TOKENS = 600
_LONG_NUM = re.compile(r"\d{6,}")
_IDS = re.compile(r"\S+@\S+|https?://\S+|www\.\S+")


def enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY")) and os.environ.get("AI_ENABLED", "true") != "false"


def mask_for_ai(text: str) -> str:
    """Last line of defence: long numbers, e-mail/UPI ids and links never leave the server."""
    return _IDS.sub("[ID]", _LONG_NUM.sub("[NUMBER]", text))[:3000]


def parse_json(raw: str) -> dict:
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    a, b = raw.find("{"), raw.rfind("}")
    if a == -1 or b <= a:
        raise ValueError("no JSON")
    obj = json.loads(raw[a : b + 1])
    if not isinstance(obj, dict):
        raise ValueError("not an object")
    return obj


def clean(obj: dict) -> dict:
    """Keep only expected keys; drop anything that looks like an invented number, id or link."""

    def ok(s: str) -> bool:
        return not (_LONG_NUM.search(s) or _IDS.search(s))

    flags = obj.get("extraRedFlags", [])
    flags = [str(x)[:140] for x in flags[:3] if ok(str(x))] if isinstance(flags, list) else []
    why, fam = str(obj.get("why", ""))[:700], str(obj.get("tellFamily", ""))[:400]
    conf = obj.get("confidence") if obj.get("confidence") in ("low", "medium", "high") else "low"
    if not (ok(why) and ok(fam)):
        raise ValueError("unsafe output")
    return {"why": why, "extraRedFlags": flags, "tellFamily": fam, "confidence": conf}


def ask_claude(system: str, user: str, model: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic(timeout=30.0, max_retries=1)
    resp = client.messages.create(
        model=model, max_tokens=max_tokens, temperature=0.2, system=system, messages=[{"role": "user", "content": user}]
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def explain(masked_text: str, rule_labels: list[str], language: str) -> dict:
    user = (
        f"Language for 'why' and 'tellFamily': {language}\nRules already triggered: {json.dumps(rule_labels)}\n"
        f"<untrusted_message>\n{mask_for_ai(masked_text)}\n</untrusted_message>"
    )
    model = os.environ.get("ANTHROPIC_MODEL_FAST", "claude-haiku-5-5")
    return clean(parse_json(ask_claude(PROMPT, user, model, MAX_TOKENS)))
