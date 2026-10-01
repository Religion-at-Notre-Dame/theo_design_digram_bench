#!/usr/bin/env python3
"""Fill incomplete council documents already present in data/councils/.

The eight councils absent from the upstream RAG release are already scraped by
``scripts/scrape_missing_councils.py``. This script completes the remaining gaps:

1. Florence — replace the three-decree extract with the full Tanner text of
   Basel–Ferrara–Florence from Papal Encyclicals Online (ecum17).
2. Trent — add Waterworth/Hanover sessions missing from the RAG extract
   (sessions 1–2, 8–12, 15–20), without rewriting sessions already present.
3. Constantinople III — replace the thin NPNF pair with Tanner's Exposition of
   Faith (ecum06), split into citable paragraphs.

Constance summary stubs are inherent to the Tanner e-text and are left as-is.
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

SESSION_HEAD_RE = re.compile(
    r"(?i)^SESSION\s+(\d+)(?:\s+(\d+))?(?:\s*[′'])?\s*(.*)$"
)
DATE_RE = re.compile(
    r"(?i)(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{4})"
)
TITLE_BRACKET_RE = re.compile(r"^\s*\[(.+)\]\s*$")
FOOTNOTE_MARK_RE = re.compile(r"\{\s*\d+\s*\}")
TRENT_SESSION_RE = re.compile(
    r"(?is)SESSION THE ("
    r"FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|"
    r"ELEVENTH|TWELFTH|THIRTEENTH|FOURTEENTH|FIFTEENTH|SIXTEENTH|"
    r"SEVENTEENTH|EIGHTEENTH|NINETEENTH|TWENTIETH|"
    r"TWENTY-FIRST|TWENTY-SECOND|TWENTY-THIRD|TWENTY-FOURTH|TWENTY-FIFTH"
    r")\b(.*?)(?=SESSION THE (?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|"
    r"SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH|THIRTEENTH|FOURTEENTH|"
    r"FIFTEENTH|SIXTEENTH|SEVENTEENTH|EIGHTEENTH|NINETEENTH|TWENTIETH|"
    r"TWENTY-FIRST|TWENTY-SECOND|TWENTY-THIRD|TWENTY-FOURTH|TWENTY-FIFTH)\b|\Z)"
)
TRENT_ORDINAL = {
    "FIRST": 1,
    "SECOND": 2,
    "THIRD": 3,
    "FOURTH": 4,
    "FIFTH": 5,
    "SIXTH": 6,
    "SEVENTH": 7,
    "EIGHTH": 8,
    "NINTH": 9,
    "TENTH": 10,
    "ELEVENTH": 11,
    "TWELFTH": 12,
    "THIRTEENTH": 13,
    "FOURTEENTH": 14,
    "FIFTEENTH": 15,
    "SIXTEENTH": 16,
    "SEVENTEENTH": 17,
    "EIGHTEENTH": 18,
    "NINETEENTH": 19,
    "TWENTIETH": 20,
    "TWENTY-FIRST": 21,
    "TWENTY-SECOND": 22,
    "TWENTY-THIRD": 23,
    "TWENTY-FOURTH": 24,
    "TWENTY-FIFTH": 25,
}
TRENT_UNIT_RE = re.compile(
    r"(?im)^("
    r"BULL\b[^\n]*|"
    r"DECREE\b[^\n]*|"
    r"DOCTRINE\b[^\n]*|"
    r"ON THE [^\n]+|"
    r"ON JUSTIFICATION|"
    r"ON COMMUNION[^\n]*|"
    r"ON THE SACRIFICE[^\n]*|"
    r"ON THE SACRAMENT[^\n]*|"
    r"ON THE MOST HOLY[^\n]*|"
    r"ON REGULARS[^\n]*|"
    r"ON CHOICE[^\n]*|"
    r"ON THE INDEX[^\n]*|"
    r"ON THE PLACE[^\n]*|"
    r"ON RECEIVING[^\n]*|"
    r"ON RECITING[^\n]*|"
    r"ON THE CLOSE[^\n]*|"
    r"ON THE INVOCATION[^\n]*|"
    r"ACCLAMATIONS[^\n]*|"
    r"CONFIRMATION OF THE COUNCIL|"
    r"SAFE-CONDUCT[^\n]*|"
    r"EXTENSION THEREOF[^\n]*|"
    r"INDICTION OF THE NEXT SESSION|"
    r"CHAPTER [IVXLC]+\.|"
    r"CANON [IVXLC]+\.-?[^\n]*|"
    r"Proem\.?"
    r")\s*$"
)
ROMAN_RE = re.compile(r"(?i)\b([ivxlc]+)\b")


def clean_text(text: str) -> str:
    text = FOOTNOTE_MARK_RE.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80] or "unit"


def roman_to_int(token: str) -> int | None:
    values = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}
    total = 0
    prev = 0
    for ch in token.lower():
        if ch not in values:
            return None
        val = values[ch]
        total += val - 2 * prev if val > prev else val
        prev = val
    return total or None


def make_base_record(
    *,
    abbrev: str,
    record_key: str,
    text: str,
    canonical_citation: str,
    document_title: str,
    document_type: str,
    council: str,
    pope: str,
    date_promulgated: str,
    source_name: str,
    source_url: str,
    edition: str,
    translator: str,
    unit_title: str | None = None,
    session: int | None = None,
    paragraph: int | None = None,
    chapter: int | None = None,
    canon: int | None = None,
    decree: str | None = None,
    source_locator: str | None = None,
) -> dict:
    text = clean_text(text)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"mag:{abbrev}:{record_key}:en",
        "corpus": CORPUS,
        "source_family": "council",
        "authority_class": "ecumenical_council",
        "document_title": document_title,
        "document_abbrev": abbrev,
        "document_type": document_type,
        "promulgating_authority": council,
        "pope": pope,
        "council": council,
        "dicastery": None,
        "date_promulgated": date_promulgated,
        "part": None,
        "section": None,
        "chapter": chapter,
        "article": None,
        "paragraph": paragraph,
        "session": session,
        "decree": decree,
        "canon": canon,
        "question": None,
        "unit_title": unit_title,
        "canonical_citation": canonical_citation,
        "language": "en",
        "translator": translator,
        "edition": edition,
        "parallel_group_id": f"mag:{abbrev}:{record_key}",
        "source_name": source_name,
        "source_url": source_url,
        "source_locator": source_locator or canonical_citation,
        "date_acquired": DATE_ACQUIRED,
        "text": text,
        "footnotes": [],
        "source_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def fetch(url: str) -> str:
    response = SESSION.get(url, timeout=120)
    response.raise_for_status()
    return response.text


def iter_blocks(html: str):
    soup = BeautifulSoup(html, "lxml")
    content = soup.find("div", class_="entry-content")
    if content is None:
        raise SystemExit("entry-content not found")
    for el in content.find_all(["h1", "h2", "h3", "h4", "h5", "p"], recursive=True):
        text = el.get_text(" ", strip=True)
        if text:
            yield el.name, text


def phase_for_year(year: int | None, current: str) -> str:
    if year is None:
        return current
    if year <= 1437:
        return "Basel"
    if year == 1438:
        return "Ferrara"
    return "Florence"


def parse_florence(html: str) -> list[dict]:
    edition = (
        "Decrees of the Ecumenical Councils, ed. Norman P. Tanner (1990), vol. 1; "
        "via Papal Encyclicals Online"
    )
    source_url = "https://www.papalencyclicals.net/councils/ecum17.htm"
    units: list[dict] = []
    phase = "Basel"
    session = None
    current = None
    pending_title = None

    def flush() -> None:
        nonlocal current
        if current and current.get("parts"):
            current["text"] = "\n\n".join(current["parts"]).strip()
            if current["text"]:
                units.append(current)
        current = None

    for tag, text in iter_blocks(html):
        if re.match(r"(?i)^(INTRODUCTION|SECOND INTRODUCTION|FOOTNOTES|BIBLIOGRAPHY)", text):
            if session is not None and re.match(r"(?i)^FOOTNOTES", text):
                break
            continue
        if re.match(r"(?i)^Introduction and translation taken from", text):
            break

        sm = SESSION_HEAD_RE.match(text)
        if sm:
            flush()
            a, b, rest = sm.group(1), sm.group(2), (sm.group(3) or "").strip()
            # Tanner e-text sometimes splits "18" as "1 8".
            if b and re.match(r"^\d{1,2}\s+\w+\s+\d{4}", rest or ""):
                session = int(a + b) if len(a) == 1 and len(b) == 1 else int(a)
                date_blob = rest
            elif b and not rest:
                session = int(a + b)
                date_blob = ""
            else:
                session = int(a)
                date_blob = ((b + " ") if b else "") + rest
            dm = DATE_RE.search(date_blob) or DATE_RE.search(text)
            year = int(dm.group(1).split()[-1]) if dm else None
            phase = phase_for_year(year, phase)
            pending_title = None
            tm = TITLE_BRACKET_RE.search(date_blob)
            if tm:
                pending_title = tm.group(1).strip()
            continue

        if session is None:
            continue

        if TITLE_BRACKET_RE.match(text):
            flush()
            pending_title = TITLE_BRACKET_RE.match(text).group(1).strip()
            current = {
                "phase": phase,
                "session": session,
                "title": pending_title,
                "parts": [text],
                "summary_only": True,
            }
            continue

        if tag != "p":
            continue

        # One JSONL record per HTML paragraph so long bulls stay citable.
        if current is not None and current.get("summary_only"):
            current["parts"] = [text]
            current["summary_only"] = False
            current["title"] = pending_title or current.get("title")
            pending_title = None
            flush()
            continue

        flush()
        current = {
            "phase": phase,
            "session": session,
            "title": pending_title,
            "parts": [text],
            "summary_only": False,
        }
        pending_title = None
        flush()

    flush()

    records: list[dict] = []
    counters: dict[tuple[str, int], int] = {}
    for unit in units:
        text = unit["text"]
        if len(text) < 20:
            continue
        # Drop pure editorial asides that are not conciliar acts.
        if text.startswith("The famous Haec Sancta"):
            continue
        key_base = (unit["phase"], unit["session"])
        counters[key_base] = counters.get(key_base, 0) + 1
        para = counters[key_base]
        phase = unit["phase"]
        sess = unit["session"]
        title = unit.get("title")
        phase_slug = phase.lower()
        if title:
            decree = slugify(title)
            citation = f"Florence ({phase}) S{sess} [{title}]"
            record_key = f"{phase_slug}:s{sess}:{decree}"
            unit_title = title
        else:
            decree = None
            citation = f"Florence ({phase}) S{sess} para. {para}"
            record_key = f"{phase_slug}:s{sess}:p{para}"
            unit_title = None
        records.append(
            make_base_record(
                abbrev="FLO",
                record_key=record_key,
                text=text,
                canonical_citation=citation,
                document_title="Council of Basel–Ferrara–Florence (1431–1445), Sessions",
                document_type="council_decree",
                council="Council of Florence",
                pope="Eugene IV",
                date_promulgated="1431-1445",
                source_name="Papal Encyclicals Online",
                source_url=source_url,
                edition=edition,
                translator="Norman P. Tanner",
                unit_title=unit_title,
                session=sess,
                paragraph=para,
                decree=decree,
            )
        )
    return records


def parse_constantinople_iii(html: str) -> list[dict]:
    edition = (
        "Decrees of the Ecumenical Councils, ed. Norman P. Tanner (1990), vol. 1; "
        "via Papal Encyclicals Online"
    )
    source_url = "https://www.papalencyclicals.net/councils/ecum06.htm"
    started = False
    paras: list[str] = []
    for tag, text in iter_blocks(html):
        if re.match(r"(?i)^Exposition of faith", text):
            started = True
            continue
        if not started:
            continue
        if re.match(r"(?i)^(FOOTNOTES|Introduction and translation)", text):
            break
        if tag == "p":
            paras.append(text)
    records = []
    for i, para in enumerate(paras, start=1):
        if len(para) < 40:
            continue
        records.append(
            make_base_record(
                abbrev="CON3",
                record_key=f"exposition:p{i}",
                text=para,
                canonical_citation=f"Constantinople III, Exposition of faith para. {i}",
                document_title=(
                    "Third Council of Constantinople (680–681), Exposition of Faith"
                ),
                document_type="council_definition",
                council="Third Council of Constantinople",
                pope="Agatho / Leo II",
                date_promulgated="680-681",
                source_name="Papal Encyclicals Online",
                source_url=source_url,
                edition=edition,
                translator="Norman P. Tanner",
                unit_title="Exposition of faith",
                paragraph=i,
                decree="exposition-of-faith",
            )
        )
    return records


def split_trent_session(session_no: int, body: str) -> list[dict]:
    body = re.sub(r"\[Page \d+\]", "", body)
    body = body.replace("\r\n", "\n")
    # Keep line-oriented headers detectable.
    lines = [ln.rstrip() for ln in body.splitlines()]
    # Drop leading date/celebrated blurb until first unit header.
    units: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_parts
        if current_title is None:
            return
        text = clean_text("\n".join(current_parts))
        if text:
            units.append((current_title, [text]))
        current_title = None
        current_parts = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_title is not None:
                current_parts.append("")
            continue
        if TRENT_UNIT_RE.match(stripped):
            flush()
            current_title = re.sub(r"\s+", " ", stripped)
            current_parts = []
            continue
        if current_title is None:
            # Prefatory celebration line — keep as session preamble if substantial.
            continue
        current_parts.append(stripped)
    flush()

    # If nothing matched, keep whole session as one decree.
    if not units:
        text = clean_text(body)
        if len(text) < 40:
            return []
        return [
            make_base_record(
                abbrev="Trent",
                record_key=f"s{session_no}:session-text",
                text=text,
                canonical_citation=f"Trent S{session_no}",
                document_title=(
                    "The Canons and Decrees of the Sacred and Oecumenical Council of Trent"
                ),
                document_type="council_decree",
                council="Council of Trent",
                pope="Paul III / Julius III / Pius IV",
                date_promulgated="1545-1563",
                source_name="Hanover Historical Texts Project (history.hanover.edu)",
                source_url="https://history.hanover.edu/texts/trent/trentall.html",
                edition=(
                    "J. Waterworth (ed. & trans.), The Canons and Decrees of the Sacred "
                    "and Oecumenical Council of Trent (London: Dolman, 1848); "
                    "Hanover Historical Texts Project scan"
                ),
                translator="J. Waterworth",
                session=session_no,
                decree="session-text",
            )
        ]

    records: list[dict] = []
    for title, parts in units:
        text = parts[0]
        if len(text) < 20:
            continue
        chapter = None
        canon = None
        decree_slug = slugify(title)
        citation = f"Trent S{session_no} {title.rstrip('.')}"
        cm = re.match(r"(?i)^CHAPTER\s+([IVXLC]+)", title)
        if cm:
            chapter = roman_to_int(cm.group(1))
            citation = f"Trent S{session_no} ch. {chapter}"
            decree_slug = f"ch{chapter}"
        am = re.match(r"(?i)^CANON\s+([IVXLC]+)", title)
        if am:
            canon = roman_to_int(am.group(1))
            # Keep canon text including the header line.
            text = clean_text(title + "\n" + text) if not text.lower().startswith("canon") else text
            citation = f"Trent S{session_no} canon {canon}"
            decree_slug = f"canon{canon}"
        record_key = f"s{session_no}:{decree_slug}"
        records.append(
            make_base_record(
                abbrev="Trent",
                record_key=record_key,
                text=text if not am else clean_text(title + " " + re.sub(r"(?i)^CANON\s+[IVXLC]+\.-?\s*", "", text)),
                canonical_citation=citation,
                document_title=(
                    "The Canons and Decrees of the Sacred and Oecumenical Council of Trent"
                ),
                document_type="council_decree",
                council="Council of Trent",
                pope="Paul III / Julius III / Pius IV",
                date_promulgated="1545-1563",
                source_name="Hanover Historical Texts Project (history.hanover.edu)",
                source_url="https://history.hanover.edu/texts/trent/trentall.html",
                edition=(
                    "J. Waterworth (ed. & trans.), The Canons and Decrees of the Sacred "
                    "and Oecumenical Council of Trent (London: Dolman, 1848); "
                    "Hanover Historical Texts Project scan"
                ),
                translator="J. Waterworth",
                unit_title=title.rstrip("."),
                session=session_no,
                paragraph=None,
                chapter=chapter,
                canon=canon,
                decree=decree_slug,
            )
        )
    return records


def complete_trent(path: Path) -> tuple[int, int]:
    existing = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    present_sessions = {
        r.get("session") for r in existing if isinstance(r.get("session"), int)
    }
    missing = sorted(set(range(1, 26)) - present_sessions)
    if not missing:
        return 0, len(existing)

    html = fetch("https://history.hanover.edu/texts/trent/trentall.html")
    text = BeautifulSoup(html, "lxml").get_text("\n")
    added: list[dict] = []
    for ordinal, body in TRENT_SESSION_RE.findall(text):
        session_no = TRENT_ORDINAL[ordinal.upper()]
        if session_no not in missing:
            continue
        added.extend(split_trent_session(session_no, body))

    # Preserve existing order: old records first, then new sessions by number.
    merged = existing + sorted(added, key=lambda r: (r.get("session") or 0, r["record_id"]))
    write_jsonl(path, merged)
    return len(added), len(merged)


def rebuild_index() -> dict:
    sys.path.insert(0, str(ROOT / "scripts"))
    from download_council_documents import build_index, write_readme  # type: ignore
    from scrape_missing_councils import update_document_catalog  # type: ignore

    index = build_index(DOCUMENTS_DIR)
    index["missingCouncils"] = []
    index["supplementalSource"] = {
        "name": "Papal Encyclicals Online / Hanover Historical Texts",
        "note": (
            "Missing RAG councils via scripts/scrape_missing_councils.py; "
            "Florence/Constantinople III/Trent gaps via "
            "scripts/complete_incomplete_councils.py."
        ),
    }
    (OUT_DIR / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_readme(OUT_DIR, index)
    update_document_catalog()
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="*",
        help="Optional targets: florence con3 trent",
    )
    args = parser.parse_args()
    only = {x.lower() for x in args.only} if args.only else None

    if only is None or "florence" in only:
        print("Completing Florence from Tanner ecum17…")
        html = fetch("https://www.papalencyclicals.net/councils/ecum17.htm")
        records = parse_florence(html)
        if len(records) < 50:
            raise SystemExit(f"Florence parse too thin: {len(records)} records")
        path = DOCUMENTS_DIR / "Florence.jsonl"
        write_jsonl(path, records)
        print(f"  wrote {len(records)} records -> {path.relative_to(ROOT)}")

    if only is None or "con3" in only:
        print("Completing Constantinople III from Tanner ecum06…")
        html = fetch("https://www.papalencyclicals.net/councils/ecum06.htm")
        records = parse_constantinople_iii(html)
        if len(records) < 5:
            raise SystemExit(f"CON3 parse too thin: {len(records)} records")
        path = DOCUMENTS_DIR / "Constantinople_III.jsonl"
        write_jsonl(path, records)
        print(f"  wrote {len(records)} records -> {path.relative_to(ROOT)}")

    if only is None or "trent" in only:
        print("Filling missing Trent sessions from Hanover…")
        path = DOCUMENTS_DIR / "Trent.jsonl"
        added, total = complete_trent(path)
        print(f"  added {added} records; Trent now {total} -> {path.relative_to(ROOT)}")

    index = rebuild_index()
    print(f"index.json documents={index['count']} missing={index['missingCouncils']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
