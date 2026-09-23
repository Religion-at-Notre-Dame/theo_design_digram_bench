#!/usr/bin/env python3
"""Draft Step 1 entries from the coverage inventory + council corpus.

Uses an OpenAI-compatible chat API when OPENAI_API_KEY (or STEP1_API_KEY) is set.
Otherwise falls back to --heuristic mode (or auto-fallback) that still grounds
every citation in a real corpus record.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_councils import load_corpus, slugify  # noqa: E402

INVENTORY_PATH = Path(__file__).resolve().parent / "coverage_inventory.json"
DEFAULT_OUT = ROOT / "outputs" / "step1" / "entries.jsonl"
DEFAULT_STAGING = ROOT / "outputs" / "step1" / "entries.draft.jsonl"


def load_inventory(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_decisions(inventory: dict, only_council: str | None, only_id: str | None):
    for block in inventory["councils"]:
        council = block["council"]
        default_abbrev = block.get("document_abbrev")
        if only_council and only_council.lower() not in council.lower():
            continue
        for decision in block["required_decisions"]:
            if only_id and decision["id"] != only_id:
                continue
            item = dict(decision)
            item["council"] = council
            item.setdefault("document_abbrev", default_abbrev)
            yield item


def pick_record(corpus, decision: dict):
    # Prefer exact record_id when inventory is comprehensive
    rid = decision.get("record_id")
    if rid:
        record = corpus.get(rid)
        if record is not None:
            return [record]
    abbrev = decision.get("document_abbrev")
    return corpus.candidates_for(
        document_abbrev=abbrev,
        keywords=decision.get("keywords") or [decision.get("theme", "")],
        citation_contains=decision.get("citation_contains") or None,
        canon=decision.get("canon"),
        session=decision.get("session"),
        prefer_full_text=False,
        limit=5,
    )


def _opening_from_text(text: str, max_len: int = 180) -> str | None:
    """Return a usable opening snippet from locus text, or None."""
    body = (text or "").strip()
    if not body:
        return None
    body = re.sub(r"^\s*\d+\s*[.)]\s*", "", body)
    body = re.sub(r"^\s*\[[^\]]+\]\s*[.]?\s*", "", body)
    # Prefer a char window over naive sentence splits (avoids "Rom." / "St." cuts)
    if len(body) <= max_len:
        snippet = body
    else:
        cut = body[:max_len]
        # Prefer breaking at sentence end when it's not a short abbreviation
        sentence_break = None
        for m in re.finditer(r"[.!?](?=\s|$)", cut):
            prev = cut[max(0, m.start() - 4) : m.start()]
            # Skip likely abbreviations: Rom. St. Mt. cf. etc.
            if re.search(r"(?i)\b(rom|st|mt|mr|lk|jn|cf|vs|vol|pp|no|ss)$", prev):
                continue
            if m.start() > 40:
                sentence_break = m.end()
        if sentence_break:
            snippet = cut[:sentence_break].strip()
        else:
            snippet = cut.rsplit(" ", 1)[0]
    snippet = snippet.rstrip(" ,;")
    return snippet if len(snippet) > 28 else None


def _theme_is_thin(theme: str, citation: str) -> bool:
    t = (theme or "").strip()
    c = (citation or "").strip()
    if not t:
        return True
    if c and t.lower() == c.lower():
        return True
    if c and t.lower() in c.lower() and len(t) <= len(c):
        # Theme is just a truncation/echo of the citation label
        return True
    if re.fullmatch(r"(?i)canon\s+\d+", t):
        return True
    if re.fullmatch(r"(?i)constitution\s+\d+", t):
        return True
    if re.search(r"(?i)\b(canon|constitution)\s+\d+\s*$", t) and len(t) < 80:
        # e.g. "Fourth Lateran Council, constitution 41"
        return True
    if len(t) < 20:
        return True
    return False


def heuristic_draft(decision: dict, record: dict) -> dict:
    theme = (decision.get("theme") or "").rstrip(".")
    citation = record["canonical_citation"]
    text = (record.get("text") or "").strip()

    if _theme_is_thin(theme, citation):
        opening = _opening_from_text(text)
        if opening:
            theme = opening

    if theme.lower().startswith(("did ", "does ", "is ", "are ", "was ", "were ", "can ")):
        question = theme if theme.endswith("?") else theme + "?"
    else:
        question = (
            f"According to {citation}, did the council teach or decree the following: {theme}?"
        )
    if len(question) > 400:
        question = question[:397].rstrip() + "…?"

    breakaway = decision.get("breakaway_hint")
    return {
        "id": slugify(decision["id"]),
        "inventory_id": decision["id"],
        "council": decision["council"],
        "document_abbrev": record.get("document_abbrev"),
        "record_id": record["record_id"],
        "canonical_citation": citation,
        "question": question,
        "breakaway": breakaway,
        "decision_summary": theme[:200],
        "source_file": record.get("_source_file"),
        "status": "draft",
        "draft_method": "heuristic",
    }


def llm_draft(decision: dict, candidates: list[dict], *, model: str, base_url: str, api_key: str) -> dict:
    compact = []
    for record in candidates:
        compact.append(
            {
                "record_id": record["record_id"],
                "document_abbrev": record.get("document_abbrev"),
                "canonical_citation": record.get("canonical_citation"),
                "unit_title": record.get("unit_title"),
                "canon": record.get("canon"),
                "session": record.get("session"),
                "paragraph": record.get("paragraph"),
                "text": (record.get("text") or "")[:2500],
            }
        )
    system = (
        "You draft Step 1 mapping entries for Catholic ecumenical councils. "
        "Use ONLY the provided passage candidates. Copy record_id and "
        "canonical_citation exactly from one candidate. Write one interrogative "
        "sentence as question. Set breakaway to a historical group name or null; "
        "do not invent a schism. Respond with JSON only."
    )
    user = {
        "inventory_id": decision["id"],
        "council": decision["council"],
        "theme": decision["theme"],
        "breakaway_hint": decision.get("breakaway_hint"),
        "candidates": compact,
        "output_schema": {
            "record_id": "string from candidates",
            "canonical_citation": "exact string from chosen candidate",
            "question": "one sentence ending with ?",
            "breakaway": "string or null",
            "decision_summary": "short label",
        },
    }
    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    data = json.loads(content)

    record_id = data.get("record_id")
    record = next((c for c in candidates if c["record_id"] == record_id), None)
    if record is None:
        raise ValueError(f"LLM chose unknown record_id: {record_id}")

    citation = data.get("canonical_citation") or record["canonical_citation"]
    if citation != record["canonical_citation"]:
        # Force exact corpus citation
        citation = record["canonical_citation"]

    question = (data.get("question") or "").strip()
    if question and not question.endswith("?"):
        question += "?"

    breakaway = data.get("breakaway")
    if breakaway in ("", "null", "None"):
        breakaway = None

    return {
        "id": slugify(decision["id"]),
        "inventory_id": decision["id"],
        "council": decision["council"],
        "document_abbrev": record.get("document_abbrev"),
        "record_id": record["record_id"],
        "canonical_citation": citation,
        "question": question,
        "breakaway": breakaway,
        "decision_summary": data.get("decision_summary") or decision["theme"],
        "source_file": record.get("_source_file"),
        "status": "draft",
        "draft_method": "llm",
    }


def write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--staging", type=Path, default=DEFAULT_STAGING)
    parser.add_argument("--council", type=str, default=None)
    parser.add_argument("--inventory-id", type=str, default=None)
    parser.add_argument(
        "--mode",
        choices=("auto", "llm", "heuristic"),
        default="auto",
        help="auto uses LLM if API key present, else heuristic",
    )
    parser.add_argument("--model", default=os.environ.get("STEP1_MODEL", "gpt-4o-mini"))
    parser.add_argument(
        "--base-url",
        default=os.environ.get("STEP1_BASE_URL", "https://api.openai.com/v1"),
    )
    args = parser.parse_args()

    api_key = os.environ.get("STEP1_API_KEY") or os.environ.get("OPENAI_API_KEY")
    mode = args.mode
    if mode == "auto":
        mode = "llm" if api_key else "heuristic"
    if mode == "llm" and not api_key:
        print("LLM mode requires OPENAI_API_KEY or STEP1_API_KEY", file=sys.stderr)
        return 1

    inventory = load_inventory(args.inventory)
    corpus = load_corpus()
    entries: list[dict] = []
    skipped = []

    for decision in iter_decisions(inventory, args.council, args.inventory_id):
        candidates = pick_record(corpus, decision)
        if not candidates:
            skipped.append(decision["id"])
            continue
        try:
            if mode == "llm":
                entry = llm_draft(
                    decision,
                    candidates,
                    model=args.model,
                    base_url=args.base_url,
                    api_key=api_key,
                )
            else:
                entry = heuristic_draft(decision, candidates[0])
            entries.append(entry)
            print(f"drafted {entry['inventory_id']} -> {entry['canonical_citation'][:70]}")
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"FAIL {decision['id']}: {exc}", file=sys.stderr)
            # Fall back to heuristic for this item
            entry = heuristic_draft(decision, candidates[0])
            entry["draft_method"] = "heuristic_fallback"
            entries.append(entry)

    write_jsonl(args.staging, entries)
    if args.inventory_id or args.council:
        # Merge into existing entries file by inventory_id
        existing = {}
        if args.out.is_file():
            for line in args.out.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    prev = json.loads(line)
                    key = prev.get("inventory_id") or prev.get("id")
                    existing[key] = prev
        for entry in entries:
            existing[entry["inventory_id"]] = entry
        merged = list(existing.values())
        write_jsonl(args.out, merged)
        print(f"merged {len(entries)} drafts into {len(merged)} entries -> {args.out}")
    else:
        write_jsonl(args.out, entries)
        print(f"wrote {len(entries)} entries -> {args.out}")
    if skipped:
        print(f"skipped (no candidates): {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
