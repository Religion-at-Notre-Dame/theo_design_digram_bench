#!/usr/bin/env python3
"""Verify Step 1 entries against the council corpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_councils import load_corpus, normalize_citation  # noqa: E402

DEFAULT_ENTRIES = ROOT / "outputs" / "step1" / "entries.jsonl"
DEFAULT_REPORT = ROOT / "outputs" / "step1" / "verify_report.json"


def validate_entry(entry: dict, corpus) -> list[str]:
    errors: list[str] = []
    record_id = entry.get("record_id")
    citation = entry.get("canonical_citation") or ""
    question = (entry.get("question") or "").strip()

    if not record_id:
        errors.append("missing_record_id")
    else:
        record = corpus.get(record_id)
        if record is None:
            errors.append("record_id_not_found")
        else:
            expected = normalize_citation(record.get("canonical_citation"))
            got = normalize_citation(citation)
            if not got:
                errors.append("missing_canonical_citation")
            elif got != expected:
                errors.append("citation_mismatch")
            if entry.get("document_abbrev") and entry["document_abbrev"] != record.get(
                "document_abbrev"
            ):
                errors.append("document_abbrev_mismatch")

    if not question:
        errors.append("empty_question")
    elif not question.endswith("?"):
        errors.append("question_not_interrogative")

    breakaway = entry.get("breakaway")
    if breakaway is not None and not isinstance(breakaway, str):
        errors.append("breakaway_not_string_or_null")

    return errors


def load_entries(path: Path) -> list[dict]:
    entries = []
    if not path.is_file():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def write_entries(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=Path, default=DEFAULT_ENTRIES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--write-status",
        action="store_true",
        help="Rewrite entries.jsonl with updated status fields",
    )
    args = parser.parse_args()

    corpus = load_corpus()
    entries = load_entries(args.entries)
    if not entries:
        print(f"No entries at {args.entries}", file=sys.stderr)
        return 1

    verified = failed = 0
    details = []
    for entry in entries:
        errors = validate_entry(entry, corpus)
        if errors:
            entry["status"] = "failed_citation"
            failed += 1
        else:
            entry["status"] = "verified"
            verified += 1
        details.append(
            {
                "id": entry.get("id"),
                "inventory_id": entry.get("inventory_id"),
                "status": entry["status"],
                "errors": errors,
                "record_id": entry.get("record_id"),
                "canonical_citation": entry.get("canonical_citation"),
            }
        )

    report = {
        "total": len(entries),
        "verified": verified,
        "failed": failed,
        "details": details,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.write_status:
        write_entries(args.entries, entries)

    print(f"verified={verified} failed={failed} total={len(entries)}")
    print(f"report -> {args.report}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
