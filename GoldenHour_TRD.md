# GoldenHour: Technical Requirements Document (TRD)

| | |
|---|---|
| **Document** | TRD v1.0, companion to `GoldenHour_BRD.md` (what/why) and `GoldenHour_DRD.md` (look/feel) |
| **Audience** | Claude Code (primary), human reviewers |
| **Baseline** | `goldenhour.zip` v0.1: a Python/Streamlit prototype with 23 passing tests. It is the **behavioural reference**, not the R1 codebase. |
| **Requirement IDs** | `BR-*` refer to the BRD. Every feature below lists the BR IDs it satisfies. |

---

## 0. Reading guide and conventions

- **MUST / SHOULD / MAY** are used in the RFC 2119 sense.
- Where this document says *"port verbatim"*, copy the behaviour (and regex) from `legacy/python-prototype/scamcore.py` and prove parity with the conformance suite (§17.3).
- Versions: pin the **current stable** release of every dependency at scaffold time and record them in the lockfile. This document deliberately names no version numbers it cannot verify.

---

## 1. Key architecture decisions

| # | Decision | Why |
|---|---|---|
| **AD-1** | **All analysis, extraction and document generation run in the user's browser** (a TypeScript core in a Web Worker). | The strongest possible privacy story: pasted text, names, UTRs and addresses never reach any server. It also gives offline use, and makes the Privacy Ledger's "nothing left your device" literally true. (BR-GD-05, O5) |
| **AD-2** | **One language: TypeScript** across core, web and the optional API. | One source of truth for rules and builders; Claude Code works best in one toolchain; shared types. |
| **AD-3** | The server exists **only** for the optional AI features (key protection, rate limits, budget caps) and for serving static files. It is stateless and stores nothing. | BR-AI-01..03, BR-AQ-02 |
| **AD-4** | Rules, advice, knowledge base, copy and portal-sheet layout are **data files** (JSON/YAML), validated by schema, not code. | BR maintainability; non-developers can PR a rule or a KB entry |
| **AD-5** | The Python prototype is kept under `legacy/` and used to **generate golden fixtures** once; the TS core must match them. | De-risks the port |
| **AD-6** | **Tokenise-then-polish** for AI: personal and transaction values are replaced by placeholders before leaving the browser; Claude never sees names, numbers or IDs. | BR-AI-01/02 |
| **AD-7** | No analytics, no third-party scripts, no third-party fonts. | Trust |

---

## 2. System architecture

