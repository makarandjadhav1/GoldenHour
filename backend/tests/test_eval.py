"""Evaluation gate (BRD O4): published thresholds must hold. Run with: uv run pytest tests/test_eval.py -s"""

import json
from collections import Counter
from pathlib import Path

from app import detect
from app.text import normalize, redact

EVAL = Path(__file__).resolve().parent.parent / "eval"


def rows(name):
    return [json.loads(l) for l in (EVAL / name).read_text().splitlines()]


def verdict(text):
    t, _ = redact(normalize(text)[0])
    return detect.detect(t)


def test_thresholds():
    scams, genuine = rows("scam_set.jsonl"), rows("genuine_set.jsonl")
    assert len(scams) >= 100 and len(genuine) >= 100
    caught, per_cat, missed = 0, Counter(), []
    for r in scams:
        v = verdict(r["text"])["verdict"] != "low"  # scam or suspicious counts as caught
        caught += v
        per_cat[r["category"]] += v
        if not v:
            missed.append(r["text"][:80])
    false_alarm = [r["text"][:80] for r in genuine if verdict(r["text"])["verdict"] != "low"]
    recall, fa_rate = caught / len(scams), len(false_alarm) / len(genuine)
    accuracy = (caught + len(genuine) - len(false_alarm)) / (len(scams) + len(genuine))
    print(f"\nscam recall {recall:.1%}  genuine false-alarm {fa_rate:.1%}  accuracy {accuracy:.1%}")
    print("per-category caught:", dict(per_cat), "\nmissed:", missed, "\nfalse alarms:", false_alarm)
    assert accuracy >= 0.85 and fa_rate <= 0.05
