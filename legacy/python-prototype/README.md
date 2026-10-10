# GoldenHour — first aid for UPI & cyber fraud (India)

Paste a suspicious message → verdict + the exact red flags.
Already paid? → a 1930 call script, a ready-to-file cybercrime.gov.in complaint, a bank letter, and the 7 steps in order.

## Run (works with no API key)
```bash
python3 -m venv .venv && source .venv/bin/activate   # venv is required on Kali/Debian
pip install -r requirements.txt
python -m pytest -q tests                            # 23 tests, no network
streamlit run app.py                                 # demo mode
# optional Claude layer:
cp .env.example .env && nano .env                    # add ANTHROPIC_API_KEY
```

## Layout
- `scamcore.py` — redaction, 19 scam rules + URL checks, incident extraction, pack builders (no network)
- `llm.py` — optional Claude layer with guard rails (numbers/UPI IDs must already exist in the draft)
- `app.py` — Streamlit UI · `samples.py` — synthetic data · `tests/test_core.py`

## Tested vs. untested
Tested: rules, redaction, extraction, builders, guard rails (23 pytest tests); the whole UI on every sample via Streamlit's
headless AppTest; server start. NOT tested: live calls to the Anthropic API (no key in the build sandbox) — the failure
paths were tested with a fake client. Check the model name in `ANTHROPIC_MODEL` against your account.

## Limitations
Rule engine = heuristics (false positives/negatives happen; novel scams slip through). English-only rules. Extracts
12-digit UPI/IMPS refs and labelled alphanumeric refs; it does not read screenshots. It does not file anything for you.
Not legal advice. Hindi UI covers verdict + step titles only; Marathi needs Claude.

## Sources behind the problem statement
I4C/NCRP figures via IANS (Jan 2026), Indian Express (Jul 2026); 1930 detail checklist from bank/I4C advisories; Chakshu scope
per DoT/Sanchar Saathi explainers.
