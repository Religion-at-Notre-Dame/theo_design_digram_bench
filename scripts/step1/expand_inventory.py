#!/usr/bin/env python3
"""Build a comprehensive coverage_inventory.json: one decision per corpus locus.

Default: every English council record in data/councils/ (no per-doc caps).
Preserves breakaway hints from prior inventory / verified entries by citation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_councils import load_corpus, slugify  # noqa: E402

INVENTORY_PATH = Path(__file__).resolve().parent / "coverage_inventory.json"
ENTRIES_PATH = ROOT / "outputs" / "step1" / "entries.jsonl"


def load_breakaway_maps(inventory_path: Path, entries_path: Path):
    by_citation = {}
    if inventory_path.is_file():
        old = json.loads(inventory_path.read_text(encoding="utf-8"))
        for block in old.get("councils", []):
            for d in block.get("required_decisions", []):
                for needle in d.get("citation_contains") or []:
                    by_citation[needle.lower()] = d.get("breakaway_hint")
    if entries_path.is_file():
        for line in entries_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            cit = (e.get("canonical_citation") or "").lower()
            if cit and e.get("breakaway") is not None:
                by_citation[cit] = e.get("breakaway")
    return by_citation


def theme_for(record: dict) -> str:
    title = (record.get("unit_title") or "").strip()
    citation = (record.get("canonical_citation") or "").strip()
    if title and len(title) < 160 and not re.fullmatch(r"(?i)canon\s+\d+", title):
        return title
    theme = citation
    theme = re.sub(
        r"^(Nicaea I|Nicaea II|Chalcedon|Ephesus|Trent|Lateran [IVX]+|"
        r"Lyons [IV]+|Vienne|Constance|Florence|Constantinople [IV]+|"
        r"DF|PA|LG|GS|SC|DV|DH|UR|OE|CD|PC|OT|GE|NA|AA|AG|IM|PO)\s*,?\s*",
        "",
        theme,
    )
    return theme or citation


def decide_breakaway(record: dict, by_citation: dict) -> str | None:
    cit = (record.get("canonical_citation") or "").lower()
    if cit in by_citation:
        return by_citation[cit]
    for needle, hint in by_citation.items():
        if needle and needle in cit and hint:
            return hint
    return None


def expand(*, min_chars: int = 0, comprehensive: bool = True) -> dict:
    corpus = load_corpus()
    by_citation = load_breakaway_maps(INVENTORY_PATH, ENTRIES_PATH)

    council_of_abbrev = {}
    for item in corpus.index_items:
        council_of_abbrev[item["id"]] = item.get("council") or item.get("title")

    by_council: dict[str, list[dict]] = {}
    skipped_short = 0
    for record in corpus.records_by_id.values():
        text_len = len(record.get("text") or "")
        if text_len < min_chars:
            skipped_short += 1
            continue
        abbrev = record.get("document_abbrev")
        if not abbrev:
            continue
        council = record.get("council") or council_of_abbrev.get(abbrev) or abbrev
        by_council.setdefault(council, []).append(record)

    councils_out = []
    total = 0
    seen_ids: set[str] = set()
    for council, records in sorted(by_council.items(), key=lambda x: x[0]):
        records = sorted(
            records,
            key=lambda r: (
                r.get("document_abbrev") or "",
                r.get("session") if isinstance(r.get("session"), int) else 10**9,
                r.get("canon") if isinstance(r.get("canon"), int) else 10**9,
                r.get("paragraph") if isinstance(r.get("paragraph"), int) else 10**9,
                r.get("canonical_citation") or "",
                r.get("record_id") or "",
            ),
        )
        decisions = []
        default_abbrev = records[0].get("document_abbrev") if records else None
        for record in records:
            citation = record.get("canonical_citation") or ""
            abbrev = record.get("document_abbrev")
            record_id = record["record_id"]
            # Stable unique id from record_id (citations alone can collide)
            inv_id = slugify(record_id.replace("mag:", ""))
            if inv_id in seen_ids:
                inv_id = slugify(f"{inv_id}-{total}")
            seen_ids.add(inv_id)
            decision = {
                "id": inv_id,
                "theme": theme_for(record),
                "breakaway_hint": decide_breakaway(record, by_citation),
                "document_abbrev": abbrev,
                "record_id": record_id,
                "keywords": [w for w in re.findall(r"[A-Za-z]{4,}", citation)[:6]],
                "citation_contains": [citation] if citation else [],
            }
            if isinstance(record.get("canon"), int):
                decision["canon"] = record["canon"]
            if isinstance(record.get("session"), int):
                decision["session"] = record["session"]
            decisions.append(decision)

        total += len(decisions)
        councils_out.append(
            {
                "council": council,
                "document_abbrev": default_abbrev,
                "required_decisions": decisions,
            }
        )

    return {
        "version": 3,
        "description": (
            "Comprehensive inventory: one Required decision per English council "
            f"locus in data/councils/ (min_chars={min_chars}, "
            f"comprehensive={comprehensive})."
        ),
        "councils": councils_out,
        "stats": {
            "required_decisions": total,
            "councils": len(councils_out),
            "corpus_english_records": len(corpus.records_by_id),
            "skipped_short": skipped_short,
            "coverage_ratio": (
                round(total / len(corpus.records_by_id), 4)
                if corpus.records_by_id
                else 0
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--min-chars",
        type=int,
        default=0,
        help="Skip loci shorter than this (default 0 = every English record)",
    )
    parser.add_argument("--out", type=Path, default=INVENTORY_PATH)
    parser.add_argument(
        "--backup",
        type=Path,
        default=INVENTORY_PATH.with_suffix(".prev.json"),
    )
    args = parser.parse_args()

    if INVENTORY_PATH.is_file():
        args.backup.write_text(INVENTORY_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"backed up prior inventory -> {args.backup}")

    inventory = expand(min_chars=args.min_chars, comprehensive=True)
    args.out.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    stats = inventory["stats"]
    print(
        f"wrote {stats['required_decisions']} decisions "
        f"(corpus={stats['corpus_english_records']}, "
        f"coverage={stats['coverage_ratio']}) -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
