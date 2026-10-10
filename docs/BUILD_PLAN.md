# GoldenHour: Build Plan (FastAPI + React + Postgres)

Companion to the BRD, DRD and TRD in the repo root. **Where this plan and the TRD disagree, this plan wins** (see §1). Product behaviour (rules, tiers, copy, guides, tokens) still comes from the BRD/DRD/TRD.

## 0. Ground rules

1. **Minimal code.** No abstraction until it is used three times. No layers, no DI containers, no repositories, no factories.
2. **Backend = plain functions.** FastAPI route functions plus pure helper functions in modules. **No classes** except Pydantic request/response models (these are schemas, not behaviour).
3. **Rules and KB are data.** Edited as JSON in the repo; loaded into Postgres by a seed script.
4. **Privacy by design.** User text is processed in memory only: never stored, never logged, never sent to a third party except the opt-in Claude call (masked, tokenised).
5. **Scale by being stateless.** Any instance can serve any request.
6. **Every phase ends with tests green and a commit.** Nothing is "done" without a test that proves it.

## 1. Deviations from the TRD (decisions to confirm)

| TRD says | This plan | Why |
|---|---|---|
| Analysis runs in the browser (TS core in a Web Worker) | **Analysis runs in FastAPI (Python)**, stateless, text held in memory only | You asked for a FastAPI backend. Python also matches the legacy prototype regexes (no JS/Python porting risk, no Appendix A rounding/Unicode traps). |
| "Zero network requests with AI off", "nothing left your device" | **Weakened.** Text is sent to our own API for checking. The Ledger shows every request honestly ("sent to GoldenHour server, not stored") | Direct consequence of the line above. BRD O5 is reworded to "zero personal data *stored* or *logged* server-side". Privacy copy in DRD §1/§6.6/§8 must change accordingly. |
| No database | **Postgres**, holding only: rules, KB entries, daily AI token counter, optional error reports. **Never user content.** | Gives live-editable KB/rules (BR-AQ-04) and a shared AI budget across instances. |
| Fastify/TS API | **FastAPI** | Your request. |
| pnpm monorepo with `core` package, Storybook, Comlink, size-limit, Radix, MiniSearch | **Two folders** (`backend/`, `frontend/`). A `/design` route replaces Storybook. | Less machinery. |
| Offline PWA | **Deferred** to R1.1 (app shell caching only) | Offline checking is impossible when analysis is server-side. |
| Ask: client-side MiniSearch | Server-side search over KB (Postgres full-text + `pg_trgm`) | Same reason. |
| Direct-to-Anthropic via Fastify | FastAPI `/v1/ai/*`, same opt-in, tokenise-then-polish, guards | Unchanged in behaviour. |

Unchanged: scoring formula, 20 rules, URL checks, redaction order, extraction patterns, Tier 1/2/3 and Mode A/B, builders, checklist, ICS, guides, tokens, copy, a11y, security headers.

## 2. Architecture

```
Browser (React SPA, static files on CDN)
   │  all calls go through ONE module: src/api.js  (logs to Privacy Ledger)
   ▼
Load balancer ──► FastAPI instance 1..N   (stateless, uvicorn workers)
                    │ rules + KB cached in process memory (reload when meta.version changes)
                    ├──► Postgres (read-mostly; rules, kb, ai_usage, error_reports)
                    └──► Anthropic API (only for opted-in /v1/ai/*)
```

### Scalability decisions (the important part)

| Concern | Design |
|---|---|
| Horizontal scale | No session, no local disk, no sticky routing. Add instances behind the LB. |
| CPU-bound regex | Compile all rules **once at startup**. Input hard-capped at 5000 chars; every pattern bounded (no nested quantifiers). Route functions are plain `def`, so FastAPI runs them in its threadpool and the event loop never blocks. Run `uvicorn` with one worker per CPU core; scale out with more containers. |
| Cheap per-request cost | `/v1/check` and `/v1/extract` touch **no database**. They only use in-memory compiled rules. Target p95 ≤ 100 ms server time. |
| DB load | Rules and KB are read at startup and cached; a 60 s check of `meta.version` refreshes them. DB is off the hot path, so Postgres never becomes the bottleneck. |
| Rate limiting | In-memory token bucket keyed by a salted hash of the IP (salt rotates daily). Fine for N small instances; if abuse appears, swap for the LB/CDN's rate limiting. No Redis in R1. |
| AI cost | Daily token cap in Postgres (`ai_usage`), one atomic `UPDATE ... RETURNING`. Shared by all instances. |
| Static frontend | Hashed filenames, long cache, served from CDN. The API never serves it in production. |
| Failure isolation | AI down or budget gone: core features unaffected. DB down: API still serves checks from the cached rules; `/v1/health` reports `db: false`. |
| Observability | Structured log line per request: `{ts, reqId, route, status, ms}`. No bodies, no IPs. |

