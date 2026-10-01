#!/usr/bin/env python3
"""Compile the breakaway-only subset of Step 1.

Writes verified entries with a non-null ``breakaway``, plus the matching
English council passages, under ``outputs/step1/breakaways/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENTRIES = ROOT / "outputs" / "step1" / "entries.jsonl"
DEFAULT_OUT = ROOT / "outputs" / "step1" / "breakaways"
DOCUMENTS_DIR = ROOT / "data" / "councils" / "documents"

# Stable historical order for summary tables
BREAKAWAY_ORDER = [
    "Arian churches",
    "Church of the East",
    "Oriental Orthodox churches",
    "Eastern Orthodox churches",
    "Wycliffites / Lollards",
    "Hussites",
    "Protestant churches",
    "Old Catholic churches",
]


def load_corpus() -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for path in DOCUMENTS_DIR.rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("language") not in (None, "en"):
                continue
            rid = record.get("record_id")
            if rid:
                by_id[rid] = record
    return by_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=Path, default=DEFAULT_ENTRIES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    entries = [
        json.loads(line)
        for line in args.entries.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    subset = [
        e
        for e in entries
        if e.get("status") == "verified" and e.get("breakaway")
    ]
    subset.sort(
        key=lambda e: (
            BREAKAWAY_ORDER.index(e["breakaway"])
            if e.get("breakaway") in BREAKAWAY_ORDER
            else 999,
            e.get("council") or "",
            e.get("canonical_citation") or "",
            e.get("id") or "",
        )
    )

    corpus = load_corpus()
    passages: list[dict] = []
    missing: list[str] = []
    for entry in subset:
        rid = entry.get("record_id")
        record = corpus.get(rid) if rid else None
        if not record:
            missing.append(rid or entry.get("id") or "?")
            continue
        passages.append(
            {
                "record_id": rid,
                "entry_id": entry.get("id"),
                "council": entry.get("council"),
                "breakaway": entry.get("breakaway"),
                "canonical_citation": record.get("canonical_citation")
                or entry.get("canonical_citation"),
                "text_status": record.get("text_status"),
                "source_url": record.get("source_url"),
                "edition": record.get("edition"),
                "text": record.get("text"),
            }
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    entries_path = args.out_dir / "entries.jsonl"
    passages_path = args.out_dir / "passages.jsonl"
    summary_path = args.out_dir / "summary.json"
    readme_path = args.out_dir / "README.md"

    with entries_path.open("w", encoding="utf-8") as handle:
        for entry in subset:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    with passages_path.open("w", encoding="utf-8") as handle:
        for passage in passages:
            handle.write(json.dumps(passage, ensure_ascii=False) + "\n")

    by_breakaway = Counter(e["breakaway"] for e in subset)
    by_council = Counter(e["council"] for e in subset)
    text_status = Counter(p.get("text_status") or "unknown" for p in passages)
    summary = {
        "description": (
            "Verified Step 1 entries whose decision is linked to a breakaway "
            "group under the project formal definition, with matching council "
            "passage text."
        ),
        "entry_count": len(subset),
        "passage_count": len(passages),
        "missing_record_ids": missing,
        "by_breakaway": [
            {"breakaway": name, "count": by_breakaway[name]}
            for name in BREAKAWAY_ORDER
            if name in by_breakaway
        ]
        + [
            {"breakaway": name, "count": n}
            for name, n in sorted(by_breakaway.items())
            if name not in BREAKAWAY_ORDER
        ],
        "by_council": [
            {"council": c, "count": n} for c, n in by_council.most_common()
        ],
        "passage_text_status": dict(text_status),
        "files": {
            "entries": str(entries_path.relative_to(ROOT)),
            "passages": str(passages_path.relative_to(ROOT)),
            "summary": str(summary_path.relative_to(ROOT)),
        },
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Compact human README
    lines = [
        "# Breakaway subset",
        "",
        "Only the Step 1 decisions tied to a **breakaway group** (formal",
        "definition in the root README). Compiled from verified",
        "`outputs/step1/entries.jsonl` plus matching English council passages.",
        "",
        f"**{len(subset)} entries** · **{len(passages)} passages** · "
        f"text_status={dict(text_status)}",
        "",
        "## Files",
        "",
        "| File | Role |",
        "|------|------|",
        "| `entries.jsonl` | Question + citation + breakaway |",
        "| `passages.jsonl` | Full council passage text for each locus |",
        "| `summary.json` | Counts by group and council |",
        "",
        "## By breakaway group",
        "",
    ]
    for item in summary["by_breakaway"]:
        lines.append(f"- **{item['breakaway']}** — {item['count']}")
    lines.extend(["", "## By council", ""])
    for item in summary["by_council"]:
        lines.append(f"- {item['council']} — {item['count']}")
    lines.extend(
        [
            "",
            "## Regenerate",
            "",
            "```bash",
            "python scripts/step1/compile_breakaways.py",
            "python scripts/step1/export_graph.py "
            "--entries outputs/step1/breakaways/entries.jsonl "
            "--out outputs/step1/breakaways/council_map.mmd",
            "```",
            "",
        ]
    )
    readme_path.write_text("\n".join(lines), encoding="utf-8")

    # Graph for this subset
    sys.path.insert(0, str(ROOT / "scripts" / "step1"))
    from export_graph import main as export_graph_main  # type: ignore

    old_argv = sys.argv
    try:
        sys.argv = [
            "export_graph.py",
            "--entries",
            str(entries_path),
            "--out",
            str(args.out_dir / "council_map.mmd"),
        ]
        export_graph_main()
    finally:
        sys.argv = old_argv

    print(
        f"compiled breakaway subset: {len(subset)} entries, "
        f"{len(passages)} passages -> {args.out_dir}"
    )
    if missing:
        print(f"WARNING missing record_ids: {missing}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
