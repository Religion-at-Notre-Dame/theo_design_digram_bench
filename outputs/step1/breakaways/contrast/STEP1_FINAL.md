# Step 1 final contrast product

For **every** breakaway group in the doctrinal match list, **all recoverable**
disagreement questions across relevant councils (primary + family secondaries +
in-window councils). Shared affirmations are dropped. Each row cites its Catholic locus.

The HTML viewer’s **Pairing** filter compares:
- **All loci** — full comprehensive set (default)
- **Doctrinal primary only** — questions whose council = doctrinal primary
- **Temporal (≤50y after council) only** — rupture during or ≤50y after council end (not before); questions whose council = that temporal primary

## Counts

- Breakaway groups (doctrinal list): **151**
- Groups with ≥1 question: **151**
- Pending (no recoverable disagreement yet): **0**
- Total contrast rows: **4594**
- By tier: `{'ai': 4487, 'strict': 107}`
- By confidence: `{'low': 4487, 'high': 63, 'medium': 44}`

## Files

| File | Role |
|------|------|
| `contrast_step1.jsonl` | Canonical Step 1 contrast rows |
| `contrast_step1.html` | Interactive Q&A viewer (Pairing: All / Doctrinal / Temporal) |
| `STEP1_FINAL_REPORT.md` | Full method + accuracy report |
| `denomination_council_matches_50y.md` | Doctrinal group↔council list |
| `denomination_council_matches_temporal.md` | Temporal (nearest-council) list |

## Regenerate

```bash
python3 scripts/step1/build_contrast_step1.py
```

## Schema (per row)

```json
{
  "question": "...",
  "catholic_answer": "...",
  "breakaway_group": "...",
  "breakaway_answer": "...",
  "council": "...",
  "canonical_citation": "...",
  "record_id": "...",
  "source_entry_id": "...",
  "passage_excerpt": "...",
  "confidence": "high|medium|low",
  "tier": "strict|ai"
}
```
