# GoldenHour: Business Requirements Document (BRD)

| | |
|---|---|
| **Product** | GoldenHour: first aid for UPI and cyber fraud in India |
| **Document** | BRD v1.0 |
| **Date** | 10 Oct 2026 |
| **Owner** | Makarand |
| **Companion documents** | `GoldenHour_DRD.md` (design), `GoldenHour_TRD.md` (technical) |
| **Status** | Draft for build with Claude Code |

---

## 1. Executive summary

India reports cyber fraud at massive scale, and the first hours after a loss decide whether money can be traced. In a panic, victims struggle to gather the right details, are unsure whom to trust on the phone, and don't know what to do in what order.

GoldenHour is a free, privacy-first web product that:

1. **Checks a suspicious message** and explains exactly what is wrong with it.
2. **Guides a victim through the first hours**, turning their own words into a call script for the 1930 helpline, a complaint ready for cybercrime.gov.in, and a letter to their bank.
3. **Lets the victim stay in control of their data** (Self-Fill Mode): only the minimum goes to a phone agent; everything else goes in the official portal, typed by the victim.
4. **Answers common questions** from a curated, sourced knowledge base.

It is delivered through two friendly virtual guides (one woman, one man) so that a frightened person feels heard.

**GoldenHour does not file complaints, does not replace 1930 or the portal, and is not affiliated with any government body.** It prepares, checks and explains.

---

## 2. Problem and evidence

### 2.1 Verified evidence

| Fact | Source |
|---|---|
| 2025: about ₹19,813 crore lost across 21.8 lakh cheating complaints; 77% of losses were investment schemes, 8% digital arrest. | IANS, Jan 2026: https://ianslive.in/indians-lose-over-rs-52976-crore-to-cyber-frauds-over-six-years-report--20260103154943 |
| 1 Jan to 30 Jun 2026: 12.71 lakh complaints, over ₹10,178.97 crore lost. | https://anantamias.com/current-affairs/cyber-fraud-complaints-12-7-lakh-six-months/?pdf=1 (reporting Indian Express) |
| 2021 to May 2026: ₹64,447 crore lost, ₹10,718 crore frozen, ₹323 crore refunded. (Secondary source.) | https://easemyprep.in/news/3062-cyber-fraud-complaints-cross-127-lakh-in-six-months-rs-10178-crore-lost |
| 1930 operators ask for minimum details (mobile, bank, account/UPI ID, 12-digit UTR, date, card details if used, screenshots); an SMS with a reference number follows; a formal complaint is due within 24 hours. | Canara Bank / I4C advisory: https://canarabank.com/UploadedFiles/Pdf/(57) Special Advisory Cyber Jagrookta Divas-April 2023.pdf |
| Victims can also file themselves on cybercrime.gov.in; 1930 is run by state/UT law enforcement. | https://newschecker.in/scam-watch/got-scammed-online-heres-what-you-can-do |
| Chakshu (Sanchar Saathi) is for suspected fraud communications, not for losses already incurred. | https://www.outlookmoney.com/retirement/financial-planning/how-to-report-suspected-fraud-communication-via-dots-chakshu-facility |
| There is no concept of "digital arrest" in Indian law. | https://www.indiaspend.com/data-viz/dataviz-how-indias-cyber-crime-incidence-is-rising-972933 |

### 2.2 Assumptions (not verified; validate in pilot)

- A meaningful share of victims fail to supply complete details at the moment of reporting.
- Some victims hesitate to read personal details to a phone agent, out of fear of fake helplines.
- No existing product turns a victim's own pasted text into a call script and portal-ready complaint. (Absence of evidence in my search, not proof.)

### 2.3 The gap

The official channels exist and work. What is missing is **preparation, trust and clarity** in the moment of panic, before and between those channels.

---

## 3. Vision, goals and objectives

**Vision:** No one in India should lose the first hour to confusion.

| # | Business objective | Measure (targets are proposals, to be baselined in pilot) |
|---|---|---|
| O1 | Reduce time from "I've been scammed" to "I have a complete report ready" | Median under 3 minutes from first input to downloaded pack |
| O2 | Increase completeness of reports | At least 90% of packs contain amount, bank, UTR and date, or an explicit "still missing" list |
| O3 | Increase user confidence and sense of safety | Post-use survey: at least 80% agree "I felt safe sharing my details here" |
| O4 | Help people recognise scams before paying | At least 85% correct verdict on the published test set; false-alarm rate on genuine messages under 5% |
| O5 | Protect privacy | Zero personal data stored server-side; zero personal data in logs (audited) |
| O6 | Be usable by everyone | WCAG 2.2 AA; usable in English, Hindi and Marathi at launch |

