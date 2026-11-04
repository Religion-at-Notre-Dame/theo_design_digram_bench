# Step 1 Final Report — Catholic vs Breakaway Disagreements

This report describes the **final Step 1 contrast product**: how breakaway groups were compiled, how conciliar documents were assembled into citable loci, how those resources were combined into disagreement questions (Catholic vs other), and how accuracy is marked so primary-source material can be distinguished from AI-drafted material.

| Item | Location |
|------|----------|
| Interactive viewer | [`contrast_step1.html`](contrast_step1.html) |
| Canonical rows | [`contrast_step1.jsonl`](contrast_step1.jsonl) |
| Viewer payload / stats | [`contrast_step1.json`](contrast_step1.json) |
| Rebuild | `python3 scripts/step1/build_contrast_step1.py` |

---

## 1. What the final product is

For every breakaway group on the **doctrinal match list**, the product collects **disagreement-only** questions: a shared natural-language question, a Catholic answer grounded in a council locus, and that group’s opposing answer. Shared affirmations, pure ceremony, and non-doctrinal process text are excluded.

The viewer’s **Pairing** control compares three cuts of the same dataset:

| Pairing | Meaning |
|---------|---------|
| **All loci** | Full comprehensive set (primary + family secondaries + in-window councils) |
| **Doctrinal primary only** | Questions whose council equals the group’s doctrinal primary |
| **Temporal (≤50y after)** | Questions for the temporal primary, and only if the group’s rupture is during that council or within **50 years after** it ends (not before) |

### Headline counts (current build)

| Metric | Value |
|--------|------:|
| Breakaway groups (doctrinal list) | **151** |
| Groups with ≥1 disagreement question | **151** |
| Pending (no recoverable disagreement) | **0** |
| Total contrast rows | **4594** |
| Groups whose doctrinal ≠ temporal primary | **89** |
| Temporal in-window groups (+50y after) | **71** |

---

## 2. Compiling the list of breakaway groups

### 2.1 Definition

A **breakaway** is a historically identifiable community whose lasting ecclesial separation can be tied to a citable conciliar decision (or a clear reception of one). The project excludes:

- Intra-Catholic parties and movements still treated as in communion for this benchmark
- Individuals without a lasting church body
- Vague umbrella labels that do not name a recoverable community
- Bodies listed as Catholic-aligned / non-breakaway in the catalog

### 2.2 Authoritative catalog

**Source:** [`outputs/step1/breakaways/groups_catalog.json`](../groups_catalog.json)

| Field | Role |
|-------|------|
| `id`, `name` | Stable identity |
| `broke_from`, `lineage`, `separation_degree` | Genealogy from the Catholic root |
| `rupture_year` / `approx_rupture` | Date used for council matching |
| `confidence` | `established` or `contested` |
| `status` | e.g. `extant`, `historical` |
| `disagreement` | Optional known locus (`council_locus` or summary) with citation / entry hints |

**Current size:** **118** catalog groups, all with a rupture year; **12** entries under `excluded_non_breakaways`.

Supporting scripts include catalog expansion, disagreement enrichment, and re-audit under `scripts/step1/` (e.g. `expand_groups_catalog.py`, `enrich_groups_disagreements.py`, `audit_fix_groups_catalog.py`).

### 2.3 Supplemental denominations

**Source:** [`denominations_extra.json`](denominations_extra.json)

Extra start-year denominations fill gaps not yet modeled as full catalog lineages (e.g. modern or narrowly scoped bodies). Loader rules:

- Require a `start_year`
- Skip flagged `skip` rows
- Drop duplicates of catalog name/id

**Current size:** **34** extras kept → **152** total denomination nodes before matching.

### 2.4 Exclusions

Excluded Catholic-aligned / non-breakaway bodies are recorded in the catalog and mirrored for contrast work (e.g. [`catholic_aligned_excluded.json`](catholic_aligned_excluded.json)) — **12** bodies. Examples of the policy: Eastern Catholic churches treated as in communion for this step; SSPX and similar cases listed as excluded rather than contrast targets; umbrella family labels that are not a single breakaway node.

### 2.5 Entry-level breakaway tags (corpus subset)

Separately from the 151-group match list, Step 1 also tags **individual council entries** with a `breakaway` label when a locus is historically associated with a schism:

| Artifact | Count |
|----------|------:|
| Verified Step 1 entries (`outputs/step1/entries.jsonl`) | **1760** |
| Breakaway-tagged entries (`outputs/step1/breakaways/entries.jsonl`) | **156** |
| Linked English passages (`outputs/step1/breakaways/passages.jsonl`) | **156** |

Scripts such as `clean_breakaways.py`, `refine_breakaway_labels.py`, and `compile_breakaways.py` clean labels and join tagged entries to full English council text. This **156-entry** subset is the seed for the **strict** contrast database; the **151-group** list is the coverage frame for the comprehensive final product.