## 3. Repository layout

```
goldenhour/
├─ docs/                      BRD, DRD, TRD, BUILD_PLAN.md
├─ CLAUDE.md                  non-negotiables (adapted from TRD §19.2)
├─ docker-compose.yml         postgres + api (+ web dev)
├─ .github/workflows/ci.yml
├─ backend/
│  ├─ pyproject.toml          (uv; ruff; pytest)
│  ├─ app/
│  │  ├─ main.py              app, middleware, startup, routes registration
│  │  ├─ routes.py            /v1/* route functions (thin)
│  │  ├─ schemas.py           Pydantic models
│  │  ├─ text.py              normalize, redact
│  │  ├─ detect.py            rule matching, URL checks, scoring, scam type
│  │  ├─ extract.py           incident extraction, amount formatting
│  │  ├─ fields.py            tiers, validators, missing items, elapsed buckets
│  │  ├─ builders.py          call script, portal sheet, complaint, bank letter, checklist, pack, ics
│  │  ├─ kb.py                search over KB
│  │  ├─ ai.py                tokenise, Claude call, guards
│  │  ├─ db.py                connection pool + a handful of SQL functions
│  │  └─ limits.py            rate limit + budget
│  ├─ data/                   rules.json  brands.json  banks.json  portal_sheet.json
│  │                          checklist.json  advice.{en,hi,mr}.json  kb.json  templates.{en,hi,mr}.json
│  ├─ schema.sql              the whole DB schema
│  ├─ seed.py                 upserts data/*.json into Postgres, bumps meta.version
│  └─ tests/                  test_*.py, vectors (T-D*, T-R*, T-E*), eval/
├─ frontend/
│  ├─ package.json  vite.config.js  index.html
│  ├─ public/fonts/           self-hosted woff2 (Bricolage Grotesque, Hind, JetBrains Mono)
│  └─ src/
│     ├─ main.jsx  App.jsx  store.js (Zustand)  api.js  i18n/{en,hi,mr}.json
│     ├─ styles/tokens.css  base.css
│     ├─ guides/ Guide.jsx  asha.jsx  kabir.jsx  moods.js  reactions.js  narrator.js
│     ├─ components/ SpeechBubble SunClock FieldCard CopyBlock VerdictBanner
│     │              HighlightedText ModeCard PrivacyLedger Stepper CallButton TopBar
│     ├─ routes/ Welcome Check Lost(Tell Review Mode Pack After) Ask Design
│     └─ a11y/ tts.js
└─ e2e/                       Playwright tests + axe
```

Frontend language: **TypeScript (`strict`)**; the `.js`/`.jsx` names above are shorthand for `.ts`/`.tsx`. The API contract is small and TS catches wiring errors cheaply. Plain CSS (tokens + CSS Modules), no Tailwind, per DRD.

## 4. Database (Postgres, never user content)

```sql
create table meta        (key text primary key, value text not null);          -- 'version'
create table rules       (id text primary key, weight int, category text, critical bool,
                          pattern text, flags text, unless_before text,
                          label jsonb, why jsonb, examples jsonb, counter_examples jsonb,
                          enabled bool default true);
create table kb_entries  (id text primary key, q jsonb, a jsonb, keywords text[],
                          sources jsonb, verified_on date, review_by date);
create table ai_usage    (day date primary key, tokens bigint not null default 0);
create table error_reports (id bigserial primary key, created_at timestamptz default now(),
                          page text, note text check (length(note) <= 500));    -- user-typed, no case data
```

Dev and tests use the same schema on a local Postgres (docker compose). Access via `asyncpg`-free simple approach: **`psycopg` with a connection pool and plain SQL strings** (no ORM, no migrations tool; `schema.sql` is idempotent: `create table if not exists`).

## 5. API contract