```
┌────────────────────────────── Browser (PWA) ───────────────────────────────┐
│  React UI (apps/web)                                                         │
│    ├─ Guide, SunClock, Fields, Ledger ... (DRD)                              │
│    ├─ Zustand store (memory only)  ◄─────┐                                   │
│    └─ ledgerFetch()  (the ONLY network egress, logs to Ledger)               │
│                                                                              │
│  Web Worker  ── @goldenhour/core (pure TS) ──────────────────────────────    │
│    normalize → redact → detect → extract → tiers → builders → ics            │
│    KB search (MiniSearch, BM25)                                              │
│                                                                              │
│  Service worker: caches app shell, fonts, i18n, KB, rules (offline)          │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ only if user opts in to AI (HTTPS, masked + tokenised)
                                ▼
┌──────────────── apps/api (Fastify, stateless) ────────────────┐
│  /v1/health  /v1/ai/explain  /v1/ai/polish  /v1/ai/ask         │
│  rate-limit · budget cap · schema validation · no body logging │
│            └────────────► Anthropic Messages API               │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Repository layout (pnpm workspaces)

```
goldenhour/
├─ CLAUDE.md                      # see §19.2
├─ docs/  BRD.md TRD.md DRD.md
├─ package.json  pnpm-workspace.yaml  tsconfig.base.json  .editorconfig
├─ .github/workflows/ci.yml
├─ packages/
│  └─ core/
│     ├─ src/
│     │  index.ts types.ts
│     │  normalize.ts redact.ts urlcheck.ts detect.ts extract.ts
│     │  tiers.ts fields.ts elapsed.ts ics.ts kb.ts
│     │  builders/ callScript.ts portalSheet.ts complaint.ts bankLetter.ts checklist.ts pack.ts
│     │  ai/ tokenise.ts guards.ts
│     ├─ data/
│     │  rules.json  advice.en.json advice.hi.json advice.mr.json
│     │  banks.json  portalSheet.json  checklist.json
│     │  kb/ entries.json         # FAQ knowledge base
│     │  schema/ rule.schema.json kb.schema.json
│     ├─ test/ unit/*.test.ts  conformance/*.json  fuzz/*.test.ts
│     └─ package.json
├─ apps/
│  ├─ web/
│  │  ├─ index.html  vite.config.ts  public/(fonts, icons, manifest.webmanifest)
│  │  └─ src/
│  │     main.tsx  App.tsx  routes/  store/  worker/  api/ledgerFetch.ts
│  │     components/ (Guide, SpeechBubble, SunClock, FieldCard, CopyBlock, VerdictBanner,
│  │                 ModeCard, PrivacyLedger, Stepper, CallButton, LanguageSwitch, TextSizeControl)
│  │     guides/ asha.tsx kabir.tsx moods.ts reactions.ts narrator.ts
│  │     i18n/ en.json hi.json mr.json index.ts
│  │     styles/ tokens.css base.css
│  │     a11y/ tts.ts voiceInput.ts
│  └─ api/
│     ├─ src/ server.ts routes/ai.ts prompts/*.md lib/{claude,limits,budget,problem}.ts
│     ├─ Dockerfile
│     └─ test/
├─ eval/  scam_set.jsonl  genuine_set.jsonl  run-eval.ts
├─ legacy/python-prototype/       # contents of goldenhour.zip (read-only reference)
└─ tools/ gen-fixtures.py         # runs legacy code, emits conformance JSON
```

---

## 4. Technology stack

| Layer | Choice | Notes |
|---|---|---|
| Language | TypeScript (strict, `noUncheckedIndexedAccess`) | |
| Package manager | pnpm workspaces | |
| Web | React 18+, Vite, React Router | |
| State | Zustand | memory-only store |
| Styling | CSS custom properties + CSS Modules | Tokens from DRD §3. **No Tailwind** (keeps the distinctive design system). |
| Accessible primitives | Radix UI (Dialog, Tabs, RadioGroup, Switch, Tooltip) | |
| Icons | Lucide | |
| Motion | `motion` (Framer Motion) limited to `transform`/`opacity` | |
| i18n | i18next + react-i18next | EN, HI, MR |
| Validation | Zod | shared with API |
| Search (Ask) | MiniSearch | client-side BM25 |
| Worker RPC | Comlink | |
| PWA | vite-plugin-pwa (Workbox) | |
| API | Fastify, `@fastify/helmet`, `@fastify/rate-limit`, `@fastify/cors` | |
| AI SDK | `@anthropic-ai/sdk` | server only |
| Tests | Vitest, Testing Library, Playwright, axe-core (via `@axe-core/playwright`), fast-check (property tests) | |
| Docs/Design | Storybook | |
| Lint/format | ESLint (typescript-eslint, jsx-a11y), Prettier | |
| Bundle control | size-limit | |
| Containers | Docker (API only) | |

---

## 5. Core library (`@goldenhour/core`)

Pure TypeScript. **No DOM, no Node-only APIs, no network.** It must run unchanged in a Web Worker, in Node (tests), and in the API for validation.

### 5.1 Pipeline

```
raw text
  → normalize()   NFKC, Devanagari digits → ASCII, collapse odd whitespace, cap 5000 chars
  → redact()      mask card / Aadhaar / OTP·PIN·CVV values (returns text + spans + count)
  → detect()      rules + URL checks → Detection
  → extract()     Incident
  → fieldsFrom()  Incident → Fields (editable)
  → builders      callScript / portalSheet / complaint / bankLetter / checklist / pack
```

**Order matters.** Redaction runs first so that secrets never appear in highlights, logs, AI prompts or exports.

### 5.2 `normalize(text): string`

1. `text.normalize("NFKC")`.
2. Map Devanagari digits `०–९` to `0–9` (and Arabic-Indic digits `٠–٩`).
3. Replace zero-width characters (`\u200B-\u200D\uFEFF`) with empty string.
4. Replace runs of whitespace (other than `\n`) with one space; collapse 3+ newlines to 2.
5. Truncate to **5000** characters. Report `truncated: boolean`.

Reason: the Python baseline's `\d` matched Unicode digits; JS `\d` is ASCII only, so normalisation keeps behaviour identical and adds Hindi/Marathi digit support.

### 5.3 `redact(text)`: port verbatim

Returns `{ text, count, masks: {kind, start, end}[] }`. Kinds: `card`, `aadhaar`, `otp`.

| Mask | Pattern (flags) | Replacement |
|---|---|---|
| card | `(?<!\d)(?:\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{1,4}\|\d{15,16})(?!\d)` | `[CARD-NO REDACTED]` |
| Aadhaar (labelled) | `(aadh?aa?r\|uid)(\D{0,15})(\d{4}\s?\d{4}\s?\d{4})(?!\d)` `i` | `$1$2[AADHAAR REDACTED]` |
| Aadhaar-like (spaced) | `(?<!\d)\d{4} \d{4} \d{4}(?!\d)` | `[AADHAAR-LIKE REDACTED]` |
| OTP/PIN/CVV after keyword | `\b(otp\|cvv\|cvc\|mpin\|upi\s*pin\|pin)\b(?!\s*code)(\D{0,20}?)(\d{3,8})(?!\d)` `i` | `$1$2[REDACTED]` |
| OTP before keyword | `(?<!\d)(\d{4,8})(?!\d)(\s+is\s+(?:your\|the)\s+(?:otp\|one[- ]time\s+password\|verification\s+code))` `i` | `[REDACTED]$2` |

**Order of application:** card → Aadhaar labelled → Aadhaar-like → OTP-after → OTP-before. 12-digit UTRs MUST survive redaction (test vector T-R3).

### 5.4 Rule engine (`detect`)

**Rule file:** `data/rules.json`, validated by `schema/rule.schema.json`.

```jsonc
{
  "id": "credential_request",
  "weight": 70,                      // 1..100
  "category": "credential",          // see §5.4.3
  "critical": true,
  "pattern": "\\b(?:share|send|tell|give|provide|forward|read\\s*out|enter|type|confirm)\\b[^.\\n]{0,40}?\\b(?:otp|pin|cvv|cvc|password|passcode|mpin)\\b",
  "flags": "i",
  "unlessBefore": "(?:\\bnever|\\bnot\\b|n't|\\bdont|\\bno\\s+one|\\bnobody)[^.\\n]{0,30}$",   // optional
  "label":  { "en": "Asks you to share an OTP / PIN / CVV / password", "hi": "...", "mr": "..." },
  "why":    { "en": "No bank, government office or genuine company needs your OTP, PIN or CVV.", "hi": "...", "mr": "..." },
  "examples":        ["Please share the OTP you just received to confirm."],
  "counterExamples": ["Never share your OTP with anyone.", "We will never ask you to share your OTP or PIN."]
}
```

A unit test auto-generated from `examples` (must fire) and `counterExamples` (must not fire) runs for every rule. **A rule cannot be merged without at least 2 examples and 2 counterExamples.**

#### 5.4.1 Matching semantics

For each rule, in file order:
1. Run `pattern` (global) over the **redacted, normalised** text.
2. For each match, if `unlessBefore` is set and matches `text.slice(max(0, m.index − 40), m.index)`, skip this match.
3. The first surviving match is the rule's hit (a rule hits at most once). Record `{ruleId, label, why, weight, evidence (≤ 90 chars), start, end}`.

> Baseline gap: the Python code did not record spans. R1 MUST record `start/end` so the UI can highlight (DRD §6.3).

#### 5.4.2 Scoring

```
p = 1 − Π (1 − w_i/100)          over all hits (rule hits + URL hits)
score = round(100 · p)
if any hit.critical: score = max(score, 85)
verdict = score ≥ 60 ? "scam" : score ≥ 30 ? "suspicious" : "low"
```

#### 5.4.3 Scam type selection

- Primary categories (ordered): `digital_arrest, kyc, electricity, investment, job_task, lottery, loan, refund, family`.
- Sum the weights of hits per category; the primary category with the highest sum wins.
- If no primary category hit: `malware` if present, else `credential` if present, else `unclear`.
- If `verdict == "low"`, force `unclear`.

#### 5.4.4 Rule catalog (R1 baseline: **20 rules**, port verbatim from the prototype)

| id | weight | category | critical |
|---|---|---|---|
| credential_request | 70 | credential | yes |
| remote_access | 65 | malware | yes |
| apk_install | 60 | malware | |
| digital_arrest | 75 | digital_arrest | yes |
| isolation | 45 | digital_arrest | |
| parcel_drugs | 55 | digital_arrest | |
| authority | 25 | digital_arrest | |
| urgency | 15 | generic | |
| account_threat | 30 | generic | |
| kyc | 35 | kyc | |
| electricity | 40 | electricity | |
| investment_promise | 45 | investment | |
| group_lure | 25 | investment | |
| task_job | 40 | job_task | |
| upfront_fee | 40 | generic | |
| lottery | 45 | lottery | |
| loan_app | 35 | loan | |
| refund_trick | 45 | refund | |
| qr_receive | 70 | refund | yes |
| family_emergency | 40 | family | |

> **Correction:** earlier materials said "19 rules". The prototype has **20**.

**R1.1 SHOULD add Hindi/Hinglish rules** (to be reviewed by a native speaker), e.g. phrases meaning "digital arrest", "your account will be blocked", "update KYC", "electricity will be cut", "share OTP". Each with examples and counterExamples.

#### 5.4.5 URL checks (`urlcheck.ts`)

`extractUrls(text)`: regex `\b(?:https?://|www\.)[^\s<>"'`]+|\b(?:bit\.ly|tinyurl\.com|t\.ly|cutt\.ly|rb\.gy|is\.gd|shorturl\.at)/[^\s<>"'`]+` (`i`); strip trailing `.,;:!?)]}>`; de-duplicate.

`analyzeUrl(url)` returns hits (each rule id counted once per message):

| id | weight | Condition |
|---|---|---|
| url_shortener | 25 | host ∈ {bit.ly, tinyurl.com, t.ly, cutt.ly, rb.gy, is.gd, shorturl.at, goo.gl, ow.ly} |
| url_http | 12 | starts with `http://` |
| url_ip | 40 | host is a dotted IPv4 |
| url_punycode | 45 | host contains `xn--` |
| url_userinfo | 40 | netloc contains `@` |
| url_tld | 20 | TLD ∈ {xyz, top, click, icu, site, vip, cc, buzz, link, cyou, sbs, cfd, tk, ml, cf, gq, rest, monster, work} |
| url_lookalike | 60 | host is **not** under an official domain **and** a brand token appears (`brand in tokens` or, for brands ≥ 5 letters, `brand in host without hyphens`), or `gov` token without `.gov.in`/`.nic.in` |

Brand → official domains: `data/brands.json` (port from prototype `BRANDS`). **URLs are analysed lexically only. The product MUST NEVER fetch, resolve, or open a user-supplied URL.**

#### 5.4.6 Output type

```ts
type Verdict = "scam" | "suspicious" | "low";
interface Hit { ruleId: string; label: string; why: string; weight: number;
                evidence: string; start: number; end: number; critical: boolean }
interface Detection {
  score: number; verdict: Verdict; scamType: ScamType; critical: boolean;
  hits: Hit[]; urls: string[]; redactedText: string; maskedCount: number; truncated: boolean;
}
```

Advice text is looked up from `advice.{lang}.json` by `scamType` (array of strings). Missing translation falls back to `en` and the UI marks it "translation pending".

### 5.5 Incident extraction (`extract`)

All patterns operate on normalised, redacted text. Port verbatim; JS flags in the right column.

| Field | Pattern (summary) | Flags |
|---|---|---|
| **amounts** | `(?:₹\|\brs\.?\|\binr)\s*([\d,]+(?:\.\d+)?)\s*(lakhs?\|lacs?\|crores?\|cr\b)?` + **Hindi addition:** `([\d,]+(?:\.\d+)?)\s*(?:रुपये\|रु\.?)` | `gi` |
| **UTR (labelled)** | `(?:\butr\b\|\brrn\b\|ref(?:erence)?(?:\s*(?:no\.?\|number\|id))?\|txn(?:\s*(?:id\|no\.?))?\|transaction\s*(?:id\|no\.?\|number\|ref)?\|upi\s*ref(?:erence)?(?:\s*(?:no\.?\|id))?)\W{0,12}(\d{12})(?!\d)` | `gi` |
| **UTR (alphanumeric, labelled)** | same label group … `\W{0,12}([A-Z0-9]{13,22})\b`; accept only if the token has ≥ 1 letter **and** ≥ 1 digit; uppercase | `gi` |
| **12-digit unlabelled** | `(?<!\d)\d{12}(?!\d)` → `possibleUtrs` unless: preceded within 25 chars by `aadh?aa?r\|uid`, or starts with `91` followed by `[6-9]` (looks like +91 phone), or already a labelled UTR | `g` |
| **phones** | `(?<!\d)(?:\+91[\s-]?\|91[\s-]\|0)?([6-9]\d{4}[\s-]?\d{5})(?!\d)` → normalise to `+91XXXXXXXXXX` | `g` |
| **UPI IDs** | `(?<![\w.\-])([A-Za-z0-9][\w.\-]{1,48})@([A-Za-z][A-Za-z0-9]{1,20})\b(?!\.[A-Za-z])` (excludes e-mail addresses) | `g` |
| **URLs** | §5.4.5 `extractUrls` | |
| **banks / apps** | alias maps in `banks.json` (SBI, HDFC Bank, ICICI Bank, Axis Bank, Kotak, PNB, Bank of Baroda, Canara Bank, Union Bank, IDFC First, Yes Bank, IndusInd, Federal Bank, Bank of India, IDBI, Indian Bank, Bandhan, RBL, Paytm Payments Bank; apps: Google Pay, PhonePe, Paytm, BHIM, Amazon Pay), matched as `\b(?:alias)\b` on lowercased text | `i` |
| **account last 4** | `\b(?:a/?c\|acct\|account\|card)\b\D{0,12}?(?:x+\|\*+)?\s?(\d{4})(?!\d)` → `"XX" + last4` | `gi` |
| **time hints** | `\b\d{1,2}[:.]\d{2}\s?(?:am\|pm)\b` (uppercased) | `gi` |
| **date hints** | `\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b` \| `\b\d{1,2}(?:st\|nd\|rd\|th)?\s+(?:jan\|feb\|mar\|apr\|may\|jun\|jul\|aug\|sep\|oct\|nov\|dec)[a-z]*\.?(?:\s+\d{2,4})?\b` \| `\b(?:today\|yesterday)\b` | `gi` |

**Amount formatting:** Indian digit grouping (`1,23,45,678`), `₹` prefix, decimals only if non-integer. Values with `lakh/lac` ×10⁵, `crore/cr` ×10⁷. Port `_indian_group` from the prototype.

**Victim-vs-scammer phone heuristic (new):** a phone number within 30 characters after `my number`, `mine`, `मेरा नंबर`, or `my mobile` is assigned to `victimPhones`; the rest to `phones`. The UI pre-fills "Your mobile" from `victimPhones[0]` and "Scammer's phone" from `phones`. The user can always edit.

**Output type:**

```ts
interface Incident {
  amounts: string[]; utrs: string[]; possibleUtrs: string[]; upiIds: string[];
  phones: string[]; victimPhones: string[]; urls: string[]; banks: string[]; apps: string[];
  accountLast4: string[]; whenHints: string[];
}
```

### 5.6 Fields, tiers and modes (`fields.ts`, `tiers.ts`)

```ts
type Tier = 1 | 2 | 3;
type Mode = "A" | "B";            // C is a disabled UI affordance only
interface FieldDef {
  key: keyof Fields; tier: Tier; labelKey: string; howToFindKey?: string;
  validator: (v: string) => ValidationResult;      // never blocks, only warns
  portalOrder?: number;                            // ordering for the portal sheet
  inCallScript: boolean;                           // Tier 1 only
}
```

| key | Tier | In 1930 script (Mode A) | In portal sheet | Validation |
|---|---|---|---|---|
| amount | 1 | yes | yes | one or more ₹ amounts |
| utrs | 1 | yes | yes | each `^\d{12}$` or alnum 13–22 w/ letter+digit |
| bank | 1 | yes | yes | non-empty |
| account | 1 | yes | yes | last 4 digits or UPI ID; if > 4 consecutive digits, **warn** "last 4 is enough to start" |
| when | 1 | yes | yes | non-empty |
| mobile | 1 | yes | yes | `^[6-9]\d{9}$` after stripping `+91`, spaces |
| scamPhones | 1 | yes | yes | phone pattern |
| scamUpi | 1 | yes | yes | UPI pattern or bank account |
| scamLinks | 1 | yes | yes | any |
| description | 2 | **no** | yes | ≤ 1500 chars |
| name | 2 | **no** | yes | |
| location (district / police station) | 2 | **no** | yes | |

**Tier 3** (OTP, PIN, CVV, password, card number, Aadhaar, ID proof) has **no field**. If the user types such a value into any free text, `redact()` masks it, a warning is shown (DRD §4.8), and the guide reacts.

> **Fix over baseline:** the prototype's call script included name and location. In R1, **Mode A prints Tier 1 only**. The script ends with: *"If you are asked for anything beyond this list, you can say you'll provide it on the portal."* Mode B prints a portal sheet (Tier 1 + Tier 2) in `portalSheet.json` order.

### 5.7 Builders

All builders are **pure functions** `(fields, opts) → string | structured`, with templates in `data/*.json` per language (`en`, `hi`, `mr`). Missing placeholders render as `[bracketed placeholder]`. Outputs MUST NOT contain `undefined`, `null` or `NaN` (property test).

| Builder | Output | BR |
|---|---|---|
| `buildCallScript(fields, lang)` | Numbered steps, **Tier 1 only**, pairs UTR↔amount when counts match, else lists separately | BR-EF-06, BR-SF-02 |
| `buildPortalSheet(fields, lang)` | Array of `{section, labelKey, value, tier, copyable}` ordered by `portalSheet.json` | BR-SF-03 |
| `buildComplaint(fields, lang)` | Text per the prototype template (SUBJECT / COMPLAINANT / INCIDENT / DESCRIPTION / TRANSACTIONS / FRAUDSTER / ACTION TAKEN / REQUEST / EVIDENCE) | BR-EF-06 |
| `buildBankLetter(fields, lang)` | Letter per the prototype template | BR-EF-06 |
| `buildChecklist(lang)` | 7 steps (see below) each `{id, title, detail, done:false}` | BR-EF-06 |
| `missingItems(fields, lang)` | List of `{key, text, howToFind}` | BR-EF-04 |
| `elapsedBanner(bucket)` | `{level: red\|orange\|yellow, message}` | BR-EF-05 |
| `buildPack(fields, mode, lang)` | Single `.txt` combining everything | BR-EF-06 |
| `buildIcs(deadline, summary)` | RFC 5545 VCALENDAR string | BR-EF-09 |

**Checklist step IDs:** `call1930`, `alertBank`, `preserveEvidence`, `fileComplaint24h`, `secureAccounts`, `bewareRecovery`, `followUp`. Texts and Hindi titles come from the prototype `STEPS`; Marathi to be authored.

**Elapsed buckets:** `lt15 → 10 min`, `m30 → 30`, `h1to2 → 90`, `sameDay → 360`, `earlier → 2000`. Banner: ≤ 120 → red ("first two hours"), ≤ 1440 → orange, else yellow. (DRD shows these as calm Sun-Clock zones, never alarming.)

**ICS rule:** deadline = `now + max(15 min, 24 h − elapsedMinutes)`. Summary: "File your formal complaint on cybercrime.gov.in". No attendees, no URL tracking. UID random (`crypto.randomUUID()`). Generated and downloaded client-side as a Blob.

### 5.8 Knowledge base and Ask (`kb.ts`)

`data/kb/entries.json` (schema-validated):

```jsonc
{
  "id": "what-is-utr",
  "q":  { "en": "What is a UTR?", "hi": "...", "mr": "..." },
  "a":  { "en": "A UTR (also called UPI Ref No. or RRN) is the 12-digit reference of a UPI transaction. Find it in your bank or UPI app's transaction history. In Google Pay it appears as 'UPI transaction ID'.", "hi": "...", "mr": "..." },
  "keywords": ["utr","rrn","reference","transaction id"],
  "sources": [{ "title": "…", "url": "https://…", "publisher": "…" }],
  "verifiedOn": "2026-10-10",
  "reviewBy": "2027-01-10"
}
```

- **Index** with MiniSearch (fields: `q`, `a`, `keywords`; boost `q`×3, `keywords`×2; fuzzy 0.2; prefix on). Built in the worker at startup from the active language plus English.
- `ask(question, lang)` → top-3 entries with score. If `topScore < threshold` (tune; start at a normalised 0.35) → `fallback: true` with the standard "I don't have a verified answer" message (BR-AQ-02).
- **Every displayed answer shows `sources` and `verifiedOn`** (BR-AQ-03).
- CI check: fail the build if any entry is past `reviewBy`, or has no source URL.
- **Seed entries (minimum 20)** covering: what 1930 is; what the portal is; calling vs portal; what to keep ready; what a UTR is and where to find it; the 24-hour formal complaint; the reference-number SMS; what Chakshu is for (and not for); "digital arrest" is not a legal concept; what to do if the agent asks for an OTP; whether to inform the bank; evidence to keep; what an acknowledgement number is; can I file from another city; what if I can't find the UTR; scam types (KYC, electricity, investment, task jobs, refund/QR). Use only the verified sources listed in the BRD §2.1; add new entries only with a source.

---

## 6. Web application (`apps/web`)

### 6.1 Routes

| Route | Screen | Default guide |
|---|---|---|
| `/` | Welcome | both |
| `/check` | Message Checker | Kabir |
| `/lost` | Emergency Flow (steps via nested routes `/lost/tell`, `/lost/review`, `/lost/mode`, `/lost/pack`, `/lost/after`) | Asha |
| `/ask` | Ask | Kabir |
| `/about`, `/privacy`, `/settings` | Static | n/a |

Deep links are allowed; state is memory-only, so entering `/lost/review` directly redirects to `/lost/tell` with a friendly guide line.

### 6.2 State (Zustand, memory only)

```ts
interface AppState {
  lang: "en" | "hi" | "mr"; guide: "asha" | "kabir"; textScale: 1 | 1.25 | 1.5;
  theme: "system" | "light" | "dark"; contrast: "normal" | "high"; reducedMotion: boolean | "system";
  readAloud: boolean; voiceInput: boolean; aiConsent: boolean;      // all default false
  check: { input: string; detection?: Detection };
  lost: {
    step: "tell" | "review" | "mode" | "pack" | "after";
    narrative: string; elapsed: ElapsedBucket; quickPath: boolean;
    incident?: Incident; fields: Fields; edited: Set<keyof Fields>;
    mode: Mode; detection?: Detection;
  };
  ledger: LedgerEntry[]; sessionStartedAt: number;
}
```

- **No persistence by default.** An opt-in toggle "Keep my draft in this tab" writes `lost.fields` and `narrative` to `sessionStorage` (cleared when the tab closes). `localStorage`/IndexedDB are not used for user data. Settings (language, text size, theme) MAY persist to `localStorage` only if the user opts in.
- **`wipeAll()`** (BR-GD-06): resets the store, clears `sessionStorage`, `localStorage`, IndexedDB, and Cache Storage entries holding user data (not the static app shell), cancels any pending worker jobs, records a ledger event "All local data deleted".

### 6.3 Emergency Flow state machine

```
tell ──NEXT(extracted)──► review ──NEXT──► mode ──NEXT──► pack ──NEXT──► after
 ▲        │                   │ ▲             │                │
 └─BACK───┴───────BACK────────┘ └───BACK──────┴────BACK────────┘
Any state ──RESET──► tell (after wipeAll)
```

- Entering `tell → review` triggers `worker.extract(narrative)` (≤ 100 ms typical). If nothing is extracted, go to `review` anyway with empty fields and the guide line for `flow.cantRead` (DRD §6.7).
- `review → mode` is **never blocked** by missing fields; missing items show as "Still missing" with a "Fill later" affordance (BR-EF-04).
- `quickPath` shows only: amount, utrs, bank, when, mobile.
- Mode C card is rendered `aria-disabled="true"` and never navigates.

### 6.4 The worker and the only egress

- `worker/core.worker.ts` exposes (via Comlink): `analyze(text, lang)`, `extract(text, lang)`, `fieldsFrom(incident)`, `pack(fields, mode, lang)`, `portalSheet(...)`, `ics(...)`, `ask(q, lang)`.
- **`api/ledgerFetch.ts` is the only module allowed to call `fetch`.** An ESLint rule (`no-restricted-globals`/custom) forbids `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `navigator.sendBeacon` and `new Image().src` anywhere else. CSP `connect-src` backs this up.
- Each call records:

```ts
interface LedgerEntry {
  id: string; t: number; label: string;      // human label, e.g. "Claude second opinion"
  host: string; path: string; method: string;
  bytesOut: number; bytesIn: number; status: number | "error";
  masked: boolean; tokenised: boolean;       // were secrets masked / identifiers tokenised?
}
```

- The ledger **never stores request or response bodies**.
- With AI off, the product makes **zero** network requests after the initial load. A Playwright test asserts this (§17.5).

### 6.5 Guides

- `Guide.tsx` props: `{ who, mood, speaking?, lookAt?, size? }`. Each guide is an inline SVG with the layer ids from DRD §4.5. Mood parameters (DRD §4.6) are CSS variables set on the SVG root and consumed by `transform`/`d` attributes on parts.
- `moods.ts`: `Record<Mood, MoodParams>`; `reactions.ts`: pure `moodFor(event, ctx) → {mood, durationMs, line?}` implementing DRD §4.8; unit-tested table.
- `narrator.ts`: a queue of `{key, vars}` messages. For each, it (a) sets the ARIA live region text immediately, (b) runs the typewriter unless reduced motion or "skip", (c) waits 600 ms between bubbles, (d) optionally speaks the line via `speechSynthesis` if read-aloud is on. Cancels cleanly on route change.
- Idle blink: random 4–6 s via `setTimeout`, paused when `document.hidden`.
- **A guide line MUST come from i18n keys**, never from hard-coded strings or from AI.

### 6.6 Components (contract summary)

| Component | Key props / behaviour |
|---|---|
| `SunClock` | `{ bucket }` → arc position, zone label, `aria-label`; no timers; recomputes only on `bucket` change |
| `FieldCard` | `{ def, value, onChange, auto?: boolean }` → tier chip, validation (non-blocking), "How to find this" disclosure; UTR displayed in groups of 4 via CSS, stored ungrouped |
| `CopyBlock` | `{ text, label }` → `navigator.clipboard.writeText` with fallback to a hidden textarea selection; "Copied" for 1.6 s; script variant has per-line checkboxes |
| `VerdictBanner` | `{ detection }` → icon, headline, score ring, type chip; tinted panel (DRD §7.4) |
| `HighlightedText` | `{ text, hits }` → splits text into text nodes and `<mark>` elements by spans; **never uses `dangerouslySetInnerHTML`** |
| `ModeCard` | `{ mode, selected, disabled? }` |
| `PrivacyLedger` | Reads `ledger`; shows the empty state when `ledger.length === 0` |
| `CallButton` | `<a href="tel:1930">`; never auto-dials |
| `Stepper` | Rail with `aria-current="step"` |

### 6.7 Internationalisation

- Namespaces: `common`, `guide`, `check`, `lost`, `ask`, `privacy`, `errors`.
- Keys are stable; copy for the first 12 keys in DRD §8 is the seed. CI fails on missing `en` keys and **warns** on missing `hi`/`mr`; `mr` strings flagged `"_review": true` are shown with a small "translation under review" hint until a native reviewer clears them.
- Number/date formatting via `Intl` with `en-IN`, `hi-IN`, `mr-IN`.
- Language switch changes UI, guide lines, advice, KB search language and builder templates, instantly and without reload.

### 6.8 Accessibility implementation

- Radix primitives + `jsx-a11y` lint.
- Skip link; landmarks; one `h1` per route; focus moves to the new route heading on navigation.
- All guide SVGs `role="img"` with names; decorative parts `aria-hidden`.
- Speech bubbles in a single `aria-live="polite"` region (no duplicate announcements).
- Keyboard: all interactions reachable; Esc closes the Ledger drawer; visible focus ring `--focus`.
- `prefers-reduced-motion`, `prefers-color-scheme`, `prefers-contrast` honoured, with manual overrides.
- Text scale applies via root `font-size`; layouts use `rem`/`clamp()`.
- **Read-aloud** (`a11y/tts.ts`): `speechSynthesis` with `lang` `en-IN|hi-IN|mr-IN`; if no matching voice is found, show the friendly message from DRD §10.
- **Voice input** (`a11y/voiceInput.ts`): off by default; before first use, a notice and a ledger entry "Browser speech service (may send audio to your browser vendor)". Feature-detect `SpeechRecognition`/`webkitSpeechRecognition`.

### 6.9 PWA and offline

- Precache: app shell, JS/CSS, fonts, `rules.json`, advice, i18n, KB, icons.
- Runtime: no API caching (AI calls are never cached).
- The product works fully offline for Checker, Emergency Flow, Ask (local KB) and all exports. Offline banner appears only when AI is requested.
- `manifest.webmanifest`: name "GoldenHour", `display: standalone`, theme colour `--lagoon`.
- Update flow: "A new version is ready" toast; reload on user action.

### 6.10 Fonts and assets

Self-hosted `woff2`, subset by unicode-range (Latin, Devanagari), `font-display: swap`, preload the two most used weights. Total font payload ≤ 150 KB. Guide SVGs inlined and code-split per guide (≤ 12 KB gz each).

### 6.11 Browser support

Chrome ≥ 90, Edge ≥ 90, Firefox ≥ 78, Safari ≥ 16.4 (regex look-behind). A feature test constructs the regexes at startup; if construction throws, show a static, non-JS-dependent help page with the essential steps (call 1930, bank, portal) and "please update your browser".

---

## 7. API (`apps/api`): optional AI only

### 7.1 Principles

- Stateless. No database. No sessions. No cookies.
- Never logs request or response bodies or IPs. Structured logs only: `{ts, level, reqId, route, status, ms}`.
- Disabled cleanly when `ANTHROPIC_API_KEY` is absent (`/v1/health` reports `ai: false`; AI routes return 503 `ai_disabled`).

### 7.2 Endpoints

| Method / path | Purpose | Request body (Zod) | Response |
|---|---|---|---|
| `GET /v1/health` | Liveness + feature flags | none | `{ status:"ok", version, ai: boolean }` |
| `POST /v1/ai/explain` | Second opinion on a message (BR-MC) | `{ maskedText: string(≤3000), ruleLabels: string[](≤30), language: "English"\|"Hindi"\|"Marathi" }` | `{ why, extraRedFlags: string[](≤3), tellFamily, confidence: "low"\|"medium"\|"high" }` |
| `POST /v1/ai/polish` | Rewrite a **tokenised** complaint | `{ tokenisedDraft: string(≤4000), tokens: string[] }` | `{ text }` |
| `POST /v1/ai/ask` | Grounded answer from supplied KB passages | `{ question: string(≤300, masked), passages: {id,text}[](1..3), language }` | `{ answer, citedIds: string[] }` |

Required header for all `/v1/ai/*`: `X-GH-AI-Consent: 1` (client sends it only when `aiConsent === true`). Without it → 400.

### 7.3 Error model (RFC 7807)

```json
{ "type": "https://goldenhour.example/errors/rate_limited", "title": "Too many requests",
  "status": 429, "detail": "Try again in 30 seconds.", "instance": "req_8f2c…" }
```

Codes: 400 `invalid_request`, 413 `too_large`, 429 `rate_limited`, 502 `ai_upstream_error`, 503 `ai_disabled` / `ai_budget_exhausted`. Error `detail` strings never echo user input.

### 7.4 Middleware and limits

| Concern | Setting |
|---|---|
| Body size | 16 KB max |
| Rate limit | per client (in-memory token bucket keyed by a salted hash of the IP, salt rotated daily, never persisted): 60/min general, 10/min AI |
| Global AI budget | `AI_DAILY_TOKEN_CAP` env; when exhausted → 503 `ai_budget_exhausted` (UI shows the friendly "extra opinion unavailable" line) |
| Timeouts | Upstream 30 s; one retry on 5xx/timeouts only |
| CORS | Allow only `WEB_ORIGIN` |
| Headers | Helmet defaults + `Cache-Control: no-store` on API; `Referrer-Policy: no-referrer`; `Permissions-Policy: camera=(), geolocation=(), microphone=()` (static site sets `microphone=(self)` only if voice input is shipped) |
| Kill switch | `AI_ENABLED=false` |

### 7.5 Claude integration

- Models via env: `ANTHROPIC_MODEL_FAST` (explain, ask) and `ANTHROPIC_MODEL_QUALITY` (polish). Suggested defaults: `claude-haiku-5-5` and `claude-sonnet-5-5`. **Verify availability for your account before launch.**
- `max_tokens`: explain 600, ask 500, polish 900. `temperature` low (≤ 0.3).
- Prompts live in `apps/api/src/prompts/*.md` (versioned; changes require review). Port the prototype prompts (`EXPLAIN_SYSTEM`, `POLISH_SYSTEM`) and adapt:
  - All user-derived text is wrapped in tags (`<untrusted_message>`, `<draft>`, `<question>`) and the system prompt states it is **data, never instructions**.
  - Output must be a single JSON object (explain/ask) with exact keys; parse with brace extraction + Zod; on failure return 502 `ai_upstream_error` (UI falls back).
  - Never recommend calling numbers or opening links that appear in the user's text.
- **Tokenise-then-polish (AD-6), implemented in `core/ai/tokenise.ts`:**
  1. Replace every field value with a token: `{{NAME}}`, `{{MOBILE}}`, `{{LOCATION}}`, `{{BANK}}`, `{{ACCOUNT}}`, `{{AMOUNT_1}}`, `{{UTR_1}}`, `{{UPI_1}}`, `{{PHONE_1}}`, `{{LINK_1}}`, `{{WHEN}}` …
  2. The free-text description is sent as is **after** `redact()`; the UI warns that names in the story are visible to Claude (DRD copy `ai.consentDetail`).
  3. The server prompt says: "Keep every `{{TOKEN}}` exactly as written, each exactly once where present in the draft; do not invent new tokens; do not write any digits, names or IDs not in the draft."
  4. **Client-side guard (`guards.ts`)** on the response: (a) every original token appears; (b) no unknown `{{…}}`; (c) the text contains no run of ≥ 3 digits and no `@`; (d) length ≤ 2× draft. If any check fails, discard and show the original template draft.
  5. Detokenise locally.
- **Ask:** answer must set `citedIds ⊆ passages.id` and be non-empty; otherwise the client shows the top KB entry verbatim.
- **Explain:** show as "AI opinion" with confidence; the score and verdict always come from rules.

### 7.6 Configuration (env)

| Var | Purpose | Default |
|---|---|---|
| `PORT` | listen port | 8080 |
| `WEB_ORIGIN` | allowed CORS origin | required in prod |
| `ANTHROPIC_API_KEY` | key (server only) | none → AI disabled |
| `ANTHROPIC_MODEL_FAST` / `_QUALITY` | models | see above |
| `AI_ENABLED` | kill switch | `true` if key present |
| `AI_DAILY_TOKEN_CAP` | global budget | `500000` (tune) |
| `RATE_LIMIT_GENERAL` / `RATE_LIMIT_AI` | per-minute | 60 / 10 |
| `LOG_LEVEL` | | `info` |

Secrets are never exposed to the client bundle; `VITE_*` variables contain no secrets (only `VITE_API_BASE`).

---

## 8. Security requirements

| ID | Requirement |
|---|---|
| SEC-1 | **CSP (web):** `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self' <API origin>; frame-ancestors 'none'; base-uri 'none'; object-src 'none'; form-action 'self'`. No inline scripts; no `unsafe-inline` styles (use CSS files and `style` via CSSOM only where unavoidable, with nonce if required). |
| SEC-2 | **No third-party requests** at runtime (fonts, analytics, CDNs). Playwright asserts the set of hosts contacted. |
| SEC-3 | **XSS:** user text is only rendered as text nodes; `dangerouslySetInnerHTML` is banned by lint. |
| SEC-4 | **SSRF:** no server or client code ever fetches a user-supplied URL. |
| SEC-5 | **Prompt injection:** §7.5 plus red-team tests (§17.6). |
| SEC-6 | **Secrets:** API key only in server env; secret scan (gitleaks) in CI. |
| SEC-7 | **Supply chain:** lockfile committed; CI actions pinned by commit SHA; Renovate/Dependabot; `pnpm audit` (fail on high/critical); minimal dependencies; licence check. |
| SEC-8 | **ReDoS:** input cap 5000 chars; all patterns bounded; each rule fuzzed with long adversarial strings, and a timing test asserts `detect+extract` ≤ 100 ms for 5000 chars on CI hardware. Core runs in a Worker so the UI never blocks. |
| SEC-9 | **Transport:** HTTPS only, HSTS in production. |
| SEC-10 | **Clipboard/downloads:** exports are Blobs created client-side; filenames fixed (`goldenhour_pack.txt`, `goldenhour_reminder.ics`). |
| SEC-11 | **Brand abuse:** the app never displays official emblems; the "Independent tool" chip is a non-removable component with a test. |
| SEC-12 | **Container (API):** non-root user, read-only root filesystem, no shell tools, healthcheck, dropped capabilities. |

---

## 9. Privacy engineering

| ID | Requirement | Verified by |
|---|---|---|
| PRV-1 | With AI off, **zero network requests** after initial load. | Playwright network assertion |
| PRV-2 | Server never receives names, mobile numbers, locations, UTRs, UPI IDs, amounts or links (tokenised) and never receives unmasked secrets. | Unit tests on `tokenise` + API contract tests rejecting bodies containing 12-digit runs or `@` |
| PRV-3 | Server stores nothing and logs no bodies/IPs. | Log-scanner test: send a known canary string, assert it never appears in captured logs |
| PRV-4 | `wipeAll()` clears all client storage. | E2E test |
| PRV-5 | Privacy Ledger shows every request and nothing else. | E2E test comparing Ledger to observed requests |
| PRV-6 | Voice input and read-aloud disclose third-party processing if applicable. | Manual + copy review |
| PRV-7 | The printed/downloaded pack carries a footer: "Delete this file from shared devices." | Unit test |

---

## 10. Performance budgets

| Metric | Budget |
|---|---|
| Initial JS (route `/`) | ≤ 180 KB gz |
| Guides (each, lazy) | ≤ 12 KB gz |
| CSS | ≤ 30 KB gz |
| Fonts total | ≤ 150 KB |
| LCP on mid-range Android, throttled 4G | ≤ 2.5 s |
| Total blocking time | ≤ 200 ms |
| `detect+extract` for 5000 chars | ≤ 100 ms (Worker) |
| Interaction latency | ≤ 100 ms |
| Animation | 60 fps, `transform`/`opacity` only |

`size-limit` in CI enforces the JS/CSS budgets.

---

## 11. Data files: schemas and governance

- `rule.schema.json`, `kb.schema.json`, `portalSheet.schema.json`, `checklist.schema.json`; validation in CI and at build time.
- **CODEOWNERS:** rules and KB changes require review by two maintainers (one domain reviewer).
- **KB freshness:** `reviewBy` dates enforced by CI (§5.8).
- **Portal sheet** (`portalSheet.json`): ordered sections/fields mapped to `FieldDef.key`. **The order is a best-effort and MUST be verified against the live portal before launch; the file has a top-level `verifiedOn` and the UI shows "Order may differ from the live form" until set.**

---

## 12. Error handling and resilience

| Failure | Behaviour |
|---|---|
| Worker fails to start | Fall back to running core on the main thread (feature flag); if regex construction fails, show the static help page (§6.11) |
| Extraction finds nothing | Continue to review step with manual fields |
| Clipboard denied | Select the text and show "Press Ctrl+C / long-press to copy" |
| AI network/API failure | Friendly guide line; core output unchanged |
| AI guard rejects output | Original draft shown; no error code displayed |
| Offline + AI requested | Inline message; nothing queued |
| Invalid input (too long) | Truncate to 5000 with a visible notice |

No stack traces or raw error text are shown to users.

---

## 13. Observability (privacy-preserving)

- API: counters by route and status (in-memory, exposed on an internal-only port), request ids.
- Client: **no telemetry**. Product KPIs (BRD §3) are measured via **pilot sessions and surveys**, not tracking.
- Optional: a local "session summary" the user can copy voluntarily when reporting a bug (contains no content).

---

## 14. Build, CI/CD and deployment

### 14.1 CI (`ci.yml`)

1. Install (frozen lockfile) · 2. Lint (ESLint + Prettier check) · 3. Typecheck (`tsc --noEmit`, all packages) · 4. Unit + property + fuzz tests · 5. Conformance tests (§17.3) · 6. Schema validation of data files + KB freshness · 7. Build web and API · 8. `size-limit` · 9. Playwright E2E + axe (headless Chromium, Firefox, WebKit) · 10. `pnpm audit` · 11. gitleaks · 12. Upload test reports and Storybook build.

### 14.2 Deployment

- **Web:** static files on any HTTPS static host/CDN with the headers in §8 (SEC-1, SEC-9).
- **API (optional):** one container, any container host; env per §7.6; autoscale 0..N is fine (stateless).
- **Local:** `pnpm dev` (web + api), `docker compose up` for the API.
- **Environments:** `local`, `staging` (pilot), `production`.
- **Versioning:** SemVer; changelog; every release re-runs the evaluation (§17.4).

---

## 15. Non-functional requirements matrix

| NFR | Target | Section |
|---|---|---|
| Availability (static) | host-dependent; works offline | 6.9 |
| Privacy | PRV-1..7 | 9 |
| Security | SEC-1..12 | 8 |
| Accessibility | WCAG 2.2 AA | DRD 10; 6.8 |
| Performance | budgets | 10 |
| Maintainability | data-driven rules/KB, strict TS, ≥ 85% line coverage in `core` | 11, 17 |
| Localisation | EN/HI/MR | 6.7 |
| Browser support | §6.11 | |

---

## 16. Requirement traceability (excerpt)

| BR | Implemented by | Verified by |
|---|---|---|
| BR-MC-01..06 | §5.4, §6.6 `VerdictBanner/HighlightedText` | E2E-01, unit rules tests, eval |
| BR-EF-01..09 | §5.5, §5.7, §6.3 | E2E-02..04, unit builders |
| BR-SF-01..06 | §5.6, §5.7, §6.3 | Unit (tier filter), E2E-03 |
| BR-AQ-01..04 | §5.8 | Unit KB tests, CI freshness |
| BR-GD-01..06 | §6.2, §6.4, §6.5 | E2E-05..07, unit `moodFor` |
| BR-AC-01..04 | §6.7, §6.8 | axe, manual SR |
| BR-AI-01..03 | §7, §AD-6 | API contract + guard tests |

---

## 17. Testing strategy

### 17.1 Unit tests (Vitest)
- Every rule: auto-tests from `examples`/`counterExamples`.
- `redact`, `normalize`, `extract`, `urlcheck`, `detect`, tiers, builders, ICS, KB search, tokenise/guards, `moodFor`, validators.
- Coverage gate: ≥ 85% lines and ≥ 80% branches in `packages/core`.

### 17.2 Property-based tests (fast-check)
- `redact` is idempotent; never removes a labelled 12-digit UTR.
- `extract(text)` never throws on arbitrary Unicode ≤ 5000 chars.
- Builders never output `undefined|null|NaN` for any `Fields`.
- `buildCallScript` output never contains `name`, `location`, `description` values (Tier filter).
- `tokenise → detokenise` round-trips.

### 17.3 Conformance tests (TS vs prototype)
`tools/gen-fixtures.py` runs the **legacy Python** code over `samples.py` plus ≥ 100 additional authored cases and writes `packages/core/test/conformance/*.json` (`input`, expected `verdict`, `score`, `ruleIds`, `scamType`, and extraction results). The TS core MUST reproduce `verdict`, `ruleIds` and extraction exactly, and `score` exactly (same noisy-OR rounding). Known intentional differences (documented in the fixture file): Devanagari-digit support, Hindi amount pattern, `victimPhones`, spans.

Seed vectors (from the prototype tests):

| ID | Input (abridged) | Expectation |
|---|---|---|
| T-D1 | "Inspector… digital arrest… RBI safe account…" | verdict scam, score ≥ 85, type digital_arrest, critical |
| T-D2 | "SBI… blocked… http://sbi-kyc-update.top/login… share the OTP" | rule ids ⊇ {credential_request, kyc, url_lookalike, url_tld}; type kyc |
| T-D3 | "…electricity… tonight… .apk" | scam; type electricity; `apk_install` hit |
| T-D4 | "Genuine HDFC OTP SMS… Do not share it…" | verdict low, not critical |
| T-D5 | "Never share your OTP" / "We will never ask you to share your OTP or PIN" | not critical |
| T-D6 | "Please share the OTP you just received to confirm." | critical |
| T-R1 | card `4111 1111 1111 1111` | masked |
| T-R2 | "aadhaar 1234 5678 9012", "123456 is your OTP" | masked |
| T-R3 | "UTR 524587920123" | **unchanged** |
| T-E1 | Electricity incident sample | amounts `₹49,999, ₹25,000`; utrs `524587920123, 524587920456`; upi `rajesh.kumar77@okaxis`; phones `+919876543210, +919123456789`; bank `SBI`; last4 `XX2234`; times include `4:10 PM` |
| T-E2 | "Aadhaar 123456789012… 919876543210… UTR: 524587920123" | utrs only `524587920123`; neither other number in `possibleUtrs` |
| T-E3 | "paid 524587920123 yesterday" | `utrs=[]`, `possibleUtrs=[524587920123]` |
| T-E4 | "john@gmail.com … Rs. 2.5 lakh to shop@oksbi." | upi `shop@oksbi` only; amount `₹2,50,000` |
| T-E5 | Trading sample | utr `612345678901`; amount `₹1,20,000`; upi `tradedesk@ybl`; bank `HDFC Bank`; last4 `XX8841` |

### 17.4 Evaluation set (BR O4)
`eval/scam_set.jsonl` (≥ 100 synthetic scam messages across all categories, English + Hinglish + Hindi) and `eval/genuine_set.jsonl` (≥ 100 genuine bank/OTP/delivery/utility messages, built from public advisories and invented examples; **no real people's data**). `run-eval.ts` prints accuracy, false-alarm rate, per-category recall, and fails CI below: **accuracy ≥ 85%, false alarms ≤ 5%**. Publish results in the README each release.

### 17.5 End-to-end (Playwright, mobile and desktop viewports)

| ID | Scenario (Gherkin summary) |
|---|---|
| E2E-01 | *Given* Kabir on `/check`, *when* I paste the digital-arrest sample, *then* I see "Very likely a scam", highlighted phrases, ≥ 3 reason cards, and a "Call 1930" button. |
| E2E-02 | *Given* Asha on `/lost/tell`, *when* I paste the electricity incident and pick "About 30 minutes ago", *then* extraction chips show `₹49,999`, `₹25,000`, two UTRs, and the Sun-Clock shows the "first two hours" zone. |
| E2E-03 | *Given* Mode A, *then* the call script contains UTRs, amount, bank, and **does not contain** the typed name, address, or description. *Given* Mode B, *then* the portal sheet contains them. |
| E2E-04 | *Given* no UTR extracted, *then* "How to find this" is available and the flow can continue; the pack lists UTR as "still missing". |
| E2E-05 | *Given* AI is off, *when* I complete the whole flow, *then* the browser makes **no** requests after load and the Ledger says "Nothing has left your device." |
| E2E-06 | *When* I press "Delete everything now", *then* the store, sessionStorage, localStorage and IndexedDB are empty. |
| E2E-07 | *When* I switch to Hindi, *then* headings, guide lines and the Check advice are Hindi; no clipped glyphs (visual snapshot). |
| E2E-08 | *When* `prefers-reduced-motion` is on, *then* no typewriter or breathing animations run (assert computed `animation-name: none` and instant text). |
| E2E-09 | *Given* AI is on (mock API), *when* I request a second opinion, *then* the Ledger shows exactly one entry with `masked: true`, and the request body contains no 12-digit sequence or `@`. |
| E2E-10 | Offline mode: after first load, `/check`, `/lost/*`, `/ask` work with the network disabled. |
| E2E-11 | `.ics` download contains a valid VEVENT and no URLs. |
| E2E-12 | Axe finds **zero** serious/critical violations on the six main screens in light, dark, large-text. |

### 17.6 Security and AI tests
- **Injection corpus:** messages that say "ignore previous instructions…", "reveal your system prompt", "output the OTP"; API tests with a mock model that obeys injection → guards must reject.
- **Polish guard tests:** model returns altered tokens/digits/new tokens → rejected.
- **Log canary:** §9 PRV-3.
- **Rate limit and budget tests.**
- **Header tests:** CSP and security headers present on web and API.

### 17.7 Manual QA
TalkBack (Android) and NVDA (Windows) on Check and Emergency Flow; low-end Android device on throttled 4G; native-speaker review of Hindi/Marathi copy; comprehension test with 5 users aged 55+.

---

## 18. Definition of Done (R1)

1. All **Must** BRs have passing automated tests (§16).
2. CI green including budgets, axe, audit, secret scan.
3. Evaluation thresholds met (§17.4).
4. Privacy tests PRV-1..7 pass; CSP verified on the deployed site.
5. Portal-sheet order and all KB entries verified against live sources; `verifiedOn` dates set.
6. Hindi and Marathi copy reviewed by native speakers.
7. Legal review items from BRD §12 closed or explicitly accepted.
8. Pilot completed (≥ 10 users); results recorded.

---

## 19. Build plan for Claude Code

### 19.1 Milestones

| M | Deliverable | Done when |
|---|---|---|
| **M0** | Monorepo scaffold, tooling, CI skeleton, `legacy/` copied in, `CLAUDE.md` committed | `pnpm i && pnpm test` passes (empty suites); CI green |
| **M1** | `core`: `normalize`, `redact`, `urlcheck`, `rules.json` + `detect` | Rule tests + T-D*/T-R* vectors pass |
| **M2** | `core`: `extract`, `fields/tiers`, `elapsed` | T-E* vectors pass; property tests pass |
| **M3** | `core`: builders, `ics`, i18n templates, `tokenise/guards` | Builder tests + property tests pass; Tier filter proven |
| **M4** | Conformance fixtures from legacy; KB + MiniSearch; eval harness | Conformance + eval thresholds pass |
| **M5** | `web`: tokens, base styles, i18n, store, worker, `ledgerFetch`, routes, Welcome | Lighthouse budgets; E2E-05 skeleton |
| **M6** | `web`: Checker screen (HighlightedText, VerdictBanner) | E2E-01 passes |
| **M7** | `web`: Emergency Flow (all steps, Sun-Clock, FieldCards, Mode cards, packs, ICS) | E2E-02, 03, 04, 06, 11 pass |
| **M8** | Guides: SVGs, moods, narrator, reactions, read-aloud; Ledger drawer; Ask screen | E2E-07, 08, 10 pass; Storybook shows all moods |
| **M9** | `api`: AI routes, limits, budget, prompts, guards; client AI opt-in UI | E2E-09 + injection tests pass |
| **M10** | Hardening: a11y pass, perf, PWA, security headers, docs, pilot build | §18 Definition of Done |

