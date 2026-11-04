#!/usr/bin/env python3
"""Build Catholic vs breakaway contrast DB from breakaway subset.

Follows the conversion rules in
outputs/step1/breakaways/contrast/agent.md
(optional LLM when OPENAI_API_KEY / STEP1_API_KEY is set).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENTRIES = ROOT / "outputs/step1/breakaways/entries.jsonl"
DEFAULT_PASSAGES = ROOT / "outputs/step1/breakaways/passages.jsonl"
DEFAULT_OUT = ROOT / "outputs/step1/breakaways/contrast"
AGENT_MD = DEFAULT_OUT / "agent.md"


# ---------------------------------------------------------------------------
# Include / exclude
# ---------------------------------------------------------------------------

# Florence OO / EO paragraphs that are ceremony, shared dogma, or non-contrast
_EXCLUDE_ID_SUFFIXES = {
    # Oriental Orthodox Florence: narrative / shared / non-distinctive
    "flo-florence-s11-bull-of-union-with-the-copts-en",
    "flo-florence-s11-p2-en",
    "flo-florence-s11-p3-en",
    "flo-florence-s11-p4-en",
    "flo-florence-s11-p6-en",  # creator God (shared)
    "flo-florence-s11-p7-en",  # OT canon list (weak OO contrast)
    "flo-florence-s11-p8-en",  # Manichees
    "flo-florence-s11-p9-en",  # Manes phantom body
    "flo-florence-s11-p10-en",  # original sin / devil (weak for OO label)
    "flo-florence-s11-p11-en",  # Mosaic law
    "flo-florence-s11-p12-en",  # infant baptism urgency
    "flo-florence-s11-p13-en",  # every creature good
    "flo-florence-s11-p15-en",  # embraces Nicaea (shared)
    "flo-florence-s11-p16-en",  # embraces Ephesus I (OO accept Ephesus)
    "flo-florence-s11-p22-en",  # form of words / Armenians
    "flo-florence-s11-p23-en",  # wheat bread baking day
    # flo-florence-s11-p24-en kept for contrast (fourth marriages — recoverable disagreement)
    "flo-florence-s11-p25-en",  # acceptance ceremony
    "flo-florence-s8-p1-en",
    "flo-florence-s8-p2-en",
    "flo-florence-s8-p3-en",
    "flo-florence-s8-p4-en",
    "flo-florence-s8-p8-en",  # sacrament scheme intro (weak distinctiveness vs Chalcedon)
    "flo-florence-s8-p9-en",  # baptism/confirmation growth (weak)
    "eph-cyril-letter3-en",  # covered by discrete anathemas
    "flo-florence-s8-p10-en",  # sacrament elements schema
    "flo-florence-s8-p11-en",  # indelible character
    "flo-florence-s8-p12-en",  # baptism first place
    "flo-florence-s8-p13-en",  # confirmation matter
    "flo-florence-s8-p14-en",  # penance matter
    "flo-florence-s8-p15-en",  # extreme unction
    "flo-florence-s8-p16-en",  # orders matter
    "flo-florence-s8-p17-en",  # matrimony
    "flo-florence-s8-p18-en",  # Athanasian intro
    "flo-florence-s8-p19-en",
    "flo-florence-s8-p20-en",
    "flo-florence-s8-p21-en",
    "flo-florence-s8-p22-en",  # Greek decree pointer
    "flo-florence-s8-p23-en",  # feast days
    "flo-florence-s8-p24-en",
    "flo-florence-s8-p25-en",
    "flo-florence-s8-p26-en",
    # flo-florence-s8-p27/p29/p31 kept for contrast (union package / water-in-wine / Filioque–purgatory–primacy)
    "flo-florence-s8-p30-en",
    "flo-florence-s8-p32-en",
    "flo-florence-s8-p33-en",
    # Eastern Orthodox Florence: ceremony / rejoicing
    "flo-florence-s6-definition-of-the-holy-ecumenical-synod-of-florence-en",
    "flo-florence-s6-p2-en",
    "flo-florence-s6-p3-en",
    "flo-florence-s6-p4-en",
    "flo-florence-s6-p5-en",
    "flo-florence-s6-p6-en",  # narrative of debate
    # Lyons: shared creed material without distinctive Latin claim
    "lyo2-profession-palaeologus-p1-en",
    "lyo2-profession-palaeologus-p2-en",
    # Constance: article lists / book process without a single answerable claim
    # (person-condemnation sentences are included separately via allowlist)
    "con-s15-sentence-condemning-260-articles-wyclif-31-en",
    "con-s8-condemnation-of-260-other-articles-of-wyclif-25-en",
    "con-s8-condemnation-of-wyclif-s-books-en",
    "con-s8-sentence-condemning-various-articles-of-john-wyclif-en",
    "con-s15-sentence-of-degradation-against-j-hus-en",
    # Ephesus: letter3 covered by discrete anathemas; letter2 included (Theotokos)
    "eph-cyril-letter3-en",
    # Trent meta only
    "trent-s22-mass-ch9-en",
    "trent-s22-mass-preamble-en",
    # Same polarity / no real Catholic–breakaway disagreement on the question as asked
    "trent-s5-original-sin-canon1-en",  # Adam’s fall: Reform interlocutors largely affirm
    "trent-s7-sacraments-canon12-en",  # unworthy minister still confers: typically shared
}

# Ephesus disciplinary canons that don't state Nestoriology
_EPH_DISCIPLINE = {
    "eph-canon1-en",
    "eph-canon3-en",
    "eph-canon5-en",
    "eph-canon8-en",
}


def is_contrastable(entry: dict, text: str) -> bool:
    eid = entry["id"]
    if eid in _EXCLUDE_ID_SUFFIXES:
        return False
    # truncated Constance id prefix match
    for bad in list(_EXCLUDE_ID_SUFFIXES):
        if eid.startswith(bad[:40]) and bad.startswith(eid[:40]):
            return False
    if eid in _EPH_DISCIPLINE:
        return False
    group = entry.get("breakaway") or ""
    if not group:
        return False
    # Always keep these councils/groups when not excluded above
    council = entry.get("council") or ""
    if group in {
        "Arian churches",
        "Melitian schism (Egypt)",
        "Waldensians",
        "Protestant churches",
        "Lutheran churches",
        "Reformed / Calvinist churches",
        "Anabaptist / Radical Reformation churches",
        "Anglican Communion / Church of England",
        "Old Catholic churches",
        "Polish National Catholic Church",
        "Philippine Independent Church (Aglipayan)",
        "Mariavite Church (Old Catholic Church of the Mariavites)",
    }:
        return True
    if group == "Wycliffites / Lollards":
        return eid not in _EXCLUDE_ID_SUFFIXES
    if group == "Hussites":
        return eid not in _EXCLUDE_ID_SUFFIXES
    if "Chalcedon" in (entry.get("canonical_citation") or ""):
        return True
    if eid.startswith("con2-"):
        return True
    if group == "Church of the East":
        return eid.startswith("eph-anathema") or eid in {
            "eph-canon2-en",
            "eph-canon7-en",
            "eph-cyril-letter2-en",
        }
    if group == "Eastern Orthodox churches":
        if eid in {
            "lyo2-profession-palaeologus-p3-en",
            "lyo2-profession-palaeologus-p4-en",
            "lyo2-profession-palaeologus-p5-en",
            "lyo2-profession-palaeologus-p6-en",
        }:
            return True
        if eid.startswith("flo-florence-s6-p"):
            return eid not in _EXCLUDE_ID_SUFFIXES
        return False
    # Oriental Orthodox family + national churches from Florence unions
    if group in {
        "Oriental Orthodox churches",
        "Armenian Apostolic Church",
        "Coptic Orthodox Church",
        "Syriac Orthodox Church",
    }:
        if eid in {
            "chal-definition-en",
            "con2-canon5-en",
            "con2-canon7-en",
            "con2-canon8-en",
        }:
            return True
        if eid in _EXCLUDE_ID_SUFFIXES:
            return False
        if eid in {
            "flo-florence-s11-p5-en",
            "flo-florence-s11-p14-en",
            "flo-florence-s11-p17-en",
            "flo-florence-s11-p18-en",
            "flo-florence-s11-p19-en",
            "flo-florence-s11-p20-en",
            "flo-florence-s11-p21-en",
            "flo-florence-s11-p24-en",
            "flo-florence-s8-p5-en",
            "flo-florence-s8-p6-en",
            "flo-florence-s8-p7-en",
            "flo-florence-s8-p27-en",
            "flo-florence-s8-p28-en",
            "flo-florence-s8-p29-en",
            "flo-florence-s8-p31-en",
            "flo-florence-s13-p8-en",
        }:
            return True
        return False
    return False


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _clean_space(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s


def _first_sentences(text: str, n: int = 2, max_chars: int = 520) -> str:
    text = _clean_space(text)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        if not p:
            continue
        out.append(p)
        if len(out) >= n:
            break
    s = " ".join(out)
    if len(s) > max_chars:
        s = s[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return s


def _ensure_q(s: str) -> str:
    s = _clean_space(s)
    if not s.endswith("?"):
        s = s.rstrip(".") + "?"
    return s


def _strip_canon_prefix(text: str) -> str:
    t = text.strip()
    t = re.sub(
        r"(?is)^CANON\s+[IVXLC\d]+[.\-–—:]?\s*",
        "",
        t,
    )
    t = re.sub(r"(?is)^CHAPTER\s+[IVXLC\d]+\.?\s*[^\.]*\.\s*", "", t)
    return t.strip()


def _extract_anathema(text: str) -> dict | None:
    """Parse anathema canons into {kind, teaching} where teaching is the Catholic claim."""
    t = _strip_canon_prefix(text)
    t = re.sub(r"^\d+\.\s*", "", t.strip())

    # If any one denieth, that TEACHING
    m = re.search(
        r"(?is)if\s+any(?:\s+one|one)\s+deni(?:eth|es),?\s*that,?\s*(.*?)"
        r"(?:;?\s*let\s+him\s+be\s+anathema\.?)",
        t,
    )
    if m:
        return {"kind": "denies", "teaching": _clean_space(m.group(1)).rstrip(" .;")}

    # If any one does not confess that TEACHING
    m = re.search(
        r"(?is)if\s+any(?:\s+one|one)\s+does\s+not\s+confess\s+that\s*(.*?)"
        r"(?:;?\s*let\s+him\s+be\s+anathema\.?)",
        t,
    )
    if m:
        return {"kind": "must_confess", "teaching": _clean_space(m.group(1)).rstrip(" .;")}

    # Whosoever shall say that ERROR / shall not confess that TEACHING
    m = re.search(
        r"(?is)whosoever\s+shall\s+not\s+(?:confess|recognize)\s+that\s+(.*?)"
        r"(?:;?\s*let\s+him\s+be\s+anathema\.?)",
        t,
    )
    if m:
        return {"kind": "must_confess", "teaching": _clean_space(m.group(1)).rstrip(" .;")}

    m = re.search(
        r"(?is)whosoever\s+shall\s+say\s+that\s+(.*?)"
        r"(?:;?\s*let\s+him\s+be\s+anathema\.?)",
        t,
    )
    if m:
        return {"kind": "error", "teaching": _clean_space(m.group(1)).rstrip(" .;")}

    # If anyone says / saith that ERROR
    m = re.search(
        r"(?is)(?:therefore,?\s+)?if\s+any(?:\s+one|one|man)\s+"
        r"(?:saith|says|shall\s+say|should\s+say|shall\s+dare\s+to\s+say|"
        r"shall\s+after|shall\s+divide|shall\s+calumniate|shall)\s*"
        r"(?:that\s*)?(.*?)"
        r"(?:;?\s*let\s+him\s+be\s+anathema\.?)",
        t,
    )
    if m:
        return {"kind": "error", "teaching": _clean_space(m.group(1)).rstrip(" .;")}

    m = re.search(
        r"(?is)if\s+anyone\s+understands\s+(.*?)"
        r"(?:;?\s*let\s+him\s+be\s+anathema\.?)",
        t,
    )
    if m:
        return {"kind": "error", "teaching": _clean_space(m.group(1)).rstrip(" .;")}
    return None


def _extract_if_anyone(text: str) -> str | None:
    parsed = _extract_anathema(text)
    return parsed["teaching"] if parsed else None


def _question_from_anathema(parsed: dict) -> str:
    teaching = parsed["teaching"]
    if teaching.lower().startswith("that "):
        teaching = teaching[5:]
    teaching = re.sub(r"^,\s*", "", teaching)
    if len(teaching) > 300:
        teaching = teaching[:297].rsplit(" ", 1)[0] + "…"
    kind = parsed["kind"]
    if kind in {"denies", "must_confess"}:
        return _ensure_q(f"Must one hold that {teaching}")
    # error proposition — ask Catholic contrary when short patterns fail
    if teaching.lower().startswith(("it is not", "there is not", "the church has erred")):
        return _ensure_q(f"Is the following false: {teaching}")
    return _ensure_q(f"Is the following error to be rejected: {teaching}")


def _question_from_condemned_prop(prop: str) -> str:
    prop = re.sub(r"^,\s*", "", prop)
    if prop.lower().startswith("that "):
        prop = prop[5:]
    if len(prop) > 300:
        prop = prop[:297].rsplit(" ", 1)[0] + "…"
    return _ensure_q(f"Is the following error to be rejected: {prop}")


def _trent_chapter_question(text: str, summary: str) -> str | None:
    m = re.match(
        r"(?is)^CHAPTER\s+[IVXLC\d]+\.\s*(That\s+)?([^\n]+?)(?:\.|$)",
        text.strip(),
    )
    title = None
    if m:
        title = _clean_space(m.group(2))
    elif summary and not summary.lower().startswith("canon"):
        title = summary.strip().rstrip(".")
    if not title:
        return None
    title = re.sub(r"(?i)^on\s+(the\s+)?", "", title)
    if re.search(r"(?i)propitiatory", title):
        return _ensure_q(
            "Is the Sacrifice of the Mass truly propitiatory for the living and the dead"
        )
    if re.search(r"(?i)institution of the most holy Sacrifice", title):
        return _ensure_q(
            "Did Christ institute the Sacrifice of the Mass as a true sacrifice of his body and blood"
        )
    if re.search(r"(?i)vulgar tongue|vulgar", title + text[:200]):
        return _ensure_q(
            "Does the Church require that the Mass not be celebrated everywhere in the vernacular, "
            "while still explaining its mysteries to the people"
        )
    if re.search(r"(?i)honour of the Saints|honor of the Saints", title):
        return _ensure_q(
            "May Masses be offered in honor of the saints"
        )
    return _ensure_q(f"Does the Catholic Church teach that {title[0].lower() + title[1:]}")


def _trent_question_from_prop(prop: str) -> str:
    """Turn condemned error into a question about the Catholic teaching."""
    p = prop
    # "that X, and denieth Y" → ask about Y / Catholic conversion
    if re.search(r"(?i)denieth that|denies that", p):
        # Eucharist transubstantiation pattern
        if re.search(r"(?i)transubstantiation|substance of the bread", p):
            return _ensure_q(
                "In the Eucharist, is the whole substance of the bread and wine "
                "converted into the body and blood of Christ, with only the appearances remaining"
            )
    if re.search(r"(?i)free will", p) and re.search(r"(?i)justif", p):
        return _ensure_q(
            "When God moves and calls a person toward justification, does that person's "
            "free will truly cooperate by assenting, rather than remaining merely passive"
        )
    if re.search(r"(?i)sacraments of the New Law", p) or re.search(
        r"(?i)more, or less, than seven", p
    ):
        return _ensure_q(
            "Are there exactly seven sacraments of the New Law, all instituted by Christ"
        )
    # Generic: "Is it true that [error]?" — better invert for Catholic framing
    # Soften: ask whether the Catholic negation holds
    if p.lower().startswith("that "):
        p = p[5:]
    # If prop is a denial, ask the positive
    m = re.match(r"(?i)(?:it is )?not\s+(.*)", p)
    if m:
        return _ensure_q(f"Is it the case that {m.group(1)}")
    return _ensure_q(
        "Does the Catholic Church rightly reject the following claim: " + p[:280]
    )


# ---------------------------------------------------------------------------
# Group answer templates (history + passage)
# ---------------------------------------------------------------------------

def _protestant_answer(citation: str, text: str, question: str) -> tuple[str, str]:
    # Prefer citation + question over body text (body often lists all seven sacraments).
    low = (citation + " " + question + " " + text[:180]).lower()
    note = (
        "Umbrella label: concrete Protestant confessions vary; answer states the "
        "Reformational position Trent is targeting."
    )
    if "penance" in low or "contrition" in low or "confession" in low:
        return (
            "Reformation churches reject mandatory auricular confession and Trent’s account "
            "of penance as a sacrament whose matter is contrition, confession, and satisfaction "
            "in that juridical sense.",
            note,
        )
    if "original sin" in low or ("adam" in low and "paradise" in low):
        return (
            "Protestant confessions affirm Adam’s fall and original sin but often describe "
            "total depravity, imputed guilt, and remaining concupiscence after baptism in ways "
            "Trent’s canons target as erroneous.",
            note,
        )
    if "priesthood" in low or "orders" in low or "consecrating and offering" in low:
        return (
            "Reformation churches reject a sacrificing ministerial priesthood as Trent "
            "defines it, teaching instead a different doctrine of ministry and often the "
            "priesthood of all believers.",
            note,
        )
    if "all christians have power" in low or "administer the word" in low:
        return (
            "Many Reformation churches teach a broad priesthood of believers and deny that "
            "sacramental ministry is restricted to Trent’s ordained hierarchy in the way "
            "this canon requires.",
            note,
        )
    if "intention" in low and "minister" in low:
        return (
            "Reformation accounts of sacramental validity often differ from Trent’s requirement "
            "that the minister intend at least to do what the Church does.",
            note,
        )
    if "mortal sin" in low and "minister" in low:
        return (
            "Reformation teaching typically denies that a minister’s personal mortal sin "
            "affects sacramental efficacy in the terms Trent debates, while also rejecting "
            "much of Trent’s sacramental system.",
            note,
        )
    if "transubstantiation" in low or (
        "eucharist" in low and "substance" in low
    ) or "species" in low:
        return (
            "Many Reformation churches reject transubstantiation. They typically teach "
            "that Christ is present spiritually or sacramentally without a conversion of "
            "the whole substance of bread and wine, or that the elements remain bread and "
            "wine while signifying or conveying Christ’s body and blood.",
            note,
        )
    if "canon of the mass" in low:
        return (
            "Reformation churches reject the Roman Canon as a pure, error-free sacrificial "
            "prayer Trent defends; they typically replace or abolish it in favor of vernacular "
            "Lord’s Supper rites without that propitiatory canon.",
            note,
        )
    if "ceremon" in low or "incense" in low or "vestment" in low:
        return (
            "Reformation churches generally deny that Trent’s solemn Mass ceremonies (lights, "
            "incense, vestments, whispered and spoken parts) are apostolic necessities; many "
            "stripped or simplified ritual as human tradition.",
            note,
        )
    if "priest alone communicates" in low or "alone communicates" in low:
        return (
            "Reformation churches typically reject private Masses in which the priest alone "
            "communicates, insisting the Lord’s Supper is a communion of the faithful, not a "
            "priestly sacrifice offered without congregational reception.",
            note,
        )
    if "water" in low and "wine" in low and ("chalice" in low or "mix" in low):
        return (
            "Many Reformation churches deny that mixing water with the wine is required by "
            "Christ or necessary to the sacrament, treating Trent’s precept as a human ceremony.",
            note,
        )
    if "sacrifice of the mass" in low or "propitiatory" in low or "mass" in low:
        return (
            "Reformation churches generally deny that the Mass is a propitiatory sacrifice "
            "offered for the living and the dead. They treat the Lord’s Supper as a "
            "commemorative and/or spiritual communion, not a repeated sacrificial offering "
            "of Christ by the priest.",
            note,
        )
    if "justif" in low:
        return (
            "Reformation teaching typically holds that justification is by grace through "
            "faith, and many classical Protestant accounts stress the passivity of the will "
            "in receiving justifying grace (against synergistic cooperation as Trent defines it).",
            note,
        )
    if "scripture" in low or "canonical" in low:
        return (
            "Reformation churches reject Trent’s closed canon as binding (especially "
            "deuterocanonical books as equal Scripture) and deny that the Church’s "
            "tradition stands alongside Scripture with equal authority in Trent’s sense.",
            note,
        )
    if "seven" in low and "sacrament" in low:
        return (
            "Reformation churches reject the claim that Christ instituted exactly seven "
            "sacraments in Trent’s list; they typically recognize baptism and the Lord’s "
            "Supper as sacraments (some add others under a broader sense) and deny "
            "Roman sacramental systematics Trent defends.",
            note,
        )
    if "sacrament" in low:
        return (
            "Reformation churches reject Trent’s sacramental teaching on this point, "
            "usually recognizing baptism and the Lord’s Supper as sacraments and denying "
            "the full Roman system Trent defends.",
            note,
        )
    if "matrimony" in low:
        return (
            "Reformation churches typically deny that marriage is a sacrament in Trent’s "
            "sense and often allow divorce/remarriage grounds Trent rejects.",
            note,
        )
    if "indulgence" in low:
        return (
            "Reformation churches reject the Church’s power to grant indulgences as Trent "
            "defends it, treating the indulgence system as unbiblical.",
            note,
        )
    if "purgatory" in low:
        return (
            "Reformation churches reject purgatory as a post-mortem purifying state where "
            "the Church’s suffrages aid the dead, as Trent teaches.",
            note,
        )
    if "saint" in low or "image" in low or "relic" in low:
        return (
            "Reformation churches generally reject the invocation of saints, veneration of "
            "relics, and sacred images as Trent decrees, regarding them as unbiblical or idolatrous.",
            note,
        )
    return (
        "Reformation churches reject the decree’s teaching on this point as contrary to "
        "Scripture and to the Reformational understanding of the gospel and the church.",
        note,
    )


def _catholic_from_anathema(prop: str, text: str) -> str:
    # Invert: Church anathematizes the error → teaches the contrary
    if re.search(r"(?i)transubstantiation|substance of the bread", prop + text[:200]):
        return (
            "The Catholic Church teaches that in the Eucharist the whole substance of bread "
            "and wine is converted into the body and blood of Christ, with only the species "
            "(appearances) remaining—a conversion it calls transubstantiation."
        )
    if re.search(r"(?i)free will", prop) and re.search(r"(?i)justif", prop + text[:100]):
        return (
            "The Catholic Church teaches that when God moves and calls a person, the free "
            "will can and does cooperate by assenting, and is not merely passive like an "
            "inanimate thing in preparing for justification."
        )
    if re.search(r"(?i)seven", prop) and re.search(r"(?i)sacrament", prop):
        return (
            "The Catholic Church teaches that Christ instituted exactly seven sacraments: "
            "Baptism, Confirmation, Eucharist, Penance, Extreme Unction, Order, and Matrimony, "
            "and that each is truly a sacrament."
        )
    if re.search(r"(?i)peter|roman pontiff|primacy", prop):
        return (
            "The Catholic Church teaches that by Christ’s institution blessed Peter has "
            "perpetual successors in the primacy over the whole Church, and that the Roman "
            "pontiff is Peter’s successor in that primacy."
        )
    # Generic
    short = _first_sentences(text, 2, 420)
    return (
        "The Catholic Church, in this decree, rejects the condemned claim and binds the "
        "contrary teaching. In substance: "
        + (short or prop[:300])
    )


def _breakaway_answer(group: str, citation: str, text: str, question: str) -> tuple[str, str]:
    notes = ""
    if group == "Arian churches":
        return (
            "Arian churches denied that the Son is consubstantial (homoousios) with the "
            "Father as Nicaea defined. They held the Son to be created or otherwise not "
            "true God in the same sense as the Father.",
            notes,
        )
    if group == "Church of the East":
        if "mother of god" in text.lower() or "theotokos" in text.lower():
            return (
                "The Church of the East historically resisted Cyril’s Ephesine settlement and "
                "preferred titles such as Mother of Christ (Christotokos) over binding reception "
                "of Theotokos as Ephesus enforced it against Nestorius; it did not enter "
                "communion on Cyril’s terms.",
                notes,
            )
        if "nestorius" in text.lower() and "deposition" in text.lower():
            return (
                "The Church of the East did not accept Ephesus’s deposition of Nestorius as "
                "binding orthodoxy; it continued a tradition that refused Cyrilline/Ephesine "
                "jurisdiction over its bishops.",
                notes,
            )
        return (
            "The Church of the East did not receive the Council of Ephesus as Rome did. It "
            "rejected the Cyrilline anathematizing of Nestorius and maintained a dyophysite "
            "confession that sharply distinguishes Christ’s divinity and humanity (two qnome), "
            "resisting Ephesus’s binding authority over its communion.",
            notes,
        )
    if group in {
        "Oriental Orthodox churches",
        "Armenian Apostolic Church",
        "Coptic Orthodox Church",
        "Syriac Orthodox Church",
    }:
        low = text.lower()
        if "proceed" in low and ("father and the son" in low or "filioque" in low):
            return (
                "Oriental Orthodox churches do not accept the Latin Filioque definition as "
                "Florence formulates eternal procession from the Father and the Son; their "
                "trinitarian confession follows the older Eastern phrasing centered on "
                "procession from the Father.",
                notes,
            )
        if "and the son" in low and "creed" in low:
            return (
                "Oriental Orthodox churches reject requiring the Constantinopolitan creed with "
                "the Latin Filioque addition as a condition of union, as Florence imposes here.",
                notes,
            )
        if "second synod of ephesus" in low or "dioscorus" in low:
            return (
                "Oriental Orthodox churches do not accept Florence’s condemnation of the second "
                "synod of Ephesus and of Dioscorus of Alexandria in these Latin terms; their "
                "tradition regards Dioscorus differently from Chalcedonian memory.",
                notes,
            )
        if "second of constantinople" in low or "fifth holy synod" in low:
            return (
                "Oriental Orthodox churches do not receive Constantinople II as Florence does, "
                "insofar as it renews Chalcedon’s two-nature definition as binding orthodoxy.",
                notes,
            )
        if "two wills" in low or ("sixth" in low and "constantinople" in low):
            return (
                "Oriental Orthodox churches do not accept Constantinople III’s dyothelete "
                "settlement as Florence requires for union; their christology is received "
                "through the pre-Chalcedonian miaphysite tradition.",
                notes,
            )
        if "roman pontiff" in low and ("universal synod" in low or "florence" in low):
            return (
                "Oriental Orthodox churches reject the claim that universal synods are those "
                "confirmed by Roman pontifical authority, and they reject Florence’s unions as "
                "binding conditions of orthodoxy.",
                notes,
            )
        if "chalcedon" in low or "two nature" in low or "leo" in low:
            return (
                "Oriental Orthodox churches reject Chalcedon’s definition of two natures "
                "united in one person after the union as Rome and Chalcedonian churches "
                "receive it. They confess a miaphysite Christology (one united nature of "
                "the Word incarnate) and do not accept Leo’s Tome / Chalcedon as the "
                "binding ecumenical settlement.",
                notes,
            )
        if "outside the catholic" in low:
            return (
                "Oriental Orthodox churches do not accept Florence’s Latin claim that those "
                "outside the Roman-defined catholic church (including their own communion) "
                "cannot be saved on Florence’s terms; they regard themselves as the "
                "orthodox church of the fathers prior to Chalcedon.",
                notes,
            )
        if "roman" in low and ("pontiff" in low or "primacy" in low or "church" in low):
            return (
                "Oriental Orthodox churches reject Latin papal supremacy as defined in the "
                "Florentine union bulls. They do not accept the Roman pontiff’s universal "
                "jurisdiction as a condition of orthodoxy.",
                notes,
            )
        if "sacrament" in low:
            return (
                "Oriental Orthodox churches have their own sacramental theology and rites; "
                "they do not accept Florence’s Latin schematization and union terms as "
                "binding conditions for communion, even where some sacramental parallels exist.",
                notes,
            )
        return (
            "Oriental Orthodox churches reject the Florentine Latin union package on this "
            "point insofar as it requires acceptance of Chalcedonian/Latin definitions "
            "foreign to their miaphysite tradition.",
            notes,
        )
    if group == "Eastern Orthodox churches":
        low = text.lower()
        if "holy spirit" in low or "filioque" in low or "from the father and the son" in low or "proceed" in low:
            return (
                "Eastern Orthodox churches teach that the Holy Spirit proceeds from the "
                "Father (alone as cause), and reject the Latin Filioque definition as "
                "Florence and Lyons formulate eternal procession from Father and Son as "
                "from one principle binding on the whole Church.",
                notes,
            )
        if ("unleavened" in low or "leavened" in low) and (
            "cleans" in low or "purgatory" in low or "suffrag" in low
        ):
            return (
                "Eastern Orthodox churches historically contested Latin azymes and reject the "
                "Florentine definition of post-mortem 'cleansing pains' (purgatory) and Latin "
                "suffrages as Rome defined them, even while praying for the dead. Florence’s "
                "compromise wording on bread did not heal the deeper dogmatic dispute.",
                notes,
            )
        if (
            "purgator" in low
            or "cleansing pains" in low
            or "purifying punishment" in low
            or "straightaway received into heaven" in low
        ):
            return (
                "Eastern Orthodox churches reject the Latin doctrine of purgatory as defined "
                "in these union texts, while affirming prayer for the dead and a mystery of "
                "purification that is not identical to the Florentine formulation.",
                notes,
            )
        if "primacy" in low or ("roman" in low and "pontiff" in low) or "apostolic see" in low:
            return (
                "Eastern Orthodox churches reject universal papal jurisdiction and the "
                "Florentine / Lyons claim that the Roman pontiff holds supreme power over "
                "the whole Church as defined there. They allow a primacy of honor to Rome "
                "in the first millennium sense, not Vatican-style supremacy.",
                notes,
            )
        if "unleavened" in low or "leavened" in low:
            return (
                "Eastern Orthodox churches insist on leavened bread in the Eucharist in their "
                "own rite and historically contested Latin azymes; they do not treat Florence’s "
                "parity formula as settling the wider ecclesiological dispute.",
                notes,
            )
        if "sacrament" in low and "seven" in low:
            return (
                "Eastern Orthodox churches affirm the mystery/sacramental life of the Church "
                "but do not accept these Latin union professions as the price of communion "
                "with Rome, especially where coupled to Filioque and papal claims.",
                notes,
            )
        return (
            "Eastern Orthodox churches reject this Latin union definition as a condition of "
            "orthodoxy, holding their own patristic consensus against Florence/Lyons on the "
            "disputed points (Filioque, primacy, and related doctrines).",
            notes,
        )
    if group == "Wycliffites / Lollards":
        if "heretic" in text.lower() or "memory" in text.lower() or "condemn" in citation.lower():
            return (
                "Wycliffites / Lollards rejected Constance’s judgment that Wyclif was a heretic "
                "whose memory and teaching were to be condemned; they continued to treat him as "
                "a gospel reformer and to circulate the contested articles.",
                notes,
            )
        return (
            "Wycliffites / Lollards defended the condemned articles (or the reform program "
            "behind them)—for example remanence views of the Eucharist, critiques of "
            "ecclesiastical dominion, and challenges to practices Constance judged heretical—"
            "against the council’s censures.",
            notes,
        )
    if group == "Hussites":
        if "jerome" in text.lower() or "jerome" in citation.lower():
            return (
                "Hussites rejected Constance’s condemnation of Jerome of Prague as a heretic; "
                "they honored him among the Bohemian reform martyrs rather than accepting the "
                "council’s sentence.",
                notes,
            )
        if "hus" in text.lower() or "hus" in citation.lower():
            return (
                "Hussites rejected Constance’s sentence that John Hus was a heretic to be "
                "condemned; they regarded him as unjustly judged and continued the Bohemian "
                "reform program the council tried to suppress.",
                notes,
            )
        return (
            "Hussites defended the condemned Hussite articles and reform demands Constance "
            "rejected—especially a predestinarian or congregational account of the church "
            "and related critiques of ecclesiastical power—rather than submitting to the "
            "council’s doctrinal censures.",
            notes,
        )
    if group in {
        "Protestant churches",
        "Lutheran churches",
        "Reformed / Calvinist churches",
        "Anabaptist / Radical Reformation churches",
        "Anglican Communion / Church of England",
    }:
        ans, note = _protestant_answer(citation, text, question)
        if group == "Lutheran churches":
            note = (
                (note + " ") if note else ""
            ) + "Primary Trent interlocutor; Reformed/Anglican/Anabaptist often share the rejection."
        return ans, note.strip()
    if group == "Old Catholic churches":
        if re.search(r"(?i)infallible|ex cathedra", text):
            return (
                "Old Catholic churches reject the First Vatican Council’s definition that "
                "the Roman pontiff, when speaking ex cathedra on faith or morals, possesses "
                "infallible teaching authority from himself (not from the consent of the Church).",
                notes,
            )
        return (
            "Old Catholic churches reject Vatican I’s definition that the Roman pontiff is, "
            "by divine law, the perpetual successor of Peter in universal primacy over the "
            "whole Church as that council defined it.",
            notes,
        )
    if group == "Melitian schism (Egypt)":
        return (
            "No. The parallel Melitian hierarchy and its claims of episcopal legitimacy are "
            "not surrendered to that Alexandrian settlement; Meletius’s party continued as "
            "a rigorist communion rather than accepting that the schism’s authority is "
            "extinguished under those terms.",
            notes,
        )
    if group == "Waldensians":
        return (
            "No. Their preaching and apostolic poverty are not condemned heresy under that "
            "regime; the anathematizing of dissenters who preach without episcopal license "
            "is refused.",
            notes,
        )
    if group in {
        "Polish National Catholic Church",
        "Philippine Independent Church (Aglipayan)",
        "Mariavite Church (Old Catholic Church of the Mariavites)",
    }:
        if re.search(r"(?i)infallible|ex cathedra|definition of ours", text):
            return (
                "No. Ex cathedra infallible teaching authority of that kind is refused; "
                "doctrinal definitions are not accepted as bound by a personal papal "
                "privilege apart from the wider Church.",
                notes,
            )
        if re.search(r"(?i)jurisdiction|supervision and guidance|ordinary and immediate", text):
            return (
                "No. The Roman pontiff does not hold full and supreme ordinary jurisdiction "
                "over the whole Church in that sense; national or independent Catholic "
                "structures govern without that absolute papal power.",
                notes,
            )
        return (
            "No. Peter’s primacy is not received as a true and proper jurisdiction over the "
            "whole militant Church in that sense; a primacy of honor or a rejected papal "
            "claim is taught instead.",
            notes,
        )
    return (
        f"{group} historically rejected or refused this conciliar determination as binding "
        "on their communion.",
        notes,
    )


# ---------------------------------------------------------------------------
# Per-locus curated overrides (highest quality)
# ---------------------------------------------------------------------------

CURATED: dict[str, dict] = {
    "eph-cyril-letter2-en": {
        "question": (
            "Is the Holy Virgin rightly called Mother of God (Theotokos) because the Word united "
            "to flesh is one Christ and one Son from two natures in true union?"
        ),
        "catholic_answer": (
            "Yes. Cyril’s second letter, approved at Ephesus, teaches that the holy Fathers called "
            "the Virgin Mother of God not because the Word’s divinity began from her, but because "
            "of him who was born from her in the flesh; the two natures being brought together in "
            "a true union, there is of both one Christ and one Son."
        ),
    },
    "eph-canon2-en": {
        "question": (
            "If bishops subscribe Nestorius’s deposition and then reverse course, are they to be "
            "treated as having joined apostasy from Ephesus’s judgment?"
        ),
        "catholic_answer": (
            "Yes. Ephesus disciplines provincial bishops who were absent or who, after "
            "subscribing Nestorius’s deposition, went back to the assembly of apostasy; such "
            "are to be removed from the priesthood."
        ),
    },
    "flo-florence-s11-p17-en": {
        "question": (
            "Should the second synod of Ephesus be condemned as impious for approving Eutychian "
            "error under Dioscorus?"
        ),
        "catholic_answer": (
            "Yes. Florence condemns, anathematizes, and rejects the second synod of Ephesus, "
            "in which Dioscorus of Alexandria, defending Eutyches and persecuting Flavian, led "
            "the synod to approve Eutychian impiety."
        ),
    },
    "flo-florence-s11-p19-en": {
        "question": (
            "Must Christians accept Constantinople II, which renewed Chalcedon’s definition of "
            "two natures in one person of Christ?"
        ),
        "catholic_answer": (
            "Yes. Florence embraces Constantinople II, which renewed Chalcedon’s definition about "
            "the two natures and the one person of Christ and condemned Origenist errors."
        ),
    },
    "flo-florence-s11-p20-en": {
        "question": (
            "Must Christians accept Constantinople III’s definition that in Christ there are two "
            "natures, two principles of action, and two wills in one person?"
        ),
        "catholic_answer": (
            "Yes. Florence embraces Constantinople III, which defined two perfect natures, two "
            "principles of action, and two wills in the one person of our Lord Jesus Christ."
        ),
    },
    "flo-florence-s11-p21-en": {
        "question": (
            "Are universal synods those legitimately confirmed by the authority of a Roman pontiff, "
            "including Florence’s unions with the Greeks and Armenians?"
        ),
        "catholic_answer": (
            "Yes. Florence teaches acceptance of universal synods confirmed by Roman pontifical "
            "authority, and especially Florence itself with its unions and definitions."
        ),
    },
    "flo-florence-s8-p5-en": {
        "question": (
            "Must the Constantinopolitan creed be received with the added phrase 'and the Son' "
            "(Filioque) and used in the Armenian churches as Florence decrees?"
        ),
        "catholic_answer": (
            "Yes. Florence gives the Armenians the creed of Constantinople with the added phrase "
            "'and the Son,' which it says was licitly added to declare the truth, and decrees that "
            "this creed be sung or read at Mass in Armenian churches on Sundays and greater feasts."
        ),
    },
    "lyo2-profession-palaeologus-p4-en": {
        "question": (
            "If the baptized die truly repentant before making full satisfaction, are their souls "
            "cleansed after death by purifying punishments, helped by Masses, prayers, and alms?"
        ),
        "catholic_answer": (
            "Yes. The Lyons profession teaches that such souls are cleansed after death by "
            "purgatorical or purifying punishments, and that offerings of the living—Masses, "
            "prayers, alms, and other duties of piety—relieve those punishments."
        ),
    },
    "lyo2-profession-palaeologus-p5-en": {
        "question": (
            "Does the Roman Church rightly teach seven sacraments and prepare the Eucharist from "
            "unleavened bread, with the bread changed into Christ’s body and the wine into his blood?"
        ),
        "catholic_answer": (
            "Yes. The Lyons profession teaches seven ecclesiastical sacraments and that the Roman "
            "Church prepares the Eucharist from unleavened bread, holding that the bread is changed "
            "into Christ’s body and the wine into his blood."
        ),
    },
    "trent-s22-mass-ch4-en": {
        "question": (
            "Is the Canon of the Mass free from error and rightly retained as the Church’s holy "
            "prayer for offering the sacrifice?"
        ),
        "catholic_answer": (
            "Yes. Trent teaches that the Catholic Church instituted the sacred Canon, so pure from "
            "every error that nothing in it fails to savour of holiness and piety, composed from "
            "the Lord’s words and apostolic and pious ordinances."
        ),
    },
    "trent-s22-mass-ch5-en": {
        "question": (
            "Has the Church rightly instituted solemn Mass ceremonies—lights, incense, vestments, "
            "and varied tones of voice—as helps to divine worship?"
        ),
        "catholic_answer": (
            "Yes. Trent teaches that holy Mother Church instituted rites and ceremonies such as "
            "mystic benedictions, lights, incense, and vestments, derived from apostolical "
            "discipline, to raise minds to the contemplation of divine things."
        ),
    },
    "trent-s22-mass-ch6-en": {
        "question": (
            "Are Masses in which the priest alone communicates sacramentally lawful and to be approved?"
        ),
        "catholic_answer": (
            "Yes. Trent prefers that the faithful present also communicate sacramentally, but "
            "approves and commends masses in which the priest alone communicates, as still true "
            "and proper sacrifices."
        ),
    },
    "trent-s22-mass-ch7-en": {
        "question": (
            "Must water be mixed with the wine in the chalice at Mass?"
        ),
        "catholic_answer": (
            "Yes. Trent notices that the Church enjoins priests to mix water with the wine offered "
            "in the chalice, as believed to follow Christ’s practice and the blood and water from "
            "his side, renewing that mystery."
        ),
    },
    "con-s8-the-council-pronounces-john-wyclif-a-heretic-condemns-his-memory-and-orde": {
        "question": (
            "Was John Wyclif rightly judged a heretic whose memory and teaching are to be condemned?"
        ),
        "catholic_answer": (
            "Yes. Constance, after process and examination of witnesses, pronounces Wyclif a "
            "heretic and condemns his memory, no defender of him having appeared."
        ),
    },
    "con-s15-sentence-against-john-hus-en": {
        "question": (
            "Was John Hus rightly condemned by Constance as a heretic for obstinately holding "
            "Wycliffite and related errors?"
        ),
        "catholic_answer": (
            "Yes. Constance sentences John Hus as a heretic, treating him as a noxious successor "
            "of Wyclif’s teaching and judging him obstinate against the catholic faith as the "
            "council defined it."
        ),
    },
    "con-s21-sentence-condemning-jerome-of-prague-en": {
        "question": (
            "Was Jerome of Prague rightly condemned by Constance as a heretic?"
        ),
        "catholic_answer": (
            "Yes. Constance, in its inquiry into heresy, condemns Jerome of Prague as not abiding "
            "in Christ according to the council’s judgment of his teaching and conduct."
        ),
    },
    "nic1-creed-en": {
        "question": "Is the Son of God true God from true God, begotten not made, consubstantial with the Father?",
        "catholic_answer": (
            "Yes. The Nicene Creed confesses one Lord Jesus Christ, the only-begotten Son of God, "
            "God from God, Light from Light, true God from true God, begotten not made, "
            "consubstantial (homoousios) with the Father, through whom all things were made."
        ),
    },
    "chal-definition-en": {
        "question": (
            "After the Incarnation, is Jesus Christ to be confessed in two natures, without "
            "confusion, change, division, or separation, united in one person and one hypostasis?"
        ),
        "catholic_answer": (
            "Yes. Chalcedon defines that the one and the same Son, our Lord Jesus Christ, is "
            "perfect in deity and perfect in humanity, consubstantial with the Father as to "
            "deity and with us as to humanity, made known in two natures without confusion, "
            "change, division, or separation, the property of each nature preserved and "
            "concurring in one person and one hypostasis."
        ),
    },
    "flo-florence-s6-p7-en": {
        "question": (
            "Does the Holy Spirit proceed eternally from the Father and the Son as from one "
            "principle and a single spiration?"
        ),
        "catholic_answer": (
            "Yes. Florence defines that the Holy Spirit is eternally from the Father and the "
            "Son, has his essence and subsistent being from the Father together with the Son, "
            "and proceeds from both eternally as from one principle and a single spiration."
        ),
    },
    "flo-florence-s6-p8-en": {
        "question": (
            "Because the Father gave the Son everything except being the Father, does the Son "
            "also have it from the Father that the Holy Spirit proceeds from the Son?"
        ),
        "catholic_answer": (
            "Yes. Florence teaches that since the Father gave his only-begotten Son in begetting "
            "him everything the Father has except to be the Father, the Son eternally has from "
            "the Father that the Holy Spirit proceeds from the Son."
        ),
    },
    "flo-florence-s6-p9-en": {
        "question": (
            "Was it licit to add the explanation 'and from the Son' (Filioque) to the Creed "
            "for the sake of declaring the truth?"
        ),
        "catholic_answer": (
            "Yes. Florence defines that the explanation of those words 'and from the Son' was "
            "licitly and reasonably added to the Creed for the sake of declaring the truth and "
            "under urgent necessity."
        ),
    },
    "pa-ch2-canon1-en": {
        "question": (
            "Is it by Christ’s own institution that Peter has perpetual successors in the "
            "primacy over the whole Church, and is the Roman pontiff that successor?"
        ),
        "catholic_answer": (
            "Yes. Vatican I teaches that by divine law blessed Peter has perpetual successors "
            "in the primacy over the whole Church, and that the Roman pontiff is Peter’s "
            "successor in that primacy."
        ),
    },
    "pa-ch4-p9-en": {
        "question": (
            "When the Roman pontiff speaks ex cathedra defining a doctrine of faith or morals "
            "to be held by the whole Church, does he possess infallible teaching authority?"
        ),
        "catholic_answer": (
            "Yes. Vatican I defines that when the Roman pontiff speaks ex cathedra—exercising "
            "his office as shepherd and teacher of all Christians, by his supreme apostolic "
            "authority, defining a doctrine of faith or morals to be held by the whole Church—"
            "he possesses, by the divine assistance promised to him in blessed Peter, that "
            "infallibility with which the divine Redeemer willed his Church to be endowed."
        ),
    },
    "con-s15-condemned-articles-of-j-hus-en": {
        "question": (
            "Is the one holy universal church identical with the total number of those "
            "predestined to salvation?"
        ),
        "catholic_answer": (
            "No. Constance condemned this Hussite article. The Catholic Church does not equate "
            "the visible universal church simply with the set of the predestined in the sense "
            "Hus’s condemned articles taught."
        ),
    },
    "con-s15-articles-of-john-wyclif-selected-from-the-260-en": {
        "question": (
            "After consecration, does the host remain true bread in nature while being Christ’s "
            "body only figuratively (remanence)?"
        ),
        "catholic_answer": (
            "No. Constance condemned Wyclif’s article that the consecrated host is at once "
            "Christ’s body and true bread in nature (body only in figure). Catholic teaching "
            "holds the real conversion of the substance; the bread does not remain in substance."
        ),
    },
    "trent-s13-eucharist-canon2-en": {
        "question": (
            "In the Eucharist, is the whole substance of bread and wine converted into Christ’s "
            "body and blood, with only the appearances remaining (transubstantiation)?"
        ),
        "catholic_answer": (
            "Yes. Trent anathematizes anyone who says the substance of bread and wine remains "
            "conjointly with Christ’s body and blood and denies that conversion which the "
            "Church calls transubstantiation."
        ),
    },
    "trent-s7-sacraments-canon1-en": {
        "question": (
            "Did Christ institute exactly seven sacraments—Baptism, Confirmation, Eucharist, "
            "Penance, Extreme Unction, Order, and Matrimony?"
        ),
        "catholic_answer": (
            "Yes. Trent teaches that the sacraments of the New Law are neither more nor fewer "
            "than these seven, all instituted by Christ, and each truly a sacrament."
        ),
    },
    "trent-s6-justification-canon4-en": {
        "question": (
            "In coming to justification, does the human free will cooperate by assenting to "
            "God’s call, rather than remaining wholly passive?"
        ),
        "catholic_answer": (
            "Yes. Trent rejects the claim that free will, moved by God, in no way cooperates "
            "and is merely passive; Catholic teaching holds that the will can assent or refuse."
        ),
    },
    "flo-florence-s6-p10-en": {
        "question": (
            "Is Christ’s body truly confected in both unleavened and leavened bread, and are "
            "souls who die penitent but without full satisfaction cleansed after death by "
            "cleansing pains, aided by the Church’s suffrages?"
        ),
        "catholic_answer": (
            "Yes. Florence teaches that the body of Christ is truly confected in either "
            "unleavened or leavened wheat bread according to each church’s custom, and that "
            "truly penitent souls who die in God’s love before making full satisfaction are "
            "cleansed after death by cleansing pains, helped by the suffrages of the living."
        ),
    },
    "flo-florence-s6-p11-en": {
        "question": (
            "Do souls free of sin (or cleansed of it) go straight to the beatific vision, while "
            "those dying in mortal or original sin alone go straight to hell?"
        ),
        "catholic_answer": (
            "Yes. Florence defines that purified souls are straightaway received into heaven "
            "and behold the triune God, graded by merits, while those who die in actual mortal "
            "sin or in original sin alone go down straightaway to hell, though with unequal pains. "
            "It also defines the holy apostolic see and the Roman pontiff hold primacy over the "
            "whole world (as continued in the definition)."
        ),
    },
    "flo-florence-s6-p12-en": {
        "question": (
            "Does the Roman pontiff rank first among the patriarchs, with Constantinople second, "
            "then Alexandria, Antioch, and Jerusalem?"
        ),
        "catholic_answer": (
            "Yes. Florence renews the canonical order: the patriarch of Constantinople second "
            "after the most holy Roman pontiff, then Alexandria, Antioch, and Jerusalem, without "
            "prejudice to their privileges."
        ),
    },
    "flo-florence-s11-p5-en": {
        "question": (
            "Does the Holy Spirit proceed from the Father and the Son, as the holy Roman church "
            "professes in its teaching on the Trinity?"
        ),
        "catholic_answer": (
            "Yes. Florence’s union bull with the Copts professes one God in three persons, with "
            "the Holy Spirit proceeding from the Father and the Son."
        ),
    },
    "flo-florence-s11-p14-en": {
        "question": (
            "Can anyone outside the Catholic Church—pagans, Jews, heretics, or schismatics—"
            "share eternal life unless joined to that Church before death?"
        ),
        "catholic_answer": (
            "Florence professes that those outside the Catholic Church cannot share eternal life "
            "and will go into everlasting fire unless joined to the Catholic Church before the "
            "end of their lives, so great is the unity of the ecclesiastical body."
        ),
    },
    "flo-florence-s11-p18-en": {
        "question": (
            "Must Christians embrace the Council of Chalcedon (630 fathers) as a universal "
            "council of the Church?"
        ),
        "catholic_answer": (
            "Yes. Florence’s union text embraces, approves, and accepts Chalcedon as fourth "
            "among the universal synods."
        ),
    },
    "flo-florence-s8-p6-en": {
        "question": (
            "Must the Armenians (and those entering Latin union) accept Chalcedon’s definition "
            "of two natures in the one person of Christ?"
        ),
        "catholic_answer": (
            "Yes. Florence gives them Chalcedon’s definition of two natures in the one person "
            "of Christ, later renewed in the fifth and sixth universal councils, as part of "
            "the union teaching."
        ),
    },
    "flo-florence-s8-p28-en": {
        "question": (
            "Did Chalcedon and Pope Leo rightly define the truth about two natures in Christ?"
        ),
        "catholic_answer": (
            "Yes. The Florentine Armenian decree declares that the synod of Chalcedon and most "
            "blessed pope Leo rightly defined the truth about two natures."
        ),
    },
    "lyo2-profession-palaeologus-p3-en": {
        "question": (
            "Is the Holy Spirit true God, proceeding from the Father and the Son?"
        ),
        "catholic_answer": (
            "Yes. The Lyons II profession (Michael VIII Palaeologus) confesses the Holy Spirit "
            "as complete and true God, proceeding from the Father and the Son, coequal and "
            "consubstantial with the Father and the Son."
        ),
    },
    "lyo2-profession-palaeologus-p6-en": {
        "question": (
            "Does the Roman Church hold the highest and complete primacy and spiritual power "
            "over the universal Catholic Church, received in Peter by the Roman pontiff?"
        ),
        "catholic_answer": (
            "Yes. The Lyons profession teaches that the holy Roman Church holds the highest and "
            "complete primacy and spiritual power over the universal Catholic Church, received "
            "with fullness of power from the Lord in blessed Peter, whose successor is the "
            "Roman pontiff."
        ),
    },
    "eph-canon7-en": {
        "question": (
            "Is it unlawful to compose or introduce a creed different from the faith of Nicaea "
            "as received by the Council of Ephesus?"
        ),
        "catholic_answer": (
            "Yes. Ephesus decreed it unlawful to bring forward, write, or compose a different "
            "faith as a rival to that established by the fathers at Nicaea, and disciplines "
            "those who dare to offer another creed."
        ),
    },
    "eph-anathema3-en": {
        "question": (
            "After the hypostatic union, may one divide the hypostases in the one Christ as "
            "joined only by worthiness or authority rather than by natural union?"
        ),
        "catholic_answer": (
            "No. Cyril’s third anathema (received at Ephesus) anathematizes anyone who after "
            "the hypostatic union divides the hypostases in the one Christ, joining them only "
            "by worthiness or authority rather than by a natural union."
        ),
    },
    "eph-anathema4-en": {
        "question": (
            "May scriptural sayings about Christ be divided between two persons—some to a man "
            "apart from the Word, others only to the Word as God?"
        ),
        "catholic_answer": (
            "No. Cyril’s fourth anathema condemns dividing evangelical and apostolic expressions "
            "about Christ between two persons or subsistences in that Nestorianizing way."
        ),
    },
    "eph-anathema8-en": {
        "question": (
            "Is the assumed man to be worshipped together with the Word as two different things, "
            "or is Emmanuel worshipped with one adoration?"
        ),
        "catholic_answer": (
            "Emmanuel is worshipped with one adoration. Cyril’s eighth anathema rejects saying "
            "the assumed man is worshipped together with the Word as two different things."
        ),
    },
    "eph-anathema9-en": {
        "question": (
            "Was the one Lord Jesus Christ glorified by the Holy Spirit as using a power not "
            "his own, or as his own Spirit working miracles?"
        ),
        "catholic_answer": (
            "Cyril’s ninth anathema rejects the claim that Christ was glorified by the Spirit "
            "through a power not his own; the Spirit is his own, working wonders."
        ),
    },
    "eph-anathema10-en": {
        "question": (
            "Is our Great High Priest the divine Word made flesh himself, or another man "
            "distinct from the Word?"
        ),
        "catholic_answer": (
            "The divine Word made flesh is himself our Great High Priest and Apostle; Cyril’s "
            "tenth anathema rejects positing another man distinct from him who offers sacrifice."
        ),
    },
    "eph-anathema11-en": {
        "question": (
            "Does the flesh of the Lord give life because it is the Word’s own flesh?"
        ),
        "catholic_answer": (
            "Yes. Cyril’s eleventh anathema requires confessing that the Lord’s flesh gives life "
            "and pertains to the Word of God the Father as his very own."
        ),
    },
    "eph-anathema12-en": {
        "question": (
            "Did the Word of God suffer, get crucified, and taste death in the flesh?"
        ),
        "catholic_answer": (
            "Yes. Cyril’s twelfth anathema requires recognizing that the Word of God suffered "
            "in the flesh, was crucified in the flesh, and tasted death in that same flesh."
        ),
    },
    "flo-florence-s8-p7-en": {
        "question": (
            "Must the Armenians accept Chalcedon and Pope Leo, contrary to the claim that both "
            "taught Nestorius’s heresy?"
        ),
        "catholic_answer": (
            "Yes. Florence declares false the suggestion that Chalcedon and Leo defined according "
            "to Nestorius’s heresy, and instructs the Armenians to accept those later synods and Leo."
        ),
    },
    "con2-canon5-en": {
        "question": (
            "When Chalcedon speaks of one person/hypostasis of Christ, does that mean a Nestorian "
            "union of many hypostases, or the Word united to flesh in one hypostasis?"
        ),
        "catholic_answer": (
            "Constantinople II anathematizes reading Chalcedon’s ‘one person’ as a mere union of "
            "many hypostases in the Nestorian sense; the Word of God is united to flesh hypostatically "
            "as Chalcedon rightly meant."
        ),
    },
    "trent-s5-original-sin-canon1-en": {
        "question": (
            "Did Adam, by transgressing God’s commandment, lose holiness and justice, incur death "
            "and the devil’s captivity, and harm the whole human race?"
        ),
        "catholic_answer": (
            "Yes. Trent requires confessing that Adam immediately lost the holiness and justice "
            "in which he was constituted, incurred God’s wrath and death, captivity under the devil, "
            "and that the entire Adam through that offence was changed for the worse in body and soul."
        ),
    },
    "trent-s14-penance-canon4-en": {
        "question": (
            "For the entire remission of sins in the sacrament of Penance, are contrition, "
            "confession, and satisfaction required as its three parts?"
        ),
        "catholic_answer": (
            "Yes. Trent teaches that three acts in the penitent—contrition, confession, and "
            "satisfaction—are as it were the matter of the sacrament of Penance, and rejects "
            "reducing penance to terror of conscience plus faith alone."
        ),
    },
    "trent-s23-orders-canon1-en": {
        "question": (
            "Is there in the New Testament a visible priesthood with power to consecrate and "
            "offer Christ’s body and blood and to forgive and retain sins?"
        ),
        "catholic_answer": (
            "Yes. Trent anathematizes anyone who says there is no visible external priesthood, "
            "or no power of consecrating and offering the true body and blood of the Lord and "
            "of forgiving and retaining sins, but only an office of preaching."
        ),
    },
    "trent-s7-sacraments-canon10-en": {
        "question": "Do all Christians have power to administer the word and all the sacraments?",
        "catholic_answer": (
            "No. Trent anathematizes anyone who says that all Christians have power to administer "
            "the word and all the sacraments."
        ),
    },
    "trent-s7-sacraments-canon11-en": {
        "question": (
            "When ministers confer the sacraments, must they intend at least to do what the Church does?"
        ),
        "catholic_answer": (
            "Yes. Trent requires in ministers, when they effect and confer the sacraments, the "
            "intention at least of doing what the Church does."
        ),
    },
    "trent-s7-sacraments-canon12-en": {
        "question": (
            "Does a minister in mortal sin, observing the essentials, still truly effect or "
            "confer the sacrament?"
        ),
        "catholic_answer": (
            "Yes. Trent anathematizes anyone who says a minister in mortal sin, observing the "
            "essentials, neither effects nor confers the sacrament."
        ),
    },
    "trent-s24-matrimony-canon7-en": {
        "question": (
            "Has the Church erred in teaching that the marriage bond cannot be dissolved by "
            "adultery and that neither party may marry another during the other’s life?"
        ),
        "catholic_answer": (
            "No. Trent teaches that the Church has not erred: the bond of matrimony cannot be "
            "dissolved on account of adultery, and neither spouse may marry another during the "
            "other’s lifetime."
        ),
    },
    "trent-s22-mass-ch1-en": {
        "question": (
            "Did Christ institute the Sacrifice of the Mass as a true sacrifice of his body and blood?"
        ),
        "catholic_answer": (
            "Yes. Trent teaches the institution of the most holy Sacrifice of the Mass, in which "
            "Christ left to the Church a visible sacrifice as the bloody sacrifice of the cross "
            "is represented and its memory continued."
        ),
    },
    "trent-s22-mass-ch3-en": {
        "question": "May Masses be offered in honor of the saints?",
        "catholic_answer": (
            "Yes. Trent teaches that it is good and useful to offer Masses in honor of the saints "
            "to obtain their intercession, while the sacrifice is still offered to God alone."
        ),
    },
    "trent-s22-mass-ch8-en": {
        "question": (
            "Does the Church forbid celebrating the Mass everywhere in the vernacular, while "
            "requiring that its mysteries be explained to the people?"
        ),
        "catholic_answer": (
            "Yes. Trent teaches that it has not judged it expedient that the Mass be everywhere "
            "celebrated in the vulgar tongue, yet pastors must frequently explain something of "
            "its mysteries to the people."
        ),
    },
    "trent-s22-mass-ch2-en": {
        "question": (
            "Is the Sacrifice of the Mass truly propitiatory for both the living and the dead?"
        ),
        "catholic_answer": (
            "Yes. Trent teaches that in the Mass the same Christ who offered himself bloody "
            "on the cross is contained and immolated in an unbloody manner, and that this "
            "sacrifice is truly propitiatory for the living and the dead."
        ),
    },
    "trent-s4-scripture-decree-en": {
        "question": (
            "Has the Church authoritatively fixed the canon of Scripture, including the "
            "deuterocanonical books, and must sacred tradition be received with Scripture?"
        ),
        "catholic_answer": (
            "Yes. Trent, to preserve the purity of the Gospel, receives the sacred books with "
            "their traditional canon and treats apostolic traditions concerning faith and morals "
            "with equal piety and reverence alongside Scripture."
        ),
    },
    "trent-s25-purgatory-decree-en": {
        "question": "Is there a purgatory, and can the souls detained there be helped by the suffrages of the faithful?",
        "catholic_answer": (
            "Yes. Trent teaches that there is a purgatory and that the souls there detained are "
            "helped by the suffrages of the faithful, especially the acceptable sacrifice of the altar."
        ),
    },
    "trent-s25-indulgences-decree-en": {
        "question": "Did Christ grant the Church power to confer indulgences, and should that power be used?",
        "catholic_answer": (
            "Yes. Trent teaches that the power of conferring indulgences was granted by Christ "
            "to the Church and that she has used it even in ancient times; it condemns those "
            "who say indulgences are useless or that the Church has no power to grant them."
        ),
    },
    "trent-s25-saints-images-decree-en": {
        "question": (
            "Should the faithful invoke the saints, venerate their relics, and honor sacred images?"
        ),
        "catholic_answer": (
            "Yes. Trent decrees the invocation of saints, the veneration of relics, and the "
            "lawful use of sacred images, against those who reject these practices."
        ),
    },
}


def _load_extra_curated() -> dict[str, dict]:
    path = DEFAULT_OUT / "_new_curated.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    # normalize to CURATED shape
    out = {}
    for eid, d in data.items():
        out[eid] = {
            "question": d["question"],
            "catholic_answer": d["catholic_answer"],
        }
    return out


def _load_direct_answers() -> dict[str, dict]:
    path = DEFAULT_OUT / "direct_answers.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def convert_heuristic(entry: dict, text: str) -> dict | None:
    if not is_contrastable(entry, text):
        return None

    eid = entry["id"]
    group = entry["breakaway"]
    citation = entry.get("canonical_citation") or ""

    curated = CURATED.get(eid) or _load_extra_curated().get(eid)
    if curated:
        question = curated["question"]
        catholic = curated["catholic_answer"]
    else:
        parsed = _extract_anathema(text)
        ch_q = _trent_chapter_question(text, entry.get("decision_summary") or "")
        if parsed and re.search(
            r"(?i)(if\s+any|whosoever\s+shall|let\s+him\s+be\s+anathema)", text[:800]
        ):
            tq = _trent_question_from_prop(parsed["teaching"])
            if tq.startswith("Does the Catholic Church rightly reject"):
                question = _question_from_anathema(parsed)
            else:
                question = tq
            catholic = _catholic_from_anathema(parsed["teaching"], text)
        elif ch_q and "Trent" in citation:
            question = ch_q
            catholic = "Yes. " + _first_sentences(text, 2, 420)
        elif group in {"Wycliffites / Lollards", "Hussites"}:
            claim = entry.get("decision_summary") or _first_sentences(text, 1, 240)
            claim = re.sub(r"^\d+\.\s*", "", claim)
            if len(claim) < 40 or claim.lower().startswith("the twelve"):
                claim = _first_sentences(text, 1, 260)
            question = _ensure_q(f"Is the following true: {claim[:300]}")
            catholic = (
                "No. The Council of Constance judged this article heretical (or part of a "
                "condemned set) and bound Catholics to reject it. "
                + _first_sentences(text, 1, 280)
            )
        elif re.search(
            r"(?i)firmly believes, professes|we define|we (?:teach|believe)|it firmly believes|"
            r"the same holy roman church",
            text[:500],
        ):
            claim = _first_sentences(text, 2, 360)
            claim_q = re.sub(
                r"(?i)^(also,?\s*)?(it|the holy roman church|we|the same holy.*?church)\s+"
                r"(firmly\s+)?(believes|professes|teaches|preaches|defines|holds|declare[sd]?)"
                r"(?: and (?:professes|teaches|preaches|holds))*\s*(?:that\s*)?",
                "",
                claim,
            )
            claim_q = _clean_space(claim_q)
            if len(claim_q) < 40:
                claim_q = claim
            question = _ensure_q(f"Is it to be believed that {claim_q[:300]}")
            catholic = "Yes. " + _first_sentences(text, 2, 420)
        else:
            theme = (entry.get("decision_summary") or "").strip()
            # Avoid thin labels like "The Twelve Anathemas…, 10"
            if (
                len(theme) < 40
                or re.search(r"(?i)anathemas of|^canon\s+\d+", theme)
                or theme.lower() == citation.lower()
            ):
                theme = _first_sentences(text, 1, 260)
            theme = re.sub(
                r"(?i)^according to .*?,\s*did the council teach or decree the following:\s*",
                "",
                theme,
            )
            if re.search(r"(?i)let him be anathema", text):
                prop2 = _extract_if_anyone(text) or theme
                question = _question_from_condemned_prop(prop2)
                catholic = _catholic_from_anathema(prop2, text)
            else:
                question = _ensure_q(
                    f"Is the following conciliar teaching true: {theme[:300]}"
                )
                catholic = (
                    "Yes. The Catholic Church affirms this conciliar teaching. "
                    + _first_sentences(text, 2, 360)
                )

    b_ans, notes = _breakaway_answer(group, citation, text, question)
    # Prefer hand-tuned answers that respond directly to the question
    direct = _load_direct_answers().get(eid) or {}
    if direct.get("catholic_answer"):
        catholic = direct["catholic_answer"]
    if direct.get("breakaway_answer"):
        b_ans = direct["breakaway_answer"]
    row = {
        "id": eid,
        "question": question,
        "catholic_answer": _clean_space(catholic),
        "breakaway_group": group,
        "breakaway_answer": _clean_space(b_ans),
        "answer_basis": "passage+history",
        "notes": notes,
        "council": entry.get("council"),
        "canonical_citation": citation,
        "record_id": entry.get("record_id"),
        "passage_excerpt": _first_sentences(text, 3, 500),
        "source_entry_id": eid,
    }
    return row


# ---------------------------------------------------------------------------
# Optional LLM path
# ---------------------------------------------------------------------------

def convert_llm(entry: dict, text: str, *, model: str, base_url: str, api_key: str) -> dict | None:
    if not is_contrastable(entry, text):
        return None
    system = (AGENT_MD.read_text(encoding="utf-8") if AGENT_MD.exists() else "") + (
        "\n\nRespond with a single JSON object matching the output schema. "
        "If the locus should be excluded, respond {\"exclude\": true}."
    )
    user = {
        "entry_id": entry["id"],
        "council": entry.get("council"),
        "canonical_citation": entry.get("canonical_citation"),
        "breakaway": entry.get("breakaway"),
        "decision_summary": entry.get("decision_summary"),
        "legacy_question": entry.get("question"),
        "passage_text": text[:6000],
    }
    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    data = json.loads(body["choices"][0]["message"]["content"])
    if data.get("exclude"):
        return None
    return {
        "id": entry["id"],
        "question": data["question"],
        "catholic_answer": data["catholic_answer"],
        "breakaway_group": entry["breakaway"],
        "breakaway_answer": data["breakaway_answer"],
        "answer_basis": data.get("answer_basis") or "passage+history",
        "notes": data.get("notes") or "",
        "council": entry.get("council"),
        "canonical_citation": entry.get("canonical_citation"),
        "record_id": entry.get("record_id"),
        "passage_excerpt": _first_sentences(text, 3, 500),
        "source_entry_id": entry["id"],
        "draft_method": "llm",
    }


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entries", type=Path, default=DEFAULT_ENTRIES)
    ap.add_argument("--passages", type=Path, default=DEFAULT_PASSAGES)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--mode",
        choices=("heuristic", "llm", "auto"),
        default="auto",
        help="auto uses LLM when API key present",
    )
    ap.add_argument("--model", default=os.environ.get("STEP1_MODEL", "gpt-4o-mini"))
    ap.add_argument(
        "--base-url",
        default=os.environ.get("STEP1_BASE_URL", "https://api.openai.com/v1"),
    )
    args = ap.parse_args()

    api_key = os.environ.get("STEP1_API_KEY") or os.environ.get("OPENAI_API_KEY")
    mode = args.mode
    if mode == "auto":
        mode = "llm" if api_key else "heuristic"
    if mode == "llm" and not api_key:
        print("LLM mode requires OPENAI_API_KEY or STEP1_API_KEY", file=sys.stderr)
        return 1

    entries = load_jsonl(args.entries)
    passages = {p["entry_id"]: p for p in load_jsonl(args.passages)}

    out_rows: list[dict] = []
    skipped = 0
    for entry in entries:
        pas = passages.get(entry["id"]) or {}
        text = pas.get("text") or ""
        if mode == "llm":
            try:
                row = convert_llm(
                    entry,
                    text,
                    model=args.model,
                    base_url=args.base_url,
                    api_key=api_key,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"LLM fail {entry['id']}: {exc}; falling back", file=sys.stderr)
                row = convert_heuristic(entry, text)
                if row:
                    row["draft_method"] = "heuristic_fallback"
        else:
            row = convert_heuristic(entry, text)
            if row:
                row["draft_method"] = "heuristic"
        if row is None:
            skipped += 1
            continue
        out_rows.append(row)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "contrast.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_group: dict[str, int] = {}
    by_council: dict[str, int] = {}
    for r in out_rows:
        by_group[r["breakaway_group"]] = by_group.get(r["breakaway_group"], 0) + 1
        by_council[r["council"] or "?"] = by_council.get(r["council"] or "?", 0) + 1

    summary = {
        "n_contrast": len(out_rows),
        "n_source_breakaways": len(entries),
        "n_excluded_not_contrastable": skipped,
        "mode": mode,
        "by_breakaway_group": dict(sorted(by_group.items(), key=lambda x: -x[1])),
        "by_council": dict(sorted(by_council.items(), key=lambda x: -x[1])),
        "agent_prompt": "agent.md",
        "files": ["contrast.jsonl", "contrast.html", "agent.md", "README.md", "summary.json"],
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    readme = f"""# Contrast database (Catholic vs breakaway)

