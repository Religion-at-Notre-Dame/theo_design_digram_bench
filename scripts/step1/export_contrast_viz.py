#!/usr/bin/env python3
"""Export interactive HTML viewer for the contrast database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN = ROOT / "outputs/step1/breakaways/contrast/contrast.jsonl"
DEFAULT_OUT = ROOT / "outputs/step1/breakaways/contrast/contrast.html"


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def build_html(
    rows: list[dict],
    *,
    title: str | None = None,
    lede: str | None = None,
    source_name: str | None = None,
    regenerate_cmd: str | None = None,
    all_groups: list[str] | None = None,
) -> str:
    has_tier = any(r.get("tier") for r in rows)
    slim = []
    for r in rows:
        item = {
            "id": r["id"],
            "question": r["question"],
            "catholic_answer": r["catholic_answer"],
            "breakaway_group": r["breakaway_group"],
            "breakaway_answer": r["breakaway_answer"],
            "council": r.get("council") or "",
            "canonical_citation": r.get("canonical_citation") or "",
            "notes": r.get("notes") or "",
            "tier": r.get("tier") or "",
            "confidence": r.get("confidence") or "",
            "contrast_kind": r.get("contrast_kind") or "",
        }
        slim.append(item)
    # Prefer authoritative match-list groups when provided (viz basis)
    row_groups = {r["breakaway_group"] for r in slim}
    if all_groups:
        groups = sorted(set(all_groups) | row_groups)
    else:
        groups = sorted(row_groups)
    councils = sorted({r["council"] for r in slim if r["council"]})
    n_strict = sum(1 for r in slim if r["tier"] == "strict")
    n_extended = sum(1 for r in slim if r["tier"] == "extended")
    data = {
        "rows": slim,
        "groups": groups,
        "councils": councils,
        "n": len(slim),
        "has_tier": has_tier,
        "n_strict": n_strict,
        "n_extended": n_extended,
    }
    payload = json.dumps(data, ensure_ascii=False)

    page_title = title or "Catholic vs breakaway — contrast questions"
    page_lede = lede or (
        "Natural-language questions from council loci where both the Catholic answer "
        "and the breakaway group’s answer can be traced, with the conciliar citation."
    )
    src = source_name or "contrast.jsonl"
    regen = regenerate_cmd or "python scripts/step1/export_contrast_viz.py"

    tier_stat = ""
    tier_filter = ""
    if has_tier:
        tier_stat = """
      <div class="stat"><strong id="stat-strict">0</strong><span>strict (high)</span></div>
      <div class="stat"><strong id="stat-ext">0</strong><span>extended (low)</span></div>"""
        tier_filter = """
      <label>Tier
        <select id="filter-tier">
          <option value="">All tiers</option>
          <option value="strict">Strict only</option>
          <option value="extended">Extended only</option>
        </select>
      </label>
      <label>Kind
        <select id="filter-kind">
          <option value="">All kinds</option>
          <option value="explicit_trace">explicit_trace</option>
          <option value="inferred_opposition">inferred_opposition</option>
          <option value="ai_expanded">ai_expanded</option>
        </select>
      </label>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_title}</title>
  <style>
    :root {{
      --ink: #1c2430;
      --muted: #5c6b7a;
      --line: #d5dde5;
      --accent: #2a5f7a;
      --accent2: #8a4b2f;
      --catholic: #2f6b4f;
      --break: #8a4b2f;
      --paper: #f7f5f1;
      --card: #fffcf7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Source Serif 4", "Iowan Old Style", Palatino, "Palatino Linotype", Georgia, serif;
      color: var(--ink);
      background:
        radial-gradient(ellipse at top, #fffdf8 0%, var(--paper) 55%, #efebe4 100%);
      min-height: 100vh;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 1.25rem 3.5rem;
    }}
    h1 {{
      font-size: clamp(1.55rem, 3vw, 2.15rem);
      font-weight: 600;
      letter-spacing: -0.02em;
      margin: 0 0 0.35rem;
    }}
    .lede {{
      color: var(--muted);
      max-width: 40rem;
      line-height: 1.5;
      margin: 0 0 1.35rem;
    }}
    .stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem 1.75rem;
      margin-bottom: 1.1rem;
      padding-bottom: 0.9rem;
      border-bottom: 1px solid var(--line);
    }}
    .stat strong {{
      display: block;
      font-size: 1.45rem;
      color: var(--accent);
      font-variant-numeric: tabular-nums;
    }}
    .stat span {{ color: var(--muted); font-size: 0.88rem; }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem 1.1rem;
      align-items: end;
      margin-bottom: 1.35rem;
    }}
    label {{
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      font-size: 0.78rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    select, input[type="search"] {{
      font: inherit;
      color: var(--ink);
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 0.4rem 0.55rem;
      min-width: 11rem;
    }}
    input[type="search"] {{ min-width: 14rem; }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 15rem) minmax(0, 1fr);
      gap: 1.25rem;
      align-items: start;
    }}
    @media (max-width: 820px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .toc {{ max-height: 12rem; }}
    }}
    .toc {{
      border: 1px solid var(--line);
      background: var(--card);
      border-radius: 6px;
      max-height: calc(100vh - 12rem);
      overflow: auto;
      position: sticky;
      top: 1rem;
    }}
    .toc button {{
      display: block;
      width: 100%;
      text-align: left;
      font: inherit;
      font-size: 0.82rem;
      line-height: 1.35;
      color: var(--ink);
      background: transparent;
      border: 0;
      border-bottom: 1px solid var(--line);
      padding: 0.55rem 0.7rem;
      cursor: pointer;
    }}
    .toc button:hover {{ background: rgba(42, 95, 122, 0.06); }}
    .toc button.active {{
      background: rgba(42, 95, 122, 0.1);
      color: var(--accent);
      font-weight: 600;
    }}
    .toc .g {{
      display: block;
      font-size: 0.7rem;
      color: var(--muted);
      text-transform: none;
      letter-spacing: 0;
      margin-top: 0.15rem;
      font-weight: 400;
    }}
    .viewer {{
      border: 1px solid var(--line);
      background: var(--card);
      border-radius: 6px;
      padding: 1.35rem 1.4rem 1.5rem;
      min-height: 22rem;
    }}
    .nav {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }}
    .nav button {{
      font: inherit;
      font-size: 0.9rem;
      color: var(--accent);
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 0.35rem 0.75rem;
      cursor: pointer;
    }}
    .nav button:hover {{ border-color: var(--accent); }}
    .nav button:disabled {{
      opacity: 0.4;
      cursor: default;
      border-color: var(--line);
    }}
    .pos {{
      color: var(--muted);
      font-size: 0.88rem;
      font-variant-numeric: tabular-nums;
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem 0.85rem;
      margin-bottom: 0.85rem;
      font-size: 0.82rem;
      color: var(--muted);
    }}
    .pill {{
      display: inline-block;
      padding: 0.12rem 0.45rem;
      border-radius: 3px;
      background: rgba(138, 75, 47, 0.1);
      color: var(--break);
    }}
    .question {{
      font-size: clamp(1.15rem, 2.2vw, 1.45rem);
      font-weight: 600;
      line-height: 1.35;
      letter-spacing: -0.015em;
      margin: 0 0 1.25rem;
    }}
    .answers {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }}
    @media (max-width: 700px) {{
      .answers {{ grid-template-columns: 1fr; }}
    }}
    .answer {{
      border-top: 3px solid var(--line);
      padding-top: 0.7rem;
    }}
    .answer.catholic {{ border-top-color: var(--catholic); }}
    .answer.breakaway {{ border-top-color: var(--break); }}
    .answer h2 {{
      margin: 0 0 0.45rem;
      font-size: 0.78rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .answer.catholic h2 {{ color: var(--catholic); }}
    .answer.breakaway h2 {{ color: var(--break); }}
    .answer p {{
      margin: 0;
      line-height: 1.55;
      font-size: 0.98rem;
    }}
    .cite {{
      margin-top: 1.35rem;
      padding-top: 0.9rem;
      border-top: 1px solid var(--line);
      font-size: 0.9rem;
      line-height: 1.45;
    }}
    .cite strong {{
      display: block;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
      font-weight: 600;
      margin-bottom: 0.25rem;
    }}
    .notes {{
      margin-top: 0.75rem;
      font-size: 0.85rem;
      color: var(--muted);
      font-style: italic;
    }}
    .badge {{
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 0.18rem 0.45rem;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
    }}
    .badge.strict {{ color: var(--catholic); border-color: #b7d4c4; background: #f0f7f3; }}
    .badge.extended {{ color: var(--accent2); border-color: #e2c4b4; background: #faf3ef; }}
    .empty {{
      color: var(--muted);
      padding: 2rem 0.5rem;
      text-align: center;
    }}
    footer {{
      margin-top: 1.75rem;
      color: var(--muted);
      font-size: 0.85rem;
    }}
    footer code {{ font-size: 0.8em; }}
  </style>
</head>
<body>
  <main>
    <h1>{page_title.split("—")[0].strip()}</h1>
    <p class="lede">{page_lede}</p>
    <div class="stats">
      <div class="stat"><strong id="stat-n">0</strong><span>questions</span></div>
      <div class="stat"><strong id="stat-shown">0</strong><span>matching filter</span></div>
      <div class="stat"><strong id="stat-groups">0</strong><span>breakaway groups</span></div>
      {tier_stat}
    </div>
    <div class="controls">
      <label>Breakaway group
        <select id="filter-group"><option value="">All groups</option></select>
      </label>
      <label>Council
        <select id="filter-council"><option value="">All councils</option></select>
      </label>
      {tier_filter}
      <label>Search
        <input type="search" id="filter-q" placeholder="Question or citation…" />
      </label>
    </div>
    <div class="layout">
      <nav class="toc" id="toc" aria-label="Question list"></nav>
      <section class="viewer" id="viewer" aria-live="polite"></section>
    </div>
    <footer>
      Source: <code>{src}</code> · regenerate with
      <code>{regen}</code>
    </footer>
  </main>
  <script>
    const DATA = {payload};

    const elGroup = document.getElementById("filter-group");
    const elCouncil = document.getElementById("filter-council");
    const elSearch = document.getElementById("filter-q");
    const elTier = document.getElementById("filter-tier");
    const elKind = document.getElementById("filter-kind");
    const elToc = document.getElementById("toc");
    const elViewer = document.getElementById("viewer");

    DATA.groups.forEach((g) => {{
      const o = document.createElement("option");
      o.value = g; o.textContent = g;
      elGroup.appendChild(o);
    }});
    DATA.councils.forEach((c) => {{
      const o = document.createElement("option");
      o.value = c; o.textContent = c;
      elCouncil.appendChild(o);
    }});

    document.getElementById("stat-n").textContent = String(DATA.n);
    document.getElementById("stat-groups").textContent = String(DATA.groups.length);
    if (DATA.has_tier) {{
      const s = document.getElementById("stat-strict");
      const e = document.getElementById("stat-ext");
      if (s) s.textContent = String(DATA.n_strict);
      if (e) e.textContent = String(DATA.n_extended);
    }}

    let filtered = DATA.rows.slice();
    let index = 0;

    function applyFilter() {{
      const g = elGroup.value;
      const c = elCouncil.value;
      const q = (elSearch.value || "").trim().toLowerCase();
      const tier = elTier ? elTier.value : "";
      const kind = elKind ? elKind.value : "";
      filtered = DATA.rows.filter((r) => {{
        if (g && r.breakaway_group !== g) return false;
        if (c && r.council !== c) return false;
        if (tier && r.tier !== tier) return false;
        if (kind && r.contrast_kind !== kind) return false;
        if (q) {{
          const hay = (r.question + " " + r.canonical_citation + " " + r.breakaway_group + " " + r.council + " " + (r.contrast_kind || "")).toLowerCase();
          if (!hay.includes(q)) return false;
        }}
        return true;
      }});
      document.getElementById("stat-shown").textContent = String(filtered.length);
      index = 0;
      renderToc();
      render();
    }}

    function esc(s) {{
      return String(s || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function shortQ(s) {{
      s = String(s || "");
      return s.length > 72 ? s.slice(0, 69) + "…" : s;
    }}

    function renderToc() {{
      elToc.innerHTML = "";
      filtered.forEach((r, i) => {{
        const b = document.createElement("button");
        b.type = "button";
        b.className = i === index ? "active" : "";
        const tag = r.tier ? ' · ' + r.tier : "";
        b.innerHTML = esc(shortQ(r.question)) + '<span class="g">' + esc(r.breakaway_group) + esc(tag) + "</span>";
        b.addEventListener("click", () => {{ index = i; render(); }});
        elToc.appendChild(b);
      }});
    }}

    function render() {{
      if (!filtered.length) {{
        elViewer.innerHTML = '<p class="empty">No questions match this filter.</p>';
        return;
      }}
      const r = filtered[index];
      const notes = r.notes
        ? '<p class="notes">' + esc(r.notes) + "</p>"
        : "";
      const badges = r.tier
        ? `<span class="badge ${{esc(r.tier)}}">${{esc(r.tier)}} · ${{esc(r.confidence || "")}}</span>
           <span class="badge">${{esc(r.contrast_kind || "")}}</span>`
        : "";
      elViewer.innerHTML = `
        <div class="nav">
          <button type="button" id="prev" ${{index === 0 ? "disabled" : ""}}>← Previous</button>
          <span class="pos">${{index + 1}} / ${{filtered.length}}</span>
          <button type="button" id="next" ${{index >= filtered.length - 1 ? "disabled" : ""}}>Next →</button>
        </div>
        <div class="meta-row">
          <span>${{esc(r.council)}}</span>
          <span class="pill">${{esc(r.breakaway_group)}}</span>
          ${{badges}}
        </div>
        <p class="question">${{esc(r.question)}}</p>
        <div class="answers">
          <article class="answer catholic">
            <h2>Catholic answer</h2>
            <p>${{esc(r.catholic_answer)}}</p>
          </article>
          <article class="answer breakaway">
            <h2>${{esc(r.breakaway_group)}}</h2>
            <p>${{esc(r.breakaway_answer)}}</p>
          </article>
        </div>
        <div class="cite">
          <strong>Citation</strong>
          ${{esc(r.canonical_citation)}}
        </div>
        ${{notes}}
      `;
      document.getElementById("prev").addEventListener("click", () => {{
        if (index > 0) {{ index -= 1; render(); }}
      }});
      document.getElementById("next").addEventListener("click", () => {{
        if (index < filtered.length - 1) {{ index += 1; render(); }}
      }});
      [...elToc.querySelectorAll("button")].forEach((b, i) => {{
        b.classList.toggle("active", i === index);
      }});
      const active = elToc.querySelector("button.active");
      if (active) active.scrollIntoView({{ block: "nearest" }});
    }}

    elGroup.addEventListener("change", applyFilter);
    elCouncil.addEventListener("change", applyFilter);
    elSearch.addEventListener("input", applyFilter);
    if (elTier) elTier.addEventListener("change", applyFilter);
    if (elKind) elKind.addEventListener("change", applyFilter);

    document.addEventListener("keydown", (e) => {{
      if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "SELECT")) return;
      if (e.key === "ArrowLeft" && index > 0) {{ index -= 1; render(); }}
      if (e.key === "ArrowRight" && index < filtered.length - 1) {{ index += 1; render(); }}
    }});

    applyFilter();
  </script>
</body>
</html>
"""


def _load_match_groups() -> list[str] | None:
    """Authoritative breakaway list from denomination_council_matches_50y.json."""
    path = ROOT / "outputs/step1/breakaways/contrast/denomination_council_matches_50y.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    matches = data.get("matches") or []
    names = [m.get("group_name") for m in matches if m.get("group_name")]
    return names or None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="inp", type=Path, default=DEFAULT_IN)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--title", default=None)
    ap.add_argument("--lede", default=None)
    ap.add_argument(
        "--no-match-groups",
        action="store_true",
        help="Do not seed group filter from denomination_council_matches_50y.json",
    )
    args = ap.parse_args()

    rows = load_rows(args.inp)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {
        "title": args.title,
        "lede": args.lede,
        "source_name": args.inp.name,
        "regenerate_cmd": (
            f"python3 scripts/step1/export_contrast_viz.py --in {args.inp} --out {args.out}"
        ),
        "all_groups": None if args.no_match_groups else _load_match_groups(),
    }
    args.out.write_text(build_html(rows, **kwargs), encoding="utf-8")

    # Link from contrast README
    readme = args.out.parent / "README.md"
    if readme.exists():
        body = readme.read_text(encoding="utf-8")
        line = (
            "| `contrast.html` | Interactive viewer (question + both answers + citation) |\n"
            "| `direct_answers.json` | Hand-tuned Yes/No answers applied on rebuild |\n"
        )
        if "contrast.html" not in body:
            body = body.replace(
                "| `agent.md` | Conversion prompt / rules (NL question + dual answers) |\n",
                "| `agent.md` | Conversion prompt / rules (NL question + dual answers) |\n" + line,
            )
            readme.write_text(body, encoding="utf-8")
        elif "direct_answers.json" not in body:
            body = body.replace(
                "| `contrast.html` | Interactive viewer (question + both answers + citation) |\n",
                line,
            )
            readme.write_text(body, encoding="utf-8")

    parent = ROOT / "outputs/step1/breakaways/README.md"
    if parent.exists():
        body = parent.read_text(encoding="utf-8")
        if "contrast/contrast.html" not in body and "Contrast database" in body:
            body = body.replace(
                "[`contrast/agent.md`](contrast/agent.md).",
                "[`contrast/agent.md`](contrast/agent.md). "
                "Viewer: [`contrast/contrast.html`](contrast/contrast.html).",
            )
            parent.write_text(body, encoding="utf-8")

    print(json.dumps({"wrote": str(args.out), "n": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
