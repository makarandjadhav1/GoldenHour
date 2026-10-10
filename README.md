# GoldenHour

First aid for UPI and cyber fraud in India: check a suspicious message, then turn what happened into a 1930 call script,
a cybercrime.gov.in complaint sheet and a bank letter. Independent tool, not a government service. It does not file anything.

## Run locally
```
# Postgres (any 14+), then:
cd backend && export DATABASE_URL=postgresql://user@host/goldenhour
uv sync && uv run python seed.py && uv run uvicorn app.main:app --port 8000
cd frontend && npm i && npm run dev        # http://localhost:5173 (proxies /v1 to :8000)
```
`docker compose up` starts Postgres + API. Env: `DATABASE_URL`, `WEB_ORIGIN`, `ANTHROPIC_API_KEY` (optional), `ANTHROPIC_MODEL_FAST`,
`AI_ENABLED`, `AI_DAILY_TOKEN_CAP`, `RATE_LIMIT_GENERAL`, `RATE_LIMIT_AI`, `TRUST_PROXY`.

## Tests
`cd backend && uv run pytest` (unit, property, API, privacy canary, eval gate) · `cd frontend && npx vitest run && npx playwright test` (E2E + axe).

## Scaling
Stateless API (add instances behind a load balancer); rules and KB cached in memory; check/extract/pack never touch the DB;
static frontend served from a CDN. Rate limits are per-instance in memory: use LB/CDN limits when running many instances.

## Honest gaps (verify before public launch)
- Evaluation sets were written by the same author as the rules, so the measured accuracy is optimistic. Needs an independent set.
- Portal field order (`backend/data/portal_sheet.json`) is unverified (`verifiedOn: null`); the UI says so.
- KB has 17 entries (target 20), only from the sources in the BRD; verification dates are copied from the BRD, not re-checked.
- Hindi and Marathi copy is machine-authored and needs native-speaker review; rules have no Hindi/Hinglish patterns beyond English keywords.
- The AI second opinion was tested only against a mock; no live Anthropic call was made. AI "polish" is not built (R1.1).
- No offline/PWA (analysis is server-side), no read-aloud voice testing on real devices, no TalkBack/NVDA pass, no legal review.
- Privacy claim is "nothing stored or logged on our server", not "nothing leaves your device".
# GoldenHour