### 2.6 Match list (authoritative group frame for the final product)

**Script:** `scripts/step1/match_denominations_to_councils.py`

| Output | Role |
|--------|------|
| [`denominations_by_start.json`](denominations_by_start.json) | All breakaway nodes ordered by start year |
| [`denomination_council_matches_50y.md`](denomination_council_matches_50y.md) / `.json` | **Doctrinal** pairing (authoritative for Step 1 groups) |
| [`denomination_council_matches_temporal.md`](denomination_council_matches_temporal.md) / `.json` | **Temporal** pairing (compare / filter) |

**Doctrinal matches:** **151** (1 unmatched: Priestless Old Believers, 1666 — no council within ±50y under doctrinal rules).

---

## 3. Compiling the council documents

### 3.1 Corpus layout

**Root:** `data/councils/`

| Resource | Role |
|----------|------|
| `index.json` | Document inventory (~**37** documents across **21** councils) |
| `document_catalog.json` / `coverage_status.json` | Catalog and full-vs-summary status |
| `documents/*.jsonl` (incl. Vatican II) | One citable English unit per line |

Typical record fields: `session`, `canon`, `paragraph` / `chapter`, `canonical_citation`, `text`, `text_status` (`full` / `summary` / `empty`), `source_url`, `record_id`, `language`.

Council year spans used for matching (e.g. Trent 1545–1563, Florence 1431–1445, Vatican II 1962–1965) are maintained as `COUNCIL_SPANS` in the matcher so single promulgation dates do not misplace multi-year councils.

### 3.2 Ingest and completion

Upstream scripts gather and complete English text (download from the project’s council corpus, scrape supplements, fill known gaps, annotate `text_status`). Step 1 then indexes the corpus for decision-complete coverage.

### 3.3 From documents to decision loci (entries)

Pipeline (under `scripts/step1/`):

1. **Inventory** — one planned locus per recoverable English unit (`expand_inventory.py`)
2. **Draft entries** — question + decision summary (`draft_entries.py`; heuristic or LLM)
3. **Verify** — resolve `record_id` + `canonical_citation`; set status (`verify_entries.py`)
4. **Naturalize questions** — plain-English interrogatives (`naturalize_questions.py`)
5. **Coverage report** — completeness checks

**Entry schema (essentials):** `id`, `council`, `document_abbrev`, `record_id`, `canonical_citation`, `question`, `breakaway` (or null), `decision_summary`, `status`, `draft_method`.

**Current:** **1760** verified entries; corpus treated as decision-complete for the indexed English set.

These entries are the **Catholic-side backbone** of every contrast row: even AI-filled rows cite a real `source_entry_id`, `record_id`, and `canonical_citation` from this layer.

---

## 4. Pairing groups to councils

### 4.1 Doctrinal pairing (±50 years, preference-driven)

Default window: **±50 years** around the council span (symmetric).

Primary council selection prefers **doctrinal family rupture** over pure nearest-year when known:

- Family / `broke_from` / id tokens → preferred council (e.g. Lutheran/Reformed/Baptist → Trent; Oriental Orthodox families → Chalcedon; Eastern Orthodox → Florence; Old Catholic / Vatican I refusals → Vatican I)
- Citation / `entry_id` hints on the group’s disagreement object
- Hard overrides (`FORCE_COUNCIL_BY_ID`) even outside the window (e.g. Novatianists / Melitians / Donatists → Nicaea I)

**Doctrinal primary distribution (approximate):** Trent dominates modern Protestant families; Chalcedon / Ephesus / Florence / Constance / Vatican I–II cover ancient and modern non-Protestant ruptures.

### 4.2 Temporal pairing (+50 years after only)

Temporal pairing is **forward-only**:

- Eligible councils are those the rupture falls **during or after** (never “up to 50 years before” a council)
- Distance = years after council end (0 if during the council)
- **In-window** iff years-after ≤ **50**
- Primary = nearest such prior/concurrent council

**Current:** **149** temporal matches; **71** in +50y window; **78** outside window (nearest prior still recorded for audit); **89** differ from doctrinal primary.

### 4.3 Multi-council loci in the comprehensive build

For disagreement recovery, each group is not limited to a single council. `build_contrast_step1.py` gathers:

1. Doctrinal **primary**
2. **Family secondary** councils (e.g. Protestants → Trent + Vatican I; Oriental Orthodox → Chalcedon + Constantinople II + Florence; sedevacantist lines → Vatican I + II)
3. Any council within ±50y of the group’s start year

Theme/signature loci in the AI expander can also pull entries from related councils when family tokens match. The result is multi-council disagreement coverage per group where recoverable.

---

## 5. Forming the disagreement questions

### 5.1 Design rule (contrast, not affirmation)

