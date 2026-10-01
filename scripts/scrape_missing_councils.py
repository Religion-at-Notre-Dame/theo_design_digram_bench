#!/usr/bin/env python3
"""Scrape the eight councils missing from the Magisteium RAG release.

Source: Papal Encyclicals Online (Tanner, Decrees of the Ecumenical Councils),
the same edition already used for Lyons II and Florence in data/councils/.

Writes JSONL records that match theology_ai_magisterium_v1 and rebuilds
data/councils/index.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "councils"
DOCUMENTS_DIR = OUT_DIR / "documents"

SCHEMA_VERSION = "theology_ai_magisterium_v1"
CORPUS = "Catholic Doctrine and Magisterium"
SOURCE_NAME = "Papal Encyclicals Online"
TRANSLATOR = "Norman P. Tanner"
EDITION = (
    "Decrees of the Ecumenical Councils, ed. Norman P. Tanner (1990), vol. 1; "
    "via Papal Encyclicals Online"
)
DATE_ACQUIRED = date.today().isoformat()

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "theo-design-diagram-bench/0.1 "
            "(+https://github.com/; research corpus builder)"
        )
    }
)

SKIP_HEADING_RE = re.compile(
    r"(?i)^(INTRODUCTION|SECOND INTRODUCTION|BIBLIOGRAPHY|FOOTNOTES|"
    r"NOTES|C\s*A\s*N\s*O\s*N\s*S|C\s*O\n?\s*N\s*S\s*T\s*I\s*T\s*U\s*T\s*I\s*O\s*N\s*S|"
    r"CONSTITUTIONS|CANONS)\s*$"
)
SECTION_START_RE = re.compile(
    r"(?i)^(C\s*A\s*N\s*O\s*N\s*S|C\s*O\s*N\s*S\s*T\s*I\s*T\s*U\s*T\s*I\s*O\s*N\s*S|"
    r"CONSTITUTIONS|CANONS|SESSION\s+\d+|Bull\b)"
)
LEADING_NUM_RE = re.compile(r"^\s*(\d+)\s*[.]?\s*(?:\{\s*\d+\s*\}\s*)?(.*)$", re.S)
BRACKET_NUM_RE = re.compile(r"^\s*\[(\d+[a-z]?)\]\s*[.]?\s*(.*)$", re.S)
STANDALONE_NUM_RE = re.compile(r"^\s*(\d+)\s*$")
SESSION_RE = re.compile(r"(?i)^SESSION\s+(\d+)\b")
TITLE_BRACKET_RE = re.compile(r"^\s*\[(.+)\]\s*$")
FOOTNOTE_MARK_RE = re.compile(r"\{\s*\d+\s*\}")
WHITESPACE_RE = re.compile(r"[ \t]+\n")


COUNCILS = [
    {
        "ecum": "08",
        "filename": "Constantinople_IV.jsonl",
        "abbrev": "CON4",
        "council": "Fourth Council of Constantinople",
        "document_title": "Fourth Council of Constantinople (869–870), Canons",
        "pope": "Hadrian II",
        "date_promulgated": "869-870",
        "document_type": "council_canon",
        "citation_name": "Constantinople IV",
        "parser": "standalone_number",
    },
    {
        "ecum": "09",
        "filename": "Lateran_I.jsonl",
        "abbrev": "LAT1",
        "council": "First Lateran Council",
        "document_title": "First Lateran Council (1123), Canons",
        "pope": "Callistus II",
        "date_promulgated": "1123",
        "document_type": "council_canon",
        "citation_name": "Lateran I",
        "parser": "leading_number",
    },
    {
        "ecum": "10",
        "filename": "Lateran_II.jsonl",
        "abbrev": "LAT2",
        "council": "Second Lateran Council",
        "document_title": "Second Lateran Council (1139), Canons",
        "pope": "Innocent II",
        "date_promulgated": "1139",
        "document_type": "council_canon",
        "citation_name": "Lateran II",
        "parser": "leading_number",
    },
    {
        "ecum": "11",
        "filename": "Lateran_III.jsonl",
        "abbrev": "LAT3",
        "council": "Third Lateran Council",
        "document_title": "Third Lateran Council (1179), Canons",
        "pope": "Alexander III",
        "date_promulgated": "1179",
        "document_type": "council_canon",
        "citation_name": "Lateran III",
        "parser": "leading_number",
    },
    {
        "ecum": "13",
        "filename": "Lyons_I.jsonl",
        "abbrev": "LYO1",
        "council": "First Council of Lyons",
        "document_title": "First Council of Lyons (1245), Constitutions",
        "pope": "Innocent IV",
        "date_promulgated": "1245",
        "document_type": "constitution",
        "citation_name": "Lyons I",
        "parser": "lyons_i",
    },
    {
        "ecum": "15",
        "filename": "Vienne.jsonl",
        "abbrev": "VIE",
        "council": "Council of Vienne",
        "document_title": "Council of Vienne (1311–1312), Decrees",
        "pope": "Clement V",
        "date_promulgated": "1311-1312",
        "document_type": "decree",
        "citation_name": "Vienne",
        "parser": "vienne",
    },
    {
        "ecum": "16",
        "filename": "Constance.jsonl",
        "abbrev": "CON",
        "council": "Council of Constance",
        "document_title": "Council of Constance (1414–1418), Sessions",
        "pope": "Martin V",
        "date_promulgated": "1414-1418",
        "document_type": "council_decree",
        "citation_name": "Constance",
        "parser": "sessions",
    },
    {
        "ecum": "18",
        "filename": "Lateran_V.jsonl",
        "abbrev": "LAT5",
        "council": "Fifth Lateran Council",
        "document_title": "Fifth Lateran Council (1512–1517), Sessions",
        "pope": "Julius II / Leo X",
        "date_promulgated": "1512-1517",
        "document_type": "council_decree",
        "citation_name": "Lateran V",
        "parser": "sessions",
    },
]


def clean_text(text: str) -> str:
    text = FOOTNOTE_MARK_RE.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80] or "unit"


def fetch_html(ecum: str) -> str:
    url = f"https://www.papalencyclicals.net/councils/ecum{ecum}.htm"
    response = SESSION.get(url, timeout=90)
    response.raise_for_status()
    return response.text


def iter_blocks(soup: BeautifulSoup):
    content = soup.find("div", class_="entry-content")
    if content is None:
        raise SystemExit("entry-content not found")
    for el in content.find_all(["h1", "h2", "h3", "h4", "h5", "p"], recursive=True):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        # Skip navigation / footnote lists buried in the tree when they are
        # clearly editorial apparatus rather than conciliar text.
        yield el.name, text


def make_record(
    cfg: dict,
    *,
    record_key: str,
    text: str,
    canonical_citation: str,
    unit_title: str | None = None,
    document_type: str | None = None,
    document_title: str | None = None,
    canon: int | None = None,
    session: int | None = None,
    paragraph: int | None = None,
    decree: str | None = None,
    source_locator: str | None = None,
) -> dict:
    text = clean_text(text)
    abbrev = cfg["abbrev"]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"mag:{abbrev}:{record_key}:en",
        "corpus": CORPUS,
        "source_family": "council",
        "authority_class": "ecumenical_council",
        "document_title": document_title or cfg["document_title"],
        "document_abbrev": abbrev,
        "document_type": document_type or cfg["document_type"],
        "promulgating_authority": cfg["council"],
        "pope": cfg["pope"],
        "council": cfg["council"],
        "dicastery": None,
        "date_promulgated": cfg["date_promulgated"],
        "part": None,
        "section": None,
        "chapter": None,
        "article": None,
        "paragraph": paragraph,
        "session": session,
        "decree": decree,
        "canon": canon,
        "question": None,
        "unit_title": unit_title,
        "canonical_citation": canonical_citation,
        "language": "en",
        "translator": TRANSLATOR,
        "edition": EDITION,
        "parallel_group_id": f"mag:{abbrev}:{record_key}",
        "source_name": SOURCE_NAME,
        "source_url": f"https://www.papalencyclicals.net/councils/ecum{cfg['ecum']}.htm",
        "source_locator": source_locator or canonical_citation,
        "date_acquired": DATE_ACQUIRED,
        "text": text,
        "footnotes": [],
        "source_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def flush_unit(units: list[dict], current: dict | None) -> dict | None:
    if current and current.get("parts"):
        current["text"] = "\n\n".join(current["parts"]).strip()
        if current["text"]:
            units.append(current)
    return None


def parse_leading_number(cfg: dict, blocks) -> list[dict]:
    """Lateran I–III style: 'N. canon text…'."""
    started = False
    units: list[dict] = []
    current = None
    for tag, text in blocks:
        if SKIP_HEADING_RE.match(text.replace(" ", "")) or SKIP_HEADING_RE.match(text):
            # spaced C A N O N S
            compact = re.sub(r"\s+", "", text)
            if re.fullmatch(r"(?i)CANONS|CONSTITUTIONS", compact):
                started = True
                current = flush_unit(units, current)
                continue
            if re.match(r"(?i)^(INTRODUCTION|BIBLIOGRAPHY|FOOTNOTES)", text):
                if started:
                    break
                continue
        if re.match(r"(?i)^Introduction and translation taken from", text):
            break
        if re.match(r"(?i)^FOOTNOTES", text):
            break
        if not started:
            if SECTION_START_RE.match(text) or re.fullmatch(
                r"(?i)C\s*A\s*N\s*O\s*N\s*S", text
            ):
                started = True
            continue
        if tag in {"h1", "h2", "h3", "h4", "h5"}:
            continue
        # editorial variants mixed into Lateran I
        if text.startswith("[") and text.endswith("]") and len(text) < 40:
            continue
        if text.startswith("Msi ") or text.startswith("In Pertz") or text.startswith(
            "The remaining canons"
        ):
            continue
        if text.startswith("If anyone should violate a truce") and current is None:
            # alternate transmission note body — skip unless already in a unit
            continue

        m = LEADING_NUM_RE.match(text)
        if m and m.group(1).isdigit():
            num = int(m.group(1))
            # Only treat as new canon when number is plausible succession
            if current is None or num == (current.get("canon") or 0) + 1 or num > 0:
                current = flush_unit(units, current)
                body = m.group(2).strip()
                current = {
                    "canon": num,
                    "parts": [f"{num}. {body}" if body else f"{num}."],
                }
                continue
        if current is not None:
            # Skip short editorial asides
            if re.match(r"(?i)^(Msi|B\b|Pertz|We believe the)", text):
                continue
            current["parts"].append(text)
    flush_unit(units, current)

    records = []
    for unit in units:
        canon = unit["canon"]
        citation = f"{cfg['citation_name']} canon {canon}"
        records.append(
            make_record(
                cfg,
                record_key=f"canon{canon}",
                text=unit["text"],
                canonical_citation=citation,
                unit_title=f"Canon {canon}",
                canon=canon,
                source_locator=f"Canon {canon}",
            )
        )
    return records


def parse_standalone_number(cfg: dict, blocks) -> list[dict]:
    """Constantinople IV: a paragraph that is only 'N', then body paragraphs."""
    started = False
    units: list[dict] = []
    current = None
    for tag, text in blocks:
        compact = re.sub(r"\s+", "", text)
        if re.fullmatch(r"(?i)CANONS", compact):
            started = True
            current = flush_unit(units, current)
            continue
        if re.match(r"(?i)^(INTRODUCTION|FOOTNOTES|BIBLIOGRAPHY)", text):
            if started:
                break
            continue
        if not started:
            continue
        if STANDALONE_NUM_RE.match(text):
            current = flush_unit(units, current)
            current = {"canon": int(text.strip()), "parts": []}
            continue
        if current is not None and tag == "p":
            current["parts"].append(text)
    flush_unit(units, current)

    records = []
    for unit in units:
        canon = unit["canon"]
        citation = f"{cfg['citation_name']} canon {canon}"
        records.append(
            make_record(
                cfg,
                record_key=f"canon{canon}",
                text=unit["text"],
                canonical_citation=citation,
                unit_title=f"Canon {canon}",
                canon=canon,
                source_locator=f"Canon {canon}",
            )
        )
    return records


def parse_lyons_i(cfg: dict, blocks) -> list[dict]:
    """Bull of deposition + Coll. I / Coll. II constitutions (Tanner numbering)."""
    mode = None  # None | bull | constitutions
    collection = "I"
    units: list[dict] = []
    current = None
    for tag, text in blocks:
        if re.match(r"(?i)^INTRODUCTION", text):
            mode = None
            current = flush_unit(units, current)
            continue
        if re.match(r"(?i)^Bull Deposing", text):
            mode = "bull"
            current = flush_unit(units, current)
            current = {
                "kind": "bull",
                "title": "Bull Deposing The Emperor Frederick II",
                "parts": [],
            }
            continue
        compact = re.sub(r"\s+", "", text)
        if re.fullmatch(r"(?i)CONSTITUTIONS", compact) or re.match(
            r"(?i)^CONSTITUTIONS", text
        ):
            mode = "constitutions"
            collection = "I"
            current = flush_unit(units, current)
            continue
        if re.match(r"(?i)^(FOOTNOTES|ENDNOTES|Introduction and translation)", text):
            break
        if mode == "bull" and tag == "p":
            if current is None:
                current = {
                    "kind": "bull",
                    "title": "Bull Deposing The Emperor Frederick II",
                    "parts": [],
                }
            current["parts"].append(text)
            continue
        if mode != "constitutions":
            continue
        # Collection markers "I" / "II" appear as short paragraphs in Tanner e-text
        if re.fullmatch(r"[IVX]+", text.strip()):
            current = flush_unit(units, current)
            collection = text.strip()
            continue
        if tag != "p":
            continue
        m = LEADING_NUM_RE.match(text)
        if m and m.group(1).isdigit():
            num = int(m.group(1))
            body = m.group(2).strip()
            # Title-only lines look like "1.On rescripts" or "2. {19} Those to whom..."
            title = FOOTNOTE_MARK_RE.sub("", body).strip(" .")
            current = flush_unit(units, current)
            current = {
                "kind": "constitution",
                "collection": collection,
                "canon": num,
                "title": title if len(title) < 120 else title[:120],
                "parts": [],
            }
            # If the heading line already carries substantial body text, keep it
            if len(body) > 160:
                current["parts"].append(f"{num}. {body}")
            continue
        if current is not None:
            current["parts"].append(text)
    flush_unit(units, current)

    records = []
    for unit in units:
        if unit.get("kind") == "bull":
            records.append(
                make_record(
                    cfg,
                    record_key="bull-deposition-frederick-ii",
                    text=unit["text"],
                    canonical_citation="Lyons I, Bull deposing Frederick II",
                    unit_title=unit["title"],
                    document_type="bull",
                    document_title=(
                        "First Council of Lyons (1245), Bull Deposing Frederick II"
                    ),
                    decree="deposition-frederick-ii",
                    source_locator="Bull Deposing The Emperor Frederick II",
                )
            )
            continue
        canon = unit["canon"]
        coll = unit.get("collection") or "I"
        title = unit.get("title") or f"Constitution {canon}"
        # Prefer body text; if only a title was captured, keep the title as text.
        text = unit["text"] if unit["text"] else title
        citation = f"Lyons I Coll. {coll} constitution {canon} ({title})"
        records.append(
            make_record(
                cfg,
                record_key=f"coll{coll.lower()}-constitution{canon}",
                text=text,
                canonical_citation=citation,
                unit_title=title,
                canon=canon,
                decree=f"coll-{coll.lower()}",
                source_locator=f"Coll. {coll} constitution {canon}",
            )
        )
    return records


def parse_vienne(cfg: dict, blocks) -> list[dict]:
    """Vienne decrees often marked [N]. …"""
    started = False
    units: list[dict] = []
    current = None
    for tag, text in blocks:
        if re.match(r"(?i)^(INTRODUCTION|NOTES)", text) and tag.startswith("h"):
            if started:
                break
            continue
        if re.match(r"(?i)^FOOTNOTES", text):
            break
        # Start once we see a bracketed decree number or a clear decree heading
        m = BRACKET_NUM_RE.match(text)
        if m:
            started = True
            current = flush_unit(units, current)
            num = m.group(1)
            body = m.group(2).strip()
            current = {
                "num": num,
                "parts": [f"[{num}]. {body}" if body else f"[{num}]."],
            }
            continue
        if not started:
            # Also accept "DECREES" heading
            if re.search(r"(?i)decree|constitution|we decree", text) and tag == "p":
                # Wait for numbered units; skip pure intro prose
                continue
            continue
        if current is not None and tag == "p":
            if re.match(r"(?i)^(Given at|FOOTNOTES)", text):
                current["parts"].append(text)
                continue
            current["parts"].append(text)
    flush_unit(units, current)

    records = []
    for unit in units:
        num = unit["num"]
        key = f"decree{num}"
        records.append(
            make_record(
                cfg,
                record_key=key,
                text=unit["text"],
                canonical_citation=f"Vienne decree [{num}]",
                unit_title=f"Decree [{num}]",
                decree=f"decree-{num}",
                paragraph=int(re.sub(r"\D", "", num) or 0) or None,
                source_locator=f"[{num}]",
            )
        )
    return records


def parse_sessions(cfg: dict, blocks) -> list[dict]:
    """Constance / Lateran V: SESSION N + optional [title] decrees."""
    session = None
    units: list[dict] = []
    current = None
    pending_date = None
    for tag, text in blocks:
        if re.match(r"(?i)^(INTRODUCTION|SECOND INTRODUCTION|FOOTNOTES)", text):
            if session is not None and re.match(r"(?i)^FOOTNOTES", text):
                break
            continue
        # Skip known e-text editor interpolations (not conciliar text).
        if re.match(r"(?i)^The famous Haec Sancta decree contradicting", text):
            continue
        sm = SESSION_RE.match(text)
        if sm:
            current = flush_unit(units, current)
            session = int(sm.group(1))
            pending_date = None
            continue
        if session is None:
            continue
        if re.fullmatch(r"\d{1,2}\s+\w+\s+\d{4}", text):
            pending_date = text
            continue
        # Whole-paragraph bracket summary (common in Constance e-text)
        tm = TITLE_BRACKET_RE.match(text)
        if tm:
            current = flush_unit(units, current)
            title = tm.group(1).strip()
            current = {
                "session": session,
                "title": title,
                # Keep the editorial summary as text when no decree body follows
                "parts": [text],
                "date": pending_date,
                "summary_only": True,
            }
            pending_date = None
            continue
        if tag == "p":
            if current is not None and current.get("summary_only"):
                # Real decree body after a summary title — replace summary stub
                current["parts"] = [text]
                current["summary_only"] = False
            elif current is None:
                current = {
                    "session": session,
                    "title": None,
                    "parts": [text],
                    "date": pending_date,
                    "summary_only": False,
                }
                pending_date = None
            else:
                current["parts"].append(text)
    flush_unit(units, current)

    records = []
    para_counters: dict[int, int] = {}
    for unit in units:
        sess = unit["session"]
        title = unit.get("title")
        text = unit["text"]
        if not text or len(text) < 20:
            continue
        para_counters[sess] = para_counters.get(sess, 0) + 1
        para = para_counters[sess]
        if title:
            decree = slugify(title)
            citation = f"{cfg['citation_name']} S{sess} [{title}]"
            unit_title = title
            key = f"s{sess}:{decree}"
        else:
            decree = None
            citation = f"{cfg['citation_name']} S{sess} para. {para}"
            unit_title = None
            key = f"s{sess}:p{para}"
        records.append(
            make_record(
                cfg,
                record_key=key,
                text=text,
                canonical_citation=citation,
                unit_title=unit_title,
                session=sess,
                paragraph=para,
                decree=decree,
                source_locator=citation,
            )
        )
    return records


PARSERS = {
    "leading_number": parse_leading_number,
    "standalone_number": parse_standalone_number,
    "lyons_i": parse_lyons_i,
    "vienne": parse_vienne,
    "sessions": parse_sessions,
}


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def rebuild_index() -> dict:
    # Reuse the download script's index builder if present; otherwise local copy.
    sys.path.insert(0, str(ROOT / "scripts"))
    from download_council_documents import build_index, write_readme  # type: ignore

    index = build_index(DOCUMENTS_DIR)
    present = {item["council"] for item in index["items"]}
    still_missing = []
    mapping = {
        "Constantinople IV (869–870)": "Fourth Council of Constantinople",
        "Lateran I (1123)": "First Lateran Council",
        "Lateran II (1139)": "Second Lateran Council",
        "Lateran III (1179)": "Third Lateran Council",
        "Lyons I (1245)": "First Council of Lyons",
        "Vienne (1311–1312)": "Council of Vienne",
        "Constance (1414–1418)": "Council of Constance",
        "Lateran V (1512–1517)": "Fifth Lateran Council",
    }
    for label, council_name in mapping.items():
        if council_name not in present:
            still_missing.append(label)
    index["missingCouncils"] = still_missing
    index["supplementalSource"] = {
        "name": SOURCE_NAME,
        "edition": EDITION,
        "note": (
            "Councils absent from the Magisterium RAG v1.0.0 release were "
            "scraped from Papal Encyclicals Online (Tanner) by "
            "scripts/scrape_missing_councils.py."
        ),
    }
    (OUT_DIR / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_readme(OUT_DIR, index)
    update_document_catalog()
    return index


def update_document_catalog() -> None:
    """Merge scraped councils into document_catalog.json."""
    catalog_path = OUT_DIR / "document_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else []
    by_abbrev = {entry.get("document_abbrev"): entry for entry in catalog}

    for cfg in COUNCILS:
        path = DOCUMENTS_DIR / cfg["filename"]
        if not path.exists():
            continue
        records = [json.loads(line) for line in path.open(encoding="utf-8")]
        en = [r for r in records if r.get("language") == "en"]
        if not en:
            continue
        sample = en[0]
        by_abbrev[cfg["abbrev"]] = {
            "authority_class": "ecumenical_council",
            "chunk_count": len(en),
            "date_promulgated": sample["date_promulgated"],
            "document_abbrev": cfg["abbrev"],
            "document_title": sample["document_title"],
            "document_type": sample["document_type"],
            "languages": ["en"],
            "promulgating_authority": sample["promulgating_authority"],
            "record_count": len(en),
            "source_family": "council",
            "supplemental": True,
            "source_url": sample["source_url"],
        }

    merged = sorted(by_abbrev.values(), key=lambda e: e.get("document_abbrev") or "")
    catalog_path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def scrape_one(cfg: dict) -> list[dict]:
    html = fetch_html(cfg["ecum"])
    soup = BeautifulSoup(html, "lxml")
    blocks = list(iter_blocks(soup))
    parser = PARSERS[cfg["parser"]]
    records = parser(cfg, blocks)
    if not records:
        raise SystemExit(f"No records parsed for {cfg['abbrev']} (ecum{cfg['ecum']})")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="*",
        help="Optional abbrev filter, e.g. LAT1 CON4",
    )
    args = parser.parse_args()
    only = {a.upper() for a in args.only} if args.only else None

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for cfg in COUNCILS:
        if only and cfg["abbrev"] not in only:
            continue
        print(f"Scraping {cfg['abbrev']} (ecum{cfg['ecum']})…")
        records = scrape_one(cfg)
        path = DOCUMENTS_DIR / cfg["filename"]
        write_jsonl(path, records)
        summary.append((cfg["abbrev"], len(records), path))
        print(f"  wrote {len(records)} records -> {path.relative_to(ROOT)}")

    index = rebuild_index()
    print(f"index.json now has {index['count']} documents; missing={index['missingCouncils']}")
    for abbrev, count, path in summary:
        print(f"  {abbrev}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
