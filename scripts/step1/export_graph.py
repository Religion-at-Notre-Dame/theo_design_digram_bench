#!/usr/bin/env python3
"""Export a Mermaid graph from verified Step 1 entries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENTRIES = ROOT / "outputs" / "step1" / "entries.jsonl"
DEFAULT_OUT = ROOT / "outputs" / "step1" / "council_map.mmd"


def node_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if cleaned and cleaned[0].isdigit():
        cleaned = "n_" + cleaned
    return cleaned[:60] or "node"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=Path, default=DEFAULT_ENTRIES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--include-null-breakaway", action="store_true")
    args = parser.parse_args()

    entries = []
    for line in args.entries.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("status") != "verified":
            continue
        if not entry.get("breakaway") and not args.include_null_breakaway:
            continue
        entries.append(entry)

    lines = ["flowchart LR"]
    seen_edges = set()
    for entry in entries:
        council = entry.get("council") or "Council"
        summary = entry.get("decision_summary") or entry.get("id")
        breakaway = entry.get("breakaway") or "No_breakaway"
        c = node_id(council)
        d = node_id(entry.get("id") or summary)
        b = node_id(breakaway)
        lines.append(f'  {c}["{council}"]')
        lines.append(f'  {d}["{summary[:80]}"]')
        if entry.get("breakaway"):
            lines.append(f'  {b}["{breakaway}"]')
        edge1 = (c, d)
        if edge1 not in seen_edges:
            lines.append(f"  {c} --> {d}")
            seen_edges.add(edge1)
        if entry.get("breakaway"):
            edge2 = (d, b)
            if edge2 not in seen_edges:
                lines.append(f"  {d} --> {b}")
                seen_edges.add(edge2)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} breakaway-linked nodes -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
