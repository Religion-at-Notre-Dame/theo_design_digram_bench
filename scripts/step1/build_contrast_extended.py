#!/usr/bin/env python3
"""Build contrast_extended.jsonl: disagreement-only, loosened recoverability.

Does NOT modify contrast.jsonl (status quo / explicit-trace).
Copies strict rows, then adds previously excluded loci only when the breakaway
stance is inferred *opposition* (not shared affirmation, ceremony, or narrative).

Expansion goal: more breakaway groups with real disagreement — never Yes/Yes
or “no distinctive doctrinal rupture” padding.
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

DEFAULT_ENTRIES = ROOT / "outputs/step1/breakaways/entries.jsonl"
DEFAULT_PASSAGES = ROOT / "outputs/step1/breakaways/passages.jsonl"
DEFAULT_STRICT = ROOT / "outputs/step1/breakaways/contrast/contrast.jsonl"
DEFAULT_OUT = ROOT / "outputs/step1/breakaways/contrast"


_SHARED_HINT = re.compile(
    r"(?i)\b("
    r"manich|manes|two first principles|creator of all|"
    r"consubstantial with the Father|embrace(?:s|d)? (?:the )?(?:holy )?(?:synod|council) of Nicaea|"
    r"Ephesus I|first of Ephesus|"
    r"mutual love|rejoic|united with the holy|within three years|"
    r"abbott? andrew|acceptance|envoy|ambassador|"
    r"feast day|fourth marriage|wheat bread|baking|"
    r"every creature of God is good|mosaic (?:law|ceremonial)|"
    r"infant baptism|forty or eighty days"
    r")\b"
)

_CEREMONY_HINT = re.compile(
    r"(?i)\b(rejoic|united with|bull of union|acceptance|envoy|ceremony|"
    r"definition of the holy ecumenical synod|narrative of debate|"
    r"promise.+obey|recite the .+acceptance|word by word|"
    r"feast|annunciation|athanasian|long-desired union)\b"
)

# Florence union narrative paragraphs that are not themselves contrast claims
_FLORENCE_CEREMONY_IDS = {
    "flo-florence-s8-p1-en",
    "flo-florence-s8-p2-en",
    "flo-florence-s8-p3-en",
    "flo-florence-s8-p4-en",
    "flo-florence-s8-p18-en",
    "flo-florence-s8-p19-en",
    "flo-florence-s8-p20-en",
    "flo-florence-s8-p21-en",
    "flo-florence-s8-p22-en",
    "flo-florence-s8-p23-en",
    "flo-florence-s8-p24-en",
    "flo-florence-s8-p25-en",
    "flo-florence-s8-p26-en",
    "flo-florence-s8-p30-en",
    "flo-florence-s8-p32-en",
    "flo-florence-s8-p33-en",
    "flo-florence-s11-bull-of-union-with-the-copts-en",
    "flo-florence-s11-p2-en",
    "flo-florence-s11-p3-en",
    "flo-florence-s11-p4-en",
    "flo-florence-s11-p22-en",
    "flo-florence-s11-p23-en",
    "flo-florence-s11-p25-en",
}


def _classify_loose(entry: dict, text: str) -> str:
    eid = entry.get("id") or ""
    if eid in _FLORENCE_CEREMONY_IDS:
        # Athanasian / feast / acceptance machinery: treat as shared or ceremonial
        if re.search(r"(?i)athanasian|whoever wills to be saved|trinity in unity", text[:500]):
            return "likely_shared"
        return "ceremony_or_narrative"
    blob = " ".join(
        [
            entry.get("question") or "",
            entry.get("decision_summary") or "",
            text[:900],
        ]
    )
    if _CEREMONY_HINT.search(blob) and not re.search(
        r"(?i)chalcedon|filioque|proceed from the Father and the Son|two natures|primacy",
        blob,
    ):
        return "ceremony_or_narrative"
    if _SHARED_HINT.search(blob) and not re.search(
        r"(?i)chalcedon|filioque|two natures|papal|outside the catholic",
        blob,
    ):
        return "likely_shared"
    return "inferred_opposition"


_NAME_SCRUB = re.compile(
    r"(?i)\b(?:"
    r"(?:the\s+)?"
    r"(?:"
    r"Catholic Church|holy Roman church|Roman church|Roman pontiff|Roman see|"
    r"Oriental Orthodox(?:\s+churches?)?|Eastern Orthodox(?:\s+churches?)?|"
    r"Armenian Apostolic(?:\s+Church)?|Coptic Orthodox(?:\s+Church)?|"
    r"Syriac Orthodox(?:\s+Church)?|Church of the East|Arian churches?|"
    r"Lutheran churches?|Protestant(?:\s+churches?| confessions?)?|"
    r"Reformation churches?|Old Catholic churches?|"
    r"Wycliffites?(?:\s*/\s*Lollards)?|Lollards?|Hussites?|"
    r"this tradition|"
    r"Council of (?:Trent|Florence|Ephesus|Chalcedon|Constance|Nicaea)|"
    r"(?:First|Second|Third)?\s*Council of (?:Lyons|Constantinople|Nicaea|Vatican)|"
    r"(?:First|Second)?\s*Vatican Council|"
    r"Trent|Florence|Ephesus|Chalcedon|Constance|Lyons(?:\s+II)?|"
    r"Nicaea(?:\s+I)?|Constantinople(?:\s+I{1,3})?|"
    r"Florentine|Tridentine|Ephesine|Cyrilline|"
    r"Latin union(?:\s+package|\s+terms)?|union bull(?:s)?|"
    r"John\s+Wyclif|Wyclif|Hus|Nestorius"
    r")"
    r")\b"
)


def _scrub_names(s: str) -> str:
    """Remove church/council/document proper names from answer text."""
    s = _NAME_SCRUB.sub("", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"\bthe\s+(?=[,.])", "", s)
    # Orphan possessives only when the name was fully removed (" ’s books")
    s = re.sub(r"(?i)(?:^|\s)(?:’s|'s)\s+", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    # Leading verb after subject scrub ("teaches that…")
    s = re.sub(
        r"(?i)^(teaches|professes|defines|anathematizes|condemns|embraces)\s+that\b",
        "It is taught that",
        s,
    )
    s = re.sub(r"(?i)^teaches\b", "It is taught", s)
    s = re.sub(r"(?i)\bthe Church\b", "the rite", s)
    s = re.sub(
        r"(?i)\b(?:Armenian|Coptic|Jacobite|Greek)\s+(envoys?|acceptance|patriarch)\b",
        r"the \1",
        s,
    )
    s = re.sub(r"(?i)\bthe (?:Armenians|Copts|Jacobites|Greeks)\b", "the envoys", s)
    s = re.sub(r"(?i)\b(?:Armenian|Coptic|Jacobite|Greek)s?\b", "", s)
    s = re.sub(r"(?i)\bapostolic see\b", "that see", s)
    s = re.sub(r"(?i)\bLatin/Chalcedonian\b", "that", s)
    s = re.sub(r"(?i)\bChalcedonian\b", "", s)
    s = re.sub(r"(?i)\b(?:the\s+)?Latin\b", "", s)
    s = re.sub(r"(?i)\bThe the\b", "The", s)
    s = re.sub(r"\s{2,}", " ", s)
    return bcd._clean_space(s).strip(" ,;")


def _claim_from_question(question: str) -> str:
    """Short claim fragment (may still need wrapping into a full sentence)."""
    q = bcd._clean_space(question).rstrip("?")
    q = re.sub(r"(?i)^is it to be believed that\s+", "", q)
    q = re.sub(r"(?i)^the\s+following(?:\s+conciliar\s+teaching)?\s+true:\s*", "", q)
    q = re.sub(r"(?i)^the\s+following\s+(?:error\s+)?(?:to be rejected|true):\s*", "", q)
    q = re.sub(r"(?i)^is the following true:\s*", "", q)
    return bcd._clean_space(q)


def _third_singular(verb: str) -> str:
    v = verb.lower()
    if v.endswith(("ss", "sh", "ch", "x", "z", "o")):
        return verb + "es"
    if v.endswith("y") and len(v) > 1 and v[-2] not in "aeiou":
        return verb[:-1] + "ies"
    if not v.endswith("s"):
        return verb + "s"
    return verb


def _affirmative_from_question(question: str) -> str:
    """Best-effort declarative sentence from a Yes/No question (no names)."""
    q = bcd._clean_space(question).rstrip("?")
    low = q.lower()

    if low.startswith("if "):
        # "If X, is he Y?" / "If X, are they Y?"
        m = re.search(
            r"(?i)^if\s+(.+?),\s*(is|are|does|do|must|should)\s+(he|she|they|it)\s+(.+)$",
            q,
        )
        if m:
            cond, _aux, _subj, cons = m.group(1), m.group(2), m.group(3), m.group(4)
            return _scrub_names(
                f"When {cond[0].lower() + cond[1:]}, that person is {cons}."
                if _aux.lower() == "is"
                else f"When {cond[0].lower() + cond[1:]}, they are {cons}."
            )
        m = re.search(
            r"(?i)^if\s+(.+?),\s*(?:is|are|does|do|must|should)\s+(.+)$",
            q,
        )
        if m:
            cond, cons = m.group(1).strip(), m.group(2).strip()
            return _scrub_names(
                f"When {cond[0].lower() + cond[1:]}, {cons}."
            )
        return (
            "When the stated condition holds, the stated disciplinary consequence follows."
        )

    if re.match(r"(?i)^is the following error to be rejected\b", q):
        body = re.sub(r"(?i)^is the following error to be rejected:\s*", "", q)
        return _scrub_names(f"That claim is rejected as erroneous: {body}.")

    # Are/Is + subject + past participle / complement
    m = re.match(r"(?i)^(is|are)\s+(.+)$", q)
    if m:
        aux, rest = m.group(1).lower(), m.group(2).strip()
        # "Are all sacraments effected only when…"
        m2 = re.match(
            r"(?i)^(.+?)\s+"
            r"(effected|conferred|converted|required|present|true|identical|"
            r"lawful|unlawful|valid|binding)\b(.*)$",
            rest,
        )
        if m2:
            subj, part, tail = m2.group(1), m2.group(2), m2.group(3)
            return _scrub_names(
                f"{subj[0].upper() + subj[1:]} {aux} {part}{tail}."
            )
        return _scrub_names(f"{rest[0].upper() + rest[1:]}.")

    # Has/Have …
    m = re.match(r"(?i)^(has|have)\s+(.+)$", q)
    if m:
        rest = m.group(2).strip()
        rest = re.sub(
            r"(?i)^(?:[\w’'-]+(?:\s+[\w’'-]+){0,4})\s+(confirmed|granted|united|built)\b",
            r"\1",
            rest,
            count=1,
        )
        return _scrub_names(f"It has {rest}.")

    # Does/Did/Must/Should/May/Can …
    m = re.match(
        r"(?i)^(does|did|must|should|may|can|ought)\s+(?:it\s+be\s+believed\s+that\s+)?(.+)$",
        q,
    )
    if m:
        aux, rest = m.group(1).lower(), m.group(2).strip()
        if aux in {"must", "should", "may", "can", "ought"}:
            if re.match(r"(?i)^whoever\b", rest):
                # "Must whoever wills to be saved hold the catholic faith…"
                rest = re.sub(
                    r"(?i)^whoever\s+(wills to be saved)\s+(hold)\b",
                    r"Whoever \1 must \2",
                    rest,
                    count=1,
                )
                return _scrub_names(rest[0].upper() + rest[1:] + ".")
            # "Must the Armenians celebrate X" → "One must celebrate X"
            rest2 = re.sub(
                r"(?i)^(?:the\s+)?(?:[\w’'-]+(?:\s+[\w’'-]+){0,3})\s+",
                "",
                rest,
                count=1,
            )
            if re.match(r"(?i)^(celebrate|accept|embrace|hold|confess|believe)\b", rest2):
                return _scrub_names(f"One {aux} {rest2}.")
            return _scrub_names(f"One {aux} {rest}.")
        if aux == "did":
            # "Did this decree rejoice that X" / "Did Florence give…"
            m2 = re.match(
                r"(?i)^(?:this\s+)?(decree|bull|synod|text)\s+"
                r"(rejoice|state|declare|give|deliver|include|offer)\s+(.*)$",
                rest,
            )
            if m2:
                noun, verb, obj = m2.group(1), m2.group(2), m2.group(3)
                v3 = _third_singular(verb)
                if verb.lower() == "rejoice":
                    return _scrub_names(f"The {noun} gives thanks that {obj}.")
                return _scrub_names(f"The {noun} {v3} {obj}.")
            return _scrub_names(rest[0].upper() + rest[1:] + ".")
        if aux == "does":
            # "Does this decree rejoice that X"
            m_dec = re.match(
                r"(?i)^(?:this\s+)?(decree|bull|synod|text)\s+"
                r"(rejoice|state|declare|give|deliver|include|offer|teach|accept)\s+(.*)$",
                rest,
            )
            if m_dec:
                noun, verb, obj = m_dec.group(1), m_dec.group(2), m_dec.group(3)
                obj = re.sub(r"(?i)^that\s+", "", obj)
                if verb.lower() == "rejoice":
                    return _scrub_names(f"The {noun} gives thanks that {obj}.")
                if verb.lower() == "teach":
                    return _scrub_names(f"It is taught that {obj}.")
                return _scrub_names(f"The {noun} {_third_singular(verb)} {obj}.")
            # Prefer content after a scrubbed institutional subject:
            # "Does Trent teach that X" / "Does the Church anathematize X"
            m2 = re.match(
                r"(?i)^(?:[\w’'-]+(?:\s+[\w’'-]+){0,4})\s+"
                r"(anathematize|confess|teach|accept|embrace|confer|remain|"
                r"require|hold|profess|define|reject|condemn|publish|find|rejoice)\s+(.*)$",
                rest,
            )
            if m2:
                verb, obj = m2.group(1), m2.group(2)
                obj = re.sub(r"(?i),\s+and confess that\b", ", and confesses that", obj)
                obj = re.sub(r"(?i)\bthe Church\b", "the rite", obj)
                if verb.lower() == "teach":
                    return _scrub_names(f"It is taught {obj}.")
                if verb.lower() == "rejoice":
                    return _scrub_names(f"Thanks are given that {obj}.")
                return _scrub_names(f"It {_third_singular(verb).lower()} {obj}.")
            rest = re.sub(
                r"(?i)^((?:[\w’'-]+\s+){0,5}?)(\banathematize|confess|teach|accept|embrace|"
                r"confer|remain|require|hold|profess|define|reject|condemn|publish|find)\b",
                lambda mm: mm.group(1) + _third_singular(mm.group(2)),
                rest,
                count=1,
            )
            rest = re.sub(r"(?i)\bteachs\b", "teaches", rest)
            return _scrub_names(rest[0].upper() + rest[1:] + ".")
        return _scrub_names(f"{aux.capitalize()} {rest}.")

    claim = _claim_from_question(question)
    if claim:
        return _scrub_names(claim[0].upper() + claim[1:] + ".")
    return "The teaching asked in the question is affirmed."


def _ensure_direct(ans: str, *, default_lead: str) -> str:
    ans = bcd._clean_space(ans)
    if not re.match(r"(?i)^(yes|no)\b", ans):
        ans = f"{default_lead} {ans}"
    return ans


def _direct_catholic(question: str, text: str, entry: dict) -> str:
    """Yes/No + positive stance; no passage dump; no church/council names."""
    q = question
    low_q = q.lower()
    group = entry.get("breakaway") or ""

    # Condemned articles: Catholic rejects the article's claim
    if group in {"Wycliffites / Lollards", "Hussites"} and re.search(
        r"(?i)^is the following true:", q
    ):
        return (
            "No. That article is rejected as contrary to the faith; the opposite "
            "teaching is to be held."
        )

    # Process / book-condemnation questions (Constance lists, etc.)
    if re.search(r"(?i)260 articles|books? teaching|dialogus|trialogus", q + text[:200]):
        return (
            "Yes. Those articles and books are condemned as heretical or erroneous, "
            "and the faithful are not to defend them."
        )

    if "error to be rejected" in low_q or "rightly reject" in low_q:
        return "Yes. That claim is rejected as erroneous; the contrary teaching stands."

    stmt = _affirmative_from_question(q)
    # Avoid leaving a question mark / interrogative residue
    stmt = stmt.rstrip("?").strip()
    if re.search(r"(?i)\b(is he|are they|does he)\b", stmt):
        stmt = re.sub(r"(?i)\bis he\b", "he is", stmt)
        stmt = re.sub(r"(?i)\bare they\b", "they are", stmt)
        stmt = re.sub(r"(?i)\bdoes he\b", "he does", stmt)

    parsed = bcd._extract_anathema(text)
    if parsed and len(q) < 50:
        teaching = parsed["teaching"]
        if teaching.lower().startswith("that "):
            teaching = teaching[5:]
        teaching = _scrub_names(teaching)
        if parsed["kind"] in {"denies", "must_confess"}:
            return _ensure_direct(
                f"Yes. One must hold that {teaching}.", default_lead="Yes."
            )
        return _ensure_direct(
            f"No. The contrary is to be held, rejecting the claim that {teaching}.",
            default_lead="No.",
        )

    return _ensure_direct(_scrub_names(f"Yes. {stmt}"), default_lead="Yes.")


def _theme_blob(question: str, text: str) -> str:
    return (question + " " + text[:700]).lower()


def _direct_breakaway_opposed(group: str, question: str, text: str) -> str:
    """Inferred opposing stance: Yes/No + positive alternative; no names."""
    blob = _theme_blob(question, text)
    claim = _claim_from_question(question)

    # --- Church of the East ---
    if group == "Church of the East":
        if "theotokos" in blob or "mother of god" in blob:
            return (
                "No. Mary is confessed as Mother of Christ; the stricter Theotokos "
                "settlement is not required as the binding title."
            )
        if "nestorius" in blob or "deposition" in blob or "metropolitan" in blob:
            return (
                "No. That disciplinary settlement is not binding orthodoxy; communion "
                "may continue under a sharper distinction of divinity and humanity in Christ."
            )
        return (
            "No. Christ’s divinity and humanity are confessed as two distinct qnome; "
            "the Cyrilline anathematizing settlement is not accepted as binding."
        )

    # --- OO family ---
    if group in {
        "Oriental Orthodox churches",
        "Armenian Apostolic Church",
        "Coptic Orthodox Church",
        "Syriac Orthodox Church",
    }:
        if "filioque" in blob or (
            "proceed" in blob and "father and the son" in blob
        ):
            return (
                "No. The Spirit proceeds from the Father; eternal procession from the "
                "Father and the Son as a required formula is refused."
            )
        if "chalcedon" in blob or "two nature" in blob or "leo" in blob:
            return (
                "No. After the union he is confessed as one united nature of the Word "
                "incarnate, not ‘in two natures’ as that definition requires."
            )
        if "outside the catholic" in blob or "eternal life" in blob and "schismatic" in blob:
            return (
                "No. Salvation is not restricted to those under that Latin communion "
                "formula; the historic miaphysite church is itself the orthodox communion."
            )
        if "dioscorus" in blob or "second synod of ephesus" in blob:
            return (
                "No. That condemnation of Dioscorus and the second Ephesine synod is "
                "not accepted; the miaphysite reception of the fathers stands."
            )
        if "sacrament" in blob or "matter" in blob and "form" in blob:
            return (
                "No. Sacramental life follows the received Eastern rites and theology; "
                "that Latin matter–form–intention schematization is not binding."
            )
        if "indelibl" in blob or "character" in blob:
            return (
                "No. That Latin account of an indelible sacramental character is not "
                "required as the condition of orthodoxy."
            )
        if "orders" in blob or "handing over" in blob:
            return (
                "No. Ordination is received in the historic Eastern manner; that Latin "
                "porrectio instrumentorum formula is not the required form."
            )
        if "roman pontiff" in blob or "primacy" in blob or "universal synod" in blob:
            return (
                "No. Universal synods and primacy are not defined by Roman confirmation "
                "as a condition of orthodoxy."
            )
        if "infant baptism" in blob or "forty or eighty" in blob:
            return (
                "Yes. Infants should be baptized without undue delay when death threatens; "
                "the pastoral urgency is not the point of separation."
            )
        # Default OO inferred opposition (weak loci)
        return (
            "No. Lasting communion does not require accepting that two-natures package; "
            "after the union he is confessed as one united nature of the Word incarnate."
        )

    # --- EO ---
    if group == "Eastern Orthodox churches":
        if "filioque" in blob or "proceed" in blob or "father and the son" in blob:
            return (
                "No. The Spirit proceeds from the Father; the Filioque as a required "
                "addition to the creed is refused."
            )
        if "purgatory" in blob or "cleansing pain" in blob or "suffrage" in blob:
            return (
                "No. The Latin formulation of purgatorial cleansing pains as defined "
                "there is not received; prayer for the dead is confessed differently."
            )
        if "primacy" in blob or "roman pontiff" in blob or "highest and complete" in blob:
            return (
                "No. The bishop of Rome does not hold universal supreme jurisdiction "
                "as that profession states; primacy, if any, is of honor within conciliar bounds."
            )
        if "unleavened" in blob or "leavened" in blob:
            return (
                "Yes. Christ’s body is truly confected in leavened bread as received "
                "in the Byzantine rite; the dispute is not over validity of either custom alone."
            )
        return (
            "No. Reunion on those Latin terms—Filioque, primacy, and related definitions—"
            "is refused; the received Byzantine confession stands."
        )

    # --- Protestant / Lutheran ---
    if group in {
        "Protestant churches",
        "Lutheran churches",
        "Reformed / Calvinist churches",
        "Anabaptist / Radical Reformation churches",
        "Anglican Communion / Church of England",
    }:
        if "transubstantiation" in blob or "substance of bread" in blob:
            return (
                "No. Bread and wine are not converted in substance that way; Christ is "
                "received by faith (or sacramentally otherwise) without that metaphysics."
            )
        if (
            "propitiatory" in blob
            or "sacrifice of the mass" in blob
            or re.search(r"(?i)\bmass\b", blob)
            or ("sacrifice" in blob and "eucharist" in blob)
        ):
            return (
                "No. The Mass is not a propitiatory sacrifice offered for the living and "
                "the dead in that sense; Calvary’s sacrifice is once for all."
            )
        if "seven sacrament" in blob or "exactly seven" in blob:
            return (
                "No. There are not seven sacraments instituted by Christ in that list; "
                "Baptism and the Lord’s Supper are the Gospel sacraments."
            )
        if "indulgence" in blob:
            return (
                "No. Indulgences are not a power Christ granted the Church to apply "
                "in that penitential economy."
            )
        if "saint" in blob and ("invoke" in blob or "image" in blob or "relic" in blob):
            return (
                "No. The faithful should not invoke the saints or venerate relics and "
                "images as that decree requires."
            )
        if "free will" in blob or "justif" in blob:
            return (
                "No. Justification is by faith apart from that cooperating scheme; "
                "the will is not treated as Trent’s canons require."
            )
        if "preamble" in blob:
            return (
                "No. The Eucharist is not to be preached as a true and singular propitiatory "
                "sacrifice in that sense."
            )
        stmt = _affirmative_from_question(question)
        stmt = re.sub(r"(?i)^it is taught that\b", "that", stmt).rstrip(".")
        return (
            f"No. It is refused that {stmt[0].lower() + stmt[1:]}."
            if stmt
            else "No. That medieval sacramental and sacrificial requirement is refused."
        )

    if group == "Old Catholic churches":
        return (
            "No. Papal primacy and ex cathedra infallibility as defined there are refused; "
            "collegial and conciliar limits govern the episcopate."
        )

    if group == "Arian churches":
        return (
            "No. The Son is not of one substance with the Father; he is created or otherwise "
            "not true God in the same sense as the Father."
        )

    if group in {"Wycliffites / Lollards", "Hussites"}:
        # Affirm the condemned article when question is "Is the following true: …"
        if re.search(r"(?i)^is the following true:", question):
            body = claim or "that article"
            return _scrub_names(f"Yes. {body[0].upper() + body[1:]}.")
        return (
            "Yes. The condemned claim is defended; that synodal judgment is not accepted "
            "as settling the truth."
        )

    return _scrub_names(
        f"No. {claim[0].upper() + claim[1:]}." if claim else "No. That claim is refused."
    )


def _direct_breakaway_shared(question: str) -> str:
    stmt = _affirmative_from_question(question)
    if not stmt or re.search(r"(?i)\b(envoy|acceptance|rejoic|union with)\b", question):
        return (
            "Yes. On this ceremonial or shared point the same affirmation holds; "
            "it is not the distinctive rupture."
        )
    return _ensure_direct(_scrub_names(f"Yes. {stmt}"), default_lead="Yes.")


def _catholic_loose(entry: dict, text: str) -> tuple[str, str]:
    q = (entry.get("question") or "").strip()
    if not q:
        theme = entry.get("decision_summary") or bcd._first_sentences(text, 1, 260)
        q = bcd._ensure_q(f"Is the following true: {theme[:300]}")
    q = bcd._ensure_q(q)
    # Prefer entry question (already naturalized); only replace if anathema yields cleaner ask
    if re.search(r"(?i)let him be anathema", text[:900]) and len(q) < 40:
        parsed = bcd._extract_anathema(text)
        if parsed:
            q = bcd._question_from_anathema(parsed)
    catholic = _direct_catholic(q, text, entry)
    return q, _ensure_direct(_scrub_names(catholic), default_lead="Yes.")


def convert_loose(entry: dict, text: str, *, kind: str) -> dict | None:
    """Draft an extended row only for inferred opposition (disagreement-only)."""
    if kind in {"ceremony_or_narrative", "likely_shared"}:
        return None

    eid = entry["id"]
    group = entry["breakaway"]
    citation = entry.get("canonical_citation") or ""
    question, catholic = _catholic_loose(entry, text)

    b_ans = _direct_breakaway_opposed(group, question, text)
    notes = (
        "EXTENDED: previously excluded under explicit-trace. Breakaway stance "
        "inferred from group-level historical stake (disagreement), not locus-proven."
    )
    basis = "passage+inferred"

    b_ans = _ensure_direct(_scrub_names(b_ans), default_lead="No.")
    catholic = _ensure_direct(_scrub_names(catholic), default_lead="Yes.")

    # Drop accidental same-polarity drafts
    c_yes = catholic.lower().startswith("yes")
    c_no = catholic.lower().startswith("no")
    b_yes = b_ans.lower().startswith("yes")
    b_no = b_ans.lower().startswith("no")
    if (c_yes and b_yes) or (c_no and b_no):
        return None

    return {
        "id": eid,
        "question": question,
        "catholic_answer": catholic,
        "breakaway_group": group,
        "breakaway_answer": b_ans,
        "answer_basis": basis,
        "notes": notes,
        "council": entry.get("council"),
        "canonical_citation": citation,
        "record_id": entry.get("record_id"),
        "passage_excerpt": bcd._first_sentences(text, 3, 500),
        "source_entry_id": eid,
        "draft_method": "heuristic_extended",
        "tier": "extended",
        "confidence": "low",
        "contrast_kind": kind,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entries", type=Path, default=DEFAULT_ENTRIES)
    ap.add_argument("--passages", type=Path, default=DEFAULT_PASSAGES)
    ap.add_argument("--strict", type=Path, default=DEFAULT_STRICT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    entries = bcd.load_jsonl(args.entries)
    passages = {p["entry_id"]: p for p in bcd.load_jsonl(args.passages)}
    strict_rows = bcd.load_jsonl(args.strict) if args.strict.exists() else []
    strict_by_id = {r["id"]: r for r in strict_rows}

    out: list[dict] = []
    n_strict = 0
    n_extended = 0
    n_skipped_nondisagree = 0
    kind_counts: dict[str, int] = {}

    for entry in entries:
        eid = entry["id"]
        text = (passages.get(eid) or {}).get("text") or ""
        if eid in strict_by_id:
            row = dict(strict_by_id[eid])
            row["tier"] = "strict"
            row["confidence"] = "high"
            row["contrast_kind"] = "explicit_trace"
            out.append(row)
            n_strict += 1
            kind_counts["explicit_trace"] = kind_counts.get("explicit_trace", 0) + 1
            continue
        kind = _classify_loose(entry, text)
        row = convert_loose(entry, text, kind=kind)
        if row is None:
            n_skipped_nondisagree += 1
            kind_counts[f"skipped_{kind}"] = kind_counts.get(f"skipped_{kind}", 0) + 1
            continue
        out.append(row)
        n_extended += 1
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "contrast_extended.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_group: dict[str, int] = {}
    by_council: dict[str, int] = {}
    for r in out:
        by_group[r["breakaway_group"]] = by_group.get(r["breakaway_group"], 0) + 1
        by_council[r["council"] or "?"] = by_council.get(r["council"] or "?", 0) + 1

    summary = {
        "artifact": "contrast_extended.jsonl",
        "status": "TEST — not status quo",
        "n_total": len(out),
        "n_strict_explicit_trace": n_strict,
        "n_extended_opposition": n_extended,
        "n_skipped_nondisagreement": n_skipped_nondisagree,
        "n_source_breakaways": len(entries),
        "by_contrast_kind": dict(sorted(kind_counts.items(), key=lambda x: -x[1])),
        "by_breakaway_group": dict(sorted(by_group.items(), key=lambda x: -x[1])),
        "by_council": dict(sorted(by_council.items(), key=lambda x: -x[1])),
        "note": (
            "Disagreement-only. Strict rows copy contrast.jsonl. Extended rows are "
            "inferred opposition only; ceremony/shared loci are skipped (not padded)."
        ),
    }
    (args.out_dir / "summary_extended.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    readme = f"""# contrast_extended (TEST only)

