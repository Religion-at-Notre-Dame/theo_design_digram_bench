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
| `breakaways/` | **Breakaway-only subset** — entries + passage text + map |

## Schema

Each `entries.jsonl` line:

- `id`, `inventory_id`, `council`, `document_abbrev`
- `record_id`, `canonical_citation` — must resolve in `data/councils/`
- `question` — one interrogative sentence
- `breakaway` — string or `null` (see root README § “Breakaway group (formal definition)”; normalize with `scripts/step1/clean_breakaways.py`)
- `decision_summary`, `source_file`, `status`

## Breakaway subset

After cleaning breakaways, compile only the schism-linked decisions:

```bash
python scripts/step1/compile_breakaways.py
```

Output: [`breakaways/`](breakaways/) (`entries.jsonl`, `passages.jsonl`, `summary.json`, `council_map.mmd`).

## Commands

```bash
python scripts/step1/expand_inventory.py --min-chars 0   # 1:1 with corpus
python scripts/step1/draft_entries.py                    # heuristic; or --mode llm
python scripts/step1/verify_entries.py --write-status
python scripts/step1/clean_breakaways.py                 # formal breakaway definition
python scripts/step1/refine_breakaway_labels.py          # Armenian / Coptic / Lutheran…
python scripts/step1/naturalize_questions.py             # heuristic NL (LLM optional upstream)
python scripts/step1/compile_breakaways.py               # breakaway-only subset
python scripts/step1/build_contrast_db.py
python scripts/step1/export_contrast_viz.py
python scripts/step1/coverage_report.py                  # expect corpus_complete=True
python scripts/step1/export_graph.py                     # schism map -> council_map.mmd
python scripts/step1/export_overview.py                  # timeline bars -> council_overview.html
python scripts/step1/export_groups_viz.py
```

Only `status: verified` entries are Step 1 deliverables. Current full set covers all English council records; the breakaway subset is the schism-focused slice. Precise labels and contrast coverage: see [`breakaways/groups_degree1_coverage.md`](breakaways/groups_degree1_coverage.md).
