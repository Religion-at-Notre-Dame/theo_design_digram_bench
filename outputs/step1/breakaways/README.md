# Breakaway subset

Only the Step 1 decisions tied to a **breakaway group** (formal
definition in the root README). Compiled from verified
`outputs/step1/entries.jsonl` plus matching English council passages.

**156 entries** · **156 passages** · text_status={'full': 156}

## Files

| File | Role |
|------|------|
| `entries.jsonl` | Question + citation + breakaway |
| `passages.jsonl` | Full council passage text for each locus |
| `summary.json` | Counts by group and council |
| `groups_catalog.json` | Lineage reference (any separation degree) |
| `groups.md` / `groups_lineage.html` | Catalog table + interactive graph |
| `groups_degree1_coverage.md` | Which degree-1 groups have council loci |
| `contrast/` | Catholic vs breakaway NL Q&A |

## By breakaway group

- **Arian churches** — 1
- **Melitian schism (Egypt)** — 1
- **Church of the East** — 18
- **Oriental Orthodox churches** — 4
- **Armenian Apostolic Church** — 33
- **Coptic Orthodox Church** — 25
- **Syriac Orthodox Church** — 10
- **Eastern Orthodox churches** — 18
- **Waldensians** — 1
- **Wycliffites / Lollards** — 6
- **Hussites** — 5
- **Lutheran churches** — 26
- **Reformed / Calvinist churches** — 1
- **Anabaptist / Radical Reformation churches** — 1
- **Anglican Communion / Church of England** — 1
- **Old Catholic churches** — 2
- **Polish National Catholic Church** — 1
- **Philippine Independent Church (Aglipayan)** — 1
- **Mariavite Church (Old Catholic Church of the Mariavites)** — 1

## By council

- Council of Florence — 80
- Council of Trent — 29
- Council of Ephesus — 16
- Council of Constance — 11
- Second Council of Lyons — 6
- Second Council of Constantinople — 5
- First Vatican Council — 5
- First Council of Nicaea — 2
- Council of Chalcedon — 1
- Fourth Lateran Council — 1

## Contrast database

Natural-language questions with Catholic vs breakaway answers (explicit-trace subset): [`contrast/`](contrast/) (82 rows). Conversion rules: [`contrast/agent.md`](contrast/agent.md). Viewer: [`contrast/contrast.html`](contrast/contrast.html).


## Degree-1 coverage

Which catalog degree-1 groups have council loci vs summary-only: [`groups_degree1_coverage.md`](groups_degree1_coverage.md).

## Lineage catalog

[`groups_catalog.json`](groups_catalog.json) tracks breakaways at any separation degree (including >1). Re-audit with `python scripts/step1/audit_fix_groups_catalog.py`.

## Regenerate

```bash
python scripts/step1/refine_breakaway_labels.py
python scripts/step1/compile_breakaways.py
python scripts/step1/build_contrast_db.py
python scripts/step1/export_contrast_viz.py
python scripts/step1/export_groups_viz.py
```