---

## 4. Scope

### 4.1 In scope (Release 1)

1. **Message Checker** with explained red flags and plain-language advice.
2. **Emergency Flow** ("I already lost money"): paste or describe, extract, review and edit, choose reporting mode, receive the response pack.
3. **Self-Fill Mode** (Mode A "Minimal-call", Mode B "Portal-only") with data-sensitivity tiers.
4. **Golden Hour clock**: elapsed-time guidance.
5. **Ask**: a sourced FAQ for enquiries about 1930, the portal, documents and timelines.
6. **Two virtual guides** with expressive, accessible animation.
7. **Privacy Ledger**: a live view of what leaves the device.
8. **Languages:** English, Hindi, Marathi (UI + guide dialogue + advice).
9. **Exports:** .txt pack, print, calendar reminder (.ics) for the 24-hour complaint deadline.
10. **One-tap call button** to 1930 on mobile.

### 4.2 Out of scope (Release 1)

- Submitting complaints to the cyber cell (no known public API; see §9 roadmap).
- Accounts, logins, server-side case storage.
- Screenshot OCR, voice calls, or any AI that "talks" in real time.
- Legal advice, refund guarantees, "recovery services".
- Handling identity-proof uploads (those go only to the official portal).
- Stepping in as, or posing as, any government official.

---

## 5. Stakeholders

| Stakeholder | Interest | Involvement |
|---|---|---|
| Fraud victims and their families | Fast, safe, understandable help | Primary users |
| Potential victims (general public) | Recognise scams | Primary users |
| Elderly and low-digital-literacy users | Simple, large-type, voice-friendly help | Priority segment |
| Student/volunteer project team | Build and maintain | Owners |
| Cyber cells / I4C (future) | Better-prepared complaints | Potential partner (not in R1) |
| Banks and fintech apps | Fewer confused customers | Potential distribution partners |
| NGOs, colleges, consumer groups | Awareness | Distribution channel |
| Anthropic (API provider) | Appropriate use of Claude | Supplier |

---

## 6. Personas

| Persona | Situation | Needs | Fears |
|---|---|---|---|
| **Sunita, 58, retired teacher** | Got a "digital arrest" video call; paid ₹49,000 | Calm instructions, Hindi, large text | Being blamed, fake helplines |
| **Rohan, 24, software engineer** | Lost money on a "part-time task" scam | Speed, a script to read, a clean complaint | Wasting the golden hour |
| **Farida, 35, shopkeeper** | UPI "refund" trick | Know which details to give | Sharing bank details with the wrong person |
| **Dinesh, 66, Sunita's husband (helper)** | Helping a family member | Step-by-step, patient guide | Making it worse |
| **Priya, 19, student** | Wants to check a message before paying | Instant, clear verdict | Looking foolish |

---

## 7. Business requirements

Priority: **M** = must, **S** = should, **C** = could. IDs are referenced in the DRD and TRD.

### 7.1 Message Checker

| ID | Requirement | P |
|---|---|---|
| BR-MC-01 | A user can paste or type a suspicious message and get a verdict (Very likely a scam / Suspicious / No strong signals) with a 0–100 score. | M |
| BR-MC-02 | Every verdict shows the specific phrases or links that caused it, each with a plain-language reason. | M |
| BR-MC-03 | Genuine messages (e.g., a bank OTP SMS with "do not share") must not be flagged as scams. | M |
| BR-MC-04 | The result names the likely scam type and gives practical next steps, plus "If you already paid, tap here". | M |
| BR-MC-05 | A forwardable warning for family can be generated. | S |
| BR-MC-06 | Clearly state the verdict is a heuristic, never a guarantee. | M |

### 7.2 Emergency Flow

