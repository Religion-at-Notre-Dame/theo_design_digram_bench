#!/usr/bin/env python3
"""Clean breakaway fields in Step 1 entries under the project definition.

See README.md § “Breakaway group (formal definition)”.

Strategy: start from existing tags; clear labels that fail the definition;
normalize names for labels that pass. Do not invent new tags via substring
matching (that over-applied Trent/Vatican I/Lateran IV).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / "outputs" / "step1" / "entries.jsonl"

# Fail the definition → always null
CLEAR_LABELS = {
    "Cathars / Albigensians",  # suppressed; no lasting separate communion
    "Iconoclasts",  # condemned party, not a lasting separate church
    "Monothelites",  # same
    "Society of St. Pius X / traditionalist rejection",  # contested; claims Catholic communion
    "Society of St. Pius X / sedeprivationist critics (contested reception)",
}

# Pass the definition → keep under a normalized name
RENAME = {
    "Arians / Homoeans": "Arian churches",
    "Church of the East / Nestorians": "Church of the East",
    "Oriental Orthodox / non-union churches": "Oriental Orthodox churches",
    "Oriental Orthodox churches": "Oriental Orthodox churches",
    "Armenian Apostolic Church": "Armenian Apostolic Church",
    "Coptic Orthodox Church": "Coptic Orthodox Church",
    "Syriac Orthodox Church": "Syriac Orthodox Church",
    "Eastern Orthodox (rejection of union)": "Eastern Orthodox churches",
    "Eastern Orthodox": "Eastern Orthodox churches",
    "Eastern Orthodox churches": "Eastern Orthodox churches",
    "Wycliffites / Lollards": "Wycliffites / Lollards",
    "Hussites": "Hussites",
    "Protestant Reformers": "Protestant churches",
    "Protestant churches": "Protestant churches",
    "Lutheran churches": "Lutheran churches",
    "Reformed / Calvinist churches": "Reformed / Calvinist churches",
    "Anabaptist / Radical Reformation churches": "Anabaptist / Radical Reformation churches",
    "Anglican Communion / Church of England": "Anglican Communion / Church of England",
    "Old Catholics": "Old Catholic churches",
    "Old Catholic churches": "Old Catholic churches",
    "Arian churches": "Arian churches",
    "Church of the East": "Church of the East",
}


def resolve(old: str | None) -> str | None:
    if not old:
        return None
    if old in CLEAR_LABELS:
        return None
    if old in RENAME:
        return RENAME[old]
    # Unknown label: clear rather than invent
    return None


def assign_from_citation(council: str, citation: str, entry_id: str = "") -> str | None:
    """Re-attach breakaways after corpus citation renames (precise loci only)."""
    cit = (citation or "").lower()
    eid = entry_id or ""
    if council == "Council of Florence":
        # Union decrees / refused communion after Florence sessions.
        if "(florence) s6" in cit or eid.startswith("flo-florence-s6-"):
            return "Eastern Orthodox churches"
        if "(florence) s8" in cit or eid.startswith("flo-florence-s8-"):
            return "Armenian Apostolic Church"
        if "(florence) s11" in cit or eid.startswith("flo-florence-s11-"):
            return "Coptic Orthodox Church"
    if council == "Council of Chalcedon" and "definition" in cit:
        return "Oriental Orthodox churches"
    if council == "Second Council of Constantinople":
        return "Oriental Orthodox churches"
    if council == "Council of Trent":
        return "Lutheran churches"
    if council == "Second Council of Lyons" and "palaeologus" in cit:
        return "Eastern Orthodox churches"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=Path, default=ENTRIES)
    args = parser.parse_args()

    entries = [
        json.loads(line)
        for line in args.entries.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    cleared = renamed = kept = assigned = 0
    for entry in entries:
        old = entry.get("breakaway") or None
        if old == "":
            old = None
        new = resolve(old)
        if new is None:
            assigned_name = assign_from_citation(
                entry.get("council") or "",
                entry.get("canonical_citation") or "",
                entry.get("id") or "",
            )
            if assigned_name:
                new = assigned_name
                assigned += 1
        if old and not new:
            cleared += 1
        elif new and old and new != old:
            renamed += 1
        elif new and old == new:
            kept += 1
        entry["breakaway"] = new

    with args.entries.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    draft = args.entries.with_name("entries.draft.jsonl")
    if draft.exists():
        draft.write_text(args.entries.read_text(encoding="utf-8"), encoding="utf-8")

    remaining = sum(1 for e in entries if e.get("breakaway"))
    print(
        f"cleaned {args.entries}: "
        f"breakaways_remaining={remaining} cleared={cleared} "
        f"renamed={renamed} kept={kept} assigned={assigned}"
    )
    for name, n in Counter(e["breakaway"] for e in entries if e.get("breakaway")).most_common():
        print(f"  {n:3d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
