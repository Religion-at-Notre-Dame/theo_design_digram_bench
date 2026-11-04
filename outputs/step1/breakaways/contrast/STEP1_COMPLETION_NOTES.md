# Step 1 completion notes (method update)

Captured from project direction before finishing Step 1.

## Goals

1. **More info on non-Catholic perspectives**  
   Allow an AI agent to draft breakaway answers even when we lack a citable
   primary source for every row. Prefer historically plausible group stances
   over leaving the contrast set tiny.

2. **Specific breakaway groups**  
   Use a concrete denomination list (not only umbrella labels like “Protestant”
   / “Oriental Orthodox”). Source of truth today:
   [`groups_catalog.json`](../groups_catalog.json) (**118** groups with
   `rupture_year`) plus [`denominations_extra.json`](denominations_extra.json)
   (**60** supplemental).

3. **Denominations by start date → councils**  
   For each non–Catholic-aligned church, if its start/rupture year falls within
   **±50 years** of a council’s span, treat that council as a candidate contrast
   pairing and search/tag loci accordingly. Prefer **doctrinal** council over
   nearest-year when the family’s rupture is clear.

## Pipeline

```bash
python3 scripts/step1/match_denominations_to_councils.py --window 50
python3 scripts/step1/expand_contrast_ai.py
python3 scripts/step1/compile_breakaways.py
python3 scripts/step1/build_contrast_db.py
python3 scripts/step1/export_contrast_viz.py
python3 scripts/step1/build_contrast_extended.py
```

Outputs (in this folder):

| File | Role |
|------|------|
| `denominations_by_start.json` | Breakaway groups ordered by start year |
| `catholic_aligned_excluded.json` | Filtered in-communion / non-breakaway bodies |
| `denomination_council_matches_50y.json` | Machine matches |
| `denomination_council_matches_50y.md` | Readable match table |
| `contrast_ai.jsonl` / `.html` | Low-confidence AI fills (not strict) |

## Policy shift vs earlier contrast gate

| Earlier (explicit-trace) | Completion direction |
|--------------------------|----------------------|
| Exclude unless breakaway answer is recoverable from passage + textbook history | **Allow AI fill** of breakaway stance when direct sources are missing |
| Keep `contrast.jsonl` disagreement-only | Still prefer **disagreement** (not shared Yes/Yes) |
| Umbrella tags OK when uncertain | Prefer **specific** catalog groups from the start-date list |

`contrast.jsonl` remains the curated disagreement set. AI fills stay in
`contrast_ai.jsonl` until spot-checked and promoted.

**Hard rule for all tiers:** only breakaway groups with recoverable
*disagreement*. Skip ceremony/narrative and shared-affirmation loci — never
emit “no distinctive doctrinal rupture” (or Yes/Yes) padding. Expansion means
more disagreeing groups, not more agreeing rows.

## Done

- [x] Doctrinal council preference over nearest-year (`expand_contrast_ai.py`).
- [x] Grow list: catalog **118** + extras **60** → **178** denomination nodes.
- [x] AI fills: [`contrast_ai.jsonl`](contrast_ai.jsonl) (**117** rows) with
      theme-pool locus diversification (not only Trent justification/eucharist).
- [x] Spot-check / promote into strict (**+8** → **82** rows):
  | Id | Group |
  |----|-------|
  | `nic1-synodal-letter-en` | Melitian schism (Egypt) |
  | `lat4-constitution3-en` | Waldensians |
  | `pa-ch4-canon1-en` | Polish National Catholic Church |
  | `pa-ch3-canon1-en` | Philippine Independent Church (Aglipayan) |
  | `pa-ch1-canon1-en` | Mariavite Church |
  | `trent-s6-justification-canon9-en` | Reformed / Calvinist churches |
  | `trent-s7-baptism-canon13-en` | Anabaptist / Radical Reformation |
  | `trent-s13-eucharist-canon1-en` | Anglican Communion |

  Left in AI-only (weak / anachronistic / contested): Donatists, LDS, Iglesia ni
  Cristo, Czech Hussite @ Constance, CPA, sedevacantist/Palmarian, etc.

## Temporal track (comprehensive council coverage)

Doctrinal matching compresses most Protestants onto Trent. A parallel
**temporal** track uses nearest council by start year:

```bash
python3 scripts/step1/match_denominations_to_councils.py --mode both
python3 scripts/step1/expand_contrast_ai.py --mode temporal
python3 scripts/step1/export_match_contrast_viz.py --mode both
```

| Artifact | Role |
|----------|------|
| `denomination_council_matches_temporal.md` | Nearest-council list (152 complete) |
| `contrast_ai_temporal.jsonl` | AI disagreement rows on temporal councils |
| `match_contrast_temporal.html` | Q&A viewer for the temporal list |

## Still optional

- [ ] Grow the church list further if fuller coverage is desired.
- [ ] Re-label remaining umbrella tags on `entries.jsonl` using the specific group list.
- [ ] Promote strong temporal AI rows (esp. Vatican I/II) into strict contrast after review.
- [ ] Decide whether Step 1 “official” viz defaults to temporal or doctrinal.
