#!/usr/bin/env python3
"""Build the final Step 1 contrast product (doctrinal, comprehensive).

Vision:
  For every breakaway group in denomination_council_matches_50y (doctrinal),
  produce disagreement question(s) with a Catholic answer + breakaway answer
  and a citation for the Catholic source.

Outputs (outputs/step1/breakaways/contrast/):
  contrast_step1.jsonl   — canonical rows
  contrast_step1.html    — Q&A viewer (group → questions)
  contrast_step1.json    — viewer payload / summary stats
  STEP1_FINAL.md         — product description
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import expand_contrast_ai as eai  # noqa: E402
import match_denominations_to_councils as matcher  # noqa: E402

OUT_DIR = ROOT / "outputs/step1/breakaways/contrast"
STRICT = OUT_DIR / "contrast.jsonl"
ENTRIES = ROOT / "outputs/step1/entries.jsonl"
PASSAGES = ROOT / "outputs/step1/breakaways/passages.jsonl"
CATALOG = matcher.CATALOG
EXTRA = matcher.EXTRA

# Normalized catalog name → strict breakaway_group label (clone rows, retitle)
STRICT_ALIASES: dict[str, str] = {
    "church of the east assyrian church of the east": "Church of the East",
    "ancient church of the east": "Church of the East",
    "old catholic churches union of utrecht": "Old Catholic churches",
    "malankara orthodox syrian church": "Oriental Orthodox churches",
    "ethiopian orthodox tewahedo church": "Oriental Orthodox churches",
    "jacobite syrian christian church malankara": "Oriental Orthodox churches",
    "eritrean orthodox tewahedo church": "Oriental Orthodox churches",
}

# Additional councils (beyond primary) where a family often has real Catholic disagreement.
# Shared affirmation (e.g. most Protestants on Nicaea) is filtered out by polarity check.
FAMILY_EXTRA_COUNCILS: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (
        (
            "luther",
            "reformed",
            "calvin",
            "presbyterian",
            "anabaptist",
            "baptist",
            "mennonite",
            "hutterite",
            "anglican",
            "episcopal",
            "methodist",
            "wesley",
            "nazarene",
            "holiness",
            "pentecostal",
            "assemblies",
            "advent",
            "restoration",
            "brethren",
            "congregational",
            "separatist",
            "quaker",
            "friend",
            "salvation",
            "moravian",
            "hussite",
            "waldens",
            "vineyard",
            "calvary",
            "charismatic",
            "foursquare",
            "covenant",
            "disciple",
        ),
        ("Council of Trent", "First Vatican Council"),
    ),
    (
        ("unitarian", "oneness", "arian", "jehovah", "latter-day", "lds", "iglesia"),
        ("First Council of Nicaea", "Council of Trent", "First Vatican Council"),
    ),
    (
        ("eastern-orthodox", "old-believer", "old-calendar", "rocor", "doukhobor", "molokan"),
        ("Council of Florence", "Second Council of Lyons", "First Vatican Council"),
    ),
    (
        (
            "coptic",
            "armenian",
            "syriac",
            "ethiopian",
            "eritrean",
            "malankara",
            "oriental",
            "mar-thoma",
        ),
        (
            "Council of Chalcedon",
            "Second Council of Constantinople",
            "Council of Florence",
        ),
    ),
    (
        ("church-of-the-east", "assyrian", "chaldean-syrian", "nestor"),
        ("Council of Ephesus", "Second Council of Constantinople"),
    ),
    (
        (
            "old-catholic",
            "polish-national",
            "mariavite",
            "aglipayan",
            "philippine-independent",
            "petite-eglise",
        ),
        ("First Vatican Council",),
    ),
    (
        ("sedevacant", "palmarian", "chinese-catholic-patriotic", "brazilian-catholic"),
        ("First Vatican Council", "Second Vatican Council"),
    ),
    (("novatian", "melitian", "donatist"), ("First Council of Nicaea",)),
    (("wyclif", "lollard"), ("Council of Constance", "Council of Trent")),
]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _load_passages() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in load_jsonl(PASSAGES):
        eid = p.get("entry_id") or p.get("id")
        text = p.get("text") or ""
        if eid and text:
            out[eid] = text
    return out


def _excerpt(text: str, n: int = 3, max_chars: int = 500) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    s = " ".join(parts[:n])
    return s if len(s) <= max_chars else s[: max_chars - 1].rstrip() + "…"


def _row_from_strict(r: dict, *, group_name: str, group_id: str, match: dict) -> dict:
    return {
        "id": f"step1:{group_id}:{r.get('id') or r.get('source_entry_id')}",
        "question": r["question"],
        "catholic_answer": r["catholic_answer"],
        "breakaway_group": group_name,
        "breakaway_answer": r["breakaway_answer"],
        "answer_basis": r.get("answer_basis") or "passage+history",
        "confidence": "high",
        "tier": "strict",
        "council": r.get("council") or match["primary_council"],
        "canonical_citation": r.get("canonical_citation") or "",
        "record_id": r.get("record_id") or "",
        "source_entry_id": r.get("source_entry_id") or r.get("id") or "",
        "passage_excerpt": r.get("passage_excerpt") or "",
        "notes": r.get("notes") or "",
        "group_id": group_id,
        "start_year": match["start_year"],
        "match_primary_council": match["primary_council"],
        "match_primary_reason": match.get("primary_reason") or "doctrinal",
        "draft_method": r.get("draft_method") or "heuristic",
    }


def _council_disagreement_locus_ids(
    council: str,
    *,
    strict_rows: list[dict],
) -> list[str]:
    """Loci on this council already known to support Catholic–breakaway contrast."""
    seen: set[str] = set()
    out: list[str] = []
    for sid in eai.SIGNATURE_LOCI.get(council, []):
        if sid not in seen:
            out.append(sid)
            seen.add(sid)
    for r in strict_rows:
        if (r.get("council") or "") != council:
            continue
        eid = r.get("source_entry_id") or r.get("id")
        if eid and eid not in seen:
            out.append(eid)
            seen.add(eid)
    return out


def _councils_for_group(
    group: dict,
    match: dict,
    by_id: dict,
    *,
    all_councils: list[dict],
    window: int = 50,
) -> list[str]:
    """Primary + family secondary + in-window councils (multi-council disagreements)."""
    ordered: list[str] = []
    seen: set[str] = set()

    def _add(name: str | None) -> None:
        if not name or name in seen:
            return
        ordered.append(name)
        seen.add(name)

    _add(match.get("primary_council"))
    fam = eai._family_blob(group, by_id)
    for keys, councils in FAMILY_EXTRA_COUNCILS:
        if eai._any_token(fam, keys):
            for c in councils:
                _add(c)

    y = match.get("start_year")
    if y is not None:
        for c in all_councils:
            dist = matcher._year_distance(y, c["year_start"], c["year_end"])
            if dist <= window:
                _add(c["council"])

    return ordered


def _candidate_loci(
    councils: list[str],
    group: dict,
    entries_by_id: dict,
    entries_by_council: dict,
    by_id: dict,
    *,
    strict_rows: list[dict],
) -> list[dict]:
    """Recoverable disagreement loci across all candidate councils for this group."""
    seen: set[str] = set()
    out: list[dict] = []
    council_set = set(councils)

    def _add(eid: str) -> None:
        e = entries_by_id.get(eid)
        if not e or e["id"] in seen:
            return
        cname = e.get("council") or ""
        if cname not in council_set:
            return
        out.append(e)
        seen.add(e["id"])

    fam = eai._family_blob(group, by_id)
    # Theme loci may legitimately sit on a non-primary council
    for keys, locus_ids in eai.THEME_LOCI:
        if eai._any_token(fam, keys):
            for lid in locus_ids:
                e = entries_by_id.get(lid)
                if e:
                    council_set.add(e.get("council") or "")
                    _add(lid)

    for council in councils:
        first = eai._pick_locus(
            council, group, entries_by_id, entries_by_council, by_id
        )
        if first:
            _add(first["id"])
        for sid in _council_disagreement_locus_ids(council, strict_rows=strict_rows):
            _add(sid)

    return out


def _generate_ai_rows(
    *,
    group: dict,
    match: dict,
    entries_by_id: dict,
    entries_by_council: dict,
    by_id: dict,
    strict_by_id: dict,
    strict_rows: list[dict],
    passages: dict[str, str],
    already_entry_ids: set[str],
    all_councils: list[dict],
) -> list[dict]:
    """One disagreement row per recoverable locus across all relevant councils."""
    councils = _councils_for_group(
        group, match, by_id, all_councils=all_councils, window=50
    )
    rows: list[dict] = []
    seen_q: set[str] = set()
    for entry in _candidate_loci(
        councils,
        group,
        entries_by_id,
        entries_by_council,
        by_id,
        strict_rows=strict_rows,
    ):
        eid = entry["id"]
        if eid in already_entry_ids:
            continue
        council = entry.get("council") or match["primary_council"]
        question, catholic = eai._catholic_from_entry(entry, strict_by_id)
        if not question or not catholic:
            continue
        q_key = _norm(question)
        if q_key in seen_q:
            continue
        breakaway_ans = eai._ai_breakaway_answer(group, question, council, by_id)
        if not re.match(r"(?i)^(yes|no)\b", breakaway_ans):
            breakaway_ans = "No. " + breakaway_ans
        c_lead = re.match(r"(?i)^(yes|no)\b", catholic or "")
        b_lead = re.match(r"(?i)^(yes|no)\b", breakaway_ans)
        if c_lead and b_lead and c_lead.group(1).lower() == b_lead.group(1).lower():
            continue  # shared affirmation — not a disagreement
        seen_q.add(q_key)
        already_entry_ids.add(eid)
        text = passages.get(eid) or ""
        rows.append(
            {
                "id": f"step1:{group['id']}:{eid}",
                "question": question,
                "catholic_answer": catholic,
                "breakaway_group": group["name"],
                "breakaway_answer": breakaway_ans,
                "answer_basis": "ai_historical",
                "confidence": "low",
                "tier": "ai",
                "council": council,
                "canonical_citation": entry.get("canonical_citation") or "",
                "record_id": entry.get("record_id") or "",
                "source_entry_id": eid,
                "passage_excerpt": _excerpt(text),
                "notes": (
                    f"Doctrinal AI fill for `{group['id']}` @ {council} "
                    f"(start {match['start_year']}; primary={match['primary_council']})."
                ),
                "group_id": group["id"],
                "start_year": match["start_year"],
                "match_primary_council": match["primary_council"],
                "match_primary_reason": match.get("primary_reason") or "doctrinal",
                "draft_method": "ai_historical",
            }
        )
    return rows


def build() -> dict:
    denominations, aligned, meta = matcher.collect_denominations(CATALOG, EXTRA)
    by_id = meta["by_id"]
    councils = matcher.load_councils(matcher.COUNCILS_INDEX)
    matches, unmatched = matcher.build_matches(
        denominations, councils, by_id, window=50
    )
    temporal_matches, temporal_unmatched = matcher.build_matches_temporal(
        denominations, councils, by_id, window=50
    )
    stats_common = {k: v for k, v in meta.items() if k != "by_id"}
    matcher.write_outputs(
        out_dir=OUT_DIR,
        denominations=denominations,
        aligned=aligned,
        matches=matches,
        unmatched=unmatched,
        stats=stats_common,
        window=50,
        mode="doctrinal",
        write_denominations=True,
    )
    matcher.write_outputs(
        out_dir=OUT_DIR,
        denominations=denominations,
        aligned=aligned,
        matches=temporal_matches,
        unmatched=temporal_unmatched,
        stats=stats_common,
        window=50,
        mode="temporal",
        write_denominations=False,
    )
    temporal_by_id = {m["group_id"]: m for m in temporal_matches}

    strict_rows = load_jsonl(STRICT)
    strict_by_name: dict[str, list[dict]] = {}
    strict_by_id = {r["id"]: r for r in strict_rows}
    for r in strict_rows:
        strict_by_name.setdefault(_norm(r["breakaway_group"]), []).append(r)

    entries = load_jsonl(ENTRIES)
    entries_by_id = {e["id"]: e for e in entries}
    entries_by_council: dict[str, list] = {}
    for e in entries:
        entries_by_council.setdefault(e.get("council") or "", []).append(e)
    passages = _load_passages()

    out_rows: list[dict] = []
    group_stats: list[dict] = []
    n_pending = 0

    for m in sorted(matches, key=lambda x: (x["start_year"], x["group_name"])):
        gid = m["group_id"]
        g = by_id[gid]
        name = g["name"]
        nk = _norm(name)

        rows: list[dict] = []
        covered_entry_ids: set[str] = set()

        # 1) Exact strict name
        if nk in strict_by_name:
            for r in strict_by_name[nk]:
                rows.append(_row_from_strict(r, group_name=name, group_id=gid, match=m))
                covered_entry_ids.add(r.get("source_entry_id") or r.get("id") or "")
        else:
            # 2) Alias → clone umbrella strict rows under this group’s name
            alias = STRICT_ALIASES.get(nk)
            if alias and _norm(alias) in strict_by_name:
                for r in strict_by_name[_norm(alias)]:
                    cloned = _row_from_strict(
                        r, group_name=name, group_id=gid, match=m
                    )
                    cloned["notes"] = (
                        (cloned.get("notes") or "")
                        + f" Cloned from strict label `{alias}` for catalog group."
                    ).strip()
                    cloned["confidence"] = "medium"
                    rows.append(cloned)
                    covered_entry_ids.add(r.get("source_entry_id") or r.get("id") or "")

        # 3) Comprehensive AI fills: every recoverable disagreement locus on
        #    the doctrinal council not already covered by strict/clone rows.
        covered_entry_ids.discard("")
        rows.extend(
            _generate_ai_rows(
                group=g,
                match=m,
                entries_by_id=entries_by_id,
                entries_by_council=entries_by_council,
                by_id=by_id,
                strict_by_id=strict_by_id,
                strict_rows=strict_rows,
                passages=passages,
                already_entry_ids=covered_entry_ids,
                all_councils=councils,
            )
        )

        if not rows:
            n_pending += 1
            group_stats.append(
                {
                    "group_id": gid,
                    "group_name": name,
                    "start_year": m["start_year"],
                    "primary_council": m["primary_council"],
                    "status": "pending",
                    "n_questions": 0,
                }
            )
            continue

        out_rows.extend(rows)
        tiers = {r["tier"] for r in rows}
        confs = {r.get("confidence") for r in rows}
        if "strict" in tiers and "high" in confs:
            status = "strict"
        elif "medium" in confs:
            status = "cloned"
        else:
            status = "ai"
        councils_used = sorted({r.get("council") or "" for r in rows if r.get("council")})
        group_stats.append(
            {
                "group_id": gid,
                "group_name": name,
                "start_year": m["start_year"],
                "primary_council": m["primary_council"],
                "councils_cited": councils_used,
                "n_councils": len(councils_used),
                "status": status,
                "n_questions": len(rows),
            }
        )

    return {
        "rows": out_rows,
        "groups": group_stats,
        "n_match_groups": len(matches),
        "n_pending": n_pending,
        "n_rows": len(out_rows),
        "n_groups_with_questions": sum(1 for g in group_stats if g["n_questions"]),
        "by_tier": dict(Counter(r["tier"] for r in out_rows)),
        "by_confidence": dict(Counter(r["confidence"] for r in out_rows)),
        "by_council": dict(Counter(r["council"] for r in out_rows).most_common()),
        "by_group_status": dict(Counter(g["status"] for g in group_stats)),
        "temporal_by_id": temporal_by_id,
    }


def write_markdown(summary: dict, pending: list[dict]) -> str:
    lines = [
        "# Step 1 final contrast product",
        "",
        "For **every** breakaway group in the doctrinal match list, **all recoverable**",
        "disagreement questions across relevant councils (primary + family secondaries +",
        "in-window councils). Shared affirmations are dropped. Each row cites its Catholic locus.",
        "",
        "The HTML viewer’s **Pairing** filter compares:",
        "- **All loci** — full comprehensive set (default)",
        "- **Doctrinal primary only** — questions whose council = doctrinal primary",
        "- **Temporal (≤50y after council) only** — rupture during or ≤50y after council end "
        "(not before); questions whose council = that temporal primary",
        "",
        "## Counts",
        "",
        f"- Breakaway groups (doctrinal list): **{summary['n_match_groups']}**",
        f"- Groups with ≥1 question: **{summary['n_groups_with_questions']}**",
        f"- Pending (no recoverable disagreement yet): **{summary['n_pending']}**",
        f"- Total contrast rows: **{summary['n_rows']}**",
        f"- By tier: `{summary['by_tier']}`",
        f"- By confidence: `{summary['by_confidence']}`",
        "",
        "## Files",
        "",
        "| File | Role |",
        "|------|------|",
        "| `contrast_step1.jsonl` | Canonical Step 1 contrast rows |",
        "| `contrast_step1.html` | Interactive Q&A viewer (Pairing: All / Doctrinal / Temporal) |",
        "| `STEP1_FINAL_REPORT.md` | Full method + accuracy report |",
        "| `denomination_council_matches_50y.md` | Doctrinal group↔council list |",
        "| `denomination_council_matches_temporal.md` | Temporal (nearest-council) list |",
        "",
        "## Regenerate",
        "",
        "```bash",
        "python3 scripts/step1/build_contrast_step1.py",
        "```",
        "",
        "## Schema (per row)",
        "",
        "```json",
        "{",
        '  "question": "...",',
        '  "catholic_answer": "...",',
        '  "breakaway_group": "...",',
        '  "breakaway_answer": "...",',
        '  "council": "...",',
        '  "canonical_citation": "...",',
        '  "record_id": "...",',
        '  "source_entry_id": "...",',
        '  "passage_excerpt": "...",',
        '  "confidence": "high|medium|low",',
        '  "tier": "strict|ai"',
        "}",
        "```",
        "",
    ]
    if pending:
        lines.extend(["## Pending groups", ""])
        for g in pending:
            lines.append(
                f"- **{g['group_name']}** ({g['start_year']}) → {g['primary_council']}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    result = build()
    rows = result["rows"]
    pending = [g for g in result["groups"] if g["status"] == "pending"]

    jsonl_path = args.out_dir / "contrast_step1.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Viewer payload: group-first like match_contrast
    import export_match_contrast_viz as viz

    # Adapt to viz payload shape
    by_gid = {g["group_id"]: g for g in result["groups"]}
    groups_payload = []
    rows_by_gid: dict[str, list] = {}
    for r in rows:
        rows_by_gid.setdefault(r["group_id"], []).append(
            {
                "id": r["id"],
                "tier": r["tier"],
                "confidence": r["confidence"],
                "question": r["question"],
                "catholic_answer": r["catholic_answer"],
                "breakaway_answer": r["breakaway_answer"],
                "council": r["council"],
                "canonical_citation": r["canonical_citation"],
                "source_entry_id": r["source_entry_id"],
                "notes": r.get("notes") or "",
            }
        )

    match_doc = json.loads(
        (args.out_dir / "denomination_council_matches_50y.json").read_text(encoding="utf-8")
    )
    temporal_by_id = result.get("temporal_by_id") or {}
    n_differ = 0
    for m in sorted(match_doc["matches"], key=lambda x: (x["start_year"], x["group_name"])):
        gs = by_gid[m["group_id"]]
        qrows = rows_by_gid.get(m["group_id"]) or []
        tm = temporal_by_id.get(m["group_id"]) or {}
        temporal_council = tm.get("primary_council")  # None if no prior/during council
        differs = bool(temporal_council and temporal_council != m["primary_council"])
        if differs:
            n_differ += 1
        n_doc = sum(1 for r in qrows if (r.get("council") or "") == m["primary_council"])
        n_tmp = (
            sum(1 for r in qrows if (r.get("council") or "") == temporal_council)
            if temporal_council and tm.get("within_window")
            else 0
        )
        groups_payload.append(
            {
                "group_id": m["group_id"],
                "group_name": m["group_name"],
                "start_year": m["start_year"],
                "primary_council": m["primary_council"],
                "primary_reason": m.get("primary_reason") or "doctrinal",
                "temporal_council": temporal_council,
                "temporal_distance_years": tm.get("primary_distance_years"),
                "temporal_within_window": bool(tm.get("within_window")),
                "differs_from_temporal": differs,
                "n_questions_doctrinal": n_doc,
                "n_questions_temporal": n_tmp,
                "status": gs["status"] if gs["n_questions"] else "pending",
                "n_questions": len(qrows),
                "questions": qrows,
            }
        )

    payload = {
        "title": "Step 1 — Catholic vs breakaway disagreements",
        "description": (
            "Side-by-side disagreement questions for each breakaway group, with the Catholic "
            "answer cited to its council locus. Use Pairing to compare three cuts of the same "
            "data: all recoverable loci; only the doctrinal primary council; or only the "
            "temporal match (rupture during the council or within 50 years after it — not before)."
        ),
        "match_mode": "doctrinal+temporal_filter",
        "has_pairing_filter": True,
        "n_groups": len(groups_payload),
        "n_with_questions": result["n_groups_with_questions"],
        "n_pending": result["n_pending"],
        "n_groups_strict": sum(1 for g in groups_payload if g["status"] == "strict"),
        "n_groups_ai_only": sum(1 for g in groups_payload if g["status"] == "ai"),
        "n_questions": len(rows),
        "n_groups_differ_temporal": n_differ,
        "by_primary_council": dict(
            Counter(g["primary_council"] for g in groups_payload).most_common()
        ),
        "groups": groups_payload,
        "by_tier": result["by_tier"],
        "by_confidence": result["by_confidence"],
    }

    (args.out_dir / "contrast_step1.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.out_dir / "contrast_step1.html").write_text(
        viz.build_html(payload), encoding="utf-8"
    )
    (args.out_dir / "STEP1_FINAL.md").write_text(
        write_markdown(result, pending), encoding="utf-8"
    )

    # README pointer
    readme = args.out_dir / "README.md"
    if readme.exists():
        body = readme.read_text(encoding="utf-8")
        if "| `contrast_step1.html`" not in body:
            body = body.replace(
                "| `match_contrast.html` | Match-list Q&A viewer (**doctrinal**) |",
                "| `contrast_step1.html` | **Step 1 final** Q&A (doctrinal, comprehensive) |\n"
                "| `contrast_step1.jsonl` | Step 1 final contrast rows |\n"
                "| `STEP1_FINAL.md` | Step 1 final product notes |\n"
                "| `match_contrast.html` | Match-list Q&A viewer (**doctrinal**) |",
            )
            readme.write_text(body, encoding="utf-8")

    print(
        json.dumps(
            {
                "wrote": str(jsonl_path),
                "viewer": str(args.out_dir / "contrast_step1.html"),
                "n_match_groups": result["n_match_groups"],
                "n_groups_with_questions": result["n_groups_with_questions"],
                "n_pending": result["n_pending"],
                "n_rows": result["n_rows"],
                "by_tier": result["by_tier"],
                "by_confidence": result["by_confidence"],
                "by_group_status": result["by_group_status"],
                "pending": [p["group_name"] for p in pending],
            },
            indent=2,
        )
    )
    return 0 if result["n_pending"] == 0 else 0  # still succeed; report pending


if __name__ == "__main__":
    raise SystemExit(main())
