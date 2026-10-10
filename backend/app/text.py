"""Text cleanup and secret masking. Pure functions."""

import re
import unicodedata

MAX_CHARS = 5000
_DIGITS = str.maketrans("०१२३४५६७८९٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_ZERO_WIDTH = re.compile("[\u200b-‍﻿]")

_CARD = re.compile(r"(?<!\d)(?:\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{1,4}|\d{15,16})(?!\d)")
_AADHAAR_LABELLED = re.compile(r"(?i)(aadh?aa?r|uid)(\D{0,15})(\d{4}\s?\d{4}\s?\d{4})(?!\d)")
_AADHAAR_SPACED = re.compile(r"(?<!\d)\d{4} \d{4} \d{4}(?!\d)")
_OTP_AFTER = re.compile(r"(?i)\b(otp|cvv|cvc|mpin|upi\s*pin|pin)\b(?!\s*code)(\D{0,20}?)(\d{3,8})(?!\d)")
_OTP_BEFORE = re.compile(r"(?i)(?<!\d)(\d{4,8})(?!\d)(\s+is\s+(?:your|the)\s+(?:otp|one[- ]time\s+password|verification\s+code))")


def normalize(text: str) -> tuple[str, bool]:
    """NFKC, Indic digits to ASCII, drop zero-width chars, tidy whitespace, cap length."""
    text = unicodedata.normalize("NFKC", text).translate(_DIGITS)
    text = _ZERO_WIDTH.sub("", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:MAX_CHARS], len(text) > MAX_CHARS


def redact(text: str) -> tuple[str, int]:
    """Mask card, Aadhaar, OTP/PIN/CVV values. Returns (clean_text, n_masked)."""
    n = 0

    def sub(pattern, repl, s):
        nonlocal n
        s, k = pattern.subn(repl, s)
        n += k
        return s

    text = sub(_CARD, "[CARD-NO REDACTED]", text)
    text = sub(_AADHAAR_LABELLED, lambda m: f"{m.group(1)}{m.group(2)}[AADHAAR REDACTED]", text)
    text = sub(_AADHAAR_SPACED, "[AADHAAR-LIKE REDACTED]", text)
    text = sub(_OTP_AFTER, lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
    text = sub(_OTP_BEFORE, lambda m: f"[REDACTED]{m.group(2)}", text)
    return text, n