Natural-language questions drawn from the breakaway-tagged Step 1 subset,
each with an explicit **Catholic** answer and the tagged **breakaway** answer.

Built only where both answers can be traced from the council passage plus
established historical positions (see include/exclude rules in `agent.md`).

**{len(out_rows)} contrast rows** · source breakaways {len(entries)} · excluded {skipped} · mode `{mode}`

## Files

| File | Role |
|------|------|
| `contrast.jsonl` | One JSON object per contrast question |
| `contrast.html` | Interactive viewer (question + both answers + citation) |
| `direct_answers.json` | Hand-tuned answers that respond Yes/No to each question |
| `agent.md` | Conversion prompt / rules (NL question + dual answers) |
| `summary.json` | Counts |

## Schema

```json
{{
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
}}
```

## By breakaway group

{chr(10).join(f"- **{k}** — {v}" for k, v in summary["by_breakaway_group"].items())}

## By council

{chr(10).join(f"- {k} — {v}" for k, v in summary["by_council"].items())}

## Regenerate

```bash
python scripts/step1/build_contrast_db.py
python scripts/step1/export_contrast_viz.py
# optional LLM (uses agent.md as system prompt):
# OPENAI_API_KEY=… python scripts/step1/build_contrast_db.py --mode llm
```
"""
    (args.out_dir / "README.md").write_text(readme, encoding="utf-8")

    # Keep the HTML viewer in sync
    try:
        import importlib.util

        viz_mod_path = Path(__file__).with_name("export_contrast_viz.py")
        spec = importlib.util.spec_from_file_location("export_contrast_viz", viz_mod_path)
        if spec and spec.loader:
            viz_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(viz_mod)
            (args.out_dir / "contrast.html").write_text(
                viz_mod.build_html(out_rows), encoding="utf-8"
            )
    except Exception as exc:  # noqa: BLE001
        print(f"viz skip: {exc}", file=sys.stderr)

    # Point parent breakaways README at contrast/
    parent_readme = ROOT / "outputs/step1/breakaways/README.md"
    if parent_readme.exists():
        body = parent_readme.read_text(encoding="utf-8")
        marker = "## Contrast database"
        block = (
            "## Contrast database\n\n"
            "Natural-language questions with Catholic vs breakaway answers "
            f"(explicit-trace subset): [`contrast/`](contrast/) "
            f"({len(out_rows)} rows). Conversion rules: "
            "[`contrast/agent.md`](contrast/agent.md). "
            "Viewer: [`contrast/contrast.html`](contrast/contrast.html).\n"
        )
        if marker in body:
            # replace section until next ## or end
            body = re.sub(
                r"## Contrast database\n.*?(?=\n## |\Z)",
                block + "\n",
                body,
                flags=re.S,
            )
        else:
            # insert after Files table block / before Lineage
            if "## Lineage catalog" in body:
                body = body.replace("## Lineage catalog", block + "\n## Lineage catalog")
            else:
                body = body.rstrip() + "\n\n" + block
        parent_readme.write_text(body, encoding="utf-8")

    print(
        json.dumps(
            {
                "wrote": str(out_path),
                "n": len(out_rows),
                "excluded": skipped,
                "mode": mode,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
