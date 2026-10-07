#!/usr/bin/env python3
"""Attach disagreement loci / summaries to groups_catalog.json.

Preference: link a concrete council passage from the Step 1 breakaway subset
when one exists; otherwise store a historical disagreement summary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "outputs" / "step1" / "breakaways" / "groups_catalog.json"
# Prefer breakaway subset; fall back to full Step 1 entries for loci
# that are historically relevant but not in the breakaway compile.
ENTRIES_BREAKAWAY = ROOT / "outputs" / "step1" / "breakaways" / "entries.jsonl"
ENTRIES_FULL = ROOT / "outputs" / "step1" / "entries.jsonl"
GROUPS_MD = ROOT / "outputs" / "step1" / "breakaways" / "groups.md"


def locus(
    *,
    summary: str,
    record_id: str | None = None,
    canonical_citation: str | None = None,
    entry_id: str | None = None,
    related: list[dict] | None = None,
    parent_disagreement: str | None = None,
) -> dict:
    kind = "council_locus" if record_id and canonical_citation else "summary"
    out: dict = {
        "kind": kind,
        "summary": summary,
    }
    if record_id:
        out["record_id"] = record_id
    if canonical_citation:
        out["canonical_citation"] = canonical_citation
    if entry_id:
        out["entry_id"] = entry_id
    if related:
        out["related_loci"] = related
    if parent_disagreement:
        out["vs_parent"] = parent_disagreement
    return out


# Curated primary disagreements. Keys = group id.
# Council loci use record_ids from outputs/step1/breakaways/entries.jsonl.
# NOTE: Group membership and broke_from parents are curated by
# scripts/step1/audit_fix_groups_catalog.py (source of truth for who is a
# breakaway). This map only supplies disagreement loci/summaries.
DISAGREEMENTS: dict[str, dict] = {
    # early / degree 1
    "novatianists": locus(
        summary="Rejected readmission of the lapsed and formed a rigorist parallel hierarchy; Nicaea I canon 8 regulates reception of ‘Cathari’ (Novatianist) clergy into the Catholic Church without endorsing the schism.",
        record_id="mag:NIC1:canon8:en",
        canonical_citation="Nicaea I canon 8",
        entry_id="nic1-canon8-en",
    ),
    "melitians": locus(
        summary="Egyptian rigorist schism over discipline of the lapsed and episcopal legitimacy; Nicaea’s synodal letter to Alexandria regulates Melitian clergy without accepting the schism’s claims.",
        record_id="mag:NIC1:synodal-letter:en",
        canonical_citation="Nicaea I Synodal Letter to the Church of Alexandria",
        entry_id="nic1-synodal-letter-en",
    ),
    "donatists": locus(
        summary="Denied the validity of sacraments and ordinations performed by traditores (clergy who had handed over scriptures in persecution); rejected Catholic bishops as compromised. No dedicated ecumenical-council decree on Donatism is in this corpus (settled mainly via African synods / Augustine)."
    ),
    "arian-churches": locus(
        summary="Denied that the Son is consubstantial (homoousios) with the Father; rejected the Nicene Creed’s definition of the Son’s full divinity.",
        record_id="mag:NIC1:creed:en",
        canonical_citation="Nicaea I Creed (325 form)",
        entry_id="nic1-creed-en",
    ),
    "church-of-the-east": locus(
        summary="Rejected Ephesus’s condemnation of Nestorius and Cyril’s Christology as received by the council; maintained a dyophysite East Syriac confession distinct from imperial-church wording.",
        record_id="mag:EPH:cyril-letter3:en",
        canonical_citation="Ephesus, Third Epistle of Cyril to Nestorius (Cum salvator noster)",
        entry_id="eph-cyril-letter3-en",
        related=[
            {
                "record_id": "mag:EPH:cyril-letter2:en",
                "canonical_citation": "Ephesus, Epistle of Cyril to Nestorius (Intelligo quosdam)",
            }
        ],
    ),
    "coptic-orthodox": locus(
        summary="Alexandrian non-reception of Chalcedon’s two-nature Definition; continuity with miaphysite confession after 451.",
        record_id="mag:CHAL:definition:en",
        canonical_citation="Chalcedon, Definition of Faith",
        entry_id="chal-definition-en",
    ),
    "syriac-orthodox": locus(
        summary="West Syriac non-reception of Chalcedon’s two-nature Definition after 451.",
        record_id="mag:CHAL:definition:en",
        canonical_citation="Chalcedon, Definition of Faith",
        entry_id="chal-definition-en",
    ),
    "armenian-apostolic": locus(
        summary="Armenian church’s non-reception of Chalcedon; later Florence session 8 sought reunion on Catholic terms that were not lastingly received as ending the schism.",
        record_id="mag:CHAL:definition:en",
        canonical_citation="Chalcedon, Definition of Faith",
        entry_id="chal-definition-en",
        related=[
            {
                "note": "Later reunion bull for Armenians (Florence S8) in corpus; primary doctrinal break remains Chalcedon."
            }
        ],
    ),
    "ethiopian-orthodox": locus(
        summary="Miaphysite Tewahedo church under Coptic oversight after Chalcedon; modern autocephaly from the Coptic Orthodox Church (1959).",
        parent_disagreement="Autocephaly and patriarchal independence from the Coptic Orthodox Church of Alexandria (1959).",
        related=[
            {
                "record_id": "mag:CHAL:definition:en",
                "canonical_citation": "Chalcedon, Definition of Faith",
                "note": "Ancestral dogmatic non-reception of Chalcedon is via Coptic lineage.",
            }
        ],
    ),
    "malankara-orthodox": locus(
        summary="Indian West Syriac Orthodox autocephaly vis-à-vis the Syriac Orthodox Patriarchate of Antioch (1912).",
        parent_disagreement="Autocephaly / catholicate independence from the Syriac Orthodox Patriarchate of Antioch.",
        related=[
            {
                "record_id": "mag:CHAL:definition:en",
                "canonical_citation": "Chalcedon, Definition of Faith",
                "note": "Shared miaphysite non-reception of Chalcedon with the Syriac Orthodox parent tradition.",
            }
        ],
    ),
    "eritrean-orthodox": locus(
        summary="Autocephaly from the Ethiopian Orthodox Tewahedo Church after Eritrean independence—jurisdictional separation within Oriental Orthodoxy, not a new Christological disagreement with Rome.",
        parent_disagreement="National autocephaly and patriarchal independence from Ethiopian Tewahedo structures (1993).",
    ),
    "eastern-orthodox": locus(
        summary="East–West rupture over papal primacy, the Filioque, and related Latin practices; Florence’s union definition (Laetentur Caeli / session 6) and Lyons II’s reunion profession were not lastingly received in the Byzantine East.",
        record_id="mag:FLO:florence:s6:definition-of-the-holy-ecumenical-synod-of-florence:en",
        canonical_citation="Florence (Florence) S6 [Definition of the holy ecumenical synod of Florence]",
        entry_id="flo-florence-s6-definition-of-the-holy-ecumenical-synod-of-florence-en",
        related=[
            {
                "record_id": "mag:LYO2:profession-palaeologus:p1:en",
                "canonical_citation": "Lyons II, Profession of Faith of Michael Palaeologus (Denzinger 461)",
            }
        ],
    ),
    "waldensians": locus(
        summary="Lay preaching and apostolic poverty outside episcopal authorization; Lateran IV’s anti-heresy constitution anathematizes dissent from the Catholic faith and orders episcopal/secular action against heretics and their supporters.",
        record_id="mag:LAT4:constitution3:en",
        canonical_citation="Fourth Lateran Council, constitution 3",
        entry_id="lat4-constitution3-en",
        related=[
            {
                "note": "Waldensian break is also disciplinary (unauthorized preaching); const. 3 is the council’s general heresy regime."
            }
        ],
    ),
    "wycliffites": locus(
        summary="Condemned for Wyclif’s articles on the Eucharist, dominion, scripture, and church authority; Constance sentenced his teaching and memory.",
        record_id="mag:CON:s15:sentence-condemning-260-articles-wyclif-31:en",
        canonical_citation="Constance S15 [Sentence condemning 260 articles Wyclif] [31]",
        entry_id="con-s15-sentence-condemning-260-articles-wyclif-31-en",
        related=[
            {
                "record_id": "mag:CON:s15:articles-of-john-wyclif-selected-from-the-260:en",
                "canonical_citation": "Constance S15 [Articles of John Wyclif selected from the 260]",
            }
        ],
    ),
    "hussites": locus(
        summary="Bohemian reform after Hus: utraquism, critique of indulgences and papal power; Constance condemned Hus and his articles.",
        record_id="mag:CON:s15:sentence-against-john-hus:en",
        canonical_citation="Constance S15 [Sentence against John Hus]",
        entry_id="con-s15-sentence-against-john-hus-en",
        related=[
            {
                "record_id": "mag:CON:s15:condemned-articles-of-j-hus:en",
                "canonical_citation": "Constance S15 [Condemned articles of J. Hus]",
            }
        ],
    ),
    "unitas-fratrum": locus(
        summary="Further radicalization within the Hussite milieu toward a gathered ‘Unity of Brethren’ with distinct discipline and ministry—beyond Utraquist compromise with Rome.",
        parent_disagreement="Separated from broader Hussite/Utraquist structures toward a stricter brotherhood model (later Moravian renewal).",
    ),
    "lutheran": locus(
        summary="Justification by faith apart from Catholic scholastic accounts of merit; rejection of papal jurisdiction and several sacramental/Mass teachings defined against the Reformers at Trent.",
        record_id="mag:Trent:s6:justification:canon4:en",
        canonical_citation="Trent S6 Justification canon 4",
        entry_id="trent-s6-justification-canon4-en",
        related=[
            {
                "record_id": "mag:Trent:s4:scripture:decree:en",
                "canonical_citation": "Trent S4 Decree concerning the Canonical Scriptures",
            },
            {
                "record_id": "mag:Trent:s22:mass:ch1:en",
                "canonical_citation": "Trent S22 Doctrine on the Sacrifice of the Mass ch. 1",
            },
        ],
    ),
    "reformed": locus(
        summary="Rejection of papal jurisdiction, Catholic sacrificial Mass, and Trent’s sacramental system; strong emphasis on absolute divine sovereignty and reformed eucharistic teaching.",
        record_id="mag:Trent:s22:mass:ch1:en",
        canonical_citation="Trent S22 Doctrine on the Sacrifice of the Mass ch. 1",
        entry_id="trent-s22-mass-ch1-en",
        related=[
            {
                "record_id": "mag:Trent:s6:justification:canon4:en",
                "canonical_citation": "Trent S6 Justification canon 4",
            }
        ],
    ),
    "anglican": locus(
        summary="Royal/national rejection of papal jurisdiction (1534) and later Protestant formularies; Trent addresses shared Reformational doctrinal disputes rather than the English Act of Supremacy itself.",
        record_id="mag:Trent:s6:justification:canon4:en",
        canonical_citation="Trent S6 Justification canon 4",
        entry_id="trent-s6-justification-canon4-en",
        related=[
            {
                "note": "Jurisdictional break is the 1534 Act of Supremacy (not in this council corpus)."
            }
        ],
    ),
    "anabaptist": locus(
        summary="Believers’ baptism, separation of church from magisterial coercion, and rejection of infant baptism / state-church patterns shared by Catholics and magisterial Protestants.",
        record_id="mag:Trent:s7:sacraments:canon1:en",
        canonical_citation="Trent S7 Sacraments in General canon 1",
        entry_id="trent-s7-sacraments-canon1-en",
        related=[
            {
                "note": "Trent defends Catholic sacramental order; Anabaptist break is also vs magisterial Reformation."
            }
        ],
    ),
    "mennonite": locus(
        summary="Anabaptist continuity under Menno Simons’ pastoral leadership—believers’ baptism and gathered-church discipline—distinct from Catholic and magisterial Protestant infant-baptism establishments.",
        parent_disagreement="Organized Menno-Simons Anabaptist churches from the broader Radical Reformation stream.",
    ),
    "hutterite": locus(
        summary="Communal-goods Anabaptist discipline under Jakob Hutter; same radical-baptism rupture with Catholic sacramental order, expressed as a distinct brotherhood.",
        parent_disagreement="Community of goods and Hutterite colony discipline vs other Anabaptist groups.",
    ),
    "amish": locus(
        summary="Jakob Ammann’s stricter ban (Meidung) and shunning practices split Swiss Mennonite communities; disagreement is disciplinary rigor within Anabaptism, not a new council-level doctrine vs Rome.",
        parent_disagreement="Stricter shunning and footwashing discipline vs Swiss Mennonite practice (1693).",
    ),
    "old-catholic": locus(
        summary="Rejected Vatican I’s definition of the Roman pontiff’s universal jurisdiction and ex cathedra infallibility.",
        record_id="mag:PA:ch4:p9:en",
        canonical_citation="PA ch. 4 §9",
        entry_id="pa-ch4-p9-en",
        related=[
            {
                "record_id": "mag:PA:ch2:canon1:en",
                "canonical_citation": "PA ch. 2 canon 1",
            }
        ],
    ),
    "polish-national-catholic": locus(
        summary="Rejected Roman episcopal control over Polish immigrant parishes (property, language, appointment of pastors); formed an independent Catholic-style jurisdiction."
    ),
    "philippine-independent": locus(
        summary="National church independence from Spanish/Roman hierarchy amid Philippine revolution and colonial transition; rejected continued Roman jurisdiction."
    ),
    "brazilian-catholic-apostolic": locus(
        summary="Bishop Duarte Costa’s break over Vatican political alignments and discipline; established an independent Catholic church with married clergy and vernacular liturgy."
    ),
    "chinese-patriotic": locus(
        summary="State insistence on episcopal appointment and church governance independent of Roman mandate; contested whether this is schism or coerced parallel structure."
    ),
    "sedevacantist-bodies": locus(
        summary="Hold that recent claimants to the papal see lost office through heresy or vacancy; reject post-conciliar papal authority as illegitimate. No ecumenical decree defines against sedevacantism as such—disagreement is over who holds Peter’s office after Vatican II."
    ),
    "palmarian": locus(
        summary="Private-revelation conclavism: elected an alternative papacy at El Palmar de Troya and rejected the Roman line after Paul VI."
    ),
    # from EO
    "old-believers": locus(
        summary="Rejected Patriarch Nikon’s liturgical reforms (sign of the cross, books, rites) as illegitimate corruption of Russian Orthodoxy.",
        parent_disagreement="Nikonian ritual reform vs pre-reform Russian rite.",
    ),
    "true-orthodox": locus(
        summary="Reject mainstream Orthodox adoption of the Revised Julian calendar and/or participation in ecumenical dialogue as betrayal of Orthodoxy.",
        parent_disagreement="Calendar reform and ecumenism within Eastern Orthodoxy.",
    ),
    "greek-old-calendarists": locus(
        summary="Greek jurisdictions that refused the 1924 calendar change in the Church of Greece.",
        parent_disagreement="Revised Julian calendar introduction.",
    ),
    "russian-orthodox-church-abroad": locus(
        summary="Emigré refusal to submit to the Moscow Patriarchate under Soviet control; contested after 2007 reconciliation.",
        parent_disagreement="Canonical submission to Moscow vs independent émigré synod.",
    ),
    "oriental-orthodox-assyrian-split": locus(
        summary="Split from the Assyrian Church of the East over calendar reform and patriarchal jurisdiction (1968).",
        parent_disagreement="Gregorian calendar adoption and related governance.",
    ),
    # Anglican lineage
    "methodist": locus(
        summary="Wesleyan societies became a separate church with its own ordinations and conference polity, outside Anglican episcopal control.",
        parent_disagreement="Conference ordination and connexional structure vs Church of England episcopacy.",
    ),
    "holiness-movement": locus(
        summary="Taught a distinct experience of entire sanctification beyond mainstream Methodist practice; formed separate Holiness denominations.",
        parent_disagreement="Entire sanctification as a second definite work of grace; stricter lifestyle rules.",
    ),
    "church-of-the-nazarene": locus(
        summary="Consolidated Holiness bodies emphasizing entire sanctification and Wesleyan doctrine as a distinct denomination.",
        parent_disagreement="Organized Holiness denominationalism from Methodist/Holiness streams.",
    ),
    "church-of-god-anderson": locus(
        summary="Warner’s ‘come-out’ Holiness restorationism rejected denominationalism while forming a distinct Church of God movement.",
        parent_disagreement="Anti-denominational Holiness restoration vs existing Methodist/Holiness churches.",
    ),
    "salvation-army": locus(
        summary="Booth’s mission adopted a quasi-military structure and largely set aside ordinary sacramental practice, separating from Methodist connexional forms.",
        parent_disagreement="Military polity and non-sacramental mission methods.",
    ),
    "pentecostal": locus(
        summary="Affirmed tongues and gifts of the Spirit as normative evidence of Spirit baptism, beyond Holiness second-blessing teaching.",
        parent_disagreement="Spirit baptism evidenced by speaking in tongues.",
    ),
    "assemblies-of-god": locus(
        summary="Organized Trinitarian Pentecostal fellowship with doctrinal statements on Spirit baptism and tongues.",
        parent_disagreement="Denominational organization of classical Pentecostalism.",
    ),
    "oneness-pentecostal": locus(
        summary="Rejected Trinitarian baptismal formula and classical Trinitarian doctrine in favor of Jesus’-name Oneness teaching.",
        parent_disagreement="Oneness vs Trinitarian Pentecostal theology.",
    ),
    "charismatic-renewal-independents": locus(
        summary="Independent charismatic networks emphasizing apostolic/prophetic leadership and contemporary gifts outside classical Pentecostal denominations.",
        parent_disagreement="Apostolic-prophetic independent structures vs classical Pentecostal denominations.",
    ),
    "vineyard": locus(
        summary="Wimber’s ‘power evangelism’ charismatic evangelicalism organized apart from prior denominations.",
        parent_disagreement="Signs-and-wonders charismatic practice in a distinct association.",
    ),
    "puritan-separatists": locus(
        summary="Held that the Church of England remained insufficiently reformed; Separatists gathered autonomous congregations outside parish/episcopal structures.",
        parent_disagreement="Congregational separation vs Anglican parish settlement.",
    ),
    "baptist": locus(
        summary="Restricted baptism to believers (often by immersion) and gathered regenerate church membership, against infant baptism in Separatist/Anglican practice.",
        parent_disagreement="Believers’ baptism and regenerate church membership.",
    ),
    "southern-baptist": locus(
        summary="Southern US Baptists formed a separate convention over slavery and missions board control.",
        parent_disagreement="Regional convention autonomy and slavery-era missions dispute.",
    ),
    "seventh-day-baptist": locus(
        summary="Observed the seventh-day Sabbath while remaining Baptist in baptism and congregational polity.",
        parent_disagreement="Seventh-day Sabbath vs Sunday Baptist practice.",
    ),
    "quakers": locus(
        summary="Rejected outward sacraments, paid clergy, and set liturgy in favor of the inward light and silent worship.",
        parent_disagreement="Inward light vs Separatist/Puritan sacramental and clerical forms.",
    ),
    "unitarian": locus(
        summary="Anti-Trinitarian and later liberal Protestant churches; Anglo-American Unitarianism grew mainly from Congregational/Separatist settings (Transylvanian Unitarianism is a separate early stream).",
        parent_disagreement="Doctrinal liberalization / anti-Trinitarian identity within English-speaking Congregational-Separatist Protestantism.",
    ),
    "plymouth-brethren": locus(
        summary="Rejected denominational clergy and formal membership for gathered open/exclusive assemblies under supposed New Testament pattern.",
        parent_disagreement="Anti-denominational assembly fellowship vs Anglican/evangelical parish forms.",
    ),
    "exclusive-brethren": locus(
        summary="Darbyite exclusivism: tight disciplinary separation from Open Brethren and other Christians.",
        parent_disagreement="Exclusive table fellowship and Darbyite discipline.",
    ),
    "presbyterian": locus(
        summary="Reformed churches with Presbyterian polity (e.g. Church of Scotland)—typically the national form of the Reformed Reformation, not a later schism from continental Reformed churches.",
        parent_disagreement="Polity/national expression within Reformed Protestantism (not a classic secession event).",
    ),
    "dutch-reformed-splits": locus(
        summary="Seceded from the Netherlands state church over doctrinal liberalism and church order (Afscheiding/Doleantie).",
        parent_disagreement="Confessional orthodoxy and free-church order vs Nederlandse Hervormde Kerk.",
    ),
    "missouri-synod": locus(
        summary="U.S. confessional Lutheran synod organized by immigrants (1847); confessional Lutheran identity rather than a schism from one European Lutheran church body.",
        parent_disagreement="Immigrant confessional organization within Lutheranism (founding is not a secession decree from a parent synod).",
    ),
    "evangelical-free": locus(
        summary="Scandinavian free-church evangelicalism: congregational, conversionist, outside state Lutheran churches.",
        parent_disagreement="Free-church polity vs state Lutheran establishment.",
    ),
    "swedenborgian": locus(
        summary="New Church bodies organized especially in England on Emanuel Swedenborg’s revelations.",
        parent_disagreement="Swedenborgian revelation vs Anglican/English Protestant orthodoxy (Swedenborg himself was Lutheran by background).",
    ),
    "restoration-movement": locus(
        summary="Sought to restore New Testament church pattern, rejecting creeds and denominational names as divisive.",
        parent_disagreement="No-creed restorationism vs Presbyterian/denominational Protestantism.",
    ),
    "churches-of-christ": locus(
        summary="Opposed instrumental music and missionary societies within the Restoration Movement.",
        parent_disagreement="A cappella worship and anti-society congregationalism.",
    ),
    "christian-and-missionary-alliance": locus(
        summary="Simpson’s deeper-life and missionary emphasis organized into a distinct evangelical denomination.",
        parent_disagreement="Alliance missionary/deeper-life identity vs Presbyterian home structures.",
    ),
    "united-church-of-christ": locus(
        summary="Mid-20th-century merger creating a liberal mainline Protestant body from Congregational and German Reformed streams.",
        parent_disagreement="Ecumenical merger identity (organizational, not a classical heresy dispute).",
    ),
    "adventist": locus(
        summary="Millerite imminent second-coming calculations and advent expectation after the Great Disappointment.",
        parent_disagreement="Specific advent chronology and remnant identity vs Baptist/evangelical churches.",
    ),
    "seventh-day-adventist": locus(
        summary="Sabbatarian adventism with remnant theology, investigative judgment, and Ellen White’s prophetic role.",
        parent_disagreement="Seventh-day Sabbath, sanctuary doctrine, and prophetic authority.",
    ),
    "bible-students": locus(
        summary="Russell’s chronological Adventism and rejection of mainstream church teaching on hell, Trinity, and organization.",
        parent_disagreement="Russellite chronology and anti-Trinitarian trajectory from adventist milieu.",
    ),
    "jehovah-witnesses": locus(
        summary="Watch Tower teachings denying the Trinity, affirming a modern governing organization, and distinctive eschatology under Rutherford.",
        parent_disagreement="Governing Body authority and non-Trinitarian Watch Tower doctrine.",
    ),
    "latter-day-saints": locus(
        summary="Restorationist church founded by Joseph Smith (1830), claiming restoration of primitive Christianity after a universal apostasy—not a schism from the Stone–Campbell Restoration Movement.",
    ),
    "community-of-christ": locus(
        summary="Reorganized Latter Day Saint succession under Joseph Smith III, rejecting Brigham Young’s Utah leadership and later polygamy.",
        parent_disagreement="Lineal succession and rejection of Utah LDS developments.",
    ),
    "christian-science": locus(
        summary="Mary Baker Eddy’s Church of Christ, Scientist (1879), arising in New England Protestant culture with a distinct metaphysics of healing and scripture interpretation.",
        parent_disagreement="New religious movement in Congregational/New England Protestant culture (not a clean congregational secession).",
    ),
    "grace-communion": locus(
        summary="Armstrongism’s British-Israel and sabbatarian system; later GCI reformed toward evangelical Trinitarianism while splinters retained older teachings.",
        parent_disagreement="Armstrongite doctrines (and later GCI’s break from them).",
    ),
    "mar-thoma": locus(
        summary="Reforming party in Malankara under Anglican CMS influence; accepted reformed liturgy/theology while remaining West Syriac in heritage.",
        parent_disagreement="Anglican-influenced reform vs Malankara Orthodox traditionalism.",
    ),
    "jacobite-syrian-malankara": locus(
        summary="Malankara congregations under the Syriac Orthodox Patriarch of Antioch (Jacobite Syrian Christian Church), distinct from the autocephalous Malankara Orthodox Syrian Church.",
        parent_disagreement="Remains under Antiochene patriarchal jurisdiction (not a secession from MOSC).",
    ),
    "kimbanguist": locus(
        summary="Simon Kimbangu’s Church of Jesus Christ on Earth, arising among Baptist-mission Christians in the Belgian Congo as an independent African church.",
        parent_disagreement="Independent prophetic church from Baptist mission Christianity in Congo.",
    ),
    "aladura": locus(
        summary="Yoruba Aladura prayer-healing churches emerging from Anglican and related Protestant mission settings in Nigeria.",
        parent_disagreement="Prophetic-healing independence from Anglican/mission church forms.",
    ),
    "ame-church": locus(
        summary="Black Methodists withdrew from white Methodist Episcopal control over seating and pastoral appointment (Allen).",
        parent_disagreement="Racial exclusion and self-governance within Methodism.",
    ),
    "ame-zion": locus(
        summary="Independent Black Methodist organization in New York amid similar racial barriers.",
        parent_disagreement="Racial self-determination within Methodist structures.",
    ),
    "cme-church": locus(
        summary="Organized from the Methodist Episcopal Church, South after emancipation as a separate Black Methodist body.",
        parent_disagreement="Post-emancipation separate Black Methodist jurisdiction.",
    ),
    "wesleyan-church": locus(
        summary="Abolitionist and Holiness Methodist secession emphasizing freedom from episcopal Methodist compromises on slavery and sanctification.",
        parent_disagreement="Abolition + Holiness emphases vs MEC practice.",
    ),
    "free-methodist": locus(
        summary="Opposed rented pews and lax discipline; Holiness revival within a free Methodist free-church form.",
        parent_disagreement="Free pews, Holiness, and anti-slavery free Methodism.",
    ),
    "continuing-anglican": locus(
        summary="Rejected 1970s Prayer Book/ordination changes in ECUSA/Anglican Communion as departing from historic Anglican faith and order.",
        parent_disagreement="1970s liturgical and ordination changes.",
    ),
    "acna": locus(
        summary="Conservatives left TEC/ACC over sexuality, authority, and doctrine, forming a realignment province.",
        parent_disagreement="Sexuality/doctrine disputes within North American Anglicanism.",
    ),
    "liberal-catholic": locus(
        summary="Combined Catholic sacramental forms with Theosophical freedom of belief, outside Roman and Utrecht Old Catholic doctrinal limits.",
        parent_disagreement="Theosophical doctrinal liberty vs Old Catholic/Roman dogma.",
    ),
    "iglesia-ni-cristo": locus(
        summary="Restorationist church founded by Félix Manalo (1914), teaching a restored Church of Christ after apostasy; independent of Rome and of the Philippine Independent Church.",
    ),
    # expansions (see scripts/step1/expand_groups_catalog.py)
    "mariavite": locus(
        summary="Rejected Roman suppression of the Mariavite congregation and excommunication of its leaders (1906), forming an independent hierarchy after failed appeals to Rome."
    ),
    "czechoslovak-hussite": locus(
        summary="Czech Catholic modernist clergy separated when Rome refused reform demands (vernacular Mass, optional celibacy, national church order), constituting the Czechoslovak (later Hussite) Church."
    ),
    "petite-eglise": locus(
        summary="Rejected the Concordat settlement and papal/civil reorganization of French dioceses, continuing a parallel anticoncordataire hierarchy and congregations."
    ),
    "catholic-mariavite-felicjanow": locus(
        summary="Split from the Płock Mariavite majority over Kowalski’s leadership and doctrinal/disciplinary innovations.",
        parent_disagreement="Loyalty to Kowalski and Felicjanów line vs Płock Old Catholic Mariavite majority (1935).",
    ),
    "church-of-the-brethren": locus(
        summary="Gathered a new believers’-baptism brotherhood at Schwarzenau with distinctive trine immersion and Pietist emphases alongside Anabaptist separationism.",
        parent_disagreement="Schwarzenau Brethren identity vs other Anabaptist/Mennonite streams.",
    ),
    "reformed-episcopal-church": locus(
        summary="Rejected advancing ritualism and exclusive sacramental claims in the Episcopal Church; organized a Reformed Episcopal jurisdiction with evangelical Anglican formularies.",
        parent_disagreement="Evangelical/low-church protest vs ritualist trajectory in the Episcopal Church (1873).",
    ),
    "free-church-of-scotland": locus(
        summary="Rejected state intrusion via patronage and defended the spiritual independence of the church, leaving the establishment in the Disruption of 1843.",
        parent_disagreement="Spiritual independence / anti-patronage Free Church vs established Church of Scotland.",
    ),
    "orthodox-presbyterian-church": locus(
        summary="Separated from the Presbyterian Church in the U.S.A. over doctrinal modernism and control of missions, organizing the OPC.",
        parent_disagreement="Confessional orthodoxy and independent missions vs PCUSA modernism (1936).",
    ),
    "remonstrant-brotherhood": locus(
        summary="Rejected Dort’s Calvinist condemnations of the five Remonstrant articles and formed a separate Remonstrant church.",
        parent_disagreement="Arminian Remonstrant theology vs Synod of Dort / Dutch Reformed orthodoxy.",
    ),
    "primitive-methodist": locus(
        summary="Continued open-air camp-meeting revivalism after Wesleyan Methodist authorities disciplined leaders; formed a separate Primitive Methodist connexion.",
        parent_disagreement="Camp-meeting revivalism and lay intensity vs Wesleyan Methodist connexional control.",
    ),
    "evangelical-covenant-church": locus(
        summary="Formed a free Mission Covenant church emphasizing conversion, Bible, and congregational mission outside the Lutheran state-church establishment.",
        parent_disagreement="Free-church Mission Covenant identity vs Swedish/American Lutheran establishment.",
    ),
    "catholic-apostolic-church": locus(
        summary="Taught a restored apostolate and charismatic order beyond historic Presbyterian/Anglican ministry, organizing the Catholic Apostolic Church.",
        parent_disagreement="Restored apostles and prophetic office vs Presbyterian (and Anglican) ministry norms.",
    ),
    "new-apostolic-church": locus(
        summary="Insisted on continuing to seal apostles beyond the original Catholic Apostolic college; organized separately after the Hamburg schism.",
        parent_disagreement="Ongoing apostle calling (Hamburg) vs closed original Catholic Apostolic apostolate.",
    ),
    "church-of-god-cleveland": locus(
        summary="Organized a distinct Holiness (later Pentecostal) church government and doctrine of Spirit baptism apart from Methodist-Holiness parent bodies.",
        parent_disagreement="Church of God (Cleveland) Holiness–Pentecostal order vs broader Holiness movement churches.",
    ),
    "foursquare": locus(
        summary="Organized a separate Foursquare Pentecostal denomination around McPherson’s Angelus Temple ministry and foursquare doctrinal formula.",
        parent_disagreement="Foursquare denominational organization vs other classical Pentecostal fellowships.",
    ),
    "advent-christian": locus(
        summary="Continued adventist expectation with conditional immortality while rejecting Seventh-day Adventist Sabbath and prophetic claims as binding marks of the remnant.",
        parent_disagreement="Advent Christian conditionalism vs emerging Sabbatarian Adventist (SDA) distinctives.",
    ),
    "christian-reformed-church": locus(
        summary="Seceded from the Reformed Church in America over confessional laxity, Americanization, and Freemasonry concerns among Dutch seceder immigrants.",
        parent_disagreement="Confessional Dutch seeder CRC vs RCA practice (1857).",
    ),
    "ancient-church-of-the-east": locus(
        summary="Split from the Assyrian Church of the East over calendar reform and related patriarchal/jurisdictional disputes (1968).",
        parent_disagreement="Julian calendar / jurisdiction vs Assyrian Church of the East reforms.",
    ),
    # deeper branch expansions
    "free-will-baptist": locus(
        summary="Affirmed general atonement and human free will against stricter Calvinistic Particular Baptist confessions, organizing lasting Free Will Baptist associations.",
        parent_disagreement="Arminian Free Will Baptist theology vs Particular/Calvinistic Baptist orthodoxy.",
    ),
    "disciples-of-christ": locus(
        summary="Accepted instrumental music, missionary societies, and broader open-membership practice within the Stone–Campbell movement, crystallizing as the Disciples of Christ.",
        parent_disagreement="Disciples openness (instruments, societies, membership) vs stricter Restoration congregations.",
    ),
    "independent-christian-churches": locus(
        summary="Rejected Disciples’ restructure and liberal theology while retaining instruments and remaining outside both the Disciples denomination and a cappella Churches of Christ.",
        parent_disagreement="Independent Christian Church conservatism vs Disciples denominational liberalism/restructure.",
    ),
    "american-baptist-association": locus(
        summary="Landmark ecclesiology: absolute local-church autonomy, Baptist succession claims, and refusal of ‘alien immersion’ / open pulpit practices associated with Convention Baptists.",
        parent_disagreement="Landmark associational Baptists vs Southern Baptist Convention centralization (1905).",
    ),
    "baptist-missionary-association": locus(
        summary="Split from the American Baptist Association over associational authority, missions administration, and leadership conflicts while remaining Landmark in ecclesiology.",
        parent_disagreement="BMAA associational/missions dispute vs ABA (1950).",
    ),
    "presbyterian-church-in-america": locus(
        summary="Left the Presbyterian Church in the United States citing theological liberalism and departure from confessional Reformed standards, organizing the PCA.",
        parent_disagreement="Confessional PCA vs PCUS liberalism (1973).",
    ),
    "evangelical-presbyterian-church": locus(
        summary="Separated from mainline Presbyterian structures for evangelical orthodoxy and local-church liberty on contested ethical issues, forming the EPC.",
        parent_disagreement="EPC evangelical essentials vs PC(USA)/UPCUSA mainline trajectory (1981).",
    ),
    "free-church-of-scotland-continuing": locus(
        summary="Rejected Free Church Assembly decisions on worship/discipline as departing from historic Free Church standards; organized the Continuing Free Church.",
        parent_disagreement="Continuing Free Church remnant vs Free Church of Scotland majority (2000).",
    ),
    "old-order-mennonite": locus(
        summary="Rejected Mennonite progressivism in worship, education, and later technology, preserving Old Order discipline and plain patterns.",
        parent_disagreement="Old Order Ordnung vs progressive Mennonite conferences (from 1870s).",
    ),
    "evangelical-friends": locus(
        summary="Embraced evangelical Protestant orthodoxy and pastoral programmed worship against liberal/quietist Friends trajectories.",
        parent_disagreement="Evangelical programmed Friends vs liberal/unprogrammed Quakerism.",
    ),
    "church-of-christ-temple-lot": locus(
        summary="Rejected Utah LDS leadership, temple theology as developed in Utah, and plural marriage; organized under Granville Hedrick with Temple Lot claims.",
        parent_disagreement="Hedrickite Temple Lot succession vs Brighamite LDS (Utah) leadership.",
    ),
    "church-of-god-in-christ": locus(
        summary="Organized a distinct episcopal Pentecostal church (COGIC) emphasizing sanctification and Spirit baptism, separate from other Holiness and Pentecostal bodies.",
        parent_disagreement="COGIC episcopal Pentecostal order vs other classical Pentecostal fellowships.",
    ),
    "united-pentecostal-church": locus(
        summary="Consolidated major Oneness Pentecostal organizations into UPCI with shared Jesus’-name baptism and non-Trinitarian confession.",
        parent_disagreement="UPCI organizational merger within the Oneness Pentecostal family.",
    ),
    "adventist-reform-movement": locus(
        summary="Charged the Seventh-day Adventist Church with compromising Sabbath and noncombatant principles in wartime; organized a Reform Movement.",
        parent_disagreement="Reform Movement wartime/Sabbath discipline vs SDA official wartime policy.",
    ),
    "bible-methodist": locus(
        summary="Rejected Wesleyan Church compromises on Holiness lifestyle/standards and organized the Bible Methodist Connection.",
        parent_disagreement="Conservative Holiness standards vs post-merger Wesleyan Church practice.",
    ),
    "calvary-chapel": locus(
        summary="Developed an independent Calvary Chapel model (expositional preaching, balanced charismatic practice, association polity) outside Foursquare denominational structures.",
        parent_disagreement="Calvary Chapel association model vs Foursquare denominational order.",
    ),
    "national-baptist-convention": locus(
        summary="Built independent Black Baptist national structures for missions, education, and publishing apart from white Baptist conventions.",
        parent_disagreement="National Black Baptist convention autonomy vs white Baptist convention structures.",
    ),
    "progressive-national-baptist": locus(
        summary="Split from NBCUSA over support for the civil-rights movement and convention governance (tenure) conflicts.",
        parent_disagreement="Progressive National Baptists’ civil-rights activism vs NBCUSA leadership stance (1961).",
    ),
}


def load_entries() -> dict[str, dict]:
    """Merge full Step 1 entries over breakaway subset (full wins on overlap)."""
    by_record: dict[str, dict] = {}
    for path in (ENTRIES_BREAKAWAY, ENTRIES_FULL):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            rid = e.get("record_id")
            if rid:
                by_record[rid] = e
    return by_record


def write_groups_md(catalog: dict) -> None:
    groups = catalog["groups"]
    lines = [
        "# Breakaway groups over time (lineage catalog)",
        "",
        "Reference for tracing separation from the Catholic Church, including",
        "**degree > 1**. Machine-readable: [`groups_catalog.json`](groups_catalog.json).",
        "",
        "Each group now includes a `disagreement` object: preferably a linked",
        "council locus from the Step 1 breakaway subset, otherwise a summary.",
        "",
        f"**{catalog['stats']['group_count']} groups** · "
        f"locus-linked: {catalog['stats'].get('with_council_locus', '?')} · "
        f"summary-only: {catalog['stats'].get('with_summary_only', '?')}",
        "",
        "| Deg | Group | Disagreement (locus or summary) | Kind |",
        "|---:|---|---|---|",
    ]
    for g in groups:
        d = g.get("disagreement") or {}
        kind = d.get("kind", "")
        if kind == "council_locus":
            tip = d.get("canonical_citation") or ""
            tip = f"`{tip}` — {d.get('summary', '')}"
        else:
            tip = d.get("summary") or g.get("summary") or ""
        tip = tip.replace("|", "/").replace("\n", " ")
        if len(tip) > 140:
            tip = tip[:137] + "..."
        lines.append(
            f"| {g.get('separation_degree')} | {g['name']} | {tip} | {kind} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Prefer `disagreement.canonical_citation` / `record_id` when present.",
            "- Degree > 1 rows usually summarize the break **from the parent** (`vs_parent`).",
            "- Regenerated by `python scripts/step1/enrich_groups_disagreements.py`.",
            "",
        ]
    )
    GROUPS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    entries = load_entries()

    # Fix anabaptist locus if Trent S7 canon1 missing — fall back to summary+related note
    if "mag:Trent:s7:sacraments:canon1:en" not in entries:
        # find any Trent sacramental general entry
        alt = next(
            (
                e
                for e in entries.values()
                if "Sacraments in General" in (e.get("canonical_citation") or "")
            ),
            None,
        )
        if alt:
            DISAGREEMENTS["anabaptist"].update(
                {
                    "kind": "council_locus",
                    "record_id": alt["record_id"],
                    "canonical_citation": alt["canonical_citation"],
                    "entry_id": alt.get("id"),
                }
            )
        else:
            DISAGREEMENTS["anabaptist"] = locus(
                summary=DISAGREEMENTS["anabaptist"]["summary"]
            )

    missing = []
    for gid, d in DISAGREEMENTS.items():
        rid = d.get("record_id")
        if rid and rid not in entries:
            missing.append(f"{gid}: {rid}")
    if missing:
        print("WARNING loci not in breakaway entries:")
        for m in missing:
            print(" ", m)

    # Update schema blurb
    catalog["schema"]["disagreement"] = (
        "{kind: council_locus|summary, summary, optional record_id/"
        "canonical_citation/entry_id/related_loci/vs_parent}"
    )
    catalog["preference"] = (
        catalog.get("preference", "")
        + " For each breakaway, prefer a concrete council passage outlining the "
        "disagreement; otherwise summarize it. Degree > 1: summarize vs parent."
    ).strip()

    uncovered = []
    locus_n = summary_n = 0
    for g in catalog["groups"]:
        gid = g["id"]
        if gid not in DISAGREEMENTS:
            uncovered.append(gid)
            g["disagreement"] = locus(
                summary=g.get("summary")
                or "Disagreement not yet curated; see group summary."
            )
            summary_n += 1
            continue
        d = dict(DISAGREEMENTS[gid])
        # Always sync entry_id from breakaway entries when record_id resolves
        rid = d.get("record_id")
        if rid and rid in entries:
            d["entry_id"] = entries[rid].get("id")
            if not d.get("canonical_citation"):
                d["canonical_citation"] = entries[rid].get("canonical_citation")
            d["kind"] = "council_locus"
        g["disagreement"] = d
        if d.get("kind") == "council_locus":
            locus_n += 1
        else:
            summary_n += 1

    catalog["stats"]["with_council_locus"] = locus_n
    catalog["stats"]["with_summary_only"] = summary_n
    catalog["stats"]["disagreement_coverage"] = (
        catalog["stats"]["group_count"] - len(uncovered)
    )

    args.catalog.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_groups_md(catalog)
    print(
        f"enriched {args.catalog}: locus={locus_n} summary={summary_n} "
        f"uncovered_fallback={len(uncovered)}"
    )
    if uncovered:
        print("fallback groups:", ", ".join(uncovered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