| ID | Requirement | P |
|---|---|---|
| BR-EF-01 | A victim can paste a debit SMS or describe what happened in their own words, in English, Hindi, or mixed. | M |
| BR-EF-02 | The product extracts UTR(s), amount(s), UPI IDs, phone numbers, links, bank/app, account last 4, and date/time hints. | M |
| BR-EF-03 | The victim can review and correct every extracted field before anything is generated. | M |
| BR-EF-04 | The product lists exactly what is still missing and how to find it (e.g., how to locate a UTR). | M |
| BR-EF-05 | The product shows elapsed-time guidance (first two hours, within 24 hours, later). | M |
| BR-EF-06 | The product generates: 1930 call script, portal copy sheet, complaint text, bank letter, and a prioritised checklist. | M |
| BR-EF-07 | The product never claims it filed anything. Wording must make clear the victim submits it. | M |
| BR-EF-08 | A "Quick path" for people in distress shows only the 5 essential fields. | S |
| BR-EF-09 | Calendar reminder (.ics) for the 24-hour formal-complaint deadline. | S |

### 7.3 Self-Fill Mode and trust

| ID | Requirement | P |
|---|---|---|
| BR-SF-01 | Fields are grouped in three tiers: Tier 1 (needed to trace and freeze), Tier 2 (formal complaint), Tier 3 (never share: OTP, PIN, CVV, passwords). | M |
| BR-SF-02 | Mode A prints a 1930 script containing **only Tier 1** fields. | M |
| BR-SF-03 | Mode B (portal-only) prints every field in portal order for the victim to type in. | M |
| BR-SF-04 | The product shows "Is this really 1930?" red flags (asks for OTP/PIN, asks to install an app or screen-share, asks for payment, called you first). | M |
| BR-SF-05 | A visible, always-available rule: "We will never ask for your OTP, PIN, CVV or password." | M |
| BR-SF-06 | Mode C (direct submit via an official API) is shown as "not available yet" and never simulated. | M |

### 7.4 Ask (enquiries)

| ID | Requirement | P |
|---|---|---|
| BR-AQ-01 | Users can ask questions (e.g., "What is a UTR?", "Do I need to call 1930 and file on the portal?"). | M |
| BR-AQ-02 | Answers come only from a curated knowledge base with sources; if unknown, the product says so and points to 1930 or the portal. | M |
| BR-AQ-03 | Every answer shows its source and the date the entry was last verified. | M |
| BR-AQ-04 | The knowledge base can be updated without redeploying code. | S |

### 7.5 Guides, emotional design, safety feel

| ID | Requirement | P |
|---|---|---|
| BR-GD-01 | Two virtual guides (one female, one male). The user chooses who to talk to, and can switch at any time. | M |
| BR-GD-02 | Guides show empathy: no blame, calm pacing, reactions to the user's progress. | M |
| BR-GD-03 | Guides are labelled "virtual guide, not a real person, not a government service" on every screen where they appear. | M |
| BR-GD-04 | Guides never imitate police, bank staff, or 1930 operators, never use authority language, never create urgency by threat. | M |
| BR-GD-05 | A **Privacy Ledger** shows what left the device, in real time. | M |
| BR-GD-06 | "Delete everything now" clears all data on the device with one tap. | M |

### 7.6 Access and inclusion

| ID | Requirement | P |
|---|---|---|
| BR-AC-01 | English, Hindi and Marathi; language switch at any time. | M |
| BR-AC-02 | Large-text mode, high-contrast mode, read-aloud, keyboard operation, screen-reader support. | M |
| BR-AC-03 | Works on low-end Android phones and 4G. | M |
| BR-AC-04 | A "helper mode" lets a family member fill in on behalf of the victim, with the victim's details clearly separated. | C |

### 7.7 Optional AI (Claude)

| ID | Requirement | P |
|---|---|---|
| BR-AI-01 | AI features are **opt-in**, off by default, and only receive masked text. | M |
| BR-AI-02 | AI never produces or changes transaction numbers, amounts or IDs; any output containing a number or ID not in the input is rejected. | M |
| BR-AI-03 | The product is fully usable with AI disabled or unavailable. | M |

---

## 8. Non-functional business requirements

| Area | Requirement |
|---|---|
| **Privacy** | No accounts. No server-side storage of user content. No third-party analytics or trackers. Masking of OTP/PIN/CVV/card/Aadhaar-like numbers before any processing beyond the browser. |
| **Trust** | Open, auditable rule set; published test results; disclaimers on every result. |
| **Reliability** | Core checker and pack builder work with no AI and no third-party calls. |
| **Performance** | Result within 1 second for typical input (excluding AI). |
| **Accessibility** | WCAG 2.2 AA. |
| **Cost** | Free for users. Hosting kept minimal; AI usage capped per session. |
| **Maintainability** | Scam rules and knowledge base editable as data by non-developers via pull request. |