Rules are summarized in [`agent.md`](agent.md):

- One shared natural-language **question**
- A **Catholic** answer and a **breakaway** answer
- Include only when both sides can be stated **and they disagree**
- Exclude ceremony/narrative without a contested claim, shared Yes/Yes (or No/No) affirmations, vague umbrella tags, and pure discipline without a rejected doctrine

### 5.2 Strict path (primary-source / explicit-trace)

**Builder:** `scripts/step1/build_contrast_db.py`  
**Seed DB:** [`contrast.jsonl`](contrast.jsonl) (~**82** curated rows) + [`contrast.html`](contrast.html)

Strict rows are built from breakaway-tagged entries + linked passages. Answers use `answer_basis: passage+history`: the Catholic side from the council text; the breakaway side from established historical reception of that group on that locus — not free invention.

Include/exclude filtering removes non-disagreements. Hand-tuned Yes/No anchors may live in `direct_answers.json`.

### 5.3 Cloning (umbrella → specific catalog names)

When a catalog group lacks an exact-name strict row but an umbrella label does (e.g. “Oriental Orthodox churches” → Ethiopian / Eritrean / Malankara), the final builder **clones** those strict rows onto the specific group, retitles `breakaway_group`, and marks **medium** confidence with a note that the row was cloned from the umbrella label.

**Current:** **7** groups on the cloned path; **44** medium-confidence rows.

### 5.4 AI / heuristic fills (coverage completion)

**Script:** `scripts/step1/expand_contrast_ai.py` (and assembly inside `build_contrast_step1.py`)

Direct primary sources do not exist for every breakaway × locus pair. For remaining recoverable loci:

| Side | Source |
|------|--------|
| **Question** | Prefer entry natural-language question / decision claim |
| **Catholic answer** | Prefer existing strict Q&A for the same entry; else derive from entry `decision_summary` / verified Catholic teaching at that citation |
| **Breakaway answer** | Drafted from well-known confessional / historical stance templates for that family (`answer_basis: ai_historical`) |
| **Citation** | Always a real council entry (`canonical_citation`, `record_id`, `source_entry_id`, passage excerpt when available) |

Rows where Catholic and breakaway polarity would **agree** are dropped. AI fills are explicitly **low confidence** until reviewed and promoted.

### 5.5 Final assembly order (`build_contrast_step1.py`)

For each doctrinal match group:

1. Attach exact-name **strict** rows → `tier: strict`, `confidence: high`
2. Else attach **cloned** umbrella strict rows → `tier: strict`, `confidence: medium`
3. Add **AI fills** for every remaining recoverable locus across primary + secondaries + in-window councils → `tier: ai`, `confidence: low`

Then write `contrast_step1.jsonl`, JSON payload, HTML viewer, and this product’s notes.

---

## 6. Accuracy, flags, and provenance

### 6.1 Per-row schema (final product)

```json
{
  "id": "step1:{group_id}:{entry_id}",
  "question": "...",
  "catholic_answer": "...",
  "breakaway_group": "...",
  "breakaway_answer": "...",
  "council": "...",
  "canonical_citation": "...",
  "record_id": "...",
  "source_entry_id": "...",
  "passage_excerpt": "...",
  "confidence": "high | medium | low",
  "tier": "strict | ai",
  "answer_basis": "passage+history | ai_historical",
  "draft_method": "heuristic | ai_historical",
  "group_id": "...",
  "start_year": 0,
  "match_primary_council": "...",
  "match_primary_reason": "...",
  "notes": "..."
}
```

### 6.2 Flag meanings

| Flag | Meaning | Trust for breakaway answer |
|------|---------|----------------------------|
| `tier: strict` + `confidence: high` + `answer_basis: passage+history` | Curated explicit-trace contrast against passage + established history | **Highest** — primary-source path |
| `tier: strict` + `confidence: medium` | Cloned from an umbrella strict label onto a more specific catalog group | **High lineage, medium specificity** — review group naming |
| `tier: ai` + `confidence: low` + `answer_basis: ai_historical` | Catholic side citation-grounded; breakaway side AI/heuristic-drafted | **Lowest** — needs human review before treating as authoritative |
| Group `status: strict` | Group has ≥1 high-confidence strict row | Mixed row quality possible; has a curated core |
| Group `status: cloned` | Covered via umbrella clone, no exact-name strict set | Medium |
| Group `status: ai` | AI-only coverage | Low until reviewed |
| Group `status: pending` | No recoverable disagreement row | Empty (currently none) |

### 6.3 What comes from primary sources vs AI

**Always from the council corpus / verified entries (both strict and AI rows):**

- Council name
- `canonical_citation`
- `record_id` / `source_entry_id`
- Passage excerpt (when joined)
- The fact that a Catholic teaching locus exists at that citation

**From primary-source / curated historical work (strict + clones):**

