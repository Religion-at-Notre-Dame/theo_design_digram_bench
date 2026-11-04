# Contrast database — natural-language conversion agent

Convert a **breakaway-tagged** Step 1 council locus into a contrast row:
one shared natural-language question, a Catholic answer, and the breakaway
group’s answer. Use only the linked council passage plus historically
established positions of that group. Do not invent schisms or doctrines.

## Inputs (per locus)

```json
{
  "entry_id": "string",
  "council": "string",
  "canonical_citation": "string",
  "breakaway": "string",
  "decision_summary": "string",
  "legacy_question": "string",
  "passage_text": "string"
}
```

`legacy_question` is the existing meta form (“According to …, did the council
teach …?”). Replace it; do not echo it.

## Include / exclude

**Include** only when both sides’ answers can be stated from the passage
plus well-known historical reception of that breakaway on this point,
**and** the two answers **disagree** on the question (different Yes/No or
incompatible stances). Contrast is for opposition, not shared affirmation.

**Exclude** (leave out of the contrast DB):

- Pure ceremony / envoy narrative with no contested claim
- Points both communions affirm (e.g. shared anti-Manichaean lines with no
  OO/EO/Protestant stake in *this* locus)—including cases where both would
  answer Yes (or both No) to the question as asked
- Vague umbrella tags where the passage does not pick a Reformational
  dispute (prefer keeping Trent Reform loci; drop if uncertain)
- Disciplinary process text that does not state a doctrine the breakaway
  rejects

When recoverable answers would **agree**, exclude rather than keep a
non-contrast.

### AI-filled breakaway perspectives (completion mode)

Direct primary sources will not exist for every breakaway × locus pair.
For expansion beyond the strict explicit-trace set:

- Prefer a **specific** group from `groups_catalog.json` (start/rupture year
  matched to a council within ±50 years — see
  `denomination_council_matches_50y.md`).
- An AI agent **may draft** the breakaway answer from well-known confessional
  / historical stance of that group when a citable breakaway primary text is
  missing. Mark `answer_basis: ai_historical` (or `passage+ai`) and
  `confidence: low` until reviewed.
- Still **answer the question directly** (Yes/No + positive stance). Still
  **no church or council names** in answer text.
- Do **not** invent agreement-as-contrast. If the group would affirm the same
  claim, skip the row.

Strict `contrast.jsonl` may stay higher-bar; AI fills may accumulate first in
`contrast_ai.jsonl` / `contrast_extended.jsonl` until reviewed.

**Expansion goal:** more *breakaway groups with real disagreement* — never pad
with ceremony/narrative or shared-affirmation rows (e.g. “no distinctive
doctrinal rupture”). If both sides would say the same thing, omit the row.

## Output schema (one JSON object)

```json
{
  "id": "same as entry_id",
  "question": "one natural-language interrogative, plain English, no citation prefix",
  "catholic_answer": "2–4 sentences: what the Catholic Church teaches here",
  "breakaway_group": "stable label from input.breakaway",
  "breakaway_answer": "2–4 sentences: what that group historically holds / held against this locus",
  "answer_basis": "passage | passage+history",
  "notes": "optional short caveat (umbrella label, nuance)"
}
```

Also preserve provenance fields when writing the database file:
`council`, `canonical_citation`, `record_id`, `passage_excerpt` (≤500 chars).

## How to write `question`

1. Extract the **contested claim**, not the meta-fact that a council met.
2. Ask something **both sides can answer** (doctrine, practice, or
   authority)—not “Did the council anathematize X?”
3. Prefer concrete theological wording: consubstantiality, two natures,
   Filioque, transubstantiation, seven sacraments, papal primacy, etc.
4. One sentence, end with `?`. No “According to Trent…” wrappers.
5. For **anathema / “if anyone says…”** canons: turn the *Catholic*
   teaching (the negation of the condemned error) into a direct question.