### 19.2 `CLAUDE.md` (put at repo root)

```markdown
# GoldenHour: instructions for Claude Code

## What this is
A privacy-first web app that helps people in India check scam messages and prepare their UPI/cyber-fraud
reports (1930 call script, cybercrime.gov.in complaint, bank letter). It does NOT file complaints and is NOT
a government service. Read docs/BRD.md, docs/DRD.md, docs/TRD.md before changing anything.

## Non-negotiables
1. All analysis runs in the browser (packages/core in a Web Worker). Do not add server-side processing of user text.
2. `apps/web/src/api/ledgerFetch.ts` is the ONLY place allowed to call fetch. Every request is logged to the Privacy Ledger. No bodies are ever logged.
3. Never add third-party scripts, fonts, analytics or CDNs.
4. Never store user content in localStorage/IndexedDB unless the user opted in; default is memory only.
5. Mode A call script contains Tier 1 fields only. Tier 3 data (OTP, PIN, CVV, passwords, card no., Aadhaar) has no field and is always masked.
6. Never fetch, resolve or open a URL found in user text.
7. Guide lines come from i18n keys only. Guides never imitate officials, never blame, never promise refunds.
8. AI is opt-in, tokenise-then-polish only; Claude never sees names, numbers or IDs. Output must pass guards.ts.
9. Rules/KB are data (JSON). A rule needs >=2 examples and >=2 counterExamples.
10. Do not use dangerouslySetInnerHTML.

## Commands
pnpm i · pnpm dev · pnpm test · pnpm lint · pnpm typecheck · pnpm e2e · pnpm eval · pnpm build

## Working style
- Work milestone by milestone (TRD §19.1). Write tests first for core logic. Keep PRs small.
- When behaviour is ambiguous, prefer the legacy Python prototype's behaviour and the conformance fixtures.
- If a requirement here conflicts with a convenience, keep the requirement and flag it.
- After each milestone: run the full test suite and summarise what is verified and what is not.
```

