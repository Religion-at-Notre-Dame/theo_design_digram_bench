#!/usr/bin/env python3
"""Compare coverage inventory / entries against the full council corpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_councils import load_corpus  # noqa: E402

INVENTORY_PATH = Path(__file__).resolve().parent / "coverage_inventory.json"
DEFAULT_ENTRIES = ROOT / "outputs" / "step1" / "entries.jsonl"
DEFAULT_REPORT = ROOT / "outputs" / "step1" / "coverage_report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--entries", type=Path, default=DEFAULT_ENTRIES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    corpus = load_corpus()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    entries = []
    if args.entries.is_file():
        for line in args.entries.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(json.loads(line))

    by_inv = {e.get("inventory_id"): e for e in entries if e.get("inventory_id")}
    by_record = {e.get("record_id"): e for e in entries if e.get("record_id")}

    councils = []
    total_required = 0
    total_filled = 0
    total_verified = 0

    for block in inventory["councils"]:
        missing = []
        filled = []
        for decision in block["required_decisions"]:
            total_required += 1
            entry = by_inv.get(decision["id"])
            if entry is None and decision.get("record_id"):
                entry = by_record.get(decision["record_id"])
            if entry is None:
                missing.append(decision["id"])
            else:
                filled.append(decision["id"])
                total_filled += 1
                if entry.get("status") == "verified":
                    total_verified += 1
        councils.append(
            {
                "council": block["council"],
                "required": len(block["required_decisions"]),
                "filled": len(filled),
                "missing_count": len(missing),
                "missing": missing[:20],
            }
        )

    corpus_ids = set(corpus.records_by_id)
    entry_ids = {e.get("record_id") for e in entries if e.get("record_id")}
    missing_from_entries = sorted(corpus_ids - entry_ids)
    extra_in_entries = sorted(entry_ids - corpus_ids)

    report = {
        "total_required": total_required,
        "total_filled": total_filled,
        "total_verified": total_verified,
        "complete": total_filled == total_required and total_verified == total_required,
        "corpus_english_records": len(corpus_ids),
        "entries_with_record_id": len(entry_ids),
        "corpus_loci_missing_from_entries": len(missing_from_entries),
        "corpus_complete": len(missing_from_entries) == 0,
        "missing_record_ids_sample": missing_from_entries[:30],
        "extra_record_ids": len(extra_in_entries),
        "councils": councils,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"inventory: required={total_required} filled={total_filled} verified={total_verified} "
        f"complete={report['complete']}"
    )
    print(
        f"corpus: records={len(corpus_ids)} in_entries={len(entry_ids)} "
        f"missing={len(missing_from_entries)} corpus_complete={report['corpus_complete']}"
    )
    print(f"report -> {args.report}")
    return 0 if report["complete"] and report["corpus_complete"] else 2


if __name__ == "__main__":
    sys.exit(main())
