# Degree-1 breakaway coverage (Step 1)

Status of each **separation_degree = 1** group from `groups_catalog.json`
relative to the council corpus and the contrast database.

## In the corpus (tagged on council loci)

| Catalog group | Corpus / contrast label | Notes |
|---------------|-------------------------|-------|
| Arian churches | Arian churches | Nicaea I creed |
| Church of the East | Church of the East | Ephesus |
| Armenian Apostolic Church | Armenian Apostolic Church | Florence S8 union |
| Coptic Orthodox Church | Coptic Orthodox Church | Florence S11 union |
| Syriac Orthodox Church | *(via family)* | Shared Chalcedon rupture; no distinct Florence session in tagged set |
| Oriental Orthodox (family) | Oriental Orthodox churches | Chalcedon definition; Constantinople II |
| Eastern Orthodox churches | Eastern Orthodox churches | Florence S6; Lyons II profession |
| Wycliffites / Lollards | Wycliffites / Lollards | Constance |
| Hussites | Hussites | Constance |
| Lutheran churches | Lutheran churches | Trent (primary interlocutor) |
| Reformed / Calvinist churches | *(shared Trent rejections)* | Not separately tagged per locus; see note |
| Anabaptist / Radical Reformation | *(shared Trent rejections)* | Not separately tagged per locus |
| Anglican Communion | *(partial Trent overlap)* | Break also Tudor supremacy; not tagged on Trent rows |
| Old Catholic churches | Old Catholic churches | Vatican I |

**Trent note:** Decrees answer the Reformation generally. Rows are labeled
**Lutheran churches** as the primary historical interlocutor at Trent.
Reformed, Anglican, and Anabaptist communions often reject the same points;
they remain degree-1 catalog entries with `in_step1_breakaways` reflecting
shared Reformational stake where audited.

## Degree-1 with no council locus in the breakaway subset

These stay in `groups_catalog.json` as **summary** (or non-corpus) disagreements.
They are not invented onto council paragraphs.

| Group | Why not tagged on a corpus locus |
|-------|----------------------------------|
| Novatianists | Nicaea regulates reception; rupture predates / is disciplinary |
| Melitian schism (Egypt) | Settlement letter, not a lasting rival communion in our tags |
| Donatists | No English council locus in this corpus tied as breakaway |
| Waldensians | Pre-Reformation; no dedicated ecumenical-council locus tagged |
| Petite Église | Post-concordat; not a conciliar decree locus |
| Latter-day Saints | Modern; not a council break |
| Polish National Catholic Church | Post-Vatican I / local; not tagged on PA canons (Old Catholic is) |
| Philippine Independent Church | 20th c.; not conciliar |
| Mariavite Church | Modern Old Catholic offshoot; degree issues vs Utrecht |
| Iglesia ni Cristo | Modern; not conciliar |
| Czechoslovak Hussite Church | Modern revival; Constance tags use historical Hussites |
| Brazilian Catholic Apostolic Church | Modern |
| Chinese Patriotic Association structures | Modern political/ecclesial; contested |
| Sedevacantist bodies | Post-Vatican II; contested vs breakaway definition |
| Palmarian Catholic Church | Modern; not conciliar |

## Regenerate

```bash
python scripts/step1/refine_breakaway_labels.py
python scripts/step1/compile_breakaways.py
python scripts/step1/build_contrast_db.py
python scripts/step1/export_contrast_viz.py
```
