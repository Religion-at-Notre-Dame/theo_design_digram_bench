"""Load and index council JSONL records for Step 1."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COUNCILS_DIR = ROOT / "data" / "councils"
DOCUMENTS_DIR = COUNCILS_DIR / "documents"
INDEX_PATH = COUNCILS_DIR / "index.json"

SHORT_TEXT_THRESHOLD = 300


def normalize_citation(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", value)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


@dataclass
class CouncilCorpus:
    records_by_id: dict[str, dict] = field(default_factory=dict)
    records_by_citation: dict[str, list[dict]] = field(default_factory=dict)
    records_by_abbrev: dict[str, list[dict]] = field(default_factory=dict)
    index_items: list[dict] = field(default_factory=list)
    source_files: dict[str, str] = field(default_factory=dict)

    def get(self, record_id: str) -> dict | None:
        return self.records_by_id.get(record_id)

    def resolve_citation(self, citation: str) -> dict | None:
        matches = self.records_by_citation.get(normalize_citation(citation), [])
        return matches[0] if matches else None

    def candidates_for(
        self,
        *,
        document_abbrev: str | None = None,
        keywords: list[str] | None = None,
        citation_contains: list[str] | None = None,
        canon: int | None = None,
        session: int | None = None,
        prefer_full_text: bool = True,
        limit: int = 8,
    ) -> list[dict]:
        if document_abbrev:
            pool = list(self.records_by_abbrev.get(document_abbrev, []))
        else:
            pool = list(self.records_by_id.values())

        if canon is not None:
            pool = [r for r in pool if r.get("canon") == canon]
        if session is not None:
            pool = [r for r in pool if r.get("session") == session]

        if citation_contains:
            needles = [n.lower() for n in citation_contains]

            def cit_ok(record: dict) -> bool:
                cit = (record.get("canonical_citation") or "").lower()
                for needle in needles:
                    idx = cit.find(needle)
                    if idx < 0:
                        return False
                    end = idx + len(needle)
                    # Avoid "anathema 1" matching "anathema 10"
                    if end < len(cit) and cit[end].isdigit():
                        return False
                return True

            narrowed = [r for r in pool if cit_ok(r)]
            if narrowed:
                pool = narrowed

        if keywords:
            lowered = [k.lower() for k in keywords]

            def score(record: dict) -> int:
                blob = " ".join(
                    [
                        str(record.get("canonical_citation") or ""),
                        str(record.get("unit_title") or ""),
                        str(record.get("decree") or ""),
                        str(record.get("document_title") or ""),
                        (record.get("text") or "")[:2000],
                    ]
                ).lower()
                return sum(1 for k in lowered if k in blob)

            scored_pairs = [(score(r), r) for r in pool]
            matched = [r for s, r in scored_pairs if s > 0]
            scored = [r for s, r in sorted(scored_pairs, key=lambda x: -x[0])]
            # Prefer matched; only fall back if nothing matched and we have filters
            pool = matched if matched else (
                scored
                if (canon is not None or session is not None or citation_contains)
                else []
            )
            score_by_obj = {id(r): s for s, r in scored_pairs}
            pool = sorted(
                pool,
                key=lambda r: (
                    -score_by_obj.get(id(r), 0),
                    r.get("canon") if isinstance(r.get("canon"), int) else 10**9,
                    r.get("paragraph") if isinstance(r.get("paragraph"), int) else 10**9,
                    r.get("canonical_citation") or "",
                ),
            )

        if prefer_full_text and pool:
            full = [r for r in pool if not r.get("_short_text")]
            if full:
                pool = full

        pool = [r for r in pool if r.get("language", "en") == "en"]
        if not keywords:
            pool = sorted(
                pool,
                key=lambda r: (
                    r.get("canon") if isinstance(r.get("canon"), int) else 10**9,
                    r.get("paragraph") if isinstance(r.get("paragraph"), int) else 10**9,
                    r.get("canonical_citation") or "",
                ),
            )
        return pool[:limit]


def load_corpus(councils_dir: Path | None = None) -> CouncilCorpus:
    base = councils_dir or COUNCILS_DIR
    index_path = base / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    corpus = CouncilCorpus(index_items=index.get("items", []))

    for item in corpus.index_items:
        rel = item.get("file")
        if not rel:
            continue
        path = base / rel
        if not path.is_file():
            continue
        abbrev = item.get("id")
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("language") not in (None, "en"):
                continue
            record_id = record.get("record_id")
            if not record_id:
                continue
            if record_id in corpus.records_by_id:
                # Prefer the first English copy; skip exact duplicates in abbrev lists
                continue
            text = record.get("text") or ""
            record["_short_text"] = len(text) < SHORT_TEXT_THRESHOLD
            record["_source_file"] = str(path.relative_to(ROOT)).replace("\\", "/")
            if abbrev and not record.get("document_abbrev"):
                record["document_abbrev"] = abbrev
            corpus.records_by_id[record_id] = record
            citation = normalize_citation(record.get("canonical_citation"))
            if citation:
                corpus.records_by_citation.setdefault(citation, []).append(record)
            doc_abbrev = record.get("document_abbrev") or abbrev
            if doc_abbrev:
                corpus.records_by_abbrev.setdefault(doc_abbrev, []).append(record)
            corpus.source_files[record_id] = record["_source_file"]
    return corpus


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80] or "entry"
