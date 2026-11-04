# Theological Design Diagram Bench

A two-step pattern for mapping what the Catholic Church has decided, where those decisions were contested, and how moral teaching developed afterward. Step 1 covers the ecumenical councils and their documents. Step 2 covers Catholic Social Teaching (CST) and the papal encyclicals.

The two steps are deliberately ordered by how much human judgment they need. Step 1 is largely factual and should be tractable for a model working from primary texts. Step 2 is not, and is expected to take longer and require review by someone formed in the Catholic tradition.

## Step 1 — Mapping the Councils

Map each church council and each of its documents to something that was decided. Then look specifically for the points where there was disagreement, and for the cases where a group broke away from the Church over that decision.

**Required output for each entry:**

- A sentence phrased as a question, rooted in a specific paragraph or section of a council document. The citation has to be precise enough that a reader can go find the passage — canon, session, chapter, or paragraph number, not just the document name.
- The religion, church, or movement that broke off, where one applies. Many decisions have no schism attached to them; leave the field empty rather than inventing a connection.

### Breakaway group (formal definition)

A **breakaway group**, for Step 1, is a **historically identifiable community** that, in lasting consequence of rejecting (or being rejected over) a **specific conciliar decision**, ceased to share **full communion** with the Catholic Church as that communion was understood by the council’s reception—or never entered / refused that communion after the decision—such that the group’s **distinct ecclesial identity** is thereafter marked by that rupture.

**Necessary conditions (all must hold):**

1. **Communal, not individual** — A named people, church, order, or movement with ongoing existence (or clear successor identity), not a lone theologian or temporary faction.
2. **Tied to a decision** — The rupture is historically linked to a **citable conciliar act** (creed, definition, canon, decree), not only to vague “atmosphere” or later politics alone.
3. **Ecclesial separation** — Outcome is loss or refusal of **full communion** / recognition as remaining within the same visible Church, not merely contested opinion inside it.
4. **Durable** — The separation is not a short-lived riot or retracted protest; it leaves a **recognizable tradition** (even if later reunions or fragments occur).

**Not a breakaway group** (leave `breakaway` empty):

- Intra-Catholic schools or parties that remained in communion.
- Individuals condemned as heretics without a lasting separate church.
- Later movements only loosely associated with a text (do not back-project).
- Groups that reject a council’s *implementation* while claiming the same communion (unless historians treat them as a distinct communion—and then mark that judgment as contested).
- Undifferentiated “Protestantism” unless the locus is actually about a Reformational break tied to that decree (prefer precise labels when history supports them).

**One-line test:** *If this council locus had never been decided that way, would this community’s lasting separation from Catholic communion still be the same story?* If **no** → candidate breakaway. If **yes** or **unclear** → leave empty.

Normalize labels in the dataset with `python scripts/step1/clean_breakaways.py` (clears Cathars / Iconoclasts / Monothelites / contested SSPX tags; renames kept groups to stable names).

**Optional:** a visualization. Councils over time, decisions branching into the groups that rejected them, and documents linked to the questions they settle are all reasonable things to draw.

**On automation:** this step is factual, so a model should do well at it with the source documents in hand. Spot-check the citations anyway — a plausible-looking paragraph number that points at the wrong text is the most likely failure mode.

### Step 1 pipeline (decision-complete)

Inventory-driven draft + citation verify. Deliverable: verified lines in [`outputs/step1/entries.jsonl`](outputs/step1/entries.jsonl).

```bash
# Rebuild inventory = one decision per English council locus (full corpus)
python scripts/step1/expand_inventory.py --min-chars 0

# Draft (heuristic by default; LLM if OPENAI_API_KEY / STEP1_API_KEY is set)
python scripts/step1/draft_entries.py

python scripts/step1/verify_entries.py --write-status
python scripts/step1/clean_breakaways.py  # apply formal breakaway definition
python scripts/step1/refine_breakaway_labels.py  # precise degree-1 labels (Armenian/Coptic/Lutheran…)
python scripts/step1/naturalize_questions.py     # heuristic NL questions (or draft --mode llm if keyed)
python scripts/step1/compile_breakaways.py  # breakaway-only subset -> outputs/step1/breakaways/
python scripts/step1/build_contrast_db.py   # Catholic vs breakaway contrast rows
python scripts/step1/export_contrast_viz.py
python scripts/step1/coverage_report.py   # also checks every corpus record_id is covered
python scripts/step1/export_graph.py      # schism-only Mermaid map
python scripts/step1/export_overview.py   # chronological HTML overview of all councils
python scripts/step1/export_groups_viz.py # lineage catalog HTML
```