### 19.3 Suggested prompts (copy into Claude Code, one per milestone)

- **M0:** "Read docs/TRD.md §3, §4, §14. Scaffold the pnpm monorepo exactly as described, copy the contents of goldenhour.zip into legacy/python-prototype, add CLAUDE.md from §19.2, and set up ESLint, Prettier, TypeScript strict, Vitest, and the CI workflow. Don't implement features yet. Show me `pnpm test` and CI results."
- **M1:** "Implement TRD §5.2–§5.4 in packages/core. Port the 20 rules and URL checks from legacy/python-prototype/scamcore.py into data/rules.json with examples and counterExamples (≥2 each). Write the auto-generated rule tests and the T-D*/T-R* vectors first, then make them pass. Record match spans."
- **M2:** "Implement §5.5–§5.6 (extract, fields, tiers, elapsed) with the exact patterns in the TRD. Add the Hindi amount pattern, Devanagari digit normalisation and the victim-phone heuristic. Make the T-E* vectors and the property tests pass."
- **M3:** "Implement §5.7 builders and §7.5 tokenise/guards. Mode A script must be Tier 1 only; prove it with a property test."
- **M4:** "Write tools/gen-fixtures.py to run the legacy Python code and emit conformance JSON; make the TS core match it. Build the KB schema, ≥20 seed entries (only from sources listed in BRD §2.1), MiniSearch index, and the eval harness with thresholds."
- **M5–M8:** "Follow DRD and TRD §6 to build the web app. Use the tokens in DRD §3 exactly. Implement the Guide SVGs with the layer ids and moods in DRD §4.5–§4.6, the narrator with ARIA live region, and the Privacy Ledger fed only by ledgerFetch. Add Storybook stories for every mood and component state."
- **M9:** "Implement apps/api per §7 with rate limits, budget cap, RFC 7807 errors, and prompts in /prompts. Add the injection and guard tests (§17.6) and the client opt-in UI. AI must be fully optional."
- **M10:** "Run the full Definition of Done checklist (§18). List anything unverified (portal order, translations, legal) instead of assuming."

