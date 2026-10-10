"""Postgres access: a pool and a handful of plain SQL functions. No ORM. No user content is ever stored."""

import json
import os
from datetime import date
from pathlib import Path

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

SCHEMA = Path(__file__).resolve().parent.parent / "schema.sql"
_pool: ConnectionPool | None = None


def url() -> str:
    return os.environ.get("DATABASE_URL", "postgresql://gh@/goldenhour?host=/tmp&port=5433")


def open_pool() -> None:
    global _pool
    _pool = ConnectionPool(
        url(),
        min_size=1,
        max_size=int(os.environ.get("DB_POOL_MAX", "5")),
        kwargs={"row_factory": dict_row},
        open=True,
    )


def close_pool() -> None:
    if _pool:
        _pool.close()


def _q(sql: str, args=(), fetch="all"):
    with _pool.connection() as c:  # type: ignore[union-attr]
        cur = c.execute(sql, args)
        return cur.fetchall() if fetch == "all" else cur.fetchone() if fetch == "one" else None


def ping() -> bool:
    try:
        return _q("select 1 as ok", fetch="one")["ok"] == 1
    except Exception:
        return False


def init_schema() -> None:
    _q(SCHEMA.read_text(), fetch=None)


def version() -> str:
    return _q("select value from meta where key='version'", fetch="one")["value"]


def bump_version() -> None:
    _q("update meta set value=(value::int+1)::text where key='version'", fetch=None)


def upsert_rule(r: dict) -> None:
    _q(
        """insert into rules (id,weight,category,critical,pattern,flags,unless_before,label,why,examples,counter_examples)
          values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
          on conflict (id) do update set weight=excluded.weight, category=excluded.category, critical=excluded.critical,
          pattern=excluded.pattern, flags=excluded.flags, unless_before=excluded.unless_before, label=excluded.label,
          why=excluded.why, examples=excluded.examples, counter_examples=excluded.counter_examples""",
        (
            r["id"],
            r["weight"],
            r["category"],
            r["critical"],
            r["pattern"],
            r.get("flags", "i"),
            r.get("unlessBefore"),
            json.dumps(r["label"]),
            json.dumps(r["why"]),
            json.dumps(r["examples"]),
            json.dumps(r["counterExamples"]),
        ),
        fetch=None,
    )


def upsert_kb(e: dict) -> None:
    _q(
        """insert into kb_entries (id,q,a,keywords,sources,verified_on,review_by) values (%s,%s,%s,%s,%s,%s,%s)
          on conflict (id) do update set q=excluded.q, a=excluded.a, keywords=excluded.keywords, sources=excluded.sources,
          verified_on=excluded.verified_on, review_by=excluded.review_by""",
        (
            e["id"],
            json.dumps(e["q"]),
            json.dumps(e["a"]),
            e["keywords"],
            json.dumps(e["sources"]),
            e["verifiedOn"],
            e["reviewBy"],
        ),
        fetch=None,
    )


def load_rules() -> list[dict]:
    return [
        {
            "id": r["id"],
            "weight": r["weight"],
            "category": r["category"],
            "critical": r["critical"],
            "pattern": r["pattern"],
            "unlessBefore": r["unless_before"],
            "label": r["label"],
            "why": r["why"],
            "examples": r["examples"],
            "counterExamples": r["counter_examples"],
        }
        for r in _q("select * from rules where enabled order by ctid")
    ]


def load_kb() -> list[dict]:
    return [
        {
            "id": r["id"],
            "q": r["q"],
            "a": r["a"],
            "keywords": r["keywords"],
            "sources": r["sources"],
            "verifiedOn": r["verified_on"].isoformat(),
            "reviewBy": r["review_by"].isoformat(),
        }
        for r in _q("select * from kb_entries order by id")
    ]


def spend_tokens(n: int, cap: int) -> bool:
    """Atomically add n tokens to today's counter; False if that would exceed the cap."""
    row = _q(
        """insert into ai_usage (day, tokens) values (%s, %s)
                on conflict (day) do update set tokens = ai_usage.tokens + excluded.tokens
                where ai_usage.tokens + excluded.tokens <= %s returning tokens""",
        (date.today(), n, cap),
        fetch="one",
    )
    return row is not None


def add_error_report(page: str, note: str) -> None:
    _q("insert into error_reports (page, note) values (%s, %s)", (page[:100], note), fetch=None)
