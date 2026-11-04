#!/usr/bin/env python3
"""Match breakaway denominations to councils by start/rupture year (±N years).

Authoritative source for denomination↔council pairing used by contrast expansion
and the questions visualization group list.

Sources:
  - outputs/step1/breakaways/groups_catalog.json (rupture_year)
  - outputs/step1/breakaways/contrast/denominations_extra.json (supplemental;
    catalog name/id duplicates are skipped)
  - data/councils/index.json + COUNCIL_SPANS

Excludes in-communion / non-breakaway bodies under excluded_non_breakaways.

Primary council selection: doctrinal preference (family rupture) over nearest-year
when known; may force a council outside ±WINDOW for early/late ruptures that still
have a clear locus (e.g. Novatianists → Nicaea I).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "outputs/step1/breakaways/groups_catalog.json"
EXTRA = ROOT / "outputs/step1/breakaways/contrast/denominations_extra.json"
COUNCILS_INDEX = ROOT / "data/councils/index.json"
OUT_DIR = ROOT / "outputs/step1/breakaways/contrast"

# Canonical spans where the index often stores a single promulgation year.
COUNCIL_SPANS: dict[str, tuple[int, int]] = {
    "First Council of Nicaea": (325, 325),
    "First Council of Constantinople": (381, 381),
    "Council of Ephesus": (431, 431),
    "Council of Chalcedon": (451, 451),
    "Second Council of Constantinople": (553, 553),
    "Third Council of Constantinople": (680, 681),
    "Second Council of Nicaea": (787, 787),
    "Fourth Council of Constantinople": (869, 870),
    "First Lateran Council": (1123, 1123),
    "Second Lateran Council": (1139, 1139),
    "Third Lateran Council": (1179, 1179),
    "Fourth Lateran Council": (1215, 1215),
    "First Council of Lyons": (1245, 1245),
    "Second Council of Lyons": (1274, 1274),
    "Council of Vienne": (1311, 1312),
    "Council of Constance": (1414, 1418),
    "Council of Florence": (1431, 1445),
    "Fifth Lateran Council": (1512, 1517),
    "Council of Trent": (1545, 1563),
    "First Vatican Council": (1869, 1870),
    "Second Vatican Council": (1962, 1965),
}

# Family / broke_from / id substrings → doctrinally preferred council.
DOCTRINAL_COUNCIL: dict[str, str] = {
    "novatian": "First Council of Nicaea",
    "lutheran": "Council of Trent",
    "reformed": "Council of Trent",
    "calvinist": "Council of Trent",
    "presbyterian": "Council of Trent",
    "anabaptist": "Council of Trent",
    "hutterite": "Council of Trent",
    "mennonite": "Council of Trent",
    "baptist": "Council of Trent",
    "anglican": "Council of Trent",
    "episcopal": "Council of Trent",
    "methodist": "Council of Trent",
    "wesleyan": "Council of Trent",
    "nazarene": "Council of Trent",
    "congregational": "Council of Trent",
    "separatist": "Council of Trent",
    "unitarian": "Council of Trent",
    "restoration": "Council of Trent",
    "advent": "Council of Trent",
    "brethren": "Council of Trent",
    "pentecostal": "Council of Trent",
    "assemblies": "Council of Trent",
    "holiness": "Council of Trent",
    "salvation-army": "Council of Trent",
    "moravian": "Council of Constance",
    "hussite": "Council of Constance",
    "wyclif": "Council of Constance",
    "waldens": "Fourth Lateran Council",
    "arian": "First Council of Nicaea",
    "melitian": "First Council of Nicaea",
    "donatist": "First Council of Nicaea",
    "church-of-the-east": "Council of Ephesus",
    "assyrian": "Council of Ephesus",
    "chaldean-syrian": "Council of Ephesus",
    "armenian": "Council of Chalcedon",
    "coptic": "Council of Chalcedon",
    "syriac": "Council of Chalcedon",
    "ethiopian": "Council of Chalcedon",
    "eritrean": "Council of Chalcedon",
    "oriental-orthodox": "Council of Chalcedon",
    "malankara": "Council of Chalcedon",
    "mar-thoma": "Council of Chalcedon",
    "eastern-orthodox": "Council of Florence",
    "old-believer": "Council of Florence",
    "old-calendar": "Council of Florence",
    "rocor": "Council of Florence",
    "ukrainian-autocephalous": "Council of Florence",
    "doukhobor": "Council of Florence",
    "molokan": "Council of Florence",
    "old-catholic": "First Vatican Council",
    "polish-national": "First Vatican Council",
    "mariavite": "First Vatican Council",
    "philippine-independent": "First Vatican Council",
    "aglipayan": "First Vatican Council",
    "petite-eglise": "First Vatican Council",
    "sedevacant": "Second Vatican Council",
    "palmarian": "Second Vatican Council",
    "latter-day": "First Vatican Council",
    "lds": "First Vatican Council",
}

# Hard overrides by group id (always force; even outside ±window).
FORCE_COUNCIL_BY_ID: dict[str, str] = {
    "novatianists": "First Council of Nicaea",
    "petite-eglise": "First Vatican Council",
    "melitians": "First Council of Nicaea",
    "donatists": "First Council of Nicaea",
}


def _token_in(blob: str, key: str) -> bool:
    """Whole-token match so 'arian' does not hit 'trinitarian'."""
    return re.search(rf"(^|[^a-z0-9]){re.escape(key)}([^a-z0-9]|$)", blob or "") is not None


def _norm_name(s: str) -> str:
    s = (s or "").lower().replace("’", "'").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s).strip()
    # light aliases so extras do not double catalog rows
    aliases = {
        "church of god (cleveland, tn)": "church of god (cleveland, tennessee)",
        "national baptist convention usa": "national baptist convention, usa",
        "grace communion international (ex-wcg)": (
            "grace communion international (ex–worldwide church of god)"
        ),
        "vineyard churches": "vineyard movement",
        "calvary chapel": "calvary chapel association",
        "plymouth brethren (exclusive)": "exclusive brethren (darbyite)",
    }
    return aliases.get(s, s)


def _year_distance(rupture: int, start: int, end: int) -> int:
    if start <= rupture <= end:
        return 0
    if rupture < start:
        return start - rupture
    return rupture - end


def _years_after_council(rupture: int, start: int, end: int) -> int | None:
    """Years after council end; 0 if during the council; None if before it starts.

    Temporal pairing uses this (forward-only): a breakaway may attach to a council
    only when it arises during or after that council, not up to N years before.
    """
    if rupture < start:
        return None
    if rupture <= end:
        return 0
    return rupture - end


def load_councils(index_path: Path) -> list[dict]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    by_name: dict[str, dict] = {}
    for it in data.get("items") or []:
        name = it.get("council") or it.get("title") or ""
        raw = str(it.get("datePromulgated") or "")[:4]
        try:
            year = int(raw)
        except ValueError:
            continue
        if name not in by_name:
            by_name[name] = {
                "council": name,
                "year_start": year,
                "year_end": year,
                "record_ids": [it.get("id")],
            }
        else:
            by_name[name]["year_start"] = min(by_name[name]["year_start"], year)
            by_name[name]["year_end"] = max(by_name[name]["year_end"], year)
            by_name[name]["record_ids"].append(it.get("id"))

    for name, (a, b) in COUNCIL_SPANS.items():
        if name in by_name:
            by_name[name]["year_start"] = a
            by_name[name]["year_end"] = b
        else:
            by_name[name] = {
                "council": name,
                "year_start": a,
                "year_end": b,
                "record_ids": [],
            }
    return sorted(by_name.values(), key=lambda c: c["year_start"])


def load_extra_denominations(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for d in data.get("denominations") or []:
        if d.get("skip") or not d.get("start_year"):
            continue
        out.append(
            {
                "id": d["id"],
                "name": d["name"],
                "rupture_year": int(d["start_year"]),
                "approx_rupture": str(d["start_year"]),
                "broke_from": d.get("broke_from") or "catholic-church",
                "separation_degree": d.get("separation_degree") or 2,
                "confidence": d.get("confidence") or "contested",
                "status": d.get("status") or "extant",
                "in_step1_breakaways": False,
                "summary": d.get("summary") or "",
                "disagreement": {
                    "kind": "summary",
                    "summary": d.get("summary") or "",
                },
                "source": "denominations_extra",
            }
        )
    return out


def _family_blob(group: dict, by_id: dict[str, dict]) -> str:
    parts = [group.get("id") or "", group.get("broke_from") or "", group.get("name") or ""]
    seen = set()
    cur = group.get("id")
    while cur and cur not in seen and cur != "catholic-church":
        seen.add(cur)
        g = by_id.get(cur) or {}
        parts.append(cur)
        parts.append(str(g.get("broke_from") or ""))
        cur = g.get("broke_from")
    return " ".join(parts).lower()


def preferred_council(
    group: dict,
    window_councils: list[dict],
    by_id: dict[str, dict],
    *,
    allow_force_outside: bool = True,
) -> tuple[str | None, str]:
    """Return (council_name, reason)."""
    gid = group.get("id") or ""
    if gid in FORCE_COUNCIL_BY_ID:
        return FORCE_COUNCIL_BY_ID[gid], "doctrinal"

    names_in = {c["council"] for c in window_councils}
    disc = group.get("disagreement") or {}
    cit = (disc.get("canonical_citation") or "").lower()
    eid = (disc.get("entry_id") or "").lower()

    def _pick(name: str, reason: str) -> tuple[str | None, str]:
        if name in names_in or allow_force_outside:
            return name, reason
        return None, "none"

    if "nicaea" in cit or eid.startswith("nic1-"):
        return _pick("First Council of Nicaea", "doctrinal")
    if "ephesus" in cit or eid.startswith("eph-"):
        return _pick("Council of Ephesus", "doctrinal")
    if "chalcedon" in cit or eid.startswith("chal-"):
        return _pick("Council of Chalcedon", "doctrinal")
    if "constance" in cit or eid.startswith("con-"):
        return _pick("Council of Constance", "doctrinal")
    if "lateran" in cit and "fourth" in cit:
        return _pick("Fourth Lateran Council", "doctrinal")
    if "trent" in cit or eid.startswith("trent-"):
        return _pick("Council of Trent", "doctrinal")
    if "vatican ii" in cit or eid.startswith(("lg-", "ur-", "dv-")):
        return _pick("Second Vatican Council", "doctrinal")
    if "vatican" in cit or eid.startswith(("pa-", "df-")):
        return _pick("First Vatican Council", "doctrinal")

    blob = _family_blob(group, by_id)
    for key, council in sorted(DOCTRINAL_COUNCIL.items(), key=lambda kv: -len(kv[0])):
        if _token_in(blob, key):
            if council in names_in or allow_force_outside:
                return council, "doctrinal"

    if window_councils:
        return window_councils[0]["council"], "nearest_year"
    return None, "none"


def collect_denominations(
    catalog_path: Path,
    extra_path: Path,
) -> tuple[list[dict], list[dict], dict]:
    """Return (denominations, excluded_aligned, stats). Dedupes extras vs catalog."""
    cat = json.loads(catalog_path.read_text(encoding="utf-8"))
    groups = list(cat.get("groups") or [])
    excluded = cat.get("excluded_non_breakaways") or []

    by_id: dict[str, dict] = {g["id"]: g for g in groups}
    seen_ids = set(by_id)
    seen_names = {_norm_name(g.get("name") or "") for g in groups}

    extras_raw = load_extra_denominations(extra_path)
    extras_kept = []
    extras_skipped_dup = []
    for e in extras_raw:
        n = _norm_name(e["name"])
        if e["id"] in seen_ids or n in seen_names:
            extras_skipped_dup.append({"id": e["id"], "name": e["name"]})
            continue
        seen_ids.add(e["id"])
        seen_names.add(n)
        e = {**e, "catholic_aligned": False}
        groups.append(e)
        by_id[e["id"]] = e
        extras_kept.append(e)

    denominations = []
    for g in groups:
        denominations.append(
            {
                "id": g["id"],
                "name": g["name"],
                "start_year": g.get("rupture_year"),
                "approx_rupture": g.get("approx_rupture"),
                "broke_from": g.get("broke_from"),
                "separation_degree": g.get("separation_degree"),
                "confidence": g.get("confidence"),
                "status": g.get("status"),
                "in_step1_breakaways": bool(g.get("in_step1_breakaways")),
                "catholic_aligned": False,
                "source": g.get("source") or "groups_catalog",
                "summary": g.get("summary") or "",
                "disagreement": g.get("disagreement") or {},
            }
        )
    denominations.sort(
        key=lambda d: (d["start_year"] is None, d["start_year"] or 9999, d["name"])
    )

    aligned = []
    for e in excluded:
        aligned.append(
            {
                "id": e.get("id"),
                "name": e.get("name") or e.get("id"),
                "reason": e.get("notes") or e.get("summary") or "excluded_non_breakaway",
                "catholic_aligned": True,
            }
        )

    stats = {
        "n_catalog": len(cat.get("groups") or []),
        "n_extra_file": len(extras_raw),
        "n_extra_kept": len(extras_kept),
        "n_extra_skipped_dup": len(extras_skipped_dup),
        "extra_skipped_dup": extras_skipped_dup,
        "n_denominations": len(denominations),
        "n_catholic_aligned_excluded": len(aligned),
    }
    return denominations, aligned, {"by_id": by_id, **stats}


def _all_council_distances(y: int, councils: list[dict]) -> list[dict]:
    rows = []
    for c in councils:
        dist = _year_distance(y, c["year_start"], c["year_end"])
        rows.append(
            {
                "council": c["council"],
                "council_span": [c["year_start"], c["year_end"]],
                "distance_years": dist,
            }
        )
    rows.sort(key=lambda x: (x["distance_years"], x["council_span"][0]))
    return rows


def build_matches(
    denominations: list[dict],
    councils: list[dict],
    by_id: dict[str, dict],
    *,
    window: int,
) -> tuple[list[dict], list[dict]]:
    """Doctrinal-primary matches (may force a council outside ±window)."""
    matches = []
    unmatched = []
    for d in denominations:
        y = d["start_year"]
        if y is None:
            unmatched.append({**d, "reason": "no_start_year"})
            continue
        all_dist = _all_council_distances(y, councils)
        near = [c for c in all_dist if c["distance_years"] <= window]

        group = {
            "id": d["id"],
            "name": d["name"],
            "broke_from": d.get("broke_from"),
            "disagreement": d.get("disagreement") or {},
        }
        primary, reason = preferred_council(group, near, by_id, allow_force_outside=True)

        if primary and primary not in {c["council"] for c in near}:
            span = COUNCIL_SPANS.get(primary)
            near = [
                {
                    "council": primary,
                    "council_span": list(span) if span else [y, y],
                    "distance_years": abs((span[0] if span else y) - y),
                    "doctrinal_force": True,
                }
            ] + near
            reason = "doctrinal"

        if not primary and near:
            primary = near[0]["council"]
            reason = "nearest_year"

        if primary:
            matches.append(
                {
                    "group_id": d["id"],
                    "group_name": d["name"],
                    "start_year": y,
                    "separation_degree": d.get("separation_degree"),
                    "in_step1_breakaways": d.get("in_step1_breakaways"),
                    "source": d.get("source"),
                    "councils_within_window": near,
                    "nearest_council": all_dist[0]["council"] if all_dist else None,
                    "nearest_distance_years": all_dist[0]["distance_years"] if all_dist else None,
                    "primary_council": primary,
                    "primary_reason": reason,
                    "match_mode": "doctrinal",
                }
            )
        else:
            unmatched.append({**d, "reason": f"no_council_within_±{window}y"})

    return matches, unmatched


def _all_council_distances_after(y: int, councils: list[dict]) -> list[dict]:
    """Councils at or before rupture year, sorted by years-after (forward distance)."""
    rows = []
    for c in councils:
        after = _years_after_council(y, c["year_start"], c["year_end"])
        if after is None:
            continue
        rows.append(
            {
                "council": c["council"],
                "council_span": [c["year_start"], c["year_end"]],
                "distance_years": after,
                "years_after": after,
            }
        )
    rows.sort(key=lambda x: (x["distance_years"], x["council_span"][0]))
    return rows


def build_matches_temporal(
    denominations: list[dict],
    councils: list[dict],
    by_id: dict[str, dict],
    *,
    window: int,
) -> tuple[list[dict], list[dict]]:
    """Forward-window temporal matches: council → breakaway within +window years after.

    Only pairs a group to a council if the rupture is during or after that council
    (never up to N years *before* the council). Primary = nearest such council.
    `within_window` is true when years-after ≤ window.
    """
    matches = []
    unmatched = []
    for d in denominations:
        y = d["start_year"]
        if y is None:
            unmatched.append({**d, "reason": "no_start_year"})
            continue
        after_dist = _all_council_distances_after(y, councils)
        if not after_dist:
            unmatched.append({**d, "reason": "no_council_at_or_before_start_year"})
            continue
        nearest = after_dist[0]
        within = [c for c in after_dist if c["distance_years"] <= window]
        in_window = nearest["distance_years"] <= window
        primary = nearest["council"]
        reason = (
            "nearest_after_within_window" if in_window else "nearest_after_outside_window"
        )

        # Doctrinal alt still uses symmetric ±window for comparison notes.
        all_sym = _all_council_distances(y, councils)
        within_sym = [c for c in all_sym if c["distance_years"] <= window]
        group = {
            "id": d["id"],
            "name": d["name"],
            "broke_from": d.get("broke_from"),
            "disagreement": d.get("disagreement") or {},
        }
        doctrinal, doctrinal_reason = preferred_council(
            group, within_sym, by_id, allow_force_outside=True
        )

        matches.append(
            {
                "group_id": d["id"],
                "group_name": d["name"],
                "start_year": y,
                "separation_degree": d.get("separation_degree"),
                "in_step1_breakaways": d.get("in_step1_breakaways"),
                "source": d.get("source"),
                "councils_within_window": within,
                "councils_by_distance": after_dist[:5],
                "primary_council": primary,
                "primary_reason": reason,
                "primary_distance_years": nearest["distance_years"],
                "within_window": in_window,
                "window_direction": "after_only",
                "doctrinal_council": doctrinal,
                "doctrinal_reason": doctrinal_reason,
                "differs_from_doctrinal": bool(doctrinal and doctrinal != primary),
                "match_mode": "temporal",
            }
        )
    return matches, unmatched


def write_outputs(
    *,
    out_dir: Path,
    denominations: list[dict],
    aligned: list[dict],
    matches: list[dict],
    unmatched: list[dict],
    stats: dict,
    window: int,
    mode: str = "doctrinal",
    match_basename: str | None = None,
    write_denominations: bool = True,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    denom_path = out_dir / "denominations_by_start.json"
    aligned_path = out_dir / "catholic_aligned_excluded.json"
    if match_basename:
        stem = match_basename
    elif mode == "temporal":
        stem = "denomination_council_matches_temporal"
    else:
        stem = "denomination_council_matches_50y"
    match_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"

    if write_denominations:
        denom_path.write_text(
            json.dumps(
                {
                    "description": (
                        "Breakaway denominations ordered by start/rupture year "
                        "(groups_catalog + unique denominations_extra)."
                    ),
                    "n": len(denominations),
                    "n_catalog": stats.get("n_catalog"),
                    "n_extra_kept": stats.get("n_extra_kept"),
                    "denominations": [
                        {k: v for k, v in d.items() if k != "disagreement"}
                        for d in denominations
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        aligned_path.write_text(
            json.dumps(
                {
                    "description": (
                        "Bodies filtered out as Catholic-aligned / non-breakaway "
                        "for contrast pairing."
                    ),
                    "n": len(aligned),
                    "bodies": aligned,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    by_council: dict[str, int] = {}
    for m in matches:
        by_council[m["primary_council"]] = by_council.get(m["primary_council"], 0) + 1
    n_outside = sum(1 for m in matches if m.get("within_window") is False)
    n_differ = sum(1 for m in matches if m.get("differs_from_doctrinal"))

    primary_selection = (
        "nearest prior/during council by start/rupture year (temporal); "
        f"in-window only if within +{window}y after council end (not before)"
        if mode == "temporal"
        else "doctrinal preference over nearest-year when known"
    )

    summary = {
        "window_years": window,
        "window_direction": "after_only" if mode == "temporal" else "symmetric",
        "match_mode": mode,
        "primary_selection": primary_selection,
        "n_catalog_groups": stats.get("n_catalog"),
        "n_extra_kept": stats.get("n_extra_kept"),
        "n_extra_skipped_dup": stats.get("n_extra_skipped_dup"),
        "extra_skipped_dup": stats.get("extra_skipped_dup"),
        "n_denominations_total": len(denominations),
        "n_catholic_aligned_excluded": len(aligned),
        "n_matched": len(matches),
        "n_unmatched": len(unmatched),
        "n_outside_window": n_outside if mode == "temporal" else None,
        "n_differs_from_doctrinal": n_differ if mode == "temporal" else None,
        "by_primary_council": dict(sorted(by_council.items(), key=lambda x: -x[1])),
        "complete": len(unmatched) == 0,
        "matches": matches,
        "unmatched": [
            {
                "id": u["id"],
                "name": u["name"],
                "start_year": u.get("start_year"),
                "reason": u.get("reason"),
            }
            for u in unmatched
        ],
    }
    match_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if mode == "temporal":
        md = [
            f"# Denominations ↔ councils (temporal / +{window}y after council only)",
            "",
            "Comprehensive **time-based** pairing: each breakaway’s primary council is the",
            "**nearest prior or concurrent** council by start/rupture year. A match is",
            f"**in-window** only when the rupture is during the council or within **+{window}y",
            "after** it ends — never by being up to N years *before* the council.",
            "",
            "Doctrinal pairing remains in [`denomination_council_matches_50y.md`](denomination_council_matches_50y.md).",
            "",
            f"- Catalog groups: **{stats.get('n_catalog')}**",
            f"- Extra denominations kept: **{stats.get('n_extra_kept')}**",
            f"- Total breakaway nodes: **{len(denominations)}**",
            f"- Matched (nearest prior/during): **{len(matches)}**"
            + (" — **complete**" if not unmatched else ""),
            f"- Outside +{window}y-after window (still assigned nearest prior): **{n_outside}**",
            f"- Differs from doctrinal primary: **{n_differ}**",
            f"- Unmatched: **{len(unmatched)}**",
            "",
            "### Primary councils (temporal)",
            "",
        ]
        for council, n in sorted(by_council.items(), key=lambda x: -x[1]):
            md.append(f"- **{council}** — {n}")
        md.extend(
            [
                "",
                f"| Start | Group | Nearest prior council | Years after | In +{window}y | Doctrinal alt |",
                "|------:|------|-----------------------|------------:|:-------------:|---------------|",
            ]
        )
        for m in sorted(matches, key=lambda x: (x["start_year"], x["group_name"])):
            win = "yes" if m.get("within_window") else "no"
            doc = m.get("doctrinal_council") or "—"
            if m.get("differs_from_doctrinal"):
                doc = f"**{doc}**"
            md.append(
                f"| {m['start_year']} | {m['group_name']} | {m['primary_council']} | "
                f"{m.get('primary_distance_years', '')} | {win} | {doc} |"
            )
    else:
        md = [
            f"# Denominations ↔ councils (±{window}y, doctrinal primary)",
            "",
            "Authoritative **doctrinal** breakaway list for contrast expansion.",
            "Catalog + unique extras; Catholic-aligned bodies filtered out.",
            "Primary council prefers **doctrinal** family rupture over nearest-year.",
            "",
            "Temporal (nearest-year) pairing:",
            "[`denomination_council_matches_temporal.md`](denomination_council_matches_temporal.md).",
            "",
            f"- Catalog groups: **{stats.get('n_catalog')}**",
            f"- Extra denominations kept: **{stats.get('n_extra_kept')}** "
            f"(skipped {stats.get('n_extra_skipped_dup')} catalog duplicates)",
            f"- Total breakaway nodes: **{len(denominations)}**",
            f"- Matched to a primary council: **{len(matches)}**"
            + (" — **complete**" if not unmatched else ""),
            f"- Unmatched: **{len(unmatched)}**",
            f"- Filtered Catholic-aligned: **{len(aligned)}**",
            "",
            "| Start | Group | Primary council | Reason | Source |",
            "|------:|------|-----------------|--------|--------|",
        ]
        for m in sorted(matches, key=lambda x: (x["start_year"], x["group_name"])):
            src = "extra" if (m.get("source") or "").endswith("extra") else "catalog"
            md.append(
                f"| {m['start_year']} | {m['group_name']} | {m['primary_council']} | "
                f"{m['primary_reason']} | {src} |"
            )

    md.extend(["", "## Unmatched", ""])
    if not unmatched:
        md.append("_None — every breakaway node has a primary council._")
    else:
        for u in unmatched:
            md.append(f"- **{u['name']}** ({u.get('start_year')}) — {u.get('reason')}")
    md.append("")
    md_path.write_text("\n".join(md), encoding="utf-8")

    return {
        "denominations": str(denom_path) if write_denominations else None,
        "matches": str(match_path),
        "markdown": str(md_path),
        "mode": mode,
        "n_matched": len(matches),
        "n_unmatched": len(unmatched),
        "n_total": len(denominations),
        "by_primary_council": by_council,
        "complete": len(unmatched) == 0,
        "window": window,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=int, default=50, help="± years around council span")
    ap.add_argument(
        "--mode",
        choices=("doctrinal", "temporal", "both"),
        default="both",
        help="doctrinal (family rupture), temporal (nearest year), or both",
    )
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    ap.add_argument("--extra", type=Path, default=EXTRA)
    ap.add_argument("--councils", type=Path, default=COUNCILS_INDEX)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    denominations, aligned, meta = collect_denominations(args.catalog, args.extra)
    by_id = meta.pop("by_id")
    councils = load_councils(args.councils)

    results = {}
    modes = (
        ["doctrinal", "temporal"]
        if args.mode == "both"
        else [args.mode]
    )
    for i, mode in enumerate(modes):
        if mode == "temporal":
            matches, unmatched = build_matches_temporal(
                denominations, councils, by_id, window=args.window
            )
        else:
            matches, unmatched = build_matches(
                denominations, councils, by_id, window=args.window
            )
        results[mode] = write_outputs(
            out_dir=args.out_dir,
            denominations=denominations,
            aligned=aligned,
            matches=matches,
            unmatched=unmatched,
            stats=meta,
            window=args.window,
            mode=mode,
            write_denominations=(i == 0),
        )
    print(json.dumps(results if len(results) > 1 else next(iter(results.values())), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
