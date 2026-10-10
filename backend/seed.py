"""Upsert data/*.json into Postgres and bump the data version. Run: uv run python seed.py"""

import json

from app import db
from app.detect import DATA

db.open_pool()
db.init_schema()
for r in json.loads((DATA / "rules.json").read_text()):
    db.upsert_rule(r)
for e in json.loads((DATA / "kb.json").read_text()):
    db.upsert_kb(e)
db.bump_version()
print("seeded, version", db.version())
db.close_pool()