6. For **condemned articles** (Constance vs Wyclif/Hus): phrase the
   *article’s claim* as the question; Catholic answer rejects it;
   breakaway answer affirms or defends it.
7. For **creeds / definitions**: ask the central dogmatic assertion
   (e.g. is the Son consubstantial with the Father?).

### Good / bad

- Bad: “According to Trent S13 Eucharist canon 2, did the council teach Canon 2…?”
- Good: “In the Eucharist, is the whole substance of bread and wine converted into Christ’s body and blood, with only the appearances remaining?”

- Bad: “Did Constance condemn John Hus?”
- Good: “Is the holy universal church identical with the total number of those predestined to salvation?”

## How to write answers (both sides)

**Both `catholic_answer` and `breakaway_answer` must directly answer
`question`.** Lead with Yes / No / the specific alternative the question
asks for. If the answer is No (or a rejection), also state the positive
stance on the issue in a short following clause—not only the negation.

**Do not name churches or documents in either answer.** No “Catholic
Church,” “Oriental Orthodox,” “Protestant,” “Trent,” “Florence,” “Cyril’s
anathema,” etc. State the claim itself. Group identity belongs in
`breakaway_group`; citation belongs in `canonical_citation`.

- Bad: “Oriental Orthodox churches reject Chalcedon’s definition…”
- Good: “No. After the union he is confessed as one united nature of the
  Word incarnate, not ‘in two natures.’”

- Bad: “Reformation churches generally deny that the Mass is a propitiatory
  sacrifice as Trent teaches…”
- Good (to “May Masses be offered in honor of the saints?”): “No. Masses
  should not be offered in honor of the saints.”

Do **not** paste a generic group brief that could fit any locus. If the
question is about remanence, answer remanence—not a condemnation narrative.

### `catholic_answer`

- Affirm what the passage defines, decrees, or anathematizes *against*.
- Stay inside the passage’s claim; add only standard Catholic gloss needed
  for clarity (e.g. name “transubstantiation” if the text does).
- Do not argue apologetically; answer the question.

### `breakaway_answer`

Answer the same question from that group’s historical position. Use the
table only as background, not as the answer text:

| Group | Typical stake |
|-------|---------------|
| Arian churches | Deny consubstantiality / full divinity of the Son as Nicaea defined |
| Church of the East | Refuse Ephesine/Cyrilline settlement; dyophysite two-qnome christology |
| Oriental Orthodox churches | Reject Chalcedon / Leo; miaphysite; refuse Latin union terms requiring Chalcedon |
| Eastern Orthodox churches | Reject Filioque as Florence/Lyons define it; reject papal supremacy / Latin purgatory formulations |
| Wycliffites / Lollards | Affirm the condemned article or deny the condemnation at issue |
| Hussites | Affirm the condemned article or deny the condemnation at issue |
| Protestant churches | Affirm the Reformational claim Trent targets (note variety in `notes`) |
| Old Catholic churches | Deny Vatican I papal primacy / ex cathedra infallibility as defined |

- Answer in the content of the claim (“No. …”), never “Group X rejects…”.
- Umbrella labels (esp. Protestant): one-line `notes` that confessions vary.
- Never treat modern soft diplomacy as erasing the historical disagreement.

## Tone and limits

- Neutral, precise, short.
- No sneer words (“heretics,” “schismatics”) except when quoting the
  council’s own vocabulary and clearly marked as such.
- English; keep technical terms when the passage uses them.
- If the passage is bilingual/garbled OCR, repair lightly for the answers
  without changing meaning.

## Batch checklist

For each candidate breakaway entry:

1. Read full `passage_text`.
2. Decide include/exclude.
3. Draft `question` → `catholic_answer` → `breakaway_answer`.
4. Set `answer_basis` to `passage` only when both answers are explicit in
   the text; otherwise `passage+history`.
5. Emit JSON; skip excluded loci silently (count them in the run summary).
