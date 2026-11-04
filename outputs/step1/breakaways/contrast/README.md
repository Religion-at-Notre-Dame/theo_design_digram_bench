# Contrast database (Catholic vs breakaway)

Natural-language questions drawn from the breakaway-tagged Step 1 subset,
each with an explicit **Catholic** answer and the tagged **breakaway** answer.

Built only where both answers can be traced from the council passage plus
established historical positions (see include/exclude rules in `agent.md`).

**82 contrast rows** · source breakaways 156 · excluded 74 · mode `heuristic`

## Files

| File | Role |
|------|------|
| `contrast.jsonl` | One JSON object per contrast question |
| `contrast.html` | Interactive viewer (question + both answers + citation) |
| `direct_answers.json` | Hand-tuned answers that respond Yes/No to each question |
| `agent.md` | Conversion prompt / rules (NL question + dual answers) |
| `summary.json` | Counts |
| `contrast_ai.jsonl` / `contrast_ai.html` | AI-expanded disagreement rows (low confidence) |
| `denominations_by_start.json` | Breakaway start-year list |
| `denomination_council_matches_50y.md` | **Authoritative** breakaway↔council list (viz group basis) |
| `match_contrast_temporal.html` | Match-list Q&A viewer (**temporal / nearest**) |
| `denomination_council_matches_temporal.md` | Temporal nearest-council match list |
| `match_contrast.html` | **Match-list Q&A viewer** (group → questions) |
| `match_contrast.json` | Data behind the match-list viewer |

Regenerate the match list (then AI / viewers) with:

```bash
python3 scripts/step1/match_denominations_to_councils.py
python3 scripts/step1/expand_contrast_ai.py
python3 scripts/step1/export_contrast_viz.py
```

## Schema

```json
{
  "id": "entry id",
  "question": "natural-language theological question",
  "catholic_answer": "…",
  "breakaway_group": "…",
  "breakaway_answer": "…",
  "answer_basis": "passage+history",
  "notes": "optional caveat",
  "council": "…",
  "canonical_citation": "…",
  "record_id": "…",
  "passage_excerpt": "…",
  "source_entry_id": "…",
  "draft_method": "heuristic|llm"
}
```

## By breakaway group

- **Lutheran churches** — 22
- **Church of the East** — 13
- **Eastern Orthodox churches** — 10
- **Coptic Orthodox Church** — 8
- **Armenian Apostolic Church** — 7
- **Oriental Orthodox churches** — 4
- **Hussites** — 4
- **Wycliffites / Lollards** — 2
- **Old Catholic churches** — 2
- **Arian churches** — 1
- **Melitian schism (Egypt)** — 1
- **Syriac Orthodox Church** — 1
- **Waldensians** — 1
- **Reformed / Calvinist churches** — 1
- **Anabaptist / Radical Reformation churches** — 1
- **Anglican Communion / Church of England** — 1
- **Polish National Catholic Church** — 1
- **Philippine Independent Church (Aglipayan)** — 1
- **Mariavite Church (Old Catholic Church of the Mariavites)** — 1

## By council

- Council of Trent — 25
- Council of Florence — 22
- Council of Ephesus — 11
- Council of Constance — 6
- Second Council of Constantinople — 5
- First Vatican Council — 5
- Second Council of Lyons — 4
- First Council of Nicaea — 2
- Council of Chalcedon — 1
- Fourth Lateran Council — 1

## Regenerate

```bash
python scripts/step1/build_contrast_db.py
python scripts/step1/export_contrast_viz.py
# optional LLM (uses agent.md as system prompt):
# OPENAI_API_KEY=… python scripts/step1/build_contrast_db.py --mode llm
```