- Coverage checklist: [`scripts/step1/coverage_inventory.json`](scripts/step1/coverage_inventory.json) — **comprehensive** (1:1 with English loci in `data/councils/`).
- Current verified set: **1760** entries in [`outputs/step1/entries.jsonl`](outputs/step1/entries.jsonl) (`corpus_complete=True`).
- Breakaway subset: **148** entries in [`outputs/step1/breakaways/`](outputs/step1/breakaways/) (questions + full passage text).
- Contrast DB: **74** explicit-trace rows in [`outputs/step1/breakaways/contrast/`](outputs/step1/breakaways/contrast/).
- Degree-1 coverage notes: [`outputs/step1/breakaways/groups_degree1_coverage.md`](outputs/step1/breakaways/groups_degree1_coverage.md).
- Only `status: verified` entries count; the verifier resolves `record_id` and matches `canonical_citation` to the corpus.
- Optional: re-draft with `draft_entries.py --mode llm` when `OPENAI_API_KEY` / `STEP1_API_KEY` is set (same citations).
- See [`outputs/step1/README.md`](outputs/step1/README.md) for the entry schema.

## Step 2 — Mapping Moral Teaching from CST Documents and Papal Encyclicals

Same shape as Step 1: a question sentence anchored to a specific paragraph, tied to the document it comes from. The difference is the subject matter. These texts teach morally rather than settle points of doctrine by canon, so the mapping requires reading for development and emphasis instead of extracting a decision.

Expect this step to take longer. A model can draft it, but the result needs judgment applied on top: whether a passage is actually teaching what the question implies, how it relates to earlier and later encyclicals, and where the Church's position developed rather than reversed.

## Setup

Python 3.13, with the CST dataset vendored as a git submodule and council documents extracted under `data/councils/`.

```bash
git clone --recurse-submodules <this-repo>
cd theo_design_digram_bench

# if you already cloned without --recurse-submodules
git submodule update --init

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# refresh council extract from the upstream release (optional; files are already present)
python scripts/download_council_documents.py
```

## Source Documents

### Step 1 — Councils

Council texts come from [GibbilyGooo/catholic-doctrine-magisterium-rag-corpus](https://github.com/GibbilyGooo/catholic-doctrine-magisterium-rag-corpus) v1.0.0, a citation-preserving Magisterium corpus. `scripts/download_council_documents.py` pulls the release zip (SHA-256 verified), keeps only the council slice, and writes it to `data/councils/`.

**29 documents from the upstream release**, plus **8 councils** scraped from Papal Encyclicals Online (Tanner) into the same JSONL schema — **37 document files**, covering all 21 Catholic ecumenical councils. English records carry `session`, `canon`, `paragraph`, `chapter`, `canonical_citation`, `text`, and `source_url`.

```python
import json
from pathlib import Path

index = json.load(open("data/councils/index.json"))
print(index["count"], "council documents; missing:", index["missingCouncils"])

# Example: Trent Session 5, Original Sin, canon 1
for line in Path("data/councils/documents/Trent.jsonl").open():
    record = json.loads(line)
    if record.get("language") == "en" and record.get("session") == 5 and record.get("canon") == 1:
        print(record["canonical_citation"])
        print(record["text"][:200])
        break
```

Prefer `canonical_citation` when writing the required question sentence (e.g. `Trent S5 Original Sin canon 1`, `LG 8`, `Lateran I canon 1`, `Constance S15 […]`).

Supplemental scrapes (Constantinople IV, Lateran I–III, Lyons I, Vienne, Constance, Lateran V) come from [papalencyclicals.net/councils](https://www.papalencyclicals.net/councils) via `scripts/scrape_missing_councils.py`. Refresh both layers with:

```bash
python scripts/download_council_documents.py   # also re-runs the scrape
# or just:
python scripts/scrape_missing_councils.py
```

See `data/councils/README.md` and `data/councils/COPYRIGHT_AND_SOURCES.md` for layout and rights.

### Step 2 — CST / Encyclicals

CST documents come from [Religion-at-Notre-Dame/catholic_text_json](https://github.com/Religion-at-Notre-Dame/catholic_text_json), pinned as a submodule at `data/catholic_text_json`. Use it as the corpus for Step 2 rather than re-scraping the texts. Three collections live under `data/catholic_text_json/data/`: `encyclicals`, `bible-nabre-json-dataset`, and `catholicism-in-json`.

The encyclicals are the relevant ones for Step 2 — 211 English documents under `encyclicals/en/`, with `encyclicals/index.json` listing every document with its pope, publication date, paragraph count, and Vatican source URL. Each document is a JSON object carrying `title`, `pope`, `publicationDate`, `vaticanUrl`, and a `paragraphs` list of `{paragraph, text}` records:

```python
import json

index = json.load(open("data/catholic_text_json/data/encyclicals/index.json"))
doc = json.load(open("data/catholic_text_json/data/encyclicals/en/rerum-novarum.json"))
print(doc["title"], doc["paragraphCount"])
```

**A caveat that affects the required output:** the `paragraph` field is `null` for about 27% of paragraphs (8,268 of 11,306 are numbered), and 4 of the 211 documents have no paragraph numbers at all. Opening sections in particular tend to be unnumbered — in *Rerum Novarum* the first paragraph is `null` and numbering starts at 2. Entries drawn from unnumbered text need a different anchor, such as a quoted phrase plus the document slug.
