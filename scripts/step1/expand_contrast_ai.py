#!/usr/bin/env python3
"""Expand contrast with AI-filled breakaway answers for denomination↔council matches.

1. Prefer doctrinally right council when several fall in ±50y window.
2. Merge supplemental denominations_extra.json.
3. For groups not yet in strict contrast tags, pick a signature locus and draft
   a disagreement row (answer_basis=ai_historical).

Writes contrast_ai.jsonl (+ HTML) without replacing contrast.jsonl.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_contrast_db as bcd  # noqa: E402
import match_denominations_to_councils as matcher  # noqa: E402

CATALOG = ROOT / "outputs/step1/breakaways/groups_catalog.json"
ENTRIES = ROOT / "outputs/step1/entries.jsonl"
EXTRA = ROOT / "outputs/step1/breakaways/contrast/denominations_extra.json"
STRICT = ROOT / "outputs/step1/breakaways/contrast/contrast.jsonl"
OUT_DIR = ROOT / "outputs/step1/breakaways/contrast"

# Family / broke_from → doctrinally preferred council (overrides mere nearest-year).
DOCTRINAL_COUNCIL: dict[str, str] = {
    # keys matched as substrings against group id / broke_from / lineage
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
    "armenian": "Council of Chalcedon",
    "coptic": "Council of Chalcedon",
    "syriac": "Council of Chalcedon",
    "ethiopian": "Council of Chalcedon",
    "oriental-orthodox": "Council of Chalcedon",
    "eastern-orthodox": "Council of Florence",
    "old-believer": "Council of Florence",
    "old-calendar": "Council of Florence",
    "rocor": "Council of Florence",
    "old-catholic": "First Vatican Council",
    "polish-national": "First Vatican Council",
    "mariavite": "First Vatican Council",
    "sedevacant": "Second Vatican Council",
    "palmarian": "Second Vatican Council",
    "latter-day": "First Vatican Council",
    "lds": "First Vatican Council",
}

# Signature loci per council when catalog has no entry_id
SIGNATURE_LOCI: dict[str, list[str]] = {
    "First Council of Nicaea": ["nic1-creed-en", "nic1-canon8-en"],
    "Council of Ephesus": ["eph-anathema1-en", "eph-cyril-letter2-en"],
    "Council of Chalcedon": ["chal-definition-en"],
    "Council of Constance": [
        "con-s13-condemnation-of-communion-under-both-kinds-recently-revived-among-the-bo",
        "con-s15-articles-of-john-wyclif-selected-from-the-260-en",
    ],
    "Fourth Lateran Council": ["lat4-constitution3-en", "lat4-constitution1-en"],
    "Council of Florence": [
        "flo-florence-s6-p9-en",
        "flo-florence-s6-p11-en",
        "flo-florence-s6-p12-en",
        "lyo2-profession-palaeologus-p6-en",
    ],
    "Council of Trent": [
        "trent-s6-justification-canon4-en",
        "trent-s6-justification-canon9-en",
        "trent-s6-justification-canon30-en",
        "trent-s7-sacraments-canon1-en",
        "trent-s7-baptism-canon13-en",
        "trent-s7-baptism-canon11-en",
        "trent-s5-original-sin-canon4-en",
        "trent-s13-eucharist-canon1-en",
        "trent-s13-eucharist-canon2-en",
        "trent-s13-eucharist-canon3-en",
        "trent-s22-mass-ch1-en",
        "trent-s22-mass-ch2-en",
        "trent-s22-mass-ch3-en",
        "trent-s24-matrimony-canon1-en",
        "trent-s24-matrimony-canon7-en",
        "trent-s25-indulgences-decree-en",
        "trent-s25-saints-images-decree-en",
    ],
    "First Vatican Council": [
        "pa-ch3-canon1-en",
        "pa-ch4-canon1-en",
        "pa-ch4-p9-en",
        "pa-ch1-canon1-en",
    ],
    "Second Vatican Council": [
        "lg-18-en",
        "lg-22-en",
        "ur-1-en",
    ],
    "Fifth Lateran Council": [
        "lat5-s11-on-how-to-preach-en",
        "lat5-s10-on-printing-books-en",
        "lat5-s8-condemnation-of-every-proposition-contrary-to-the-truth-of-the-enlighten",
    ],
    "Second Council of Lyons": [
        "lyo2-profession-palaeologus-p3-en",
        "lyo2-profession-palaeologus-p6-en",
    ],
    "Third Lateran Council": ["lat3-canon1-en", "lat3-canon27-en"],
    "Second Lateran Council": ["lat2-canon23-en", "lat2-canon1-en"],
    "First Lateran Council": ["lat1-canon1-en", "lat1-canon9-en"],
    "First Council of Lyons": ["lyo1-colli-constitution1-en"],
    "Council of Vienne": ["vie-decree1-en", "vie-decree3-en"],
    "Second Council of Nicaea": ["nic2-canon1-en", "nic2-definition-en"],
    "Fourth Council of Constantinople": ["con4-canon1-en", "con4-canon21-en"],
    "First Council of Constantinople": ["con1-canon1-en", "con1-canon3-en"],
    "Third Council of Constantinople": ["con3-exposition-p1-en", "con3-exposition-p3-en"],
    "Second Council of Constantinople": ["con2-canon5-en", "con2-canon7-en"],
}

# Theme → preferred locus pool (hash-pick within pool to diversify)
THEME_LOCI: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (
        ("anabaptist", "baptist", "mennonite", "hutterite", "brethren", "immersion"),
        (
            "trent-s7-baptism-canon13-en",
            "trent-s5-original-sin-canon4-en",
            "trent-s7-baptism-canon11-en",
        ),
    ),
    (
        ("methodist", "wesley", "holiness", "nazarene"),
        (
            "trent-s6-justification-canon4-en",
            "trent-s6-justification-canon9-en",
            "trent-s14-penance-canon4-en",
        ),
    ),
    (
        ("pentecostal", "assemblies", "charismatic", "vineyard", "foursquare"),
        (
            "trent-s7-sacraments-canon1-en",
            "trent-s23-orders-canon1-en",
            "trent-s6-justification-canon4-en",
        ),
    ),
    (
        ("anglican", "episcopal", "continuing"),
        (
            "trent-s22-mass-ch2-en",
            "trent-s13-eucharist-canon1-en",
            "trent-s23-orders-canon1-en",
        ),
    ),
    (
        ("reformed", "calvin", "presbyterian"),
        (
            "trent-s6-justification-canon9-en",
            "trent-s13-eucharist-canon2-en",
            "trent-s25-indulgences-decree-en",
        ),
    ),
    (("luther",), ("trent-s6-justification-canon4-en", "trent-s6-justification-canon30-en")),
    (
        ("advent", "sabbath"),
        ("trent-s25-saints-images-decree-en", "trent-s25-purgatory-decree-en"),
    ),
    (
        ("restoration", "disciple", "campbell", "churches of christ"),
        ("trent-s7-sacraments-canon1-en", "trent-s7-baptism-canon13-en"),
    ),
    (
        ("quaker", "shaker", "friend"),
        ("trent-s7-sacraments-canon1-en", "trent-s22-mass-ch1-en"),
    ),
    (("unitarian", "oneness"), ("nic1-creed-en",)),
    (
        ("old-catholic", "polish-national", "mariavite", "philippine-independent", "aglipayan"),
        ("pa-ch3-canon1-en", "pa-ch4-canon1-en", "pa-ch1-canon1-en"),
    ),
    (("sedevacant", "palmarian"), ("pa-ch4-p9-en", "pa-ch3-canon1-en")),
    (("waldens",), ("lat4-constitution3-en", "lat4-constitution1-en")),
    (("melitian", "melet"), ("nic1-synodal-letter-en",)),
    (
        ("hussite", "moravian"),
        (
            "con-s13-condemnation-of-communion-under-both-kinds-recently-revived-among-the-bo",
        ),
    ),
]


def _token_in(blob: str, key: str) -> bool:
    """Whole-token match so 'arian' does not hit 'trinitarian'."""
    return re.search(rf"(^|[^a-z0-9]){re.escape(key)}([^a-z0-9]|$)", blob or "") is not None


def _any_token(blob: str, keys: tuple[str, ...] | list[str]) -> bool:
    return any(_token_in(blob, k) for k in keys)


def _scrub(s: str) -> str:
    s = re.sub(
        r"(?i)\b(?:Catholic Church|Roman Church|Roman pontiff|Trent|Florence|"
        r"Vatican|Chalcedon|Ephesus|Nicaea|Constance|Lateran|Lutheran|Protestant|"
        r"Orthodox|Coptic|Armenian|this tradition)\b",
        "",
        s,
    )
    s = re.sub(r"\s{2,}", " ", s)
    return bcd._clean_space(s).strip(" ,;")


def _lineage_ids(group_id: str, by_id: dict[str, dict]) -> list[str]:
    out = []
    seen = set()
    cur = group_id
    while cur and cur not in seen and cur != "catholic-church":
        seen.add(cur)
        out.append(cur)
        g = by_id.get(cur) or {}
        parent = g.get("broke_from")
        # supplemental extras may point at catalog slugs
        cur = parent
    return out


def preferred_council(group: dict, window_councils: list[dict], by_id: dict) -> str | None:
    """Pick doctrinally best council among those in-window; may force Florence for EO family."""
    names_in = {c["council"] for c in window_councils}
    # Explicit catalog locus citation → council name guess
    disc = group.get("disagreement") or {}
    cit = (disc.get("canonical_citation") or "").lower()
    if "nicaea" in cit and "First Council of Nicaea" in names_in:
        return "First Council of Nicaea"
    if "ephesus" in cit:
        return "Council of Ephesus" if "Council of Ephesus" in names_in else None
    if "chalcedon" in cit:
        return "Council of Chalcedon" if "Council of Chalcedon" in names_in else None
    if "constance" in cit:
        return "Council of Constance" if "Council of Constance" in names_in else None
    if "lateran" in cit and "fourth" in cit:
        return "Fourth Lateran Council"
    if "trent" in cit:
        return "Council of Trent"
    if "vatican i" in cit or "pastor aeternus" in cit or "pa ch" in cit:
        return "First Vatican Council"
    if "vatican ii" in cit:
        return "Second Vatican Council"

    tokens = []
    for gid in _lineage_ids(group["id"], by_id):
        tokens.append(gid)
        g2 = by_id.get(gid) or {}
        if g2.get("broke_from"):
            tokens.append(str(g2["broke_from"]))
    tokens.append(group.get("id") or "")
    blob = " ".join(tokens).lower()

    pref = None
    # longer keys first for specificity
    for key, council in sorted(DOCTRINAL_COUNCIL.items(), key=lambda kv: -len(kv[0])):
        if _token_in(blob, key):
            pref = council
            break
    if pref:
        if pref in names_in:
            return pref
        # Force doctrinally required councils even if outside ±50y
        return pref

    if window_councils:
        return min(window_councils, key=lambda c: (c["distance_years"], c["council_span"][0]))[
            "council"
        ]
    return None


def _pick_locus(
    council: str,
    group: dict,
    entries_by_id: dict,
    entries_by_council: dict,
    by_id: dict | None = None,
) -> dict | None:
    """Pick a locus on the *requested* council (do not jump to Trent via themes)."""
    disc = group.get("disagreement") or {}
    eid = disc.get("entry_id")
    if eid and eid in entries_by_id:
        hit = entries_by_id[eid]
        if (hit.get("council") or "") == council:
            return hit

    fam = _family_blob(group, by_id or {group["id"]: group})
    # Theme routing only when the themed locus belongs to this council
    for keys, locus_ids in THEME_LOCI:
        if not _any_token(fam, keys):
            continue
        pool = [
            entries_by_id[lid]
            for lid in locus_ids
            if lid in entries_by_id and (entries_by_id[lid].get("council") or "") == council
        ]
        if pool:
            idx = sum(ord(c) for c in (group.get("id") or "")) % len(pool)
            return pool[idx]

    gid = (group.get("id") or "").lower()
    sig = list(SIGNATURE_LOCI.get(council, []))
    # Avoid pairing non-Arian Nicaea rigorists with the creed
    if council == "First Council of Nicaea":
        if "arian" in gid:
            sig = ["nic1-creed-en"] + [s for s in sig if s != "nic1-creed-en"]
        elif "donatist" in gid or "melitian" in gid or "novatian" in gid:
            sig = [
                "nic1-canon8-en",
                "nic1-synodal-letter-en",
            ] + [s for s in sig if s not in {"nic1-creed-en"}]

    available = [entries_by_id[sid] for sid in sig if sid in entries_by_id]
    if available:
        idx = sum(ord(c) for c in (group.get("id") or "")) % len(available)
        return available[idx]

    pool = entries_by_council.get(council) or []
    if not pool:
        return None
    idx = sum(ord(c) for c in (group.get("id") or "")) % len(pool)
    return pool[idx]


def _family_blob(group: dict, by_id: dict) -> str:
    parts = [group.get("id") or "", group.get("name") or "", group.get("broke_from") or ""]
    for gid in _lineage_ids(group["id"], by_id):
        parts.append(gid)
        g2 = by_id.get(gid) or {}
        parts.append(g2.get("name") or "")
    parts.append((group.get("disagreement") or {}).get("summary") or "")
    parts.append(group.get("summary") or "")
    return " ".join(parts).lower()


def _ai_breakaway_answer(group: dict, question: str, council: str, by_id: dict) -> str:
    """Heuristic AI-style fill — direct Yes/No, no church/council names."""
    q = question.lower()
    fam = _family_blob(group, by_id)

    # Question-led templates (prefer these over raw summaries)
    if any(k in q for k in ("pontiff", "primacy", "infallib", "ex cathedra", "supreme power")):
        return (
            "No. No bishop holds universal ordinary jurisdiction or ex cathedra "
            "infallibility as that definition requires."
        )
    if "seven sacrament" in q or (
        "matrimony" in q and "sacrament" in q
    ):
        return (
            "No. There are not seven sacraments of the New Law in that list; the Gospel "
            "sacraments are Baptism and the Lord’s Supper."
        )
    if (
        "transubstant" in q
        or "substance of bread" in q
        or ("truly" in q and "really" in q and "substantially" in q)
        or ("whole christ" in q and "eucharist" in q)
    ):
        return (
            "No. Bread and wine are not converted in substance that way; Christ is "
            "received without that metaphysics."
        )
    if "propitiatory" in q or ("mass" in q and "sacrifice" in q):
        return (
            "No. Calvary’s sacrifice is once for all; the Mass is not a propitiatory "
            "sacrifice offered for the living and the dead."
        )
    if "indulgence" in q:
        return "No. Indulgences are not a power to remit temporal punishment in that economy."
    if "justif" in q or ("free will" in q and "cooperat" in q):
        return (
            "No. Justification is by faith apart from that cooperating scheme of infused "
            "justice and condign merit."
        )
    if ("infant" in q or "little children" in q) and "baptis" in q:
        return (
            "No. Baptism belongs to believers upon confession of faith; infants are not "
            "baptized into the church as that requirement states."
        )
    if "reckon" in q and "faithful" in q and "baptis" in q:
        return (
            "No. Without their own confession of faith, the baptized are not reckoned among "
            "the faithful that way; believers’ baptism is required."
        )
    if "both kinds" in q or ("bread and wine" in q and "laity" in q):
        return (
            "Yes. The sacrament should be given under both kinds; withholding the cup "
            "from the people is refused."
        )
    if "mother of god" in q or "theotokos" in q:
        return (
            "No. Mother of Christ language is preferred; the forced Theotokos settlement "
            "is not accepted as binding."
        )
    if "two nature" in q or "acknowledged in two" in q:
        return (
            "No. After the union he is confessed as one united nature of the Word "
            "incarnate, not ‘in two natures.’"
        )
    if "proceed" in q and "father and the son" in q:
        return (
            "No. The Spirit proceeds from the Father; procession from the Father and "
            "the Son as a required formula is refused."
        )
    if "consubstantial" in q or ("true god from true god" in q):
        # Only nontrinitarian families reject the Nicene homoousios.
        if _any_token(
            fam,
            (
                "arian",
                "unitarian",
                "oneness",
                "jehovah",
                "latter-day",
                "lds",
                "iglesia",
            ),
        ):
            return (
                "No. The Son is not of one substance with the Father; he is created or "
                "otherwise not true God in the same sense as the Father."
            )
        return (
            "Yes. The Son is true God from true God, of one substance with the Father."
        )
    if "deuterocanon" in q or ("canon of scripture" in q):
        return (
            "No. The deuterocanonical books are not received as that fixed canon requires; "
            "Scripture’s rule is confessed without that list as binding."
        )

    # Family defaults by council pairing
    if council == "Council of Trent" or _any_token(
        fam,
        ("luther", "reformed", "baptist", "methodist", "anglican", "anabaptist"),
    ):
        return (
            "No. That requirement is refused; justification, sacraments, and ministry are "
            "confessed on Reformational terms instead."
        )
    if council == "First Vatican Council":
        return (
            "No. Universal papal jurisdiction and ex cathedra infallibility are refused."
        )
    if council == "Council of Florence":
        return (
            "No. Reunion on those terms—Filioque, primacy, and related definitions—is refused."
        )
    if council == "Council of Chalcedon":
        return (
            "No. After the union he is confessed as one united nature of the Word incarnate."
        )
    if council == "First Council of Nicaea":
        return (
            "No. That disciplinary or dogmatic settlement is not accepted as binding on "
            "this communion’s terms."
        )

    return (
        "No. The teaching required here is not received; the historic confession of "
        "this communion stands against that definition."
    )


def _catholic_from_entry(entry: dict, strict_by_id: dict) -> tuple[str, str]:
    """Return question, catholic_answer."""
    if entry["id"] in strict_by_id:
        r = strict_by_id[entry["id"]]
        return r["question"], r["catholic_answer"]
    q = bcd._ensure_q(entry.get("question") or "")
    # Prefer decision_summary as affirmative claim when present
    summary = bcd._clean_space(entry.get("decision_summary") or "")
    if summary and len(summary) > 40:
        summary = re.sub(r"(?i)^that\s+", "", summary)
        if len(summary) > 240:
            summary = summary[:237].rsplit(" ", 1)[0] + "…"
        catholic = f"Yes. {summary[0].upper() + summary[1:]}."
    else:
        claim = bcd._clean_space(q).rstrip("?")
        claim = re.sub(r"(?i)^(is|are|does|did|must|should|may|can)\s+", "", claim)
        catholic = f"Yes. {claim[0].upper() + claim[1:]}." if claim else "Yes."
    catholic = re.sub(r"(?i)\b(trent|florence|vatican|chalcedon|ephesus|nicaea)\b", "", catholic)
    catholic = re.sub(r"\s{2,}", " ", catholic).strip()
    return q, catholic


def load_extra() -> list[dict]:
    if not EXTRA.exists():
        return []
    data = json.loads(EXTRA.read_text(encoding="utf-8"))
    out = []
    for d in data.get("denominations") or []:
        if d.get("skip") or not d.get("start_year"):
            continue
        out.append(
            {
                "id": d["id"],
                "name": d["name"],
                "approx_rupture": str(d["start_year"]),
                "rupture_year": d["start_year"],
                "broke_from": d.get("broke_from") or "catholic-church",
                "separation_degree": d.get("separation_degree") or 2,
                "relation": "supplemental",
                "confidence": "contested",
                "summary": d.get("summary") or "",
                "council_link_in_corpus": False,
                "in_step1_breakaways": False,
                "lineage": ["catholic-church", d.get("broke_from"), d["id"]],
                "status": "extant",
                "disagreement": {
                    "kind": "summary",
                    "summary": d.get("summary") or "",
                },
                "notes": "from denominations_extra.json",
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=int, default=50)
    ap.add_argument(
        "--mode",
        choices=("doctrinal", "temporal"),
        default="doctrinal",
        help="doctrinal family rupture vs nearest-year temporal pairing",
    )
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    temporal = args.mode == "temporal"

    # Authoritative denomination↔council list (catalog + unique extras)
    denominations, _aligned, meta = matcher.collect_denominations(CATALOG, EXTRA)
    by_id = meta["by_id"]
    councils = matcher.load_councils(matcher.COUNCILS_INDEX)
    if temporal:
        match_rows, _unmatched = matcher.build_matches_temporal(
            denominations, councils, by_id, window=args.window
        )
    else:
        match_rows, _unmatched = matcher.build_matches(
            denominations, councils, by_id, window=args.window
        )
    # Persist match table for this mode (do not clobber the other mode's files)
    matcher.write_outputs(
        out_dir=args.out_dir,
        denominations=denominations,
        aligned=_aligned,
        matches=match_rows,
        unmatched=_unmatched,
        stats={k: v for k, v in meta.items() if k != "by_id"},
        window=args.window,
        mode=("temporal" if temporal else "doctrinal"),
        write_denominations=not temporal,
    )

    groups = list(by_id.values())
    extras = [d for d in denominations if (d.get("source") or "").endswith("extra")]

    entries = [
        json.loads(l) for l in ENTRIES.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    entries_by_id = {e["id"]: e for e in entries}
    entries_by_council: dict[str, list] = {}
    for e in entries:
        entries_by_council.setdefault(e.get("council") or "", []).append(e)

    strict_rows = []
    if STRICT.exists():
        strict_rows = [
            json.loads(l) for l in STRICT.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
    strict_by_id = {r["id"]: r for r in strict_rows}
    strict_groups = {r["breakaway_group"] for r in strict_rows}

    # Targets: fill AI rows where this mode's primary council is not already
    # covered by a strict contrast row for the same group.
    strict_by_group_councils: dict[str, set[str]] = {}
    for r in strict_rows:
        k = re.sub(r"[^a-z0-9]+", " ", (r.get("breakaway_group") or "").lower()).strip()
        strict_by_group_councils.setdefault(k, set()).add(r.get("council") or "")

    targets = []
    seen_names: set[str] = set()
    for m in match_rows:
        g = by_id[m["group_id"]]
        name_l = re.sub(r"[^a-z0-9]+", " ", g["name"].lower()).strip()
        if name_l in seen_names:
            continue
        covered_councils: set[str] = set()
        for sk, councils_set in strict_by_group_councils.items():
            if name_l == sk or name_l in sk or sk in name_l or g["id"].replace("-", " ") in sk:
                covered_councils |= councils_set
        if m["primary_council"] in covered_councils:
            continue
        if not temporal:
            # Doctrinal mode: skip catalog groups already tagged — except Reform
            # families that share Lutheran Trent tags without their own rows.
            shared_reform = g["id"] in {
                "reformed",
                "anabaptist",
                "anglican",
            } or any(
                k in g["id"]
                for k in ("reformed", "anabaptist", "anglican")
            )
            if g.get("in_step1_breakaways") and not shared_reform:
                # Still allow if doctrinal primary council not in their strict rows
                if covered_councils:
                    continue
        seen_names.add(name_l)
        targets.append(m)

    def _candidate_loci(council: str, group: dict) -> list[dict]:
        """Ordered locus candidates on this council (signature then pool)."""
        seen: set[str] = set()
        out: list[dict] = []
        first = _pick_locus(council, group, entries_by_id, entries_by_council, by_id)
        if first:
            out.append(first)
            seen.add(first["id"])
        for sid in SIGNATURE_LOCI.get(council, []):
            e = entries_by_id.get(sid)
            if e and e["id"] not in seen:
                out.append(e)
                seen.add(e["id"])
        for e in entries_by_council.get(council) or []:
            if e["id"] not in seen:
                out.append(e)
                seen.add(e["id"])
            if len(out) >= 12:
                break
        return out

    ai_rows = []
    skipped = []
    for m in targets:
        g = by_id[m["group_id"]]
        council = m["primary_council"]
        chosen = None
        question = catholic = breakaway_ans = ""
        tried = []
        for entry in _candidate_loci(council, g):
            tried.append(entry["id"])
            question, catholic = _catholic_from_entry(entry, strict_by_id)
            breakaway_ans = _ai_breakaway_answer(g, question, council, by_id)
            if not re.match(r"(?i)^(yes|no)\b", breakaway_ans):
                breakaway_ans = "No. " + breakaway_ans
            c_lead = re.match(r"(?i)^(yes|no)\b", catholic)
            b_lead = re.match(r"(?i)^(yes|no)\b", breakaway_ans)
            if c_lead and b_lead and c_lead.group(1).lower() == b_lead.group(1).lower():
                continue  # try another locus on the same council
            chosen = entry
            break
        if not chosen:
            skipped.append(
                {
                    "group_id": g["id"],
                    "reason": "same_polarity_or_no_locus",
                    "council": council,
                    "tried": tried[:8],
                }
            )
            continue
        entry = chosen

        ai_rows.append(
            {
                "id": f"ai:{g['id']}::{entry['id']}",
                "source_entry_id": entry["id"],
                "question": question,
                "catholic_answer": _scrub(catholic) if False else catholic,  # keep curated catholic
                "breakaway_group": g["name"],
                "breakaway_answer": _scrub(breakaway_ans) if "Catholic" in breakaway_ans else breakaway_ans,
                "answer_basis": "ai_historical",
                "notes": (
                    f"AI fill for catalog group `{g['id']}` paired to {council} "
                    f"(start {m['start_year']}; primary={m['primary_reason']}"
                    f"{'; temporal' if temporal else ''}). "
                    "Not yet promoted to contrast.jsonl."
                ),
                "council": entry.get("council") or council,
                "canonical_citation": entry.get("canonical_citation") or "",
                "record_id": entry.get("record_id"),
                "passage_excerpt": "",
                "draft_method": "ai_historical",
                "tier": "ai",
                "confidence": "low",
                "contrast_kind": "ai_expanded_temporal" if temporal else "ai_expanded",
                "match_mode": "temporal" if temporal else "doctrinal",
                "group_id": g["id"],
                "start_year": m["start_year"],
                "match_primary_council": council,
                "doctrinal_council": m.get("doctrinal_council"),
                "primary_distance_years": m.get("primary_distance_years"),
            }
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = "contrast_ai_temporal" if temporal else "contrast_ai"
    match_md = (
        "denomination_council_matches_temporal.md"
        if temporal
        else "denomination_council_matches_50y.md"
    )
    out_path = args.out_dir / f"{stem}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in ai_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    mode_label = "temporal / nearest-year" if temporal else "doctrinal primary"
    md = [
        f"# AI-expanded contrast (`{stem}.jsonl`)",
        "",
        "Disagreement rows for denominations from",
        f"[`{match_md}`]({match_md})",
        f"({mode_label}), with **AI-filled** breakaway answers.",
        "Does **not** replace `contrast.jsonl`.",
        "",
        f"- Match-list denominations: **{len(match_rows)}** (complete basis)",
        f"- Extra denominations kept: {len(extras)}",
        f"- AI contrast rows written: **{len(ai_rows)}**",
        f"- Skipped (same-polarity / no locus / already covered): {len(skipped)}",
        "",
        "| Group | Start | Council | Dist | Locus |",
        "|------|------:|---------|-----:|-------|",
    ]
    for r in ai_rows:
        dist = r.get("primary_distance_years")
        dist_s = "" if dist is None else str(dist)
        md.append(
            f"| {r['breakaway_group']} | {r['start_year']} | {r['match_primary_council']} | "
            f"{dist_s} | `{r['source_entry_id']}` |"
        )
    md.append("")
    (args.out_dir / f"{stem}.md").write_text("\n".join(md), encoding="utf-8")

    (args.out_dir / f"{stem}_skipped.json").write_text(
        json.dumps({"n": len(skipped), "skipped": skipped}, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    try:
        import export_contrast_viz as viz

        match_groups = [m["group_name"] for m in match_rows]
        html = viz.build_html(
            ai_rows,
            title=(
                "Catholic vs breakaway — AI temporal (nearest council)"
                if temporal
                else "Catholic vs breakaway — AI expanded (doctrinal)"
            ),
            lede=(
                "AI-filled breakaway answers using **nearest council by start year** "
                "(temporal match list). Low confidence. Comprehensive council coverage."
                if temporal
                else "AI-filled breakaway answers for denomination↔council matches "
                "(doctrinal council preference; ±50y discovery). Low confidence. "
                "Group list from denomination_council_matches_50y."
            )
            + " Not a replacement for contrast.jsonl.",
            source_name=f"{stem}.jsonl",
            regenerate_cmd=(
                f"python3 scripts/step1/expand_contrast_ai.py --mode "
                f"{'temporal' if temporal else 'doctrinal'}"
            ),
            all_groups=match_groups,
        )
        (args.out_dir / f"{stem}.html").write_text(html, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"viz skip: {exc}", file=sys.stderr)

    # Council diversity summary
    from collections import Counter

    print(
        json.dumps(
            {
                "wrote": str(out_path),
                "mode": "temporal" if temporal else "doctrinal",
                "n_ai_rows": len(ai_rows),
                "n_skipped": len(skipped),
                "n_denominations": len(match_rows),
                "n_extra": len(extras),
                "match_complete": len(_unmatched) == 0,
                "by_council": dict(
                    Counter(r["match_primary_council"] for r in ai_rows).most_common()
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
