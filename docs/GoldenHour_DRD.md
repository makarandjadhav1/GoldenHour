# GoldenHour: Design Requirements Document (DRD)

| | |
|---|---|
| **Document** | DRD v1.0, companion to `GoldenHour_BRD.md` and `GoldenHour_TRD.md` |
| **Goal** | A product that feels warm, calm, deeply caring and safe to a frightened person, and is beautiful and fully interactive |
| **Design name** | "First Light" |

---

## 1. Design intent

A person arriving here may have just lost their savings. They are scared, ashamed, and rushed. The design must say, within five seconds:

1. **"You are not alone."** A guide greets you by name-less warmth, not forms.
2. **"This is not your fault."** No blame in any word.
3. **"You are safe here."** Visible privacy, no secrets asked, no tricks.
4. **"Here is what to do next."** One clear action at a time.

### Principles

| Principle | In practice |
|---|---|
| **Calm over alarm** | Urgency is shown through a gentle sun-clock, never red flashing banners or countdown panic. |
| **One thing at a time** | One question per screen in the emergency flow; big targets; short sentences. |
| **Show, don't claim, safety** | The Privacy Ledger shows real network activity. A claim of safety without proof is not allowed. |
| **Warm, never authoritative** | Guides never speak like police, banks or officials. They are friends who know the process. |
| **Honest limits** | "I can't file this for you" is said openly and kindly. |
| **Everyone included** | Hindi, Marathi, English; large text; read-aloud; keyboard; screen reader; low-end phone. |

### The one memorable thing

The **Sun-Clock** (§7.1): a quiet arc of light that tracks the first two hours, then the first day. It is the product's identity ("Golden Hour"). Everything else stays quiet.

---

## 2. Brand

- **Name:** GoldenHour
- **Voice:** a kind, calm, knowledgeable neighbour. Plain verbs, short sentences, sentence case, no jargon (say "transaction ID", then "UTR" in brackets).
- **Never:** blame words ("careless", "mistake"), threats, ALL CAPS shouting, fake urgency, official-looking emblems, saffron-white-green tricolour layouts that suggest a government site.
- **Always visible:** a small chip "Independent tool. Not a government service."

---

## 3. Design tokens

Define as CSS custom properties on `:root`, redefine under `@media (prefers-color-scheme: dark)` guarded as `:root:not([data-theme="light"])`, and again under `:root[data-theme="dark"]`. Also a high-contrast set under `[data-contrast="high"]`.

### 3.1 Colour (light theme)

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#EEF3F5` | Page background ("dawn mist") |
| `--surface` | `#FFFFFF` | Cards |
| `--surface-2` | `#E3ECEF` | Inset areas, chips |
| `--ink` | `#13232E` | Body text (contrast on `--bg` ≥ 12:1) |
| `--ink-soft` | `#44606F` | Secondary text (≥ 5.5:1) |
| `--lagoon` | `#0E6E7E` | Primary actions, links |
| `--lagoon-deep` | `#0A4F5B` | Pressed/hover primary |
| `--sun` | `#E8A33D` | **Reserved for the Sun-Clock and golden-hour moments only** |
| `--sun-soft` | `#FBE7C2` | Sun-Clock glow background |
| `--safe` | `#2E7D5B` | Safe/positive verdicts, tier-1 ticks |
| `--caution` | `#B8741A` | Suspicious verdicts |
| `--danger` | `#B3322F` | Scam verdicts (used in a soft tinted panel, never full-bleed) |
| `--line` | `#C9D6DC` | Borders |
| `--focus` | `#0B5FFF` | Focus ring (3px, offset 2px) |

### 3.2 Colour (dark theme)

`--bg #0D1A22`, `--surface #14262F`, `--surface-2 #1B323D`, `--ink #E9F1F4`, `--ink-soft #A7BCC6`, `--lagoon #4FC1D3`, `--lagoon-deep #7FD6E4`, `--sun #F2B558`, `--sun-soft #3A2E17`, `--safe #5ECB9A`, `--caution #E3A24B`, `--danger #F27A76`, `--line #2A4350`, `--focus #6BA1FF`.

All text/background pairs must meet WCAG 2.2 AA (4.5:1 body, 3:1 large and UI). Colour never carries meaning alone (add icon + text).

### 3.3 Typography

