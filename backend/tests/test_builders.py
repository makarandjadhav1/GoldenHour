import re
from datetime import UTC, datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from app import builders as b
from app.fields import elapsed_banner, empty_fields, fields_from, missing_items, validate

txt = st.text(alphabet=st.characters(exclude_characters="QZXJ", exclude_categories=["Cs"]), max_size=40).filter(
    lambda s: not re.search(r"none|nan|undefined|null", s, re.I)
)
fields_st = st.fixed_dictionaries(
    {
        "amount": txt,
        "bank": txt,
        "account": txt,
        "when": txt,
        "mobile": txt,
        "name": txt,
        "location": txt,
        "description": txt,
        "utrs": st.lists(txt, max_size=3),
        "scamPhones": st.lists(txt, max_size=2),
        "scamUpi": st.lists(txt, max_size=2),
        "scamLinks": st.lists(txt, max_size=2),
    }
)


SECRET = st.text(alphabet=st.sampled_from("QZXJ"), min_size=4, max_size=10)


@settings(max_examples=100)
@given(fields_st, SECRET, SECRET, SECRET)
def test_call_script_never_has_tier2(f, name, loc, desc):
    f = f | {"name": name, "location": loc, "description": desc}
    out = "\n".join(b.call_script(f))
    assert name not in out and loc not in out and desc not in out


def test_mode_a_excludes_tier2_values():
    f = empty_fields() | {
        "name": "Zed Qwerty",
        "location": "Kothrud Pune",
        "description": "weird story xyz",
        "amount": "₹100",
    }
    out = b.pack_txt(f, "A").split("COMPLAINT TEXT")[0]
    assert "Zed Qwerty" not in out and "Kothrud" not in out and "xyz" not in out and "₹100" in out
    out_b = b.pack_txt(f, "B").split("COMPLAINT TEXT")[0]
    assert "Zed Qwerty" in out_b and "Kothrud" in out_b


@settings(max_examples=100)
@given(fields_st, st.sampled_from("AB"))
def test_no_none_nan(f, mode):
    out = b.pack_txt(f, mode)
    assert not re.search(r"\bNone\b|\bnan\b|undefined|\bnull\b", out)


def test_pairing_and_missing():
    f = empty_fields() | {"amount": "₹49,999, ₹25,000", "utrs": ["111111111111", "222222222222"]}
    assert "UTR 111111111111: ₹49,999" in "\n".join(b.call_script(f)) and "UTR 222222222222: ₹25,000" in "\n".join(b.call_script(f))
    assert any(m["key"] == "utrs" for m in missing_items(empty_fields()))
    assert "UPI Ref No." in missing_items(empty_fields())[0]["howToFind"]


def test_footer_and_ics():
    assert "Delete this file from shared devices." in b.pack_txt(empty_fields(), "A")
    s = b.ics(30, datetime(2026, 10, 10, tzinfo=UTC))
    assert "BEGIN:VEVENT" in s and "DTSTART:20261010T233000Z" in s and "http" not in s


def test_checklist_and_hi():
    assert [s["id"] for s in b.checklist()][0] == "call1930" and len(b.checklist()) == 7
    assert b.checklist("hi")[0]["title"] == "अभी 1930 पर कॉल करें"


def test_validate_and_elapsed():
    assert validate("utrs", ["123"]) and not validate("utrs", ["524587920123"])
    assert validate("mobile", "12345") and not validate("mobile", "+91 98765 43210")
    assert validate("account", "123456789012")
    assert [elapsed_banner(m)["zone"] for m in (30, 600, 3000)] == ["first2h", "day", "later"]


def test_fields_from():
    f = fields_from(
        {
            "amounts": ["₹1"],
            "utrs": ["1"],
            "banks": ["SBI"],
            "apps": [],
            "accountLast4": ["XX1"],
            "whenHints": ["today"],
            "victimPhones": ["+911"],
            "phones": ["+912"],
            "upiIds": ["a@b"],
            "urls": [],
        }
    )
    assert f["bank"] == "SBI" and f["mobile"] == "+911" and f["scamPhones"] == ["+912"]
