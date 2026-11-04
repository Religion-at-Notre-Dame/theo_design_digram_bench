# Audit: expand contrast.jsonl from all 1760 Step 1 questions

**Date:** 28 October 2026  
**Rule:** Include only recoverable **disagreement** (Catholic and breakaway say different things). No shared-affirmation rows.

## Method

1. Re-classify the previously excluded breakaway-tagged loci.
2. Keyword-scan the **1630** untagged entries (Filioque, Chalcedon, Theotokos, sacraments, purgatory, both kinds, etc.).
3. Add only conservative, recoverable disagreements; skip ceremony, shared dogma, weak tags, and near-duplicates already covered.

Working files: `_audit_excluded69_*.json`, `_audit_untagged_*.json`.

## Result

| Stage | Count |
|-------|------:|
| Prior contrast (after agreement purge) | 61 |
| **New contrast rows added** | **+13** |
| **Current contrast.jsonl** | **74** |
| Breakaway-tagged loci (after new tags) | 148 |
| Still excluded from contrast | 74 |

## Added from already-tagged excludes (+4)

| Id | Group | Disagreement |
|----|-------|--------------|
| `flo-florence-s8-p27-en` | Armenian Apostolic | Filioque + Chalcedon + two wills package |
| `flo-florence-s8-p29-en` | Armenian Apostolic | Water mixed with wine in the chalice |
| `flo-florence-s8-p31-en` | Armenian Apostolic | Filioque, purgatory, papal primacy |
| `flo-florence-s11-p24-en` | Coptic Orthodox | Fourth+ marriages freely lawful |

**Reviewed but not added:** Florence S6 §6 (debate narrative); S8 §17 indissolubility (too weak); Trent Mass preamble (duplicate of existing S22 ch.1–2).

## Added from untagged loci (+9) — new breakaway tags

| Id | New tag | Disagreement |
|----|---------|--------------|
| `eph-anathema1-en` | Church of the East | Theotokos / Emmanuel very God |
| `con-s13-condemnation-of-communion-under-both-kinds-…` | Hussites | Utraquism / cup for the laity |
| `flo-florence-s13-p8-en` | Syriac Orthodox Church | Two natures without confusion… |
| `trent-s6-justification-canon30-en` | Lutheran churches | Residual temporal punishment / Purgatory |
| `trent-s24-matrimony-canon1-en` | Lutheran churches | Matrimony as sacrament conferring grace |
| `con2-canon6-en` | Church of the East | Mary exactly and truly Mother of God |
| `con2-canon7-en` | Oriental Orthodox churches | “In two natures” hypostatic union |
| `con2-canon8-en` | Oriental Orthodox churches | Regulation of two-natures / one-nature phrasing |
| `con2-canon14-en` | Church of the East | Ibas letter to be rejected |

**Reviewed but not added:** Trent S22 Mass canon 3 (duplicate of existing propitiatory Mass chapters); most other keyword hits were Chalcedon disciplinary canons, VII Marian loci, or narrative false positives.

## Side effect

Florence **S13** (Syrian union) paragraphs are now breakaway-tagged **Syriac Orthodox Church** for session consistency with S8/S11; only **S13 §8** is in the strict contrast set so far.

## Regenerated

```bash
python3 scripts/step1/compile_breakaways.py
python3 scripts/step1/build_contrast_db.py
python3 scripts/step1/export_contrast_viz.py   # via build
python3 scripts/step1/build_contrast_extended.py
```

## Later promote from AI spot-check (+8)

Spot-checked AI fills and tagged solid degree-1 rows into strict contrast
(see `STEP1_COMPLETION_NOTES.md`). **contrast.jsonl → 82**; breakaways → 156.