| Role | Family | Fallback | Notes |
|---|---|---|---|
| Display / headings / guide speech | **Bricolage Grotesque** | `system-ui, sans-serif` | Friendly, slightly quirky |
| Body / UI / Devanagari | **Hind** | `"Noto Sans Devanagari", system-ui, sans-serif` | Supports Latin and Devanagari in one family |
| Code / numbers (UTRs) | **JetBrains Mono** | `ui-monospace, monospace` | UTRs shown in groups of 4 for readability |

- **Self-host all fonts** (no Google Fonts requests) so loading fonts doesn't leak user IPs to a third party.
- Scale (rem, base 1.0625 = 17px): 0.8125, 0.9375, 1.0625, 1.25, 1.5, 1.875, 2.5. Large-text mode multiplies the root size by 1.25 (and a second step 1.5).
- Line length ≤ 70 characters; body line-height 1.55 (Latin) and 1.7 (Devanagari).
- Sentence case everywhere. No all-caps labels, no letter-spaced eyebrows.

### 3.4 Space, shape, depth

- Space scale: 4, 8, 12, 16, 24, 32, 48, 72.
- Radius: 10 (inputs), 16 (cards), 28 (guide speech bubbles), 999 (chips). Different radii on purpose; not one radius everywhere.
- Shadows: only two: `--lift` (`0 2px 10px rgba(19,35,46,.10)`) for floating speech bubbles and the call button; everything else is flat with a 1px `--line` border.
- Minimum touch target 48 × 48 px; spacing between targets ≥ 8 px.

### 3.5 Iconography

Line icons, 2px stroke, rounded caps (use Lucide). Each icon is paired with a text label.

---

## 4. The two guides

### 4.1 Rules for both guides

- Fictional illustrated characters, **not real people**. A permanent chip near the speech bubble says **"Virtual guide. Not a real person. Not a government service."**
- They speak in short messages, one idea at a time, with a visible pause (typing indicator) of 400–700 ms. Users can tap to skip animation.
- They **never** ask for an OTP, PIN, CVV or password, and they say so at the start.
- They **never** promise money back. They say what they can and can't do.
- They never use authority language ("you are required", "or else"), never shame, never create false urgency.
- The user chooses a guide on first visit ("Who would you like to talk to?") and can change at any time from the top bar. The choice is remembered only for the session unless the user opts in to remember it on the device.

### 4.2 Asha (woman): the Reporter guide

| Aspect | Spec |
|---|---|
| **Role** | Leads the Emergency Flow and Self-Fill Mode |
| **Personality** | Calm, steady, warm; the person you'd want at your side in a crisis |
| **Look** | Early 30s. Shoulder-length dark wavy hair tucked behind one ear. Warm medium-brown skin (`#B9794D`). Soft teal kurta with a small stitched collar (`#0E6E7E`), light scarf in `--sun-soft`. Small studs. No religious symbols. |
| **Signature gesture** | Open palm at chest height when reassuring; small nod when a field is valid |
| **Voice sample (EN)** | "Take a breath. This isn't your fault. Tell me what happened, at your pace." |

### 4.3 Kabir (man): the Checker guide

| Aspect | Spec |
|---|---|
| **Role** | Leads the Message Checker and Ask |
| **Personality** | Patient, curious, clear; explains things without talking down |
| **Look** | Late 30s. Short dark hair, round glasses, light stubble. Medium-dark brown skin (`#8E5A3A`). Mustard shirt (`#C98F2B`) with sleeves rolled to the elbows, open charcoal overshirt. No religious symbols. |
| **Signature gesture** | Pushes glasses up when "inspecting" a message; points to the exact phrase being explained |
| **Voice sample (EN)** | "Paste it here. I'll show you exactly what looks off, and why." |

