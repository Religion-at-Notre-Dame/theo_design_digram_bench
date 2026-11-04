# contrast_extended (TEST only)

**Not status quo.** Do not replace `contrast.jsonl` / `contrast.html` with these files.

**Disagreement-only:** ceremony, narrative, and likely-shared loci are **skipped**
(no “no distinctive doctrinal rupture” rows). Expansion adds breakaway groups with
real opposition; it does not pad with agreement.

| | Strict | Extended (test) |
|--|--:|--:|
| Data | `contrast.jsonl` (82) | `contrast_extended.jsonl` (**119**) |
| Viewer | `contrast.html` | [`contrast_extended.html`](contrast_extended.html) |
| Gate | Explicit-trace disagreement | Inferred opposition as well |
| Confidence | high | mixed (high + low) |

- **82** rows: copied from `contrast.jsonl` (`tier=strict`, `confidence=high`).
- **37** rows: inferred disagreement (`tier=extended`, `confidence=low`).
- **37** breakaway-tagged loci skipped (ceremony / shared / same polarity).

### `contrast_kind` counts

- `explicit_trace` — 82
- `inferred_opposition` — 37
- `skipped_ceremony_or_narrative` — 21
- `skipped_likely_shared` — 11
- `skipped_inferred_opposition` — 5

### Regenerate

```bash
python3 scripts/step1/build_contrast_extended.py
```