---

## 9. Release plan

| Release | Contents | Notes |
|---|---|---|
| **R0 (done)** | Streamlit prototype: checker, extractor, response pack, 23 tests | Baseline code (`goldenhour.zip`) |
| **R1** | Full web product per §4.1 | Target of this build |
| **R1.1** | Helper mode, more rules, expanded knowledge base, PWA offline | After pilot feedback |
| **R2** | Private mode (all processing in the browser), screenshot reading, more languages | Needs evaluation |
| **R3** | Direct submission via official integration | Needs an approved partnership with the relevant authority. Not assumed to be possible. |

---

## 10. Success criteria for R1 sign-off

1. All **Must** requirements pass acceptance tests (see TRD §20).
2. Published evaluation: scam test set accuracy and genuine-message false-alarm rate meet O4.
3. Privacy audit passes: server logs contain no user content; no data stored; no third-party requests.
4. Accessibility audit passes (automated plus manual screen-reader pass).
5. Pilot with at least 10 volunteers across ages: median time-to-pack and confidence survey recorded.

---

## 11. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Users think GoldenHour is a government service | Misplaced trust | Persistent disclaimer; guides labelled; never use official emblems or authority language |
| Product itself is cloned/spoofed by scammers | Harm | Publish official URL; never ask for secrets; "Is this really us?" rule on site |
| False negative (scam called safe) | User pays | Never say "safe"; wording "no strong signals, not a guarantee" |
| False positive (genuine called scam) | Lost trust | Negation handling, genuine-message test set, user can see reasons |
| Wrong portal details (forms change) | Misguidance | Date-stamp every instruction; link to live portal; review cycle |
| Over-promising recovery | Harm, liability | Copy review: never promise refunds |
| Data breach | Severe | Collect nothing; stateless API; no logs of bodies |
| AI hallucination | Wrong IDs/advice | AI opt-in; number/ID guard; knowledge-base-only answers |
| Characters feel manipulative | Trust loss | Clear "virtual guide" labels, no emotional pressure, no dark patterns |
| Regulatory changes | Compliance | Legal review before public launch (see §12) |

---

## 12. Legal and compliance (to be confirmed by counsel; not legal advice)

- Review obligations under India's Digital Personal Data Protection Act, 2023 and applicable rules, and the IT Act, before public launch. By design the product avoids collecting personal data server-side.
- Use "1930", "cybercrime.gov.in" and agency names only as factual references; no logos or emblems; no implied endorsement.
- Terms of use and privacy notice in plain language, in all three languages.
- Content about law ("no digital arrest in Indian law") is cited to its source and reviewed periodically.

---

## 13. Dependencies and constraints

- Official portals and the 1930 process can change. Every instruction is dated and sourced.
- Anthropic API (optional features only).
- Hosting with HTTPS.
- No assumed access to any government system.

---

## 14. Go-to-market (non-commercial)

1. Pilot with a college community and a senior-citizen group.
2. Share with consumer-protection NGOs and bank awareness desks.
3. Publish the rule set and evaluation results openly.
4. Provide a short printable "If you've been scammed" card linking to the product.

---

## 15. Open questions

1. Is any official submission API available to civic-tech apps, and who would approve access?
2. What exact fields does the live portal currently require? (Verify before launch.)
3. Which languages after the first three?
4. Who hosts and who is the long-term maintainer?
5. Does the legal review require a data-protection officer or notice formats?

---

## 16. Glossary

| Term | Meaning |
|---|---|
| **1930** | National cyber-crime helpline for financial fraud |
| **NCRP / cybercrime.gov.in** | National Cyber Crime Reporting Portal |
| **I4C** | Indian Cyber Crime Coordination Centre |
| **UTR / RRN** | 12-digit transaction reference for UPI/IMPS |
| **Digital arrest** | A scam where fraudsters pose as officials on video calls; not a real legal concept |
| **Golden hour** | The first hours after a fraud, when tracing money is most likely to succeed |
| **Tier 1/2/3** | Data-sensitivity levels used for Self-Fill Mode |
| **Guide** | An illustrated virtual character that talks the user through the product |
