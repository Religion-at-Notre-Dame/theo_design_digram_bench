# Council documents

Citation-preserving ecumenical council texts for Step 1, extracted from
[GibbilyGooo/catholic-doctrine-magisterium-rag-corpus](https://github.com/GibbilyGooo/catholic-doctrine-magisterium-rag-corpus)
v1.0.0.

Each `.jsonl` line is one citable unit with fields such as `session`,
`canon`, `paragraph`, `chapter`, `canonical_citation`, `text`, and
`source_url`. Prefer `canonical_citation` when writing question sentences.

## Layout

```
data/councils/
├── index.json
├── document_catalog.json
├── COPYRIGHT_AND_SOURCES.md
└── documents/
    ├── Nicaea_I.jsonl
    ├── Trent.jsonl
    ├── Vatican_II/
    │   ├── LG.jsonl
    │   └── ...
    └── ...
```

**37 documents** in this extract.

The eight councils absent from the upstream release (Constantinople IV, Lateran I–III, Lyons I, Vienne, Constance, Lateran V) were scraped from Papal Encyclicals Online (Tanner) into the same JSONL schema by `scripts/scrape_missing_councils.py`.

## Rights

Upstream code/docs are MIT; the data-layer organization is CC0. The
underlying Church documents and translations retain their own rights.
See `COPYRIGHT_AND_SOURCES.md` before redistributing.

## Refresh

```bash
python scripts/download_council_documents.py
python scripts/scrape_missing_councils.py
```