Either guide can appear on any screen (the user's choice). Their dialogue scripts are equivalent in meaning.

### 4.4 Art direction

- Flat vector, geometric shapes, rounded joins, **no outlines**; soft shading with two flat tones per surface.
- Half-body framing (waist up) in a 4:5 viewBox (`0 0 400 500`) so they sit comfortably above the content.
- Background behind the guide: a soft circle in `--sun-soft` ("dawn halo"), echoing the product's golden-hour idea.
- Delivered as **inline SVG with named layers** (so Claude Code can animate parts), not video.

### 4.5 SVG layer structure (per guide)

```
<svg viewBox="0 0 400 500" role="img" aria-label="Asha, virtual guide">
  <g id="halo"/>
  <g id="torso">
     <g id="clothing"/> <g id="neck"/>
  </g>
  <g id="arm-left"/>  <g id="arm-right"> <g id="hand-right"/> </g>
  <g id="head">
     <g id="hair-back"/> <g id="face"/> <g id="ears"/>
     <g id="eyes">  <g id="eye-left"><ellipse id="sclera"/><circle id="iris"/><path id="lid"/></g> ... </g>
     <g id="brows"> <path id="brow-left"/> <path id="brow-right"/> </g>
     <path id="mouth"/>
     <g id="nose"/> <g id="glasses"/> (Kabir) <g id="hair-front"/>
  </g>
</svg>
```

### 4.6 Moods (expressions)

Each mood is a set of parameters applied via CSS variables/transforms (no separate drawings needed).

| Mood | Brows (y offset, inner raise) | Eyes | Mouth | Head | Hand | Used when |
|---|---|---|---|---|---|---|
| `idle` | 0, 0 | open, blink every 4–6 s (random) | soft closed smile | 0° | rest | Waiting |
| `welcome` | −2, 0 | open | warm smile | tilt 3° | wave (1 cycle) | First screen |
| `listening` | −3, +4 | open, gaze toward input | neutral-soft | tilt 4° toward input | rest | User typing/pasting |
| `concerned` | −4, +8 (inner ends raised) | slightly wider | small, slightly down | tilt 3° | hand to chest | User reports losing money |
| `reassure` | −2, +3 | soft | gentle smile | 0° | open palm | After empathy, before steps |
| `thinking` | −3, +2 | look up-right | pursed small | tilt 6° | chin touch | Analysing/processing |
| `nod` | 0 | blink once | smile | nod 2× (6px) | rest | A field is validated |
| `alert` (Kabir) | −5, 0 | wide | flat | 0° | pointing | Dangerous phrase found |
| `relief` | −1 | soft | small smile | 0° | hand down | Genuine message / pack ready |

No mood may ever be used to push the user (no sad faces for hesitation, no fake delight at a payment-related action).

### 4.7 Speech bubble

- Radius 28, `--surface`, 1px `--line`, `--lift` shadow, tail pointing to the guide.
- Text typed at ~35 chars/s (skippable). Screen readers receive the full text immediately via `aria-live="polite"`, not the animation.
- Max 2 sentences (≈ 160 characters) per bubble; longer content is split into consecutive bubbles with 600 ms between.
- Every bubble has a tiny speaker icon button for **read-aloud** and an option row (chips) for quick replies.

### 4.8 Behaviour reactions

| Event | Reaction |
|---|---|
| Page load | Guide fades in (200 ms) and plays `welcome`. |
| User starts typing | `listening`, gaze moves toward the input. |
| UTR validated (12 digits) | `nod`, tick appears on the field card, short line: "That looks right." |
| Amount found | `idle` with line "Got the amount." No celebration. |
| Missing UTR | `reassure` with line: "No problem. Open your bank or UPI app, go to history, and open the payment." |
| Verdict scam | `alert` for 1 s, then `reassure`. Line: "Please don't pay. Here's why I think so." |
| Verdict low | `relief`, line: "Nothing alarming matched. That isn't a guarantee, so verify before paying." |
| 60 s idle | Soft prompt: "I'm here whenever you're ready." One time only. |
| User tries to enter an OTP/PIN | Field shows gentle warning and masks; guide `concerned`: "Please don't share that with anyone, including me." |
| Pack ready | `relief` + `reassure`, line: "Your pack is ready. I can't file it for you, but you now have everything in the right order." |

---

## 5. Motion

| Motion | Spec |
|---|---|
| Durations | 120 ms (micro), 240 ms (UI), 480 ms (scene change), easing `cubic-bezier(.2,.8,.2,1)` |
| **Orchestrated moment** | On entering the Emergency Flow: the dawn halo expands from the Sun-Clock, the guide steps in, the first question fades up. Once only per session. |
| Micro-interactions | Field valid: 240 ms check draw; copy button: icon swap + "Copied" for 1.6 s; chip select: scale 0.97→1. |
| Page transitions | Cross-fade + 8 px upward settle; no sliding screens. |
| Idle life | Blink, breathing (torso scaleY 1→1.012 over 4 s), subtle halo shimmer. Pauses when the tab is hidden. |
| Reduced motion | Under `prefers-reduced-motion` (or a settings toggle): no typing animation, no breathing, no halo shimmer, instant cross-fades; guide poses change without tweening. |
| Performance | Animate `transform` and `opacity` only; target 60 fps on a low-end Android; total animation JS budget 20 KB gz. |

---

## 6. Information architecture and screens

```
Welcome ─┬─ Choose guide
         ├─ Check a message (Kabir default)
         ├─ I lost money (Asha default) ─ Emergency Flow (5 steps)
         ├─ Ask (Kabir default)
         └─ About / Privacy / Settings
Always present: Top bar, "Call 1930" button, Privacy Ledger drawer, language switch
```

### 6.1 Global chrome

| Element | Spec |
|---|---|
| **Top bar** | Logo "GoldenHour" (sun-dot mark), guide switcher (avatar), language (EN/हिं/मरा), text size (A / A+), theme, privacy ledger icon. Compact on mobile. |
| **Trust bar** (below top bar, slim) | "Nothing is stored. We never ask for your OTP or PIN. Independent tool, not a government service." Collapses to a lock icon after first view; always re-openable. |
| **Call 1930 button** | Floating action (bottom-right on mobile, in the bar on desktop). `tel:1930`. Label "Call 1930". Never auto-dials. 56 px target. Shown on every screen of the Emergency Flow, and on Check results with verdict scam/suspicious. |
| **Footer** | Disclaimer, sources, last-reviewed dates, "Report an error". |

### 6.2 Welcome screen

```
┌────────────────────────────────────────────────────────────┐
│  GoldenHour                       EN | हिं | मरा   A  ◐  🔒 │
├────────────────────────────────────────────────────────────┤
│            (Asha and Kabir, side by side, haloed)           │
│        "Hi. I'm here to help, at your pace."                │
│   Independent tool · Nothing stored · No OTP, ever          │
│                                                            │
│   ┌───────────────────┐ ┌─────────────────┐ ┌────────────┐ │
│   │ I got a message   │ │ I lost money    │ │ I have a   │ │
│   │ I'm unsure about  │ │ (start here if  │ │ question   │ │
│   │ → Check it        │ │ it just happened)│ │ → Ask      │ │
│   └───────────────────┘ └─────────────────┘ └────────────┘ │
│                                                            │
│      [ Who would you like to talk to?  Asha · Kabir ]       │
└────────────────────────────────────────────────────────────┘
```

- "I lost money" is the most prominent card (filled `--lagoon`).
- Both guides appear on this screen only; afterwards, one guide at a time.

### 6.3 Message Checker (Kabir)

1. Large paste area with example chips ("Bank KYC SMS", "Parcel call", "Part-time job") and a voice-input button (see §10 for privacy note).
2. As the user pastes, the guide shows `thinking` for ≤ 600 ms.
3. **Result panel:**
   - **Verdict banner:** soft tinted panel, icon + words ("Very likely a scam"), score ring (not a raw number alone), type of scam.
   - **Highlighted message:** the user's text with each risky phrase underlined; hovering/tapping a phrase shows its reason and the guide points to it.
   - **Why list:** cards sorted by weight, each with plain reason.
   - **What to do:** 2–4 steps.
   - **Actions:** "Copy a warning for family", "I already paid → open Emergency Flow" (carries the text over).
4. Genuine messages show a green, quiet "No strong signals" panel and the caution line.

### 6.4 Emergency Flow (Asha)

Five steps with a vertical stepper rail (horizontal on mobile). A "Quick path" toggle reduces the flow to 5 fields.

| Step | Screen | What happens |
|---|---|---|
| **1. Tell me** | Asha: "Tell me what happened, at your pace." Big paste/type box; voice option; "When did the money leave?" as five large radio cards. | Asha `listening`; extraction chips animate in beneath the box as the user types ("₹49,999", "UTR ···· 0123"). |
| **2. Check the details** | Field cards, one per item, each with a **tier chip** (see below). | Edit freely; validation ticks; Asha nods. Missing items show a "How to find this" expandable. |
| **3. How would you like to report?** | Two big cards: **A: Short call (recommended)** and **B: Portal only**; Mode C card greyed with "Not available yet". | Asha explains the trade-off in two bubbles. |
| **4. Your pack** | Tabs: *Call script*, *Portal sheet*, *Bank letter*, *Checklist*. | One-tap copy per field. |
| **5. After this** | Reminder (.ics), "What to do if the agent asks for an OTP", "Beware of recovery offers". | Asha `reassure`. |

**Tier chips:** Tier 1 `Share on the 1930 call` (lagoon outline), Tier 2 `Type into the portal yourself` (neutral), Tier 3 `Never share` (danger outline, lock icon).

**Sun-Clock** sits at the top of steps 1–5 (see §7.1).

### 6.5 Ask (Kabir)

- A chat-like pane with suggested questions as chips ("What is a UTR?", "Do I call 1930 or use the portal?", "What if I can't find my transaction ID?").
- Each answer: short text, **source chip** (e.g., "Canara Bank / I4C advisory"), "last verified" date, and a link to the official page.
- Unknown question: "I don't have a verified answer for that. The best next step is calling 1930 or checking cybercrime.gov.in." No guessing.

### 6.6 Privacy Ledger (drawer)

A drawer from the right (bottom sheet on mobile) titled **"What left your device"**.

| Element | Spec |
|---|---|
| Summary | "Stored on our servers: nothing. Third-party trackers: none." |
| Live list | One line per network request: time, endpoint name ("Check message"), size in bytes, and whether the content was masked. **Never shows the content.** Updates in real time. |
| Local data | Shows what's kept in the browser session (e.g., "your draft") with **Delete everything now**. |
| Proof | A short plain-language explanation and a link to the open-source repository. |

Visual: a simple lock-and-sun glyph; entries slide in softly. When nothing has been sent, the panel shows a calm empty state: "Nothing has left your device."

### 6.7 Empty, error and offline states

| State | Guide line | Notes |
|---|---|---|
| Empty | "Whenever you're ready." | Examples offered |
| Can't read input | "I couldn't find amounts or transaction IDs. You can type them in yourself, it only takes a minute." | Shows manual form |
| Offline / no connection | "You're offline. Everything here still works on your phone, except my optional extra opinion." | Checker, Emergency Flow, Ask and exports all run on the device |
| AI unavailable | "My extra opinion isn't available right now, but the main check above is complete." | No error codes |
| Invalid number | "That doesn't look like a 12-digit transaction ID. Check your bank app?" | Never blame |

---

## 7. Key components

### 7.1 Sun-Clock

- A circular arc (180° "horizon" arc) with a sun disc that moves from left (incident) to right (24 hours).
- Zones: **0–2 h** `--sun` glow ("First two hours"), **2–24 h** warm `--caution` tint ("Within a day"), **after 24 h** muted `--ink-soft` ("Report anyway").
- Elapsed time is chosen with five radio cards (not a free time picker) to reduce effort.
- Below the arc: a single sentence from the elapsed-time banner. No flashing, no countdown digits, no red.
- Accessible: `role="img"` with an `aria-label` that states the zone and message; text equivalent always rendered.

### 7.2 Field card

```
┌───────────────────────────────────────────┐
│ Transaction ID (UTR)     [Share on 1930 call]│
│ [ 5245 8792 0123 ]    ✓                    │
│ ▸ How to find this                          │
└───────────────────────────────────────────┘
```

States: empty, filled, auto-filled (small sparkle-free "found in your text" tag), edited, invalid, warning. Monospace groups of 4 for numeric IDs.

### 7.3 Copy block

Monospace text, line numbers off, a primary "Copy" button, success micro-animation, and (for the call script) a numbered checkbox column so the user can tick lines as they read them aloud.

### 7.4 Verdict banner

Soft-tinted panel (`color-mix` of the verdict colour at 12% on `--surface`), left icon, headline, score ring, scam-type chip. Never full-bleed red.

### 7.5 Mode cards (A/B/C)

Each: title, who sees what (3 lines), pro/con, "Choose". A is pre-selected with a "Recommended for the first hours" label. C is disabled, with an `aria-disabled` explanation.

### 7.6 Language and text controls

Three-way segmented control; text size stepper (100%, 125%, 150%); read-aloud toggle; high-contrast toggle; reduced-motion toggle. Persisted only for the session unless the user opts in.

---

## 8. Copy library (excerpt; all strings go in i18n files)

| Key | English | हिन्दी |
|---|---|---|
| `welcome.title` | Hi. I'm here to help, at your pace. | नमस्ते। मैं आपकी मदद के लिए हूँ, आपकी गति से। |
| `welcome.notyourfault` | This isn't your fault. Scammers are skilled at this. | यह आपकी गलती नहीं है। ठग इसमें माहिर होते हैं। |
| `trust.line` | Nothing is stored. We never ask for your OTP or PIN. | कुछ भी सेव नहीं होता। हम आपका OTP या PIN कभी नहीं माँगते। |
| `disclaimer.chip` | Independent tool. Not a government service. | स्वतंत्र टूल। सरकारी सेवा नहीं। |
| `guide.label` | Virtual guide. Not a real person. | वर्चुअल गाइड। असली व्यक्ति नहीं। |
| `flow.start` | Tell me what happened, at your pace. | बताइए क्या हुआ, अपनी गति से। |
| `flow.missingUtr` | No problem. Open your bank or UPI app, go to history, and open the payment. | कोई बात नहीं। अपना बैंक या UPI ऐप खोलें, हिस्ट्री में जाएँ और उस भुगतान को खोलें। |
| `flow.cantFile` | I can't file this for you. You'll submit it yourself, and I'll make it easy. | मैं इसे आपके लिए दर्ज नहीं कर सकती। आप इसे खुद दर्ज करेंगे, मैं इसे आसान बनाऊँगी। |
| `check.low` | Nothing alarming matched. That isn't a guarantee, so verify before paying. | कुछ चिंताजनक नहीं मिला। यह गारंटी नहीं है, इसलिए भुगतान से पहले जाँचें। |
| `check.scam` | Please don't pay. Here's why I think so. | कृपया भुगतान न करें। मुझे ऐसा क्यों लगता है, देखिए। |
| `ledger.empty` | Nothing has left your device. | आपके डिवाइस से कुछ भी बाहर नहीं गया। |
| `call.cta` | Call 1930 | 1930 पर कॉल करें |

Marathi strings follow the same keys (to be authored and reviewed by a native speaker before launch).
Rules: never "you must"; never "hurry"; always "when you're ready", "if you can".

---

## 9. Responsive layout

| Breakpoint | Layout |
|---|---|
| < 600 px | Single column; guide shown as a compact head-and-shoulders above the bubble; Sun-Clock as a half-height arc; sticky "Call 1930" button |
| 600 to 1024 px | Two columns for review step (fields | preview) |
| > 1024 px | Guide stage left (35%), content right (65%); stepper rail fixed |

Fixed elements honour safe-area insets (`env(safe-area-inset-*)`). Orientation lock not applied.

---

## 10. Accessibility and inclusion

- WCAG 2.2 AA minimum; focus ring always visible; full keyboard operation; logical heading order.
- Guide SVGs have text alternatives; decorative parts are `aria-hidden`. Speech bubbles are live regions.
- **Read-aloud** uses the browser's speech synthesis, offline where available. Hindi and Marathi voices depend on the device; if none exists, show "Your phone has no Hindi voice installed" kindly.
- **Voice input** is optional and off by default. Because browser speech recognition may send audio to a third party, show a one-line notice before the first use and **log it in the Privacy Ledger**. Provide manual typing as the primary path.
- Plain-language mode: shorter sentences and icons for each step.
- Never time out a session abruptly; never disable paste.
- Support for screen magnification up to 200% and text spacing overrides.
- Test with a screen reader (TalkBack and NVDA) on the core flows.

---

## 11. Anti-patterns (explicitly banned)

- Countdown timers with red flashing, "act now" copy.
- Guides that pretend to be human operators or officials.
- Confetti or celebration after a user reports a loss.
- Dark patterns: pre-ticked consent, hidden "skip", guilt copy.
- Asking for any Tier 3 data, ID-proof upload, or login.
- Third-party fonts, analytics, chat widgets or trackers.
- Generic template look: avoid cream + terracotta, black + neon, or identical rounded card grids; follow the tokens above.

---

## 12. Design deliverables for Claude Code

1. `tokens.css` and `tokens.ts` (from §3).
2. `Guide.tsx` (props: `who: "asha" | "kabir"`, `mood`, `speaking`, `lookAt`), implemented as inline SVG per §4.5–4.6.
3. `SpeechBubble`, `SunClock`, `FieldCard`, `CopyBlock`, `VerdictBanner`, `ModeCard`, `PrivacyLedger`, `Stepper`, `CallButton`, `LanguageSwitch`, `TextSizeControl`.
4. Storybook (or a `/design` route) showing every guide mood and each component state.
5. i18n files `en.json`, `hi.json`, `mr.json` with all copy keys.
6. Visual regression baselines for the six main screens in light, dark and large-text modes.

## 13. Design acceptance checklist

- [ ] A first-time user can state within 5 seconds that the tool is independent, free and doesn't store data.
- [ ] Every screen shows only one primary action.
- [ ] The guide's mood changes in response to at least five distinct user events.
- [ ] Nothing in the UI blames the user.
- [ ] All text/background pairs pass AA; large-text mode breaks no layout.
- [ ] `prefers-reduced-motion` produces a fully static but usable UI.
- [ ] Privacy Ledger lists every real network request made by the app, and shows "nothing left" when none.
- [ ] Hindi and Marathi render correctly with no clipped glyphs.
- [ ] Sun-Clock is understandable without colour.
