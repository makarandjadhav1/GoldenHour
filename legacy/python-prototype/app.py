"""GoldenHour: first aid for UPI / cyber fraud in India.  Run: streamlit run app.py"""
from __future__ import annotations

import hashlib

import streamlit as st

import llm
import samples
import scamcore as sc

st.set_page_config(page_title="GoldenHour: UPI scam first aid", page_icon="🛡️", layout="wide")

st.markdown(
    """
<style>
.verdict{padding:.9rem 1.2rem;border-radius:10px;font-weight:700;font-size:1.35rem;margin:.25rem 0 .75rem 0;border:1px solid}
.v-scam{background:rgba(220,38,38,.12);border-color:rgba(220,38,38,.55)}
.v-suspicious{background:rgba(245,158,11,.14);border-color:rgba(245,158,11,.6)}
.v-low{background:rgba(22,163,74,.12);border-color:rgba(22,163,74,.5)}
.clock{padding:.8rem 1.1rem;border-radius:10px;border-left:6px solid;margin:.5rem 0 1rem 0;font-weight:600}
.c-red{background:rgba(220,38,38,.12);border-color:#dc2626}
.c-orange{background:rgba(245,158,11,.14);border-color:#f59e0b}
.c-yellow{background:rgba(234,179,8,.12);border-color:#eab308}
</style>
""",
    unsafe_allow_html=True,
)

client = llm.get_client()

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Settings")
    lang = st.radio("Language", ["English", "हिन्दी (Hindi)", "मराठी (Marathi, needs Claude)"], index=0)
    lang_key = "hi" if lang.startswith("हि") else "en"
    use_claude = False
    if client:
        use_claude = st.toggle("Use Claude for a second opinion", value=True)
        st.caption(f"Claude connected ({llm.MODEL}).")
    else:
        st.info("Demo mode: built-in rules engine only. Set ANTHROPIC_API_KEY to enable Claude.")
    st.divider()
    st.caption(
        "Secrets such as card numbers, Aadhaar numbers and OTP/PIN values are masked on your machine "
        "before analysis, and before anything is sent to Claude. Don't paste passwords."
    )
    st.caption("Heuristics, not a guarantee. Not legal advice. Emergency: call 1930.")

st.title("🛡️ GoldenHour")
st.markdown("**Paste a suspicious message to check it, or tell us what happened to get your 1930 call script "
            "and a ready-to-file complaint in under a minute.**")

tab_check, tab_paid = st.tabs(["🔍 Check a message", "🚨 I already paid / shared details"])


@st.cache_data(show_spinner=False, ttl=3600)
def cached_explain(redacted: str, labels: tuple, language: str) -> dict:
    c = llm.get_client()
    if c is None:
        raise llm.LLMError("no client")
    return llm.explain(c, redacted, list(labels), language)


def claude_language() -> str:
    if lang_key == "hi":
        return "Hindi"
    return "Marathi" if lang.startswith("मराठी") else "English"


# ------------------------------------------------------------------ tab 1
def _load_msg():
    pick = st.session_state.get("msg_sample", "")
    if pick:
        st.session_state["msg"] = samples.MESSAGES[pick]