- Breakaway answer text aligned to passage + reception
- Higher bar include/exclude decisions in `agent.md`

**From AI / heuristic completion (vast majority of rows):**

- Breakaway answer wording and Yes/No stance templates
- Expansion across many loci per group so the match list is comprehensively populated

**Catholic answer text on AI rows** is still derived from verified entry material (or reused strict Catholic answers), not invented councils — but it is not always the same hand-tuned prose as the strict DB.

### 6.4 Current accuracy mix

| Measure | Count | Share of rows |
|---------|------:|--------------:|
| Total rows | **4594** | 100% |
| `tier: ai` / `confidence: low` / `ai_historical` | **4487** | ~97.7% |
| `tier: strict` | **107** | ~2.3% |
| … of which `confidence: high` | **63** | ~1.4% |
| … of which `confidence: medium` (cloned) | **44** | ~1.0% |

| Group status | Groups |
|--------------|-------:|
| `ai` | **128** |
| `strict` | **16** |
| `cloned` | **7** |
| `pending` | **0** |

**Interpretation for supervisors / reviewers:** treat the product as a **coverage map of disagreement loci** with a small curated core. Use `confidence` / `tier` / `answer_basis` to filter for audit. Do not treat low-confidence AI breakaway answers as equivalent to passage-grounded strict rows.

### 6.5 Recommended reading order for accuracy review

1. Filter or sort to `confidence: high` (and then `medium`)
2. Spot-check AI rows where the doctrinal vs temporal pairing differs (pairing filter)
3. Promote reviewed AI rows into the strict DB (or demote/remove false disagreements)
4. Re-run `build_contrast_step1.py`

---

## 7. Deliverables and how to regenerate

### 7.1 Final package

| File | Role |
|------|------|
| [`contrast_step1.html`](contrast_step1.html) | Interactive Q&A viewer (Pairing: All / Doctrinal / Temporal) |
| [`contrast_step1.jsonl`](contrast_step1.jsonl) | Canonical contrast rows |
| [`contrast_step1.json`](contrast_step1.json) | Stats + viewer payload |
| [`STEP1_FINAL.md`](STEP1_FINAL.md) | Short product notes |
| [`STEP1_FINAL_REPORT.md`](STEP1_FINAL_REPORT.md) | This report |
| [`denomination_council_matches_50y.md`](denomination_council_matches_50y.md) | Doctrinal group↔council list |
| [`denomination_council_matches_temporal.md`](denomination_council_matches_temporal.md) | Temporal group↔council list |

### 7.2 Intermediate / upstream artifacts

| File | Role |
|------|------|
| `contrast.jsonl` / `contrast.html` | Strict curated DB (~82) |
| `contrast_ai.jsonl` | Doctrinal AI expansion scratch |
| `match_contrast.html` / `match_contrast_temporal.html` | Earlier match-list viewers |
| `outputs/step1/entries.jsonl` | Verified council loci (1760) |
| `outputs/step1/breakaways/groups_catalog.json` | Breakaway catalog |
| `data/councils/` | English council corpus |

### 7.3 One-command rebuild

```bash
python3 scripts/step1/build_contrast_step1.py
```

This rewrites doctrinal and temporal match outputs, reassembles strict / cloned / AI rows, and regenerates the HTML viewer.

---

## 8. End-to-end pipeline (compact)

```
data/councils (English documents)
        ↓ inventory → draft → verify → naturalize
outputs/step1/entries.jsonl  (1760 verified loci)
        ↓ breakaway clean / refine / compile
breakaways entries + passages  (156 tagged)
        ↓ strict contrast rules (agent.md)
contrast.jsonl  (curated disagreements)

groups_catalog (118) + denominations_extra (34)
        − excluded_non_breakaways (12)
        ↓ match_denominations_to_councils
doctrinal matches (151)  |  temporal matches (149, +50y-after window)

        ↓ build_contrast_step1
            strict → clone → AI fills (disagreement-only, multi-council)
contrast_step1.jsonl / .json / .html  (4594 rows, 151 groups)
```

---

## 9. Summary for evaluation

1. **Breakaway list** — catalog lineages + start-year extras − Catholic-aligned exclusions → doctrinal match list of **151** groups.
2. **Council resources** — English conciliar corpus → **1760** verified decision entries with citations; **156** breakaway-tagged loci seed the strict path.
3. **Questions** — disagreement-only Catholic vs group Q&As, multi-council where recoverable; Pairing filter exposes doctrinal vs temporal (+50y after) cuts.
4. **Accuracy** — Catholic citations are corpus-grounded throughout; breakaway answers are **mostly AI/heuristic (`low`)** with a small **strict (`high`)** and **cloned (`medium`)** core. Flags `tier`, `confidence`, and `answer_basis` are the operational accuracy measures for review and promotion.