---

## 20. Acceptance criteria summary (for sign-off)

- [ ] E2E-01..12 pass on Chromium, Firefox, WebKit (mobile + desktop viewports)
- [ ] Conformance tests pass; eval thresholds met
- [ ] PRV and SEC tables verified
- [ ] Budgets met on a throttled mid-range device profile
- [ ] No Tier 3 field exists anywhere in the UI or model
- [ ] Mode A script verified Tier 1 only
- [ ] "Independent tool" chip and "Virtual guide" label present on every relevant screen
- [ ] Mode C is disabled and never simulated

---

## 21. Known gaps and risks (be honest in the README)

| Item | Status |
|---|---|
| Live Anthropic API calls | Not tested in the baseline (no key was available). Test early in M9. |
| Portal field order and current form fields | Unverified; verify before launch (`portalSheet.json`). |
| Whether portal-only filing triggers a freeze as fast as 1930 | Unverified; do not claim equivalence. |
| Direct submission to the cyber cell | No known public integration; out of scope. |
| Hindi/Marathi rules and copy | Need native review; Marathi UI strings to be authored. |
| Regex porting (Python → JS) | Covered by conformance tests; watch Unicode and look-behind support. |
| Heuristic accuracy | Bound by the eval set; novel scams will slip through; never say "safe". |
| Legal review | Pending (BRD §12). |

---

## Appendix A: Phone/UPI/other patterns, Python → JavaScript porting notes

- Python inline flags `(?i)` → JS `i` flag. Python `re.compile(..., re.I)` → `new RegExp(src, "gi")` (add `g` where iterating).
- Python `\d`, `\w`, `\s` are Unicode-aware; JS are ASCII-only (hence `normalize()`).
- Python `finditer` + `break` for "first hit" → JS `RegExp.exec` loop with `lastIndex` reset per rule.
- Look-behind `(?<!…)` requires modern engines (§6.11).
- `str.rstrip(chars)` → explicit regex `/[.,;:!?)\]}>]+$/`.
- Python `urlparse(...).hostname` → `new URL(...)` with a try/catch; prefix `http://` if the scheme is missing.
- Rounding: Python `round()` is banker's rounding; JS `Math.round` rounds .5 up. Use a helper that reproduces Python's behaviour (round half to even), or avoid exact .5 by testing; the conformance suite will catch differences.
