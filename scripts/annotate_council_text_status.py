#!/usr/bin/env python3
"""Annotate council JSONL records with text_status and write a coverage report.

Preference order for Step 1: full decree text > Tanner/editorial summary > empty.
Summaries are kept when no English full text is available in free Tanner mirrors.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = ROOT / "data" / "councils" / "documents"
OUT_DIR = ROOT / "data" / "councils"
REPORT_PATH = OUT_DIR / "coverage_status.json"

# Known e-text editor interpolations (not conciliar text).
EDITORIAL_RE = re.compile(
    r"(?i)^The famous Haec Sancta decree contradicting Vatican"
)

SUMMARY_RE = re.compile(
    r"(?is)^\s*\[.+\]\s*$"
)


def classify(text: str | None) -> str:
    t = (text or "").strip()
    if not t:
        return "empty"
    if EDITORIAL_RE.match(t):
        return "editorial"
    if SUMMARY_RE.match(t):
        return "summary"
    # Tanner sometimes prefixes a bracket title then continues; treat as full if
    # substantial non-bracket body remains after the first closing bracket.
    if t.startswith("[") and "]" in t:
        after = t.split("]", 1)[1].strip()
        if len(after) >= 120:
            return "full"
        if after and not after.startswith("["):
            # short continuation after summary title — still mostly summary
            if len(t) < 400:
                return "summary"
    return "full"


def annotate_file(path: Path) -> tuple[list[dict], Counter]:
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    kept: list[dict] = []
    counts: Counter = Counter()
    for record in records:
        if record.get("language") not in (None, "en", "la"):
            kept.append(record)
            continue
        status = classify(record.get("text"))
        record["text_status"] = status
        counts[status] += 1
        # Drop pure editorial interpolations; prefer the real decree record.
        if status == "editorial":
            counts["editorial_removed"] += 1
            continue
        kept.append(record)
    return kept, counts


def council_notes() -> dict:
    """Human-audited coverage notes (edition limits, not scrape failures)."""
    return {
        "preference": [
            "full decree/canon/definition text",
            "edition summary (Tanner bracket notes)",
            "empty (never preferred)",
        ],
        "missing_councils": [],
        "missing_documents": [],
        "incomplete": [
            {
                "scope": "Council of Constance",
                "issue": "summary_only_sessions",
                "detail": (
                    "Tanner/COD explicitly does not print many judicial and "
                    "internal-administration acts; those sessions are bracket "
                    "summaries in every free English Tanner mirror checked "
                    "(papalencyclicals.net, Catholic Culture, Documenta Catholica "
                    "Omnia). Full Latin acts exist in Hardt/Finke but are outside "
                    "the current English decree corpus."
                ),
                "sessions_summary_only": [
                    2, 6, 7, 9, 10, 11, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26,
                    27, 29, 30, 31, 32, 33, 34, 35, 36, 38, 41, 42,
                ],
            },
            {
                "scope": "Council of Florence (Basel phase)",
                "issue": "summary_only_sessions",
                "detail": (
                    "A few Basel sessions are Tanner procedural summaries only "
                    "(petition readings, receptions, deferrals). Union bulls and "
                    "major Florence decrees are full text."
                ),
            },
            {
                "scope": "Fifth Lateran Council",
                "issue": "session_1_summary",
                "detail": (
                    "Session 1 records that convoking/postponing bulls were read "
                    "(Mansi refs) but Tanner does not reproduce those bull bodies "
                    "in the decree text; later session constitutions are full."
                ),
            },
            {
                "scope": "Early councils (Nicaea I–Nicaea II)",
                "issue": "canons_definitions_extract",
                "detail": (
                    "English corpus is NPNF / Tanner decree material: creeds, "
                    "definitions, canons, selected letters — not the full day-by-day "
                    "session acta (mostly Greek/Latin in Mansi et al.)."
                ),
            },
            {
                "scope": "Third Council of Constantinople",
                "issue": "decree_only",
                "detail": (
                    "Tanner prints the Exposition of faith; the council issued no "
                    "disciplinary canons. Full session acts are not in this extract."
                ),
            },
        ],
        "full_text_sources_checked": [
            "https://www.papalencyclicals.net/councils/",
            "https://www.catholicculture.org/culture/library/",
            "https://www.documentacatholicaomnia.eu/",
            "https://history.hanover.edu/texts/trent/trentall.html",
            "https://www.newadvent.org/fathers/ (early councils)",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--documents",
        type=Path,
        default=DOCUMENTS_DIR,
    )
    args = parser.parse_args()

    by_council: dict[str, Counter] = defaultdict(Counter)
    by_file: dict[str, Counter] = {}
    summary_examples: dict[str, list[str]] = defaultdict(list)
    total = Counter()

    for path in sorted(args.documents.rglob("*.jsonl")):
        records, counts = annotate_file(path)
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        rel = str(path.relative_to(OUT_DIR))
        by_file[rel] = dict(counts)
        total.update(counts)
        for record in records:
            if record.get("language") not in (None, "en"):
                continue
            council = record.get("council") or rel
            status = record.get("text_status") or classify(record.get("text"))
            by_council[council][status] += 1
            if status == "summary" and len(summary_examples[council]) < 5:
                summary_examples[council].append(record.get("canonical_citation") or "")

    report = {
        "totals": dict(total),
        "by_council": {k: dict(v) for k, v in sorted(by_council.items())},
        "by_file": by_file,
        "summary_examples": dict(summary_examples),
        "notes": council_notes(),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"annotated council JSONL under {args.documents}")
    print(f"totals: {dict(total)}")
    print(f"report -> {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
