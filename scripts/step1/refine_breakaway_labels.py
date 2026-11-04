#!/usr/bin/env python3
"""Replace umbrella breakaway labels with precise degree-1 groups where history supports it.

- Florence S8 (Armenians) → Armenian Apostolic Church
- Florence S11 (Copts / Jacobites) → Coptic Orthodox Church
- Chalcedon / Constantinople II (shared miaphysite rupture) → Oriental Orthodox churches
- Trent Reform loci tagged Protestant → Lutheran churches (primary Trent interlocutor)

Reformed / Anglican / Anabaptist may also carry distinct Trent locus tags when
promoted into strict contrast; do not overwrite those precise labels.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / "outputs" / "step1" / "entries.jsonl"


def refine(entry: dict) -> str | None:
    old = entry.get("breakaway") or None
    if not old:
        return None
    council = entry.get("council") or ""
    cit = (entry.get("canonical_citation") or "").lower()
    eid = entry.get("id") or ""

    if old == "Oriental Orthodox churches":
        if "(florence) s8" in cit or eid.startswith("flo-florence-s8-"):
            return "Armenian Apostolic Church"
        if "(florence) s11" in cit or eid.startswith("flo-florence-s11-"):
            return "Coptic Orthodox Church"
        if "(florence) s13" in cit or eid.startswith("flo-florence-s13-"):
            return "Syriac Orthodox Church"
        # Chalcedon definition, Constantinople II, etc. — shared family rupture
        return "Oriental Orthodox churches"

    if old == "Protestant churches":
        if council == "Council of Trent" or eid.startswith("trent-"):
            return "Lutheran churches"
        return old

    return old


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entries", type=Path, default=ENTRIES)
    args = ap.parse_args()

    rows = [
        json.loads(l)
        for l in args.entries.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    counts: Counter[str] = Counter()
    for e in rows:
        new = refine(e)
        old = e.get("breakaway")
        if new != old:
            counts[f"{old} → {new}"] += 1
        e["breakaway"] = new

    with args.entries.open("w", encoding="utf-8") as f:
        for e in rows:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    draft = args.entries.with_name("entries.draft.jsonl")
    if draft.exists():
        draft.write_text(args.entries.read_text(encoding="utf-8"), encoding="utf-8")

    remaining = Counter(e.get("breakaway") for e in rows if e.get("breakaway"))
    print(json.dumps({"changes": dict(counts), "remaining": dict(remaining)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
