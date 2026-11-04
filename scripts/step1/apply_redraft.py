#!/usr/bin/env python3
"""Merge native AI redraft chunk outputs into entries.jsonl and rebuild subsets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / "outputs/step1/entries.jsonl"
CHUNKS = ROOT / "outputs/step1/_redraft_chunks"


def load_redrafts(chunks_dir: Path) -> dict[str, str]:
    merged: dict[str, str] = {}
    for path in sorted(chunks_dir.glob("out_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"{path} is not a JSON object")
        for k, v in data.items():
            q = (v or "").strip()
            if not q:
                continue
            if not q.endswith("?"):
                q += "?"
            q = re.sub(r"\s+", " ", q)
            if len(q) > 400:
                q = q[:397].rstrip() + "…?"
            merged[k] = q
    return merged


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entries", type=Path, default=ENTRIES)
    ap.add_argument("--chunks", type=Path, default=CHUNKS)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    expected = {
        json.loads(l)["id"]
        for l in args.entries.read_text(encoding="utf-8").splitlines()
        if l.strip()
    }
    redrafts = load_redrafts(args.chunks)
    missing = sorted(expected - set(redrafts))
    extra = sorted(set(redrafts) - expected)
    print(
        json.dumps(
            {
                "redrafts": len(redrafts),
                "expected": len(expected),
                "missing": len(missing),
                "extra": len(extra),
                "missing_sample": missing[:20],
                "out_files": [p.name for p in sorted(args.chunks.glob("out_*.json"))],
            },
            indent=2,
        )
    )
    if missing:
        return 1
    if args.dry_run:
        return 0

    rows = [
        json.loads(l)
        for l in args.entries.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    changed = 0
    for e in rows:
        new_q = redrafts[e["id"]]
        if e.get("question") != new_q:
            changed += 1
        e["question"] = new_q
        e["draft_method"] = "native_ai_redraft"

    # Preserve carefully curated contrast questions when present
    contrast_path = ROOT / "outputs/step1/breakaways/contrast/contrast.jsonl"
    if contrast_path.exists():
        for line in contrast_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            # Keep contrast question as authoritative for those ids
            for e in rows:
                if e["id"] == c["id"]:
                    e["question"] = c["question"]
                    break

    with args.entries.open("w", encoding="utf-8") as f:
        for e in rows:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    draft = args.entries.with_name("entries.draft.jsonl")
    draft.write_text(args.entries.read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps({"wrote": str(args.entries), "changed_vs_prior": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
