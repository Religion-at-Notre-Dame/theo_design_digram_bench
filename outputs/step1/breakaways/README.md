# Breakaway subset

Only the Step 1 decisions tied to a **breakaway group** (formal
definition in the root README). Compiled from verified
`outputs/step1/entries.jsonl` plus matching English council passages.

**130 entries** · **130 passages** · text_status={'full': 130}

## Files

| File | Role |
|------|------|
| `entries.jsonl` | Question + citation + breakaway |
| `passages.jsonl` | Full council passage text for each locus |
| `summary.json` | Counts by group and council |
| `groups_catalog.json` | **Lineage reference** for breakaways at any separation degree (incl. >1) |
| `groups.md` | Chronological/degree table of that catalog |
| `groups_lineage.html` | Interactive lineage graph (filter by degree/status) |
| `groups_lineage.mmd` | Compact Mermaid (≤ degree 2, non-synthetic) |

## Lineage catalog

[`groups_catalog.json`](groups_catalog.json) is the reference for the next phase:
tracing groups with **separation degree > 1** (broke from a prior
breakaway, not directly from Rome).

Each group includes `broke_from`, `separation_degree`, and `lineage`
(path from `catholic-church`). Degree-1 rows overlap the council-tagged
subset; higher degrees cover Methodist←Anglican, Baptist←Separatist,
Pentecostal←Holiness←Methodist, Old Believers←Eastern Orthodox, etc.

## By breakaway group

- **Arian churches** — 1
- **Church of the East** — 15
- **Oriental Orthodox churches** — 60
- **Eastern Orthodox churches** — 18
- **Wycliffites / Lollards** — 6
- **Hussites** — 4
- **Protestant churches** — 24
- **Old Catholic churches** — 2

## By council

- Council of Florence — 70
- Council of Trent — 24
- Council of Ephesus — 15
- Council of Constance — 10
- Second Council of Lyons — 6
- First Vatican Council — 2
- First Council of Nicaea — 1
- Council of Chalcedon — 1
- Second Council of Constantinople — 1

## Regenerate

```bash
python scripts/step1/compile_breakaways.py
python scripts/step1/export_graph.py --entries outputs/step1/breakaways/entries.jsonl --out outputs/step1/breakaways/council_map.mmd
```
