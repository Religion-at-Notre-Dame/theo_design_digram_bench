#!/usr/bin/env python3
"""Export a chronological council overview visualization (HTML).

Complements council_map.mmd (schism-only) with a full-corpus view:
entries per council over time, plus breakaway counts.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_councils import load_corpus  # noqa: E402

DEFAULT_ENTRIES = ROOT / "outputs" / "step1" / "entries.jsonl"
DEFAULT_OUT = ROOT / "outputs" / "step1" / "council_overview.html"

# Approximate sort keys when date_promulgated is a range or year-only.
COUNCIL_ORDER = [
    "First Council of Nicaea",
    "First Council of Constantinople",
    "Council of Ephesus",
    "Council of Chalcedon",
    "Second Council of Constantinople",
    "Third Council of Constantinople",
    "Second Council of Nicaea",
    "Fourth Council of Constantinople",
    "First Lateran Council",
    "Second Lateran Council",
    "Third Lateran Council",
    "Fourth Lateran Council",
    "First Council of Lyons",
    "Second Council of Lyons",
    "Council of Vienne",
    "Council of Constance",
    "Council of Florence",
    "Fifth Lateran Council",
    "Council of Trent",
    "First Vatican Council",
    "Second Vatican Council",
]


def year_label(raw: str | None) -> str:
    if not raw:
        return "?"
    m = re.search(r"(\d{3,4})", str(raw))
    return m.group(1) if m else str(raw)


def build_rows(entries: list[dict], corpus) -> list[dict]:
    dates = {}
    for record in corpus.records_by_id.values():
        council = record.get("council")
        date = record.get("date_promulgated")
        if council and date and council not in dates:
            dates[council] = date

    by_council = defaultdict(list)
    for entry in entries:
        if entry.get("status") and entry.get("status") != "verified":
            continue
        by_council[entry.get("council") or "Unknown"].append(entry)

    order_index = {name: i for i, name in enumerate(COUNCIL_ORDER)}
    rows = []
    for council, items in by_council.items():
        breakaways = Counter(
            e["breakaway"] for e in items if e.get("breakaway")
        )
        rows.append(
            {
                "council": council,
                "year": year_label(dates.get(council)),
                "date_raw": dates.get(council) or "",
                "entries": len(items),
                "with_breakaway": sum(1 for e in items if e.get("breakaway")),
                "breakaway_labels": [
                    {"name": name, "count": count}
                    for name, count in breakaways.most_common()
                ],
                "sort": order_index.get(council, 500),
            }
        )
    rows.sort(key=lambda r: (r["sort"], r["year"], r["council"]))
    return rows


def render_html(rows: list[dict], total_entries: int, total_breakaway: int) -> str:
    max_entries = max((r["entries"] for r in rows), default=1)
    bar_rows = []
    for r in rows:
        width = max(2, round(100 * r["entries"] / max_entries))
        labels = ", ".join(
            f"{html.escape(b['name'])} ({b['count']})"
            for b in r["breakaway_labels"][:3]
        ) or "—"
        more = len(r["breakaway_labels"]) - 3
        if more > 0:
            labels += f" (+{more})"
        bar_rows.append(
            f"""
      <tr>
        <td class="year">{html.escape(r['year'])}</td>
        <td class="council">{html.escape(r['council'])}</td>
        <td class="count">{r['entries']}</td>
        <td class="bar-cell"><div class="bar" style="width:{width}%" title="{r['entries']} entries"></div></td>
        <td class="break">{r['with_breakaway']}</td>
        <td class="labels">{labels}</td>
      </tr>"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Step 1 — Council overview</title>
  <style>
    :root {{
      --ink: #1c2430;
      --muted: #5c6b7a;
      --line: #d5dde5;
      --fill: #e8eef4;
      --accent: #2a5f7a;
      --paper: #f7f5f1;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Source Serif 4", "Iowan Old Style", Palatino, "Palatino Linotype", Georgia, serif;
      color: var(--ink);
      background:
        radial-gradient(ellipse at top, #fffdf8 0%, var(--paper) 55%, #efebe4 100%);
      min-height: 100vh;
      padding: 2.5rem 1.5rem 4rem;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
    }}
    h1 {{
      font-size: clamp(1.8rem, 3vw, 2.4rem);
      font-weight: 600;
      letter-spacing: -0.02em;
      margin: 0 0 0.4rem;
    }}
    .lede {{
      color: var(--muted);
      font-size: 1.05rem;
      max-width: 42rem;
      line-height: 1.5;
      margin: 0 0 1.75rem;
    }}
    .stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem 2rem;
      margin-bottom: 2rem;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--line);
    }}
    .stat strong {{
      display: block;
      font-size: 1.75rem;
      color: var(--accent);
      font-variant-numeric: tabular-nums;
    }}
    .stat span {{
      color: var(--muted);
      font-size: 0.9rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }}
    th {{
      text-align: left;
      font-weight: 600;
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: 0.55rem 0.6rem;
      border-bottom: 1px solid var(--line);
    }}
    td {{
      padding: 0.55rem 0.6rem;
      border-bottom: 1px solid var(--fill);
      vertical-align: middle;
      font-variant-numeric: tabular-nums;
    }}
    tr:hover td {{ background: rgba(42, 95, 122, 0.04); }}
    .year {{ width: 4.5rem; color: var(--muted); }}
    .council {{ min-width: 12rem; }}
    .count {{ width: 4rem; text-align: right; }}
    .break {{ width: 4.5rem; text-align: right; color: var(--accent); }}
    .bar-cell {{ width: 28%; }}
    .bar {{
      height: 0.7rem;
      background: linear-gradient(90deg, #3d7a96, var(--accent));
      border-radius: 2px;
      min-width: 4px;
    }}
    .labels {{
      color: var(--muted);
      font-size: 0.85rem;
      max-width: 22rem;
    }}
    footer {{
      margin-top: 2rem;
      color: var(--muted);
      font-size: 0.85rem;
    }}
    code {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 0.86em; }}
  </style>
</head>
<body>
  <main>
    <h1>Step 1 council overview</h1>
    <p class="lede">
      Every verified mapping entry across the 21 ecumenical councils, in chronological
      order. Bar length is entry count; breakaway column counts loci tagged with a
      departing group (see also <code>council_map.mmd</code>).
    </p>
    <div class="stats">
      <div class="stat"><strong>{total_entries}</strong><span>verified entries</span></div>
      <div class="stat"><strong>{len(rows)}</strong><span>councils</span></div>
      <div class="stat"><strong>{total_breakaway}</strong><span>with breakaway</span></div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Year</th>
          <th>Council</th>
          <th>Entries</th>
          <th>Volume</th>
          <th>Breakaways</th>
          <th>Top groups</th>
        </tr>
      </thead>
      <tbody>
        {''.join(bar_rows)}
      </tbody>
    </table>
    <footer>
      Generated from <code>outputs/step1/entries.jsonl</code> by
      <code>scripts/step1/export_overview.py</code>.
    </footer>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=Path, default=DEFAULT_ENTRIES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    entries = []
    for line in args.entries.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))

    corpus = load_corpus()
    rows = build_rows(entries, corpus)
    verified = [e for e in entries if e.get("status") == "verified"]
    total_entries = len(verified) if verified else len(entries)
    total_breakaway = sum(1 for e in (verified or entries) if e.get("breakaway"))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        render_html(rows, total_entries, total_breakaway),
        encoding="utf-8",
    )
    print(f"wrote overview ({len(rows)} councils, {total_entries} entries) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