**Not status quo.** Do not replace `contrast.jsonl` / `contrast.html` with these files.

**Disagreement-only:** ceremony, narrative, and likely-shared loci are **skipped**
(no “no distinctive doctrinal rupture” rows). Expansion adds breakaway groups with
real opposition; it does not pad with agreement.

| | Strict | Extended (test) |
|--|--:|--:|
| Data | `contrast.jsonl` ({n_strict}) | `contrast_extended.jsonl` (**{len(out)}**) |
| Viewer | `contrast.html` | [`contrast_extended.html`](contrast_extended.html) |
| Gate | Explicit-trace disagreement | Inferred opposition as well |
| Confidence | high | mixed (high + low) |

- **{n_strict}** rows: copied from `contrast.jsonl` (`tier=strict`, `confidence=high`).
- **{n_extended}** rows: inferred disagreement (`tier=extended`, `confidence=low`).
- **{n_skipped_nondisagree}** breakaway-tagged loci skipped (ceremony / shared / same polarity).

### `contrast_kind` counts

{chr(10).join(f"- `{k}` — {v}" for k, v in summary["by_contrast_kind"].items())}

### Regenerate

```bash
python3 scripts/step1/build_contrast_extended.py
```
"""
    (args.out_dir / "EXTENDED.md").write_text(readme, encoding="utf-8")

    # Viewer
    try:
        import export_contrast_viz as viz

        html_path = args.out_dir / "contrast_extended.html"
        html_path.write_text(
            viz.build_html(
                out,
                title="Catholic vs breakaway — extended (TEST)",
                lede=(
                    "TEST visualization of contrast_extended.jsonl: all breakaway loci. "
                    "Strict rows match the status-quo explicit-trace set; extended rows use "
                    "loosened / inferred answers (low confidence). Not a replacement for contrast.html."
                ),
                source_name="contrast_extended.jsonl",
                regenerate_cmd="python3 scripts/step1/build_contrast_extended.py",
            ),
            encoding="utf-8",
        )
        summary["viewer"] = str(html_path)
    except Exception as exc:  # noqa: BLE001
        print(f"viz skip: {exc}", file=sys.stderr)

    print(json.dumps({"wrote": str(out_path), **summary}, indent=2)[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