| Method / path | Purpose | Touches DB? |
|---|---|---|
| `GET /v1/health` | `{status, version, ai, db}` | pings |
| `POST /v1/check` | `{text, lang}` → Detection (score, verdict, scamType, hits with spans, advice, urls, redactedText, maskedCount, truncated) | no |
| `POST /v1/extract` | `{text, lang}` → Incident + Fields (with tier, valid, auto flags) + missing items | no |
| `POST /v1/pack` | `{fields, mode, lang, elapsed}` → `{callScript, portalSheet, complaint, bankLetter, checklist, packTxt, ics}` | no |
| `POST /v1/ask` | `{question, lang}` → top-3 KB entries with sources, `verifiedOn`, or `fallback: true` | reads cache |
| `POST /v1/ai/explain` | opt-in second opinion (header `X-GH-AI-Consent: 1`) | budget |
| `POST /v1/ai/polish` | opt-in, tokenised draft only | budget |
| `POST /v1/report-error` | optional feedback note (≤ 500 chars) | writes |

Rules for all routes: body ≤ 16 KB, RFC 7807 errors that never echo input, `Cache-Control: no-store`, CORS only for `WEB_ORIGIN`, helmet-style headers, 60/min general and 10/min AI limits.

AI gets **no** `/v1/ai/ask` in R1: Ask is KB-only and needs no AI (BRD BR-AQ-02). It can come back in R1.1.

## 6. Backend code style (enforced in review)

- Route function: validate with Pydantic → call 1–3 pure functions → return. Max ~10 lines.
- Pure functions take plain dicts, lists and strings and return the same. No hidden state except the module-level `RULES`/`KB` cache set in `load_data()`.
- Pydantic models are the only classes. No inheritance, no custom exceptions hierarchy: one `problem()` helper returns RFC 7807 responses.
- Lint with `ruff`; type-check lightly with `pyright` on `app/`.

## 7. Frontend plan

### 7.1 Screens
Welcome → Check (Kabir) → Lost flow (Asha: Tell, Review, Mode, Pack, After) → Ask (Kabir) → About/Privacy/Settings. Plus `/design` showing every guide mood and component state (our Storybook).

### 7.2 Global chrome
Top bar (logo, guide switch, EN/हिं/मरा, text size, theme, Ledger), trust bar, floating **Call 1930** (`tel:`), footer with disclaimer and last-reviewed dates.

### 7.3 State
One Zustand store, memory only. Drafts persist to `sessionStorage` only if the user toggles it. `wipeAll()` clears store and all storage.

### 7.4 Network
`src/api.ts` is the only file that calls `fetch`. Each call writes a Ledger entry `{time, label, path, bytesOut, bytesIn, status, masked}`. **No bodies.** ESLint `no-restricted-globals` enforces it.

### 7.5 The characters (guides)
We **draw our own** Asha and Kabir as inline SVG, to the DRD §4 specs. We do not import third-party character packs because (a) licences and a consistent look with the "dawn halo" art direction matter, and (b) named SVG layers are what lets us animate moods.

- Build order: Asha (head, hair, face, kurta, scarf, arms) → Kabir (glasses, stubble, overshirt) using shared shapes where possible.
- Moods are CSS variables on the SVG root (brow offset, eye openness, mouth path, head tilt, hand pose) set from `moods.js`; transitions use `transform`/`opacity` only.
- Idle life: random 4–6 s blink, 4 s breathing, halo shimmer; paused when the tab is hidden or reduced motion is on.
- `narrator.js` runs the speech-bubble queue: ARIA live text immediately, typewriter (skippable), 600 ms between bubbles, optional read-aloud.
- `reactions.js`: a pure `moodFor(event) → {mood, ms, line}` table from DRD §4.8, unit-tested.
- Every guide line is an i18n key. Never AI text.

### 7.6 Visual quality bar
Tokens exactly per DRD §3; the Sun-Clock as the one signature element; one primary action per screen; light, dark, high-contrast, large-text; mobile-first (< 600 px), then two-column and guide-stage layouts. Self-hosted fonts, ≤ 150 KB.

## 8. Milestones (each ends with tests and a commit)

