# Step 1 outputs

Comprehensive council mapping: **one verified entry per English locus** in `data/councils/`.

## Files

| File | Role |
|------|------|
| `entries.jsonl` | Step 1 entries (`draft` / `verified` / `failed_citation`) |
| `entries.draft.jsonl` | Staging copy from the last draft run |
| `verify_report.json` | Citation verification details |
| `coverage_report.json` | Inventory + full-corpus coverage checks |
| `council_map.mmd` | Mermaid graph of breakaway-linked decisions only |
| `council_overview.html` | Chronological full-corpus bar chart (all councils) |

## Schema

Each `entries.jsonl` line:

- `id`, `inventory_id`, `council`, `document_abbrev`
- `record_id`, `canonical_citation` — must resolve in `data/councils/`
- `question` — one interrogative sentence
- `breakaway` — string or `null`
- `decision_summary`, `source_file`, `status`

## Commands

```bash
python scripts/step1/expand_inventory.py --min-chars 0   # 1:1 with corpus
python scripts/step1/draft_entries.py                    # heuristic; or --mode llm
python scripts/step1/verify_entries.py --write-status
python scripts/step1/coverage_report.py                  # expect corpus_complete=True
python scripts/step1/export_graph.py                     # schism map -> council_map.mmd
python scripts/step1/export_overview.py                  # timeline bars -> council_overview.html
```

Only `status: verified` entries are Step 1 deliverables. Current set: **1488** entries covering all English council records.
