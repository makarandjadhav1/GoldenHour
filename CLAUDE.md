# GoldenHour: instructions for Claude Code

Privacy-first web app (React + FastAPI + Postgres) that helps people in India check scam messages and prepare UPI/cyber-fraud
reports (1930 call script, cybercrime.gov.in complaint, bank letter). It does NOT file complaints and is NOT a government service.
Read docs/BUILD_PLAN.md first; BRD/DRD/TRD in docs/ describe behaviour (BUILD_PLAN wins where they differ).

## Non-negotiables
1. Backend is plain functions. Classes only for Pydantic schemas. No ORM, no DI, no extra layers. Keep code minimal.
2. User text is processed in memory only: never stored, never logged, never in DB. Postgres holds rules, KB, AI budget, error notes only.
3. `frontend/src/api.ts` is the ONLY place allowed to call fetch (ESLint enforces). Every request goes to the Privacy Ledger; bodies are never kept.
4. No third-party scripts, fonts, analytics or CDNs.
5. Mode A call script contains Tier 1 fields only. Tier 3 (OTP, PIN, CVV, passwords, card, Aadhaar) has no field and is always masked.
6. Never fetch/resolve/open a URL found in user text (lexical checks only).
7. Guide lines come from i18n keys only. Guides never imitate officials, never blame, never promise refunds.
8. AI is opt-in, masked input only, output sanitised; verdict/score always come from rules.
9. Rules/KB are JSON data in backend/data; a rule needs >=2 examples and >=2 counterExamples. KB entries need a source.
10. No dangerouslySetInnerHTML.

## Commands
backend: `uv run pytest` · `uv run ruff check .` · `uv run python seed.py` · `uv run uvicorn app.main:app --port 8000`
frontend: `npm run dev` · `npx tsc --noEmit` · `npx eslint src` · `npx vitest run` · `npx playwright test`