with tab_check:
    st.selectbox("Try a sample", [""] + list(samples.MESSAGES), key="msg_sample", on_change=_load_msg)
    st.text_area("Paste the SMS / WhatsApp text, or describe what the caller said", key="msg", height=170)
    raw = st.session_state.get("msg", "").strip()
    if raw:
        clean, n_masked = sc.redact(raw)
        det = sc.detect(clean)
        label_en, label_hi = sc.VERDICT_LABELS[det.verdict]
        st.markdown(f'<div class="verdict v-{det.verdict}">{label_hi if lang_key == "hi" else label_en}</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        c1.metric("Scam likelihood (rule score)", f"{det.score}/100")
        if det.verdict != "low":
            c2.markdown(f"**Looks like:** {det.type_name}")
        st.progress(det.score / 100)
        if n_masked:
            st.caption(f"{n_masked} sensitive value(s) were masked before analysis.")

        if det.hits:
            st.subheader("Why")
            for h in sorted(det.hits, key=lambda x: -x.weight):
                with st.container(border=True):
                    st.markdown(f"**{h.label}**")
                    st.caption(h.why)
                    st.code(h.evidence, language=None)
        elif det.verdict == "low":
            st.success("No known scam patterns matched. Still verify through an official channel before paying or clicking.")

        st.subheader("What to do now")
        for line in sc.ADVICE.get(det.scam_type, sc.ADVICE["unclear"]):
            st.markdown(f"- {line}")
        st.markdown("- Report the sender at **sancharsaathi.gov.in > Chakshu**. If money is already gone, call **1930** "
                    "and open the *I already paid* tab.")

        if use_claude:
            with st.expander("🤖 Claude's second opinion", expanded=True):
                try:
                    with st.spinner("Asking Claude..."):
                        res = cached_explain(clean, tuple(h.label for h in det.hits), claude_language())
                    st.markdown(res["why"])
                    if res["extra_red_flags"]:
                        st.markdown("**Extra things Claude noticed:**")
                        for f in res["extra_red_flags"]:
                            st.markdown(f"- {f}")
                    if res["tell_family"]:
                        st.markdown("**Forward this to family:**")
                        st.code(res["tell_family"], language=None)
                    st.caption(f"AI opinion, confidence: {res['confidence'] or 'n/a'}. The score above comes from the rules, not from Claude.")
                except llm.LLMError as e:
                    st.warning(f"Claude is unavailable right now, so you're seeing the built-in analysis only. ({e})")
        elif claude_language() == "Marathi":
            st.caption("Marathi explanations need Claude. Add an API key to enable them.")

# ------------------------------------------------------------------ tab 2
def _load_inc():
    pick = st.session_state.get("inc_sample", "")
    if pick:
        st.session_state["inc"] = samples.INCIDENTS[pick]


AGO = {"Just now (under 15 min)": 10, "About 30 minutes ago": 30, "1 to 2 hours ago": 90,
       "A few hours ago (same day)": 360, "Yesterday or earlier": 2000}

with tab_paid:
    st.selectbox("Try a sample incident", [""] + list(samples.INCIDENTS), key="inc_sample", on_change=_load_inc)
    st.text_area("Paste what you have: the bank debit SMS, the chat, or just describe what happened", key="inc", height=170)
    ago = st.radio("When did the money leave?", list(AGO), horizontal=True)
    level, msg = sc.elapsed_banner(AGO[ago])
    st.markdown(f'<div class="clock c-{level}">⏱ {msg}</div>', unsafe_allow_html=True)

    narrative = st.session_state.get("inc", "").strip()
    if not narrative:
        st.info("Paste the debit SMS or describe what happened. We'll pull out the UTR, amounts, UPI IDs, phone numbers and links for you.")
    else:
        clean, n_masked = sc.redact(narrative)
        inc = sc.extract_incident(clean)
        det = sc.detect(clean)
        h = hashlib.sha256(clean.encode()).hexdigest()[:8]

        st.subheader("1. Check what we found (edit anything that's wrong)")
        if n_masked:
            st.caption(f"{n_masked} sensitive value(s) were masked.")
        a, b, c = st.columns(3)
        name = a.text_input("Your name", key="f_name")
        mobile = b.text_input("Your mobile number", key="f_mobile")
        location = c.text_input("District / nearest police station", key="f_loc")

        d, e, f_ = st.columns(3)
        bank_guess = ", ".join(inc.banks + inc.apps)
        bank = d.text_input("Bank / UPI app money left from", value=bank_guess, key=f"f_bank_{h}")
        account = e.text_input("Your account (last 4) / UPI ID debited", value=", ".join(inc.account_last4), key=f"f_acct_{h}")
        when = f_.text_input("Date / time of transaction(s)", value=", ".join(inc.when_hints), key=f"f_when_{h}")

        g, i = st.columns(2)
        amount = g.text_input("Amount(s) lost (comma separated)", value=", ".join(inc.amounts), key=f"f_amt_{h}")
        utrs = i.text_input("UTR / transaction ID(s) (12 digits for UPI)", value=", ".join(inc.utrs), key=f"f_utr_{h}")
        if inc.possible_utrs and not inc.utrs:
            st.warning("These 12-digit numbers might be UTRs but weren't labelled: "
                       + ", ".join(inc.possible_utrs) + ". Copy them into the box above only after checking in your bank app.")

        j, k, l_ = st.columns(3)
        s_phone = j.text_input("Scammer's phone number(s)", value=", ".join(p for p in inc.phones), key=f"f_sp_{h}")
        s_upi = k.text_input("Scammer's UPI ID / account", value=", ".join(inc.upi_ids), key=f"f_su_{h}")
        s_link = l_.text_input("Website / app / profile", value=", ".join(inc.urls), key=f"f_sl_{h}")
        st.caption("Phone numbers found include yours if you mentioned it. Remove your own number from the scammer box.")
        desc = st.text_area("What happened (this goes into your complaint)", value=sc.auto_summary(det, clean),
                            key=f"f_desc_{h}", height=110)

        fields = sc.Fields(
            name=name, mobile=mobile, location=location, bank=bank, account=account, amount=amount,
            utrs=sc.split_csv(utrs), when=when, scam_phones=sc.split_csv(s_phone), scam_upi=sc.split_csv(s_upi),
            scam_links=sc.split_csv(s_link), description=desc,
        )

        miss = sc.missing_items(fields)
        if miss:
            st.subheader("Still missing")
            for m in miss:
                st.markdown(f"- ☐ {m}")

        st.subheader("2. Do this, in this order")
        for n, (t_en, t_hi, detail) in enumerate(sc.STEPS, 1):
            st.checkbox(f"{n}. {t_hi if lang_key == 'hi' else t_en}", key=f"step_{n}")
            st.caption(detail)

        st.subheader("3. Your 1930 call script")
        st.code(sc.build_call_script(fields), language=None)

        st.subheader("4. Complaint text for cybercrime.gov.in")
        complaint = sc.build_complaint(fields)
        st.code(complaint, language=None)
        if client and use_claude:
            if st.button("✨ Polish wording with Claude"):
                try:
                    with st.spinner("Polishing..."):
                        st.session_state["polished"] = llm.polish(client, complaint)
                except llm.LLMError as e:
                    st.warning(f"Kept your original text. Claude's rewrite was not used: {e}")
            if st.session_state.get("polished"):
                st.markdown("**Claude's polished version** (every number and ID was checked against your draft):")
                st.code(st.session_state["polished"], language=None)

        st.subheader("5. Letter / email to your bank")
        st.code(sc.build_bank_letter(fields), language=None)

        st.download_button("⬇ Download the full response pack (.txt)", data=sc.build_pack(fields),
                           file_name="goldenhour_response_pack.txt", mime="text/plain", type="primary")
