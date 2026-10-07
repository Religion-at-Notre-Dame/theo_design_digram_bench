#!/usr/bin/env python3
"""Audit groups_catalog.json for factual breakaway status and parent links.

Removes non-breakaways / duplicates / synthetic scaffolding that implies false
schisms; corrects broke_from where the attributed parent is historically wrong;
recomputes lineage + separation_degree; regenerates groups.md.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "outputs" / "step1" / "breakaways" / "groups_catalog.json"
GROUPS_MD = ROOT / "outputs" / "step1" / "breakaways" / "groups.md"

# Moved out of `groups` — not breakaways (or not usable as breakaway nodes).
EXCLUDED = {
    "eastern-catholic-note": (
        "Eastern Catholic churches (Byzantine, Maronite, Chaldean, Syro-Malabar, "
        "etc.) are in full communion with Rome; not breakaways."
    ),
    "maronites-note": (
        "Maronite Church is an Eastern Catholic church in full communion with Rome; "
        "not a breakaway."
    ),
    "cathars": (
        "Cathar/Albigensian networks are contested as a durable ‘church’; excluded "
        "under the formal breakaway definition (see root README / clean_breakaways)."
    ),
    "sspx": (
        "Society of St. Pius X claims Catholic identity and the same communion; "
        "Rome treats it as irregular, not a separate church. Excluded under the "
        "formal definition (rejecting implementation while claiming same communion)."
    ),
    "assyrian-church-of-the-east": (
        "Duplicate naming of the same historic Church of the East patriarchate; "
        "canonical catalog id is church-of-the-east (Assyrian Church of the East "
        "is the common modern English name for that body)."
    ),
    "oriental-orthodox-twahedo-split-note": (
        "Synthetic alias of eritrean-orthodox; removed as redundant."
    ),
    "congregationalist-approx": (
        "Synthetic milieu node, not a historical church people broke from."
    ),
    "protestant-missions-umbrella": (
        "Synthetic umbrella, not a church; children reattached to real parents."
    ),
    "african-instituted-churches": (
        "Scholarly category, not a parent church; Kimbanguist/Aladura reattached "
        "to concrete mission contexts."
    ),
    "messianic-jewish": (
        "Modern Messianic congregations are not a schism from Baptist churches; "
        "mixed evangelical parentage — removed rather than assert a false parent."
    ),
    "pietist-movements": (
        "Pietism was largely an intra-Lutheran renewal; not a single durable "
        "separated communion."
    ),
    "oriental-orthodox": (
        "Modern family name for non-Chalcedonian miaphysite churches. Not a church "
        "polity that groups broke from; dogmatic rupture is Chalcedon (see each "
        "national church). Tracked under family_labels when present."
    ),
}

# Explicit broke_from corrections (after removals).
REPARENT: dict[str, str] = {
    # Oriental Orthodoxy: national churches’ dogmatic rupture is Chalcedon with
    # the imperial/Catholic communion. Jurisdictional children below.
    "ethiopian-orthodox": "coptic-orthodox",  # historic Coptic metropolitanate → autocephaly 1959
    "malankara-orthodox": "syriac-orthodox",  # 1912 autocephaly vs Antioch
    "jacobite-syrian-malankara": "syriac-orthodox",  # Antiochene jurisdiction in India (not a split *from* MOSC)
    # False parent
    "iglesia-ni-cristo": "catholic-church",  # Manalo founded INC independently; rejected Aglipayan as still Catholic-like
    "latter-day-saints": "catholic-church",  # restorationist NRM; not a Stone–Campbell schism
    "christian-science": "puritan-separatists",  # New England Protestant milieu (not a synthetic node)
    "kimbanguist": "baptist",  # arose among Baptist-mission converts in Belgian Congo
    "aladura": "anglican",  # Nigerian prayer-healing churches from Anglican/mission Protestant context
    "unitarian": "puritan-separatists",  # Anglo-American Unitarianism from Congregational/Separatist soil (Transylvanian stream noted in notes)
    "swedenborgian": "anglican",  # New Church organized in England (1787+); Swedenborg’s Lutheran background is biographical
}

# Field-level factual patches (applied if group remains).
PATCHES: dict[str, dict] = {
    "church-of-the-east": {
        "name": "Church of the East (Assyrian Church of the East)",
        "summary": (
            "East Syriac dyophysite patriarchate that did not accept Ephesus’s "
            "condemnation of Nestorius; modern English name often ‘Assyrian Church of the East’."
        ),
        "notes": (
            "Canonical id for this communion. ‘Assyrian Church of the East’ is the "
            "usual modern name, not a separate breakaway."
        ),
    },
    "oriental-orthodox": {
        "status": "synthetic",
        "confidence": "established",
        "relation": "family_label",
        "summary": (
            "Modern family label for the non-Chalcedonian (miaphysite) churches "
            "(Coptic, Syriac, Armenian, Ethiopian, Eritrean, Malankara). Not a polity "
            "that national churches ‘broke from’; dogmatic rupture is Chalcedon."
        ),
        "notes": (
            "Synthetic family node for reference only. National OO churches break from "
            "catholic-church (or from a jurisdictional OO parent), not from this label."
        ),
    },
    "ethiopian-orthodox": {
        "approx_rupture": "Coptic jurisdiction → autocephaly 1959 (miaphysite via Alexandria after 451)",
        "rupture_year": 1959,
        "summary": (
            "Tewahedo church historically under the Coptic Orthodox Church of Alexandria; "
            "autocephalous since 1959. Miaphysite identity via Coptic / non-Chalcedonian lineage."
        ),
        "confidence": "established",
        "notes": (
            "broke_from=coptic-orthodox is jurisdictional/autocephalous history. "
            "Dogmatic separation from Catholic/imperial Chalcedonian communion is inherited via Coptic Orthodoxy."
        ),
    },
    "malankara-orthodox": {
        "approx_rupture": "1912 autocephaly (Malankara Orthodox Syrian Church)",
        "rupture_year": 1912,
        "summary": (
            "Indian Orthodox church of West Syriac liturgy that asserted autocephaly "
            "vis-à-vis the Syriac Orthodox Patriarchate of Antioch (1912)."
        ),
        "notes": (
            "Earlier Malankara Christianity has layered East/West Syriac and colonial history; "
            "primary modern broke_from for this body is syriac-orthodox (autocephaly dispute)."
        ),
    },
    "jacobite-syrian-malankara": {
        "approx_rupture": "ongoing Antiochene jurisdiction; 20th-c. Malankara disputes",
        "rupture_year": 1912,
        "summary": (
            "Malankara church under the Syriac Orthodox Patriarch of Antioch "
            "(Jacobite Syrian Christian Church), as distinct from the autocephalous "
            "Malankara Orthodox Syrian Church."
        ),
        "notes": (
            "Not a breakaway *from* the Malankara Orthodox Syrian Church; both parties "
            "contest succession within Malankara. Catalog parent is syriac-orthodox "
            "(patriarchal jurisdiction)."
        ),
        "confidence": "established",
    },
    "iglesia-ni-cristo": {
        "approx_rupture": "1914",
        "rupture_year": 1914,
        "summary": (
            "Restorationist church founded by Félix Manalo (registered 1914). "
            "Independent of the Philippine Independent Church; Manalo rejected Aglipayan "
            "doctrine as still essentially Catholic."
        ),
        "notes": (
            "Prior catalog parent philippine-independent was incorrect. INC is a new "
            "restorationist body (Manalo had earlier Methodist and Adventist periods)."
        ),
        "confidence": "established",
        "relation": "restorationist_foundation",
    },
    "latter-day-saints": {
        "approx_rupture": "1830",
        "rupture_year": 1830,
        "summary": (
            "Church of Jesus Christ of Latter-day Saints founded by Joseph Smith as a "
            "restoration of primitive Christianity, not as a schism from the Stone–Campbell "
            "Restoration Movement."
        ),
        "notes": (
            "Prior broke_from=restoration-movement was historically false (parallel American "
            "restorationism, not a Campbellite split). Graph parent is catholic-church as the "
            "communion the movement claims was lost in apostasy; self-understanding is "
            "restoration, not Protestant denominational schism. confidence=contested for "
            "‘breakaway’ typology."
        ),
        "confidence": "contested",
        "relation": "restorationist_foundation",
    },
    "christian-science": {
        "summary": (
            "Church of Christ, Scientist founded by Mary Baker Eddy (1879) in New England "
            "Protestant culture; not a clean jurisdictional schism from a single denomination."
        ),
        "notes": (
            "broke_from=puritan-separatists is a cultural/lineage heuristic (Congregational "
            "New England), not a recorded congregational secession vote."
        ),
        "confidence": "contested",
        "relation": "new_religious_movement",
    },
    "kimbanguist": {
        "summary": (
            "Church of Jesus Christ on Earth by the Prophet Simon Kimbangu; arose among "
            "Baptist-mission Christians in the Belgian Congo and became an independent AIC."
        ),
        "notes": "Parent baptist = mission context, not a formal Baptist denominational schism decree.",
        "confidence": "contested",
    },
    "aladura": {
        "summary": (
            "Yoruba prayer-healing (Aladura) churches in Nigeria emerging from Anglican and "
            "other Protestant mission settings (e.g. Christ Apostolic Church, Cherubim and Seraphim)."
        ),
        "notes": "Parent anglican = primary mission context; some bodies have Methodist links.",
        "confidence": "contested",
    },
    "unitarian": {
        "summary": (
            "Anti-Trinitarian and later liberal Protestant churches. Anglo-American Unitarianism "
            "grew mainly from Congregational/Separatist settings; Transylvanian Unitarianism is "
            "an earlier, separate continental stream."
        ),
        "notes": (
            "broke_from=puritan-separatists tracks the Anglo-American story used elsewhere in "
            "this catalog; Transylvanian Unitarian Church is not a child of English Separatism."
        ),
        "confidence": "contested",
    },
    "swedenborgian": {
        "summary": (
            "New Church / Swedenborgian bodies organized from the late 18th century, especially "
            "in England, on the basis of Emanuel Swedenborg’s writings."
        ),
        "notes": (
            "Swedenborg was a Lutheran by background; the institutional New Church is best "
            "attached here to the English/Anglican religious setting of its organization."
        ),
        "confidence": "contested",
    },
    "presbyterian": {
        "relation": "polity_expression_not_schism",
        "confidence": "contested",
        "summary": (
            "Reformed churches with Presbyterian polity (e.g. Church of Scotland). Generally "
            "the Scottish/English form of the Reformed Reformation, not a later schism *from* "
            "continental Reformed churches."
        ),
        "notes": (
            "Kept for tracing later American Presbyterian-linked movements (e.g. Restoration "
            "Movement leaders). Do not read broke_from=reformed as a 16th-c. secession event."
        ),
    },
    "missouri-synod": {
        "relation": "immigrant_organization_not_schism",
        "confidence": "contested",
        "summary": (
            "Lutheran Church–Missouri Synod organized (1847) by Saxon and other Lutheran "
            "immigrants in the U.S.; not founded as a schism from a single existing Lutheran "
            "synod abroad."
        ),
        "notes": (
            "broke_from=lutheran means confessional tradition parentage. Later LCMS fellowship "
            "disputes with other U.S. Lutherans are separate from the 1847 founding."
        ),
    },
    "chinese-patriotic": {
        "confidence": "contested",
        "relation": "contested_communion",
        "notes": (
            "State-supervised Catholic structures; many participants still claim Catholic "
            "identity. Contested whether this is schism versus coerced jurisdictional control. "
            "Not a clean classic breakaway."
        ),
    },
    "sedevacantist-bodies": {
        "confidence": "contested",
        "notes": (
            "Hold the Holy See vacant and operate separate hierarchies/chapels. They claim "
            "to be the Catholic Church, not a new denomination; included as separated "
            "sacramental networks with contested typology."
        ),
    },
    "charismatic-renewal-independents": {
        "confidence": "contested",
        "notes": (
            "Umbrella for independent charismatic networks; parentage is mixed "
            "(Pentecostal, Baptist, Reformed, and some Catholic charismatic). "
            "broke_from=pentecostal is a simplification."
        ),
    },
    "united-church-of-christ": {
        "confidence": "contested",
        "notes": (
            "1957 merger of Congregational Christian Churches and the Evangelical and Reformed "
            "Church. broke_from=puritan-separatists reflects only the Congregational side; "
            "E&R is German Reformed."
        ),
    },
    "russian-orthodox-church-abroad": {
        "notes": (
            "Émigré Russian Orthodox jurisdiction formed amid Bolshevik-era disruption; "
            "conflict was with the Moscow Patriarchate’s situation, not a rejection of "
            "Eastern Orthodoxy as such. broke_from=eastern-orthodox is an umbrella parent."
        ),
        "confidence": "established",
    },
    "acna": {
        "notes": (
            "Formed by conservatives leaving The Episcopal Church and Anglican Church of "
            "Canada (and related realignments). broke_from=anglican = Anglican Communion umbrella."
        ),
    },
    "continuing-anglican": {
        "notes": (
            "Continuing churches after the 1977 Congress of St. Louis, chiefly from "
            "The Episcopal Church / Anglican realignment — not a break from every Anglican province."
        ),
    },
}


def recompute_lineage(groups_by_id: dict[str, dict]) -> None:
    for gid, g in groups_by_id.items():
        chain: list[str] = []
        seen: set[str] = set()
        cur: str | None = gid
        while cur and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            if cur == "catholic-church":
                break
            parent = groups_by_id.get(cur, {}).get("broke_from")
            if not parent:
                if cur != "catholic-church":
                    chain.append("catholic-church")
                break
            cur = parent
        chain = list(reversed(chain))
        if chain[0] != "catholic-church":
            chain = ["catholic-church"] + [c for c in chain if c != "catholic-church"]
        g["lineage"] = chain
        # degree = steps after catholic-church; synthetic family-only node at d1 stays 1
        if g.get("broke_from") is None and g.get("status") == "synthetic":
            g["separation_degree"] = 0
        else:
            g["separation_degree"] = max(0, len(chain) - 1)


def main() -> int:
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    original_ids = [g["id"] for g in cat["groups"]]

    # Preserve prior exclusions (ids already removed from groups on earlier runs).
    prior_excluded = {
        r["id"]: r for r in (cat.get("excluded_non_breakaways") or []) if r.get("id")
    }
    for gid, reason in EXCLUDED.items():
        prior_excluded.setdefault(
            gid,
            {"id": gid, "name": gid, "reason": reason, "former_status": None},
        )
        prior_excluded[gid]["reason"] = reason

    excluded_records = []
    kept = []
    for g in cat["groups"]:
        gid = g["id"]
        if gid in EXCLUDED:
            prior_excluded[gid] = {
                "id": gid,
                "name": g.get("name"),
                "reason": EXCLUDED[gid],
                "former_status": g.get("status"),
            }
            continue
        kept.append(g)
    excluded_records = sorted(prior_excluded.values(), key=lambda r: r["id"])

    by_id = {g["id"]: g for g in kept}

    # Reparent
    for gid, parent in REPARENT.items():
        if gid not in by_id:
            continue
        if parent != "catholic-church" and parent not in by_id:
            raise SystemExit(f"Missing parent {parent} for {gid}")
        by_id[gid]["broke_from"] = parent

    # Patches
    for gid, patch in PATCHES.items():
        if gid not in by_id:
            continue
        by_id[gid].update(patch)

    # Ensure oriental-orthodox not used as broke_from by anyone
    for g in by_id.values():
        if g.get("broke_from") == "oriental-orthodox":
            g["broke_from"] = "catholic-church"
            g.setdefault("notes", "")
            g["notes"] = (
                (g.get("notes") or "")
                + " Parent reset from oriental-orthodox family label to catholic-church "
                "(Chalcedonian rupture)."
            ).strip()

    # Clear null broke_from for real groups (only synthetic family may be odd)
    for g in by_id.values():
        if g["id"] == "oriental-orthodox":
            g["broke_from"] = "catholic-church"
            g["separation_degree"] = 1

    recompute_lineage(by_id)

    # Stable-ish order: by degree then rupture_year then name
    groups = sorted(
        by_id.values(),
        key=lambda g: (
            g.get("separation_degree") or 0,
            g.get("rupture_year") is None,
            g.get("rupture_year") or 0,
            g.get("name") or "",
        ),
    )

    cat["groups"] = groups
    cat["excluded_non_breakaways"] = excluded_records
    # Family labels (not breakaway polities)
    cat["family_labels"] = [
        {
            "id": "oriental-orthodox",
            "name": "Oriental Orthodox churches",
            "member_ids": [
                "coptic-orthodox",
                "syriac-orthodox",
                "armenian-apostolic",
                "ethiopian-orthodox",
                "eritrean-orthodox",
                "malankara-orthodox",
                "jacobite-syrian-malankara",
                "mar-thoma",
            ],
            "reason": EXCLUDED["oriental-orthodox"],
        }
    ]
    cat["description"] = (
        "Reference catalog of ecclesial communities for tracing breakaway lineages "
        "from the Catholic Church, including groups at separation_degree > 1. "
        "Only breakaway (or carefully marked synthetic/contested) nodes appear in "
        "`groups`. Communion bodies such as Eastern Catholics are listed under "
        "`excluded_non_breakaways`, not as breakaways."
    )
    cat["preference"] = (
        "Prefer durable communal identities. Mark contested cases. Synthetic nodes "
        "must not imply a false schism. Degree follows the primary broke_from chain. "
        "For each breakaway, prefer a concrete council locus; otherwise summarize. "
        "Eastern Catholics and other in-communion bodies are excluded from `groups`."
    )

    # Stats
    by_degree: dict[str, int] = {}
    status_counts = {"extant": 0, "historical": 0, "synthetic": 0, "contested_flag": 0}
    locus = summary = 0
    step1 = 0
    for g in groups:
        d = str(g.get("separation_degree", 0))
        by_degree[d] = by_degree.get(d, 0) + 1
        st = g.get("status")
        if st in status_counts:
            status_counts[st] += 1
        if g.get("confidence") == "contested":
            status_counts["contested_flag"] += 1
        if g.get("in_step1_breakaways"):
            step1 += 1
        kind = (g.get("disagreement") or {}).get("kind")
        if kind == "council_locus":
            locus += 1
        elif kind == "summary":
            summary += 1

    cat["stats"] = {
        "group_count": len(groups),
        "by_degree": dict(sorted(by_degree.items(), key=lambda kv: int(kv[0]))),
        "in_step1_true": step1,
        "extant": status_counts["extant"],
        "historical": status_counts["historical"],
        "synthetic": status_counts["synthetic"],
        "contested_confidence": status_counts["contested_flag"],
        "excluded_non_breakaways": len(excluded_records),
        "with_council_locus": locus,
        "with_summary_only": summary,
        "disagreement_coverage": locus + summary,
    }

    CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # groups.md
    lines = [
        "# Breakaway groups over time (lineage catalog)",
        "",
        "Machine-readable source: [`groups_catalog.json`](groups_catalog.json).",
        "",
        "Eastern Catholics and other **non-breakaways** are listed under "
        "`excluded_non_breakaways` in the JSON, not in this table.",
        "",
        f"**{cat['stats']['group_count']} groups** · "
        f"locus-linked: {cat['stats']['with_council_locus']} · "
        f"summary-only: {cat['stats']['with_summary_only']} · "
        f"excluded non-breakaways: {cat['stats']['excluded_non_breakaways']}",
        "",
        "| Deg | Group | Broke from | Disagreement | Kind | Confidence |",
        "|---:|---|---|---|---|---|",
    ]
    name_of = {g["id"]: g["name"] for g in groups}
    name_of["catholic-church"] = "Catholic Church"
    for g in groups:
        d = g.get("disagreement") or {}
        kind = d.get("kind", "")
        if kind == "council_locus":
            tip = f"`{d.get('canonical_citation', '')}` — {d.get('summary', '')}"
        else:
            tip = d.get("summary") or g.get("summary") or ""
        tip = tip.replace("|", "/").replace("\n", " ")
        if len(tip) > 120:
            tip = tip[:117] + "..."
        parent = g.get("broke_from") or "—"
        parent_name = name_of.get(parent, parent)
        lines.append(
            f"| {g.get('separation_degree')} | {g['name']} | {parent_name} | {tip} | "
            f"{kind} | {g.get('confidence', '')} |"
        )
    lines.extend(
        [
            "",
            "## Excluded (not breakaways)",
            "",
        ]
    )
    for r in cat["excluded_non_breakaways"]:
        lines.append(f"- **{r['name']}** (`{r['id']}`): {r['reason']}")
    lines.append("")
    GROUPS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    removed = [i for i in original_ids if i not in by_id]
    print(f"kept {len(groups)} groups; excluded/removed {len(removed)}: {', '.join(removed)}")
    print("reparents:")
    for gid, parent in sorted(REPARENT.items()):
        if gid in by_id:
            print(f"  {gid} -> {parent} (degree {by_id[gid]['separation_degree']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
