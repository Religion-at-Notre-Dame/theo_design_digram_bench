#!/usr/bin/env python3
"""Add carefully vetted breakaway groups to groups_catalog.json.

Priority: durable degree-1 separations from the Catholic Church (with council
loci when the corpus has them); then clear higher-degree forks that still trace
to catholic-church via broke_from. Skips in-communion bodies, synthetic
umbrellas, and contested “milieu” attachments.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "outputs" / "step1" / "breakaways" / "groups_catalog.json"
GROUPS_MD = ROOT / "outputs" / "step1" / "breakaways" / "groups.md"

# New groups. Every entry must have broke_from in {catholic-church} ∪ existing ids.
NEW_GROUPS: list[dict] = [
    # --- Degree 1 (from Catholic Church) ---
    {
        "id": "mariavite",
        "name": "Mariavite Church (Old Catholic Church of the Mariavites)",
        "approx_rupture": "1906",
        "rupture_year": 1906,
        "region": "Poland",
        "broke_from": "catholic-church",
        "relation": "excommunicated_separated",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Polish Catholic renewal movement around Feliksa Kozłowska; suppressed and "
            "leaders excommunicated (1906), then organized as an independent church "
            "(later allied with Utrecht Old Catholics; majority body based in Płock)."
        ),
        "notes": (
            "Papal encyclical Tribus Circiter (1906) and Holy Office acts condemn the "
            "movement; those texts are not in the Step 1 council corpus. 1935 internal "
            "split produced the smaller Catholic Mariavite Church (Felicjanów)."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected Roman suppression of the Mariavite congregation and "
                "excommunication of its leaders (1906), forming an independent hierarchy "
                "after failed appeals to Rome."
            ),
        },
    },
    {
        "id": "czechoslovak-hussite",
        "name": "Czechoslovak Hussite Church",
        "approx_rupture": "1920",
        "rupture_year": 1920,
        "region": "Czech lands / Slovakia",
        "broke_from": "catholic-church",
        "relation": "national_reform_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Founded 8 January 1920 by reformist Roman Catholic clergy (Karel Farský et al.) "
            "after Vatican rejection of vernacular liturgy, voluntary celibacy, and related "
            "demands; claims Hussite heritage while originating as a Catholic clerical schism."
        ),
        "notes": (
            "Not a direct organizational continuation of medieval Hussites (already catalogued); "
            "degree-1 parent is the Catholic Church."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Czech Catholic modernist clergy separated when Rome refused reform demands "
                "(vernacular Mass, optional celibacy, national church order), constituting the "
                "Czechoslovak (later Hussite) Church."
            ),
        },
    },
    {
        "id": "petite-eglise",
        "name": "Petite Église (anticoncordataires)",
        "approx_rupture": "1801–",
        "rupture_year": 1801,
        "region": "France / Belgium / Switzerland",
        "broke_from": "catholic-church",
        "relation": "refused_concordat",
        "confidence": "established",
        "status": "historical",
        "summary": (
            "Clergy and faithful who refused the 1801 Concordat between Napoleon and Pius VII "
            "(and related reorganizations), maintaining a small separated ‘Little Church’ "
            "in parts of France and neighboring regions."
        ),
        "notes": (
            "Historical remnant communities; not to be confused with later Independent Catholic "
            "bodies. Durable enough for cataloguing; largely faded as an organized communion."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected the Concordat settlement and papal/civil reorganization of French "
                "dioceses, continuing a parallel anticoncordataire hierarchy and congregations."
            ),
        },
    },
    # --- Degree 2+ (traceable forks) ---
    {
        "id": "catholic-mariavite-felicjanow",
        "name": "Catholic Mariavite Church (Felicjanów)",
        "approx_rupture": "1935",
        "rupture_year": 1935,
        "region": "Poland",
        "broke_from": "mariavite",
        "relation": "internal_schism",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Minority Mariavite body that remained with Archbishop Kowalski after the 1935 "
            "deposition dispute; headquartered at Felicjanów."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Split from the Płock Mariavite majority over Kowalski’s leadership and "
                "doctrinal/disciplinary innovations."
            ),
            "vs_parent": "Loyalty to Kowalski and Felicjanów line vs Płock Old Catholic Mariavite majority (1935).",
        },
    },
    {
        "id": "church-of-the-brethren",
        "name": "Church of the Brethren (Schwarzenau Brethren)",
        "approx_rupture": "1708",
        "rupture_year": 1708,
        "region": "Germany → North America",
        "broke_from": "anabaptist",
        "relation": "radical_reformation_branch",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Schwarzenau Brethren (German Baptists / Dunkers) formed 1708 under Alexander Mack "
            "with believers’ baptism and Anabaptist-Pietist practice; distinct from Mennonite "
            "conferences."
        ),
        "notes": "Parent anabaptist = Radical Reformation family; not a Mennonite conference schism.",
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Gathered a new believers’-baptism brotherhood at Schwarzenau with distinctive "
                "trine immersion and Pietist emphases alongside Anabaptist separationism."
            ),
            "vs_parent": "Schwarzenau Brethren identity vs other Anabaptist/Mennonite streams.",
        },
    },
    {
        "id": "reformed-episcopal-church",
        "name": "Reformed Episcopal Church",
        "approx_rupture": "1873",
        "rupture_year": 1873,
        "region": "United States (later wider)",
        "broke_from": "anglican",
        "relation": "evangelical_anglican_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Evangelical Anglican body founded by Bishop George David Cummins and others "
            "leaving the Protestant Episcopal Church over ritualism and catholicizing trends."
        ),
        "notes": "broke_from=anglican denotes the Anglican/Episcopal communion umbrella (specifically PECUSA).",
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected advancing ritualism and exclusive sacramental claims in the Episcopal "
                "Church; organized a Reformed Episcopal jurisdiction with evangelical Anglican formularies."
            ),
            "vs_parent": "Evangelical/low-church protest vs ritualist trajectory in the Episcopal Church (1873).",
        },
    },
    {
        "id": "free-church-of-scotland",
        "name": "Free Church of Scotland",
        "approx_rupture": "1843 (Disruption)",
        "rupture_year": 1843,
        "region": "Scotland",
        "broke_from": "presbyterian",
        "relation": "disruption",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Evangelical majority left the established Church of Scotland in the 1843 Disruption "
            "over spiritual independence and patronage, forming the Free Church of Scotland."
        ),
        "notes": (
            "Parent presbyterian = Church of Scotland / Presbyterian establishment. "
            "Later Free Church history includes the 1900 United Free merger and a continuing Free Church remnant."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected state intrusion via patronage and defended the spiritual independence "
                "of the church, leaving the establishment in the Disruption of 1843."
            ),
            "vs_parent": "Spiritual independence / anti-patronage Free Church vs established Church of Scotland.",
        },
    },
    {
        "id": "orthodox-presbyterian-church",
        "name": "Orthodox Presbyterian Church",
        "approx_rupture": "1936",
        "rupture_year": 1936,
        "region": "United States",
        "broke_from": "presbyterian",
        "relation": "confessional_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Confessional Presbyterian church formed under J. Gresham Machen after conflict "
            "with the Presbyterian Church in the U.S.A. over modernism and foreign missions."
        ),
        "notes": "broke_from=presbyterian tracks PCUSA as the Presbyterian parent body.",
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Separated from the Presbyterian Church in the U.S.A. over doctrinal modernism "
                "and control of missions (Independent Board conflict), organizing the OPC."
            ),
            "vs_parent": "Confessional orthodoxy and independent missions vs PCUSA modernism (1936).",
        },
    },
    {
        "id": "remonstrant-brotherhood",
        "name": "Remonstrant Brotherhood",
        "approx_rupture": "1619–",
        "rupture_year": 1619,
        "region": "Netherlands",
        "broke_from": "reformed",
        "relation": "doctrinal_expulsion",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Dutch Arminian (Remonstrant) churches organized after the Synod of Dort (1618–19) "
            "condemned the Remonstrant articles and expelled Arminian ministers from the "
            "Dutch Reformed Church."
        ),
        "notes": (
            "Dort is a Reformed synod, not in the Catholic ecumenical council corpus. "
            "Lineage still traces Reformed → Catholic via the magisterial Reformation break."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected Dort’s Calvinist condemnations of the five Remonstrant articles "
                "(conditional election, universal atonement, etc.) and formed a separate Remonstrant church."
            ),
            "vs_parent": "Arminian Remonstrant theology vs Synod of Dort / Dutch Reformed orthodoxy.",
        },
    },
    {
        "id": "primitive-methodist",
        "name": "Primitive Methodist Church",
        "approx_rupture": "1811",
        "rupture_year": 1811,
        "region": "England → wider",
        "broke_from": "methodist",
        "relation": "revivalist_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Hugh Bourne / William Clowes camp-meeting Methodists, excluded from Wesleyan "
            "Methodist Connexion structures, organized the Primitive Methodist Connexion (1811)."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Continued open-air camp-meeting revivalism after Wesleyan Methodist authorities "
                "disciplined leaders; formed a separate Primitive Methodist connexion."
            ),
            "vs_parent": "Camp-meeting revivalism and lay intensity vs Wesleyan Methodist connexional control.",
        },
    },
    {
        "id": "evangelical-covenant-church",
        "name": "Evangelical Covenant Church",
        "approx_rupture": "1885 (Mission Covenant)",
        "rupture_year": 1885,
        "region": "Sweden → United States",
        "broke_from": "lutheran",
        "relation": "mission_covenant_free_church",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Swedish Mission Covenant / Mission Friends free-church movement arising from "
            "Lutheran revivalism; American Evangelical Covenant Church continues that stream."
        ),
        "notes": "Parent lutheran = state-church Lutheran context of the Mission Covenant secession.",
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Formed a free Mission Covenant church emphasizing conversion, Bible, and "
                "congregational mission outside the Lutheran state-church establishment."
            ),
            "vs_parent": "Free-church Mission Covenant identity vs Swedish/American Lutheran establishment.",
        },
    },
    {
        "id": "catholic-apostolic-church",
        "name": "Catholic Apostolic Church (Irvingite)",
        "approx_rupture": "1835",
        "rupture_year": 1835,
        "region": "Britain → Europe / North America",
        "broke_from": "presbyterian",
        "relation": "apostolic_restoration",
        "confidence": "contested",
        "status": "historical",
        "summary": (
            "Apostolic restorationist body associated with Edward Irving and the Albury circle; "
            "organized with restored ‘apostles’ (c. 1835). Grew from Church of Scotland / "
            "Presbyterian and broader Protestant apocalyptic circles."
        ),
        "notes": (
            "confidence=contested for single-parent simplicity: Irving was Church of Scotland; "
            "English participants included Anglicans. broke_from=presbyterian tracks Irving’s church. "
            "The original CAC largely ceased as apostles died; New Apostolic Church is the main living fork."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Taught a restored apostolate and charismatic order beyond historic Presbyterian/"
                "Anglican ministry, organizing the Catholic Apostolic Church."
            ),
            "vs_parent": "Restored apostles and prophetic office vs Presbyterian (and Anglican) ministry norms.",
        },
    },
    {
        "id": "new-apostolic-church",
        "name": "New Apostolic Church",
        "approx_rupture": "1863",
        "rupture_year": 1863,
        "region": "Germany → global",
        "broke_from": "catholic-apostolic-church",
        "relation": "continued_apostolate",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Hamburg-centered continuation that called further apostles after conflict with "
            "remaining Catholic Apostolic apostles (1863); grew into the global New Apostolic Church."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Insisted on continuing to seal apostles beyond the original Catholic Apostolic "
                "college; organized separately after the Hamburg schism."
            ),
            "vs_parent": "Ongoing apostle calling (Hamburg) vs closed original Catholic Apostolic apostolate.",
        },
    },
    {
        "id": "church-of-god-cleveland",
        "name": "Church of God (Cleveland, Tennessee)",
        "approx_rupture": "1886 / Pentecostal turn 1907–",
        "rupture_year": 1886,
        "region": "United States → global",
        "broke_from": "holiness-movement",
        "relation": "holiness_pentecostal_denomination",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Holiness church begun in the R. G. Spurling / A. J. Tomlinson stream (1886); "
            "became a major classical Pentecostal denomination after Azusa-era Spirit baptism teaching."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Organized a distinct Holiness (later Pentecostal) church government and "
                "doctrine of Spirit baptism apart from Methodist-Holiness parent bodies."
            ),
            "vs_parent": "Church of God (Cleveland) Holiness–Pentecostal order vs broader Holiness movement churches.",
        },
    },
    {
        "id": "foursquare",
        "name": "International Church of the Foursquare Gospel",
        "approx_rupture": "1923",
        "rupture_year": 1923,
        "region": "United States → global",
        "broke_from": "pentecostal",
        "relation": "denomination_foundation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Pentecostal denomination founded by Aimee Semple McPherson (1923) with the "
            "‘Foursquare’ gospel emphasis; distinct from Assemblies of God and other classical bodies."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Organized a separate Foursquare Pentecostal denomination around McPherson’s "
                "Angelus Temple ministry and foursquare doctrinal formula."
            ),
            "vs_parent": "Foursquare denominational organization vs other classical Pentecostal fellowships.",
        },
    },
    {
        "id": "advent-christian",
        "name": "Advent Christian Church",
        "approx_rupture": "1860",
        "rupture_year": 1860,
        "region": "United States",
        "broke_from": "adventist",
        "relation": "millerite_branch",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Conditionalist Adventist denomination organized from Millerite advent believers "
            "who did not accept Seventh-day Adventist distinctive doctrines (Sabbath, EGW, sanctuary)."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Continued adventist expectation with conditional immortality while rejecting "
                "Seventh-day Adventist Sabbath and prophetic claims as binding marks of the remnant."
            ),
            "vs_parent": "Advent Christian conditionalism vs emerging Sabbatarian Adventist (SDA) distinctives.",
        },
    },
    {
        "id": "christian-reformed-church",
        "name": "Christian Reformed Church in North America",
        "approx_rupture": "1857",
        "rupture_year": 1857,
        "region": "United States / Canada",
        "broke_from": "reformed",
        "relation": "secession",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Dutch Reformed immigrants in Michigan seceded from the Reformed Church in America "
            "(1857), forming what became the Christian Reformed Church; linked to Afscheiding "
            "confessional concerns."
        ),
        "notes": (
            "broke_from=reformed uses the Reformed family umbrella (immediate parent body: RCA). "
            "Related to Netherlands Afscheiding/Doleantie confessionalism already noted under dutch-reformed-splits."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Seceded from the Reformed Church in America over confessional laxity, "
                "Americanization, and Freemasonry concerns among Dutch seceder immigrants."
            ),
            "vs_parent": "Confessional Dutch seeder CRC vs RCA practice (1857).",
        },
    },
]

# Higher-degree deepenings of existing branches (same factual bar).
DEEPER_BRANCHES: list[dict] = [
    {
        "id": "free-will-baptist",
        "name": "Free Will Baptist churches (National Association of Free Will Baptists)",
        "approx_rupture": "1727– / Nat’l Assoc. 1935",
        "rupture_year": 1780,
        "region": "United States",
        "broke_from": "baptist",
        "relation": "doctrinal_branch",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Arminian (‘General’ / Free Will) Baptist stream distinct from Particular/Calvinistic "
            "Baptists; northern and southern Free Will bodies united in the National Association "
            "of Free Will Baptists (1935)."
        ),
        "notes": (
            "broke_from=baptist as the believers’-baptism parent family. Free Will identity is "
            "doctrinal (general atonement, free will), not a single 1780 secession decree from one convention."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Affirmed general atonement and human free will against stricter Calvinistic "
                "Particular Baptist confessions, organizing lasting Free Will Baptist associations."
            ),
            "vs_parent": "Arminian Free Will Baptist theology vs Particular/Calvinistic Baptist orthodoxy.",
        },
    },
    {
        "id": "disciples-of-christ",
        "name": "Christian Church (Disciples of Christ)",
        "approx_rupture": "1906 (US Census recognition of Restoration three-way split)",
        "rupture_year": 1906,
        "region": "United States → wider",
        "broke_from": "restoration-movement",
        "relation": "restoration_wing",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Open-membership, instrumental Restoration wing that became the Christian Church "
            "(Disciples of Christ), distinguished from a cappella Churches of Christ after the "
            "early-20th-century Restoration division."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Accepted instrumental music, missionary societies, and broader open-membership "
                "practice within the Stone–Campbell movement, crystallizing as the Disciples of Christ."
            ),
            "vs_parent": "Disciples openness (instruments, societies, membership) vs stricter Restoration congregations.",
        },
    },
    {
        "id": "independent-christian-churches",
        "name": "Christian Churches and Churches of Christ (Independent)",
        "approx_rupture": "1920s–1960s",
        "rupture_year": 1927,
        "region": "United States",
        "broke_from": "disciples-of-christ",
        "relation": "conservative_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Conservative instrumental Restoration congregations that refused Disciples "
            "denominational structures and theological liberalism, remaining as Independent "
            "Christian Churches / Churches of Christ (not the a cappella Churches of Christ)."
        ),
        "notes": "Date approximates North American Christian Convention / independent alignment period.",
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected Disciples’ restructure and liberal theology while retaining instruments "
                "and remaining outside both the Disciples denomination and a cappella Churches of Christ."
            ),
            "vs_parent": "Independent Christian Church conservatism vs Disciples denominational liberalism/restructure.",
        },
    },
    {
        "id": "american-baptist-association",
        "name": "American Baptist Association",
        "approx_rupture": "1905",
        "rupture_year": 1905,
        "region": "United States",
        "broke_from": "southern-baptist",
        "relation": "landmark_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Landmark Baptist fellowship organized after withdrawal from Southern Baptist "
            "Convention structures over local-church authority, closed communion, and opposition "
            "to centralized denominationalism (Baptist General Association → ABA)."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Landmark ecclesiology: absolute local-church autonomy, Baptist succession claims, "
                "and refusal of ‘alien immersion’ / open pulpit practices associated with Convention Baptists."
            ),
            "vs_parent": "Landmark associational Baptists vs Southern Baptist Convention centralization (1905).",
        },
    },
    {
        "id": "baptist-missionary-association",
        "name": "Baptist Missionary Association of America",
        "approx_rupture": "1950",
        "rupture_year": 1950,
        "region": "United States",
        "broke_from": "american-baptist-association",
        "relation": "associational_schism",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Landmark Baptist body formed in 1950 when churches left the American Baptist "
            "Association (initially North American Baptist Association; renamed BMAA)."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Split from the American Baptist Association over associational authority, "
                "missions administration, and leadership conflicts while remaining Landmark in ecclesiology."
            ),
            "vs_parent": "BMAA associational/missions dispute vs ABA (1950).",
        },
    },
    {
        "id": "presbyterian-church-in-america",
        "name": "Presbyterian Church in America",
        "approx_rupture": "1973",
        "rupture_year": 1973,
        "region": "United States",
        "broke_from": "presbyterian",
        "relation": "confessional_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Conservative Presbyterian denomination formed chiefly from the Presbyterian Church "
            "in the United States (Southern) over biblical authority, confessional standards, "
            "and opposition to liberal trends."
        ),
        "notes": "broke_from=presbyterian umbrella; immediate parent body was PCUS.",
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Left the Presbyterian Church in the United States citing theological liberalism "
                "and departure from confessional Reformed standards, organizing the PCA."
            ),
            "vs_parent": "Confessional PCA vs PCUS liberalism (1973).",
        },
    },
    {
        "id": "evangelical-presbyterian-church",
        "name": "Evangelical Presbyterian Church",
        "approx_rupture": "1981",
        "rupture_year": 1981,
        "region": "United States",
        "broke_from": "presbyterian",
        "relation": "evangelical_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Evangelical Presbyterian denomination formed mainly by congregations leaving the "
            "United Presbyterian Church / PC(USA) stream over theology, sexuality, and property/"
            "conscience issues, with an ‘essentials’ confessional approach."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Separated from mainline Presbyterian structures for evangelical orthodoxy and "
                "local-church liberty on contested ethical issues, forming the EPC."
            ),
            "vs_parent": "EPC evangelical essentials vs PC(USA)/UPCUSA mainline trajectory (1981).",
        },
    },
    {
        "id": "free-church-of-scotland-continuing",
        "name": "Free Church of Scotland (Continuing)",
        "approx_rupture": "2000",
        "rupture_year": 2000,
        "region": "Scotland",
        "broke_from": "free-church-of-scotland",
        "relation": "confessional_remnant",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Minority that left the Free Church of Scotland in 2000 amid worship and discipline "
            "controversies, claiming to continue historic Free Church practice."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected Free Church Assembly decisions on worship/discipline as departing from "
                "historic Free Church standards; organized the Continuing Free Church."
            ),
            "vs_parent": "Continuing Free Church remnant vs Free Church of Scotland majority (2000).",
        },
    },
    {
        "id": "old-order-mennonite",
        "name": "Old Order Mennonites",
        "approx_rupture": "1872–",
        "rupture_year": 1872,
        "region": "North America",
        "broke_from": "mennonite",
        "relation": "discipline_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Mennonite groups that refused progressive innovations (meetinghouses, revivalism, "
            "later technology) and retained older Ordnung discipline; distinct from the Amish "
            "though parallel in conservatism."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected Mennonite progressivism in worship, education, and later technology, "
                "preserving Old Order discipline and plain patterns."
            ),
            "vs_parent": "Old Order Ordnung vs progressive Mennonite conferences (from 1870s).",
        },
    },
    {
        "id": "evangelical-friends",
        "name": "Evangelical Friends Church International",
        "approx_rupture": "19th–20th c. (Gurneyite / evangelical Friends)",
        "rupture_year": 1887,
        "region": "United States → wider",
        "broke_from": "quakers",
        "relation": "evangelical_branch",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Gurneyite / evangelical Friends who adopted programmed worship, pastors, and "
            "evangelical doctrine, distinct from silent unprogrammed Liberal/Hicksite Friends."
        ),
        "notes": "1887 approximates major pastoral/programmed realignments; EFCI is the modern fellowship name.",
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Embraced evangelical Protestant orthodoxy and pastoral programmed worship "
                "against liberal/quietist Friends trajectories."
            ),
            "vs_parent": "Evangelical programmed Friends vs liberal/unprogrammed Quakerism.",
        },
    },
    {
        "id": "church-of-christ-temple-lot",
        "name": "Church of Christ (Temple Lot)",
        "approx_rupture": "1863 / Hedrickite organization",
        "rupture_year": 1863,
        "region": "United States",
        "broke_from": "latter-day-saints",
        "relation": "succession_dispute",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Hedrickite Latter Day Saint body rejecting Brigham Young and plural marriage; "
            "claims the Independence Temple Lot and a restored church without Utah LDS developments."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected Utah LDS leadership, temple theology as developed in Utah, and plural "
                "marriage; organized under Granville Hedrick with Temple Lot claims."
            ),
            "vs_parent": "Hedrickite Temple Lot succession vs Brighamite LDS (Utah) leadership.",
        },
    },
    {
        "id": "church-of-god-in-christ",
        "name": "Church of God in Christ",
        "approx_rupture": "1897 / Pentecostal reorganization 1907",
        "rupture_year": 1907,
        "region": "United States → global",
        "broke_from": "pentecostal",
        "relation": "denomination_foundation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Major African American Pentecostal denomination under Charles H. Mason after "
            "Azusa Street; Holiness roots reorganized as Pentecostal COGIC."
        ),
        "notes": (
            "Parent pentecostal = classical Pentecostal family. COGIC’s Holiness beginning (1897) "
            "predates the 1907 Pentecostal turn; catalog degree follows the Pentecostal identity."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Organized a distinct episcopal Pentecostal church (COGIC) emphasizing sanctification "
                "and Spirit baptism, separate from other Holiness and Pentecostal bodies."
            ),
            "vs_parent": "COGIC episcopal Pentecostal order vs other classical Pentecostal fellowships.",
        },
    },
    {
        "id": "united-pentecostal-church",
        "name": "United Pentecostal Church International",
        "approx_rupture": "1945 (merger of Oneness bodies)",
        "rupture_year": 1945,
        "region": "United States → global",
        "broke_from": "oneness-pentecostal",
        "relation": "denominational_consolidation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Largest Oneness Pentecostal denomination, formed by merger of Pentecostal "
            "Church, Incorporated and Pentecostal Assemblies of Jesus Christ (1945)."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Consolidated major Oneness Pentecostal organizations into UPCI with shared "
                "Jesus’-name baptism and non-Trinitarian confession."
            ),
            "vs_parent": "UPCI organizational merger within the Oneness Pentecostal family.",
        },
    },
    {
        "id": "adventist-reform-movement",
        "name": "Seventh Day Adventist Reform Movement",
        "approx_rupture": "1920s (WWI crisis)",
        "rupture_year": 1925,
        "region": "Europe → global",
        "broke_from": "seventh-day-adventist",
        "relation": "discipline_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Sabbatarian Adventist reform body arising from World War I conflicts over military "
            "service and church discipline within European Seventh-day Adventism."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Charged the Seventh-day Adventist Church with compromising Sabbath and "
                "noncombatant principles in wartime; organized a Reform Movement."
            ),
            "vs_parent": "Reform Movement wartime/Sabbath discipline vs SDA official wartime policy.",
        },
    },
    {
        "id": "bible-methodist",
        "name": "Bible Methodist Connection of Churches",
        "approx_rupture": "1968–1970s",
        "rupture_year": 1970,
        "region": "United States",
        "broke_from": "wesleyan-church",
        "relation": "conservative_holiness_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Conservative Holiness Methodist body formed by congregations leaving the Wesleyan "
            "Church over perceived relaxation of Holiness standards after mid-20th-century mergers."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Rejected Wesleyan Church compromises on Holiness lifestyle/standards and "
                "organized the Bible Methodist Connection."
            ),
            "vs_parent": "Conservative Holiness standards vs post-merger Wesleyan Church practice.",
        },
    },
    {
        "id": "calvary-chapel",
        "name": "Calvary Chapel Association",
        "approx_rupture": "1965–",
        "rupture_year": 1965,
        "region": "United States → global",
        "broke_from": "foursquare",
        "relation": "pastor_led_network",
        "confidence": "contested",
        "status": "extant",
        "summary": (
            "Chuck Smith’s Calvary Chapel movement emerging from Foursquare/Pentecostal "
            "contexts into an independent charismatic-evangelical association with distinctive "
            "verse-by-verse teaching and Jesus Movement outreach."
        ),
        "notes": (
            "confidence=contested: Smith’s path involved Foursquare credentialing/influence but "
            "Calvary Chapel is not a simple congregational secession vote from ICFG. Parent "
            "foursquare = nearest classical Pentecostal institutional context."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Developed an independent Calvary Chapel model (expositional preaching, "
                "balanced charismatic practice, association polity) outside Foursquare denominational structures."
            ),
            "vs_parent": "Calvary Chapel association model vs Foursquare denominational order.",
        },
    },
    {
        "id": "national-baptist-convention",
        "name": "National Baptist Convention, USA",
        "approx_rupture": "1895",
        "rupture_year": 1895,
        "region": "United States",
        "broke_from": "baptist",
        "relation": "separate_convention",
        "confidence": "contested",
        "status": "extant",
        "summary": (
            "Major African American Baptist convention organized 1895 from earlier Black Baptist "
            "mission/publishing unions—parallel to white Baptist conventions rather than a "
            "single congregational secession."
        ),
        "notes": (
            "confidence=contested for ‘breakaway’ typology: largely organizational consolidation "
            "under segregation, not a doctrinal anathema against a parent synod. Kept because it "
            "is the parent of later clear Baptist schisms (e.g. Progressive National Baptists)."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Built independent Black Baptist national structures for missions, education, "
                "and publishing apart from white Baptist conventions."
            ),
            "vs_parent": "National Black Baptist convention autonomy vs white Baptist convention structures.",
        },
    },
    {
        "id": "progressive-national-baptist",
        "name": "Progressive National Baptist Convention",
        "approx_rupture": "1961",
        "rupture_year": 1961,
        "region": "United States",
        "broke_from": "national-baptist-convention",
        "relation": "civil_rights_separation",
        "confidence": "established",
        "status": "extant",
        "summary": (
            "Black Baptist convention formed in 1961 by leaders leaving the National Baptist "
            "Convention, USA, amid disputes over civil-rights activism and presidential tenure limits."
        ),
        "disagreement": {
            "kind": "summary",
            "summary": (
                "Split from NBCUSA over support for the civil-rights movement and convention "
                "governance (tenure) conflicts."
            ),
            "vs_parent": "Progressive National Baptists’ civil-rights activism vs NBCUSA leadership stance (1961).",
        },
    },
]


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
        if not chain or chain[0] != "catholic-church":
            chain = ["catholic-church"] + [c for c in chain if c != "catholic-church"]
        g["lineage"] = chain
        g["separation_degree"] = max(0, len(chain) - 1)


def write_groups_md(cat: dict) -> None:
    groups = cat["groups"]
    name_of = {g["id"]: g["name"] for g in groups}
    name_of["catholic-church"] = "Catholic Church"
    locus = cat["stats"].get("with_council_locus", 0)
    summary = cat["stats"].get("with_summary_only", 0)
    lines = [
        "# Breakaway groups over time (lineage catalog)",
        "",
        "Machine-readable source: [`groups_catalog.json`](groups_catalog.json).",
        "",
        "Non-breakaways are under `excluded_non_breakaways`; family labels under `family_labels`.",
        "",
        f"**{cat['stats']['group_count']} groups** · locus-linked: {locus} · "
        f"summary-only: {summary} · excluded: {cat['stats'].get('excluded_non_breakaways', 0)}",
        "",
        "| Deg | Group | Broke from | Disagreement | Kind | Confidence |",
        "|---:|---|---|---|---|---|",
    ]
    for g in sorted(
        groups,
        key=lambda x: (
            x.get("separation_degree") or 0,
            x.get("rupture_year") or 0,
            x["name"],
        ),
    ):
        d = g.get("disagreement") or {}
        kind = d.get("kind", "")
        if kind == "council_locus":
            tip = f"`{d.get('canonical_citation', '')}` — {d.get('summary', '')}"
        else:
            tip = d.get("summary") or g.get("summary") or ""
        tip = tip.replace("|", "/").replace("\n", " ")
        if len(tip) > 120:
            tip = tip[:117] + "..."
        parent = name_of.get(g.get("broke_from") or "", g.get("broke_from") or "—")
        lines.append(
            f"| {g.get('separation_degree')} | {g['name']} | {parent} | {tip} | "
            f"{kind} | {g.get('confidence', '')} |"
        )
    lines += ["", "## Excluded (not breakaways)", ""]
    for r in cat.get("excluded_non_breakaways") or []:
        lines.append(f"- **{r.get('name', r['id'])}** (`{r['id']}`): {r['reason']}")
    if cat.get("family_labels"):
        lines += ["", "## Family labels (not polities)", ""]
        for f in cat["family_labels"]:
            lines.append(
                f"- **{f['name']}** (`{f['id']}`): {f['reason']} "
                f"Members: {', '.join(f.get('member_ids') or [])}."
            )
    lines.append("")
    GROUPS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    by_id = {g["id"]: g for g in cat["groups"]}

    # Rename misleading Ancient Church of the East id if still present
    old_ace = "oriental-orthodox-assyrian-split"
    if old_ace in by_id and "ancient-church-of-the-east" not in by_id:
        g = by_id.pop(old_ace)
        g["id"] = "ancient-church-of-the-east"
        g["notes"] = (
            (g.get("notes") or "")
            + " Id normalized from oriental-orthodox-assyrian-split (not an Oriental Orthodox body)."
        ).strip()
        # fix lineage self-id
        g["lineage"] = [
            ("ancient-church-of-the-east" if x == old_ace else x)
            for x in (g.get("lineage") or [])
        ]
        by_id[g["id"]] = g
        print(f"renamed {old_ace} -> ancient-church-of-the-east")

    pending = list(NEW_GROUPS) + list(DEEPER_BRANCHES)
    pending_ids = {g["id"] for g in pending}
    added = []
    skipped = []
    for raw in pending:
        g = dict(raw)
        if isinstance(g.get("rupture_year"), str) and g["rupture_year"].endswith('"'):
            g["rupture_year"] = int(g["rupture_year"].rstrip('"'))
        gid = g["id"]
        if gid in by_id:
            skipped.append(gid)
            continue
        parent = g["broke_from"]
        if parent != "catholic-church" and parent not in by_id and parent not in pending_ids:
            raise SystemExit(f"{gid}: missing parent {parent}")
        g.setdefault("council_link_in_corpus", None)
        g.setdefault("in_step1_breakaways", False)
        g.setdefault("lineage", [])
        by_id[gid] = g
        added.append(gid)

    for gid in added:
        parent = by_id[gid]["broke_from"]
        if parent != "catholic-church" and parent not in by_id:
            raise SystemExit(f"{gid}: still missing parent {parent}")

    recompute_lineage(by_id)

    # Traceability check: every group reaches catholic-church
    bad_trace = []
    for g in by_id.values():
        if not g.get("lineage") or g["lineage"][0] != "catholic-church":
            bad_trace.append(g["id"])
        if "catholic-church" not in (g.get("lineage") or []):
            bad_trace.append(g["id"])
    if bad_trace:
        raise SystemExit(f"lineage does not reach catholic-church: {bad_trace}")

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

    by_degree: dict[str, int] = {}
    locus = summary = step1 = 0
    extant = historical = synthetic = contested = 0
    for g in groups:
        d = str(g.get("separation_degree", 0))
        by_degree[d] = by_degree.get(d, 0) + 1
        st = g.get("status")
        if st == "extant":
            extant += 1
        elif st == "historical":
            historical += 1
        elif st == "synthetic":
            synthetic += 1
        if g.get("confidence") == "contested":
            contested += 1
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
        "extant": extant,
        "historical": historical,
        "synthetic": synthetic,
        "contested_confidence": contested,
        "excluded_non_breakaways": len(cat.get("excluded_non_breakaways") or []),
        "family_labels": len(cat.get("family_labels") or []),
        "with_council_locus": locus,
        "with_summary_only": summary,
        "disagreement_coverage": locus + summary,
    }

    CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_groups_md(cat)
    print(f"added {len(added)}: {', '.join(added)}")
    if skipped:
        print(f"skipped existing: {', '.join(skipped)}")
    print(
        f"total {cat['stats']['group_count']} · by_degree={cat['stats']['by_degree']} · "
        f"d1={cat['stats']['by_degree'].get('1')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
