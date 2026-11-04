#!/usr/bin/env python3
"""Heuristic natural-language rewrite of Step 1 questions (no API key required).

Keeps record_id / citation. Rewrites meta wrappers of the form
“According to X, did the council teach or decree the following: Y?”
into a direct interrogative grounded in the theme or passage opening.

LLM mode remains available via draft_entries.py --mode llm when a key is set.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / "outputs" / "step1" / "entries.jsonl"
DOCUMENTS_DIR = ROOT / "data" / "councils" / "documents"

META = re.compile(
    r"(?is)^According to\s+.+?,\s*did the council teach or decree the following:\s*(.+)$"
)


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


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _opening(text: str, max_chars: int = 220) -> str | None:
    text = _clean(text)
    if len(text) < 28:
        return None
    # Prefer first sentence
    m = re.search(r"^(.{28," + str(max_chars) + r"}?[.!?])(?:\s|$)", text)
    if m:
        return m.group(1).strip()
    cut = text[:max_chars]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;") + "…"


def _ensure_q(s: str) -> str:
    s = _clean(s).rstrip(" .;")
    if not s.endswith("?"):
        s += "?"
    if len(s) > 400:
        s = s[:397].rstrip() + "…?"
    return s


def naturalize(entry: dict, corpus: dict[str, dict]) -> str:
    q = (entry.get("question") or "").strip()
    theme = (entry.get("decision_summary") or "").strip()
    cit = entry.get("canonical_citation") or ""
    text = ""
    rid = entry.get("record_id")
    if rid and rid in corpus:
        text = corpus[rid].get("text") or ""

    body = None
    m = META.match(q)
    if m:
        body = _clean(m.group(1)).rstrip(" ?.")
    elif q.lower().startswith(("did ", "does ", "is ", "are ", "was ", "were ", "can ", "must ", "should ", "has ", "have ")):
        return _ensure_q(q)

    if not body:
        body = theme.rstrip(" .")

    # Thin theme → passage opening
    thin = (
        not body
        or len(body) < 24
        or body.lower() == cit.lower()
        or re.fullmatch(r"(?i)canon\s+\d+", body)
        or re.search(r"(?i)^(canon|constitution|chapter)\s+", body)
        and len(body) < 60
        or re.search(r"(?i)anathemas of", body)
    )
    if thin:
        opening = _opening(text)
        if opening:
            body = opening

    body = body.rstrip(" .;")
    # Anathema / if anyone
    if re.search(r"(?i)^(?:CANON\s+\S+\.?\s*)?If any", text[:120]) or re.search(
        r"(?i)let him be anathema", text[:800]
    ):
        prop_m = re.search(
            r"(?is)if\s+any(?:\s+one|one|man)?\s+"
            r"(?:saith|says|denieth|denies|shall\s+say|does\s+not\s+confess)\s*"
            r"(?:that,?\s*)?(.*?)"
            r"(?:;?\s*let\s+him\s+be\s+anathema)",
            text[:1200],
        )
        if prop_m:
            prop = _clean(prop_m.group(1)).rstrip(" .;")
            if prop.lower().startswith("that "):
                prop = prop[5:]
            if len(prop) > 260:
                prop = prop[:257].rsplit(" ", 1)[0] + "…"
            return _ensure_q(f"Does the council anathematize the claim that {prop}")

    # Creed / definition
    if re.search(r"(?i)\b(creed|definition of faith)\b", cit):
        if body and not body.lower().startswith(("did ", "does ", "is ")):
            return _ensure_q(f"Does the council confess: {body}")

    # Already interrogative theme
    if body.lower().startswith(
        ("did ", "does ", "is ", "are ", "was ", "were ", "can ", "must ", "should ", "has ", "have ", "who ", "what ", "whether ")
    ):
        return _ensure_q(body)

    return _ensure_q(f"Did the council teach that {body[0].lower() + body[1:] if body else 'this'}".replace("that that", "that"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entries", type=Path, default=ENTRIES)
    ap.add_argument(
        "--only-breakaways",
        action="store_true",
        help="Rewrite only entries with a breakaway tag",
    )
    args = ap.parse_args()

    corpus = load_corpus()
    rows = [
        json.loads(l)
        for l in args.entries.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    changed = 0
    for e in rows:
        if args.only_breakaways and not e.get("breakaway"):
            continue
        old = e.get("question") or ""
        new = naturalize(e, corpus)
        if new != old:
            changed += 1
            e["question"] = new
            e["draft_method"] = (e.get("draft_method") or "heuristic") + "+naturalize"

    with args.entries.open("w", encoding="utf-8") as f:
        for e in rows:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(json.dumps({"n": len(rows), "changed": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
