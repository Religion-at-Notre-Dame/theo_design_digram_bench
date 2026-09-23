#!/usr/bin/env python3
"""Download and extract ecumenical-council documents for Step 1.

Source: Catholic Doctrine and Magisterium Canonical RAG Corpus v1.0.0
https://github.com/GibbilyGooo/catholic-doctrine-magisterium-rag-corpus

The release ships citation-preserving JSONL (session / canon / paragraph loci)
for early councils, Trent, Vatican I, and all sixteen Vatican II documents.
This script keeps only the council slice and writes a small index.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

RELEASE_TAG = "v1.0.0"
RELEASE_ZIP_NAME = "Catholic_Doctrine_Magisterium_RAG_Corpus_v1.0.0.zip"
RELEASE_URL = (
    "https://github.com/GibbilyGooo/catholic-doctrine-magisterium-rag-corpus"
    f"/releases/download/{RELEASE_TAG}/{RELEASE_ZIP_NAME}"
)
EXPECTED_SHA256 = "03b379edb545186890a5386252f1b540192847bb0f404883a4df7942ad7426c7"
ARCHIVE_ROOT = "github-catholic-doctrine-magisterium-rag-corpus"
COUNCILS_PREFIX = f"{ARCHIVE_ROOT}/source/canonical/councils/"
CATALOG_PATH = f"{ARCHIVE_ROOT}/data/document_catalog.json"
COPYRIGHT_PATH = f"{ARCHIVE_ROOT}/COPYRIGHT_AND_SOURCES.md"

# Catholic ecumenical councils absent from the upstream release.
# Filled by scripts/scrape_missing_councils.py from Papal Encyclicals Online.
MISSING_COUNCILS: list[str] = []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, dest: Path) -> None:
    print(f"Downloading {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out)


def extract_councils(zip_path: Path, out_dir: Path) -> list[Path]:
    written: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        members = [
            name
            for name in archive.namelist()
            if name.startswith(COUNCILS_PREFIX) and name.endswith(".jsonl")
        ]
        if not members:
            raise SystemExit(f"No council JSONL found under {COUNCILS_PREFIX}")

        for name in members:
            relative = Path(name).relative_to(COUNCILS_PREFIX)
            target = out_dir / "documents" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            written.append(target)

        # Keep provenance notes that apply to redistribution.
        if COPYRIGHT_PATH in archive.namelist():
            copyright_target = out_dir / "COPYRIGHT_AND_SOURCES.md"
            with archive.open(COPYRIGHT_PATH) as src, copyright_target.open("wb") as dst:
                shutil.copyfileobj(src, dst)

        catalog_raw = archive.read(CATALOG_PATH)
        catalog = json.loads(catalog_raw)
        council_catalog = [
            entry
            for entry in catalog
            if entry.get("source_family") == "council"
            or entry.get("authority_class") == "ecumenical_council"
        ]
        (out_dir / "document_catalog.json").write_text(
            json.dumps(council_catalog, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return written


def build_index(documents_dir: Path) -> dict:
    items = []
    for path in sorted(documents_dir.rglob("*.jsonl")):
        en_records = 0
        la_records = 0
        canons = 0
        sessions = 0
        paragraphs = 0
        sample = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            lang = record.get("language")
            if lang == "en":
                en_records += 1
                if sample is None:
                    sample = record
                if record.get("canon") is not None:
                    canons += 1
                if record.get("session") is not None:
                    sessions += 1
                if record.get("paragraph") is not None:
                    paragraphs += 1
            elif lang == "la":
                la_records += 1

        if sample is None:
            continue

        items.append(
            {
                "id": sample.get("document_abbrev"),
                "title": sample.get("document_title"),
                "council": sample.get("council") or sample.get("promulgating_authority"),
                "documentType": sample.get("document_type"),
                "datePromulgated": sample.get("date_promulgated"),
                "sourceUrl": sample.get("source_url"),
                "edition": sample.get("edition"),
                "englishRecordCount": en_records,
                "latinRecordCount": la_records,
                "englishCanonCount": canons,
                "englishSessionCount": sessions,
                "englishParagraphCount": paragraphs,
                "file": str(path.relative_to(documents_dir.parent)).replace("\\", "/"),
            }
        )

    return {
        "source": {
            "name": "Catholic Doctrine and Magisterium Canonical RAG Corpus",
            "version": RELEASE_TAG,
            "url": (
                "https://github.com/GibbilyGooo/"
                "catholic-doctrine-magisterium-rag-corpus"
            ),
            "releaseZip": RELEASE_URL,
            "sha256": EXPECTED_SHA256,
        },
        "missingCouncils": MISSING_COUNCILS,
        "count": len(items),
        "items": items,
    }


def write_readme(out_dir: Path, index: dict) -> None:
    lines = [
        "# Council documents",
        "",
        "Citation-preserving ecumenical council texts for Step 1, extracted from",
        f"[GibbilyGooo/catholic-doctrine-magisterium-rag-corpus]({index['source']['url']})",
        f"{index['source']['version']}.",
        "",
        "Each `.jsonl` line is one citable unit with fields such as `session`,",
        "`canon`, `paragraph`, `chapter`, `canonical_citation`, `text`, and",
        "`source_url`. Prefer `canonical_citation` when writing question sentences.",
        "",
        "## Layout",
        "",
        "```",
        "data/councils/",
        "├── index.json",
        "├── document_catalog.json",
        "├── COPYRIGHT_AND_SOURCES.md",
        "└── documents/",
        "    ├── Nicaea_I.jsonl",
        "    ├── Trent.jsonl",
        "    ├── Vatican_II/",
        "    │   ├── LG.jsonl",
        "    │   └── ...",
        "    └── ...",
        "```",
        "",
        f"**{index['count']} documents** in this extract.",
        "",
    ]
    missing = index.get("missingCouncils") or MISSING_COUNCILS
    if missing:
        lines.extend(["## Gaps", ""])
        for name in missing:
            lines.append(f"- {name}")
        lines.append("")
    else:
        lines.extend(
            [
                "The eight councils absent from the upstream release "
                "(Constantinople IV, Lateran I–III, Lyons I, Vienne, Constance, "
                "Lateran V) were scraped from Papal Encyclicals Online (Tanner) "
                "into the same JSONL schema by `scripts/scrape_missing_councils.py`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Rights",
            "",
            "Upstream code/docs are MIT; the data-layer organization is CC0. The",
            "underlying Church documents and translations retain their own rights.",
            "See `COPYRIGHT_AND_SOURCES.md` before redistributing.",
            "",
            "## Refresh",
            "",
            "```bash",
            "python scripts/download_council_documents.py",
            "python scripts/scrape_missing_councils.py",
            "```",
            "",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "councils",
        help="Destination directory (default: data/councils)",
    )
    parser.add_argument(
        "--zip",
        type=Path,
        default=None,
        help="Use an already-downloaded release zip instead of fetching",
    )
    parser.add_argument(
        "--keep-zip",
        action="store_true",
        help="Keep the downloaded zip under data/councils/_cache/",
    )
    args = parser.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.zip:
        zip_path = args.zip
        if not zip_path.is_file():
            raise SystemExit(f"Zip not found: {zip_path}")
        cleanup_zip = False
    else:
        cache_dir = out_dir / "_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        zip_path = cache_dir / RELEASE_ZIP_NAME
        if not zip_path.is_file():
            download(RELEASE_URL, zip_path)
        cleanup_zip = not args.keep_zip

    digest = sha256_file(zip_path)
    if digest != EXPECTED_SHA256:
        raise SystemExit(
            f"SHA-256 mismatch for {zip_path}\n"
            f"  expected: {EXPECTED_SHA256}\n"
            f"  got:      {digest}"
        )
    print(f"SHA-256 ok: {digest}")

    documents_dir = out_dir / "documents"
    if documents_dir.exists():
        shutil.rmtree(documents_dir)

    with tempfile.TemporaryDirectory() as tmp:
        # extract_councils writes directly into out_dir
        written = extract_councils(zip_path, out_dir)
    print(f"Extracted {len(written)} council JSONL files")

    # Re-apply Tanner scrapes for councils absent from the release.
    scrape_script = Path(__file__).resolve().parent / "scrape_missing_councils.py"
    if scrape_script.is_file():
        import subprocess

        print("Running scrape_missing_councils.py to restore supplemental councils…")
        subprocess.check_call([sys.executable, str(scrape_script)])
    else:
        index = build_index(documents_dir)
        (out_dir / "index.json").write_text(
            json.dumps(index, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_readme(out_dir, index)
        print(f"Wrote {out_dir / 'index.json'} ({index['count']} documents)")

    if cleanup_zip and zip_path.exists() and args.zip is None:
        zip_path.unlink()
        cache_dir = out_dir / "_cache"
        if cache_dir.exists() and not any(cache_dir.iterdir()):
            cache_dir.rmdir()

    return 0


if __name__ == "__main__":
    sys.exit(main())