| M | Deliverable | Proof |
|---|---|---|
| **P0** | Scaffold: `backend/` (uv, FastAPI hello, ruff, pytest), `frontend/` (Vite React TS), docker-compose with Postgres, `schema.sql`, CI, CLAUDE.md, `git init` | `pytest`, `npm test`, CI green |
| **P1** | `text.py` + `detect.py` + `rules.json` (20 rules, ≥ 2 examples/counterExamples each) + URL checks + brands | Auto rule tests, T-D*, T-R* vectors |
| **P2** | `extract.py`, `fields.py` (tiers, validators, elapsed) | T-E* vectors, hypothesis property tests |
| **P3** | `builders.py` (call script Tier-1 only, portal sheet, complaint, bank letter, checklist, pack, ICS) + templates EN/HI/MR | Builder tests; property test "Mode A never contains name/location/description"; no `None`/`nan` |
| **P4** | `db.py`, `schema.sql`, `seed.py`, KB (≥ 20 entries, sourced only from BRD §2.1), `kb.py`, `/v1/*` core routes, limits, headers, RFC 7807 | API tests with `httpx`, log-canary test, rate-limit test |
| **P5** | Eval harness: 100 scam + 100 genuine messages, thresholds (≥ 85% accuracy, ≤ 5% false alarms) | `pytest eval` gate in CI |
| **P6** | Frontend foundation: tokens, fonts, i18n, store, `api.ts` + Ledger, TopBar, Welcome, `/design` | Playwright smoke; Ledger matches requests |
| **P7** | Guides: Asha and Kabir SVG, moods, narrator, reactions, read-aloud | `moodFor` unit tests; `/design` shows all 9 moods; reduced-motion test |
| **P8** | Check screen: HighlightedText, VerdictBanner, advice, family warning | E2E-01 |
| **P9** | Lost flow: Tell, Review (FieldCards, tiers, missing items), Sun-Clock, Mode cards, Pack (copy, `.txt`, print, `.ics`), After, Delete-everything | E2E-02, 03, 04, 06, 11 |
| **P10** | Ask screen (sourced answers, fallback), Hindi and Marathi pass | E2E-07; Ask E2E |
| **P11** | AI: `/v1/ai/*`, tokenise, guards, budget, prompts, consent UI | Injection corpus, guard tests, E2E-09 against a mock |
| **P12** | Hardening: axe on all screens × themes, security headers/CSP, perf budgets, load test, docs/README with honest gaps | Definition of Done (TRD §18, adapted) |

## 9. Testing strategy

- **Backend:** pytest + hypothesis; one test file per module; vectors from TRD §17.3 seed vectors; coverage gate ≥ 85% on `app/`.
- **Contract:** `httpx` TestClient against every route, including 413/429/400 problems and "errors never echo input".
- **Privacy:** canary string sent through every route must not appear in captured logs or DB tables (PRV-3).
- **Eval:** scam/genuine sets must meet the thresholds before merge.
- **Frontend:** Vitest for store, reactions, validators; Playwright E2E (mobile + desktop viewports) with `@axe-core/playwright`.
- **Load:** a short `locust`/`k6` run on `/v1/check` with 5000-char payloads. Pass = p95 ≤ 100 ms server time at a stated RPS per core (we record the number, not guess it).
- **Manual:** TalkBack/NVDA, native-speaker review of Hindi/Marathi, 5 users 55+ (cannot be automated; tracked as open items).

## 10. Deployment

- Frontend: static build to any CDN/static host (CSP, HSTS headers).
- API: one Docker image (non-root, read-only FS, healthcheck); run N copies behind a load balancer; managed Postgres.
- Env: `DATABASE_URL`, `WEB_ORIGIN`, `ANTHROPIC_API_KEY` (optional), `ANTHROPIC_MODEL_FAST/QUALITY`, `AI_ENABLED`, `AI_DAILY_TOKEN_CAP`, `RATE_LIMIT_GENERAL/AI`, `LOG_LEVEL`.

## 11. Known gaps (stay honest in the README)

- Privacy claim changes from "nothing leaves your device" to "nothing stored or logged on our server". The DRD copy and BRD O5 must be edited to match.
- The legacy Python prototype (`goldenhour.zip`) is **not in this folder**. I will rebuild the 20 rules, templates and `samples.py` vectors from the TRD text. If you have the zip, drop it in `legacy/` and we will diff against it.
- Portal field order, KB freshness, Hindi/Marathi copy, legal review, and the live Anthropic call all remain **unverified** until checked against live sources/accounts.
- Heuristic accuracy is bounded by the eval set. The product never says "safe".

## 12. Decisions I need from you before P0

1. Confirm **server-side analysis** (§1) and the changed privacy wording. (Recommended; the alternative is the TRD's browser-side TS core, which drops FastAPI from the hot path.)
2. Confirm **Postgres** for rules/KB/budget. (Alternative: SQLite for a single-instance start, simpler but not scalable past one box.)
3. Do you have `goldenhour.zip`? If yes, put it in `legacy/python-prototype/`.
