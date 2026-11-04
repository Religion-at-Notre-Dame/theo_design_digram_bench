#!/usr/bin/env python3
"""Build question–answer visualization driven by denomination_council_matches_50y.

Navigation is the authoritative breakaway list. Each group shows its primary
council and every disagreement Q&A row found for that group in strict
contrast.jsonl and/or contrast_ai.jsonl.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/step1/breakaways/contrast"
STRICT = OUT_DIR / "contrast.jsonl"

MODE_PATHS = {
    "doctrinal": {
        "matches": OUT_DIR / "denomination_council_matches_50y.json",
        "ai": OUT_DIR / "contrast_ai.jsonl",
        "html": OUT_DIR / "match_contrast.html",
        "json": OUT_DIR / "match_contrast.json",
        "title": "Breakaway match list — questions & answers (doctrinal)",
        "description": (
            "One entry per denomination in denomination_council_matches_50y "
            "(doctrinal primary). Questions from strict contrast and doctrinal AI fills. "
            "Disagreement-only."
        ),
    },
    "temporal": {
        "matches": OUT_DIR / "denomination_council_matches_temporal.json",
        "ai": OUT_DIR / "contrast_ai_temporal.jsonl",
        "html": OUT_DIR / "match_contrast_temporal.html",
        "json": OUT_DIR / "match_contrast_temporal.json",
        "title": "Breakaway match list — questions & answers (temporal / nearest council)",
        "description": (
            "Comprehensive time-based pairing: each breakaway’s primary council is the "
            "nearest council by start year. Questions from strict contrast and temporal AI fills. "
            "Disagreement-only. Use this to finish Step 1 council coverage."
        ),
    },
}


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _row_slim(r: dict, *, tier: str) -> dict:
    return {
        "id": r.get("id") or "",
        "tier": tier,
        "confidence": r.get("confidence") or ("high" if tier == "strict" else "low"),
        "question": r.get("question") or "",
        "catholic_answer": r.get("catholic_answer") or "",
        "breakaway_answer": r.get("breakaway_answer") or "",
        "council": r.get("council") or r.get("match_primary_council") or "",
        "canonical_citation": r.get("canonical_citation") or "",
        "source_entry_id": r.get("source_entry_id") or r.get("id") or "",
        "notes": r.get("notes") or "",
    }


def _index_rows(rows: list[dict], *, tier: str) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for r in rows:
        slim = _row_slim(r, tier=tier)
        keys = {_key(r.get("breakaway_group") or "")}
        if r.get("group_id"):
            keys.add(r["group_id"])
        for k in keys:
            if not k:
                continue
            by.setdefault(k, []).append(slim)
    return by


def _collect_for_match(
    m: dict,
    by_strict: dict[str, list[dict]],
    by_ai: dict[str, list[dict]],
) -> list[dict]:
    gid = m["group_id"]
    name_k = _key(m["group_name"])
    found: list[dict] = []
    seen_ids: set[str] = set()

    def _add(rows: list[dict]) -> None:
        for r in rows:
            rid = r["id"]
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            found.append(r)

    _add(by_strict.get(name_k) or [])
    _add(by_ai.get(name_k) or [])
    _add(by_ai.get(gid) or [])

    # Fuzzy: match list name contains / is contained by a row group key
    if not found:
        for store in (by_strict, by_ai):
            for k, rows in store.items():
                if " " not in k and len(k) < 4:
                    continue
                if name_k == k or name_k in k or k in name_k:
                    _add(rows)

    # Prefer strict before AI; stable by id
    found.sort(key=lambda r: (0 if r["tier"] == "strict" else 1, r["id"]))
    return found


def build_payload(mode: str = "doctrinal") -> dict:
    paths = MODE_PATHS[mode]
    match_doc = json.loads(paths["matches"].read_text(encoding="utf-8"))
    matches = match_doc.get("matches") or []
    by_strict = _index_rows(load_jsonl(STRICT), tier="strict")
    by_ai = _index_rows(load_jsonl(paths["ai"]), tier="ai")

    groups = []
    n_with = 0
    n_strict = 0
    n_ai = 0
    n_pending = 0
    n_questions = 0
    by_council: dict[str, int] = {}

    for m in sorted(matches, key=lambda x: (x["start_year"], x["group_name"])):
        rows = _collect_for_match(m, by_strict, by_ai)
        # Prefer questions whose council matches the temporal/doctrinal primary
        primary = m["primary_council"]
        primary_rows = [r for r in rows if (r.get("council") or "") == primary]
        if primary_rows and mode == "temporal":
            # Keep primary-council rows first; still show others as extras
            other = [r for r in rows if r not in primary_rows]
            rows = primary_rows + other

        has_strict = any(r["tier"] == "strict" for r in rows)
        has_ai = any(r["tier"] == "ai" for r in rows)
        status = (
            "strict"
            if has_strict
            else ("ai" if has_ai else "pending")
        )
        if rows:
            n_with += 1
            n_questions += len(rows)
        else:
            n_pending += 1
        if has_strict:
            n_strict += 1
        if has_ai and not has_strict:
            n_ai += 1
        by_council[primary] = by_council.get(primary, 0) + 1

        groups.append(
            {
                "group_id": m["group_id"],
                "group_name": m["group_name"],
                "start_year": m["start_year"],
                "primary_council": primary,
                "primary_reason": m.get("primary_reason") or "",
                "primary_distance_years": m.get("primary_distance_years"),
                "within_window": m.get("within_window"),
                "doctrinal_council": m.get("doctrinal_council"),
                "differs_from_doctrinal": m.get("differs_from_doctrinal"),
                "source": m.get("source") or "",
                "in_step1_breakaways": bool(m.get("in_step1_breakaways")),
                "status": status,
                "n_questions": len(rows),
                "questions": rows,
            }
        )

    return {
        "title": paths["title"],
        "description": paths["description"],
        "match_mode": mode,
        "n_groups": len(groups),
        "n_with_questions": n_with,
        "n_pending": n_pending,
        "n_groups_strict": n_strict,
        "n_groups_ai_only": n_ai,
        "n_questions": n_questions,
        "by_primary_council": dict(sorted(by_council.items(), key=lambda x: -x[1])),
        "groups": groups,
    }


def build_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{data["title"]}</title>
  <style>
    :root {{
      --ink: #1a222c;
      --muted: #5a6a7a;
      --line: #d7dde4;
      --accent: #1f5a72;
      --catholic: #2c6b4f;
      --break: #8b4518;
      --ai: #6b5a2e;
      --pending: #7a7a7a;
      --paper: #f4f1ec;
      --card: #fffcf8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Source Serif 4", "Iowan Old Style", Palatino, Georgia, serif;
      color: var(--ink);
      background:
        radial-gradient(ellipse at 20% 0%, #fffdf9 0%, var(--paper) 50%, #ebe6dd 100%);
      min-height: 100vh;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 1.75rem 1.2rem 3rem;
    }}
    h1 {{
      font-size: clamp(1.5rem, 2.8vw, 2.05rem);
      font-weight: 600;
      letter-spacing: -0.02em;
      margin: 0 0 0.35rem;
    }}
    .lede {{
      color: var(--muted);
      max-width: 42rem;
      line-height: 1.5;
      margin: 0 0 1.1rem;
    }}
    .stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.9rem 1.5rem;
      margin-bottom: 1rem;
      padding-bottom: 0.85rem;
      border-bottom: 1px solid var(--line);
    }}
    .stat strong {{
      display: block;
      font-size: 1.35rem;
      color: var(--accent);
      font-variant-numeric: tabular-nums;
    }}
    .stat span {{ color: var(--muted); font-size: 0.85rem; }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.7rem 1rem;
      align-items: end;
      margin-bottom: 1.15rem;
    }}
    label {{
      display: flex;
      flex-direction: column;
      gap: 0.22rem;
      font-size: 0.74rem;
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
      padding: 0.38rem 0.5rem;
      min-width: 11rem;
    }}
    input[type="search"] {{ min-width: 15rem; }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 17rem) minmax(0, 1fr);
      gap: 1.1rem;
      align-items: start;
    }}
    @media (max-width: 860px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .toc {{ max-height: 14rem; position: static; }}
    }}
    .toc {{
      border: 1px solid var(--line);
      background: var(--card);
      border-radius: 6px;
      max-height: calc(100vh - 10rem);
      overflow: auto;
      position: sticky;
      top: 0.85rem;
    }}
    .toc button {{
      display: block;
      width: 100%;
      text-align: left;
      font: inherit;
      font-size: 0.8rem;
      line-height: 1.3;
      color: var(--ink);
      background: transparent;
      border: 0;
      border-bottom: 1px solid var(--line);
      padding: 0.5rem 0.65rem;
      cursor: pointer;
    }}
    .toc button:hover {{ background: rgba(31, 90, 114, 0.06); }}
    .toc button.active {{
      background: rgba(31, 90, 114, 0.11);
      color: var(--accent);
      font-weight: 600;
    }}
    .toc .sub {{
      display: block;
      font-size: 0.68rem;
      color: var(--muted);
      font-weight: 400;
      margin-top: 0.12rem;
    }}
    .dot {{
      display: inline-block;
      width: 0.45rem;
      height: 0.45rem;
      border-radius: 50%;
      margin-right: 0.35rem;
      vertical-align: middle;
    }}
    .dot.strict {{ background: var(--catholic); }}
    .dot.ai {{ background: var(--ai); }}
    .dot.pending {{ background: var(--pending); }}
    .viewer {{
      border: 1px solid var(--line);
      background: var(--card);
      border-radius: 6px;
      padding: 1.2rem 1.3rem 1.4rem;
      min-height: 24rem;
    }}
    .group-head h2 {{
      margin: 0 0 0.25rem;
      font-size: clamp(1.2rem, 2vw, 1.45rem);
      letter-spacing: -0.015em;
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem 0.75rem;
      margin: 0 0 1rem;
      font-size: 0.82rem;
      color: var(--muted);
    }}
    .pill {{
      display: inline-block;
      padding: 0.1rem 0.42rem;
      border-radius: 3px;
      background: rgba(31, 90, 114, 0.1);
      color: var(--accent);
    }}
    .pill.strict {{ background: rgba(44, 107, 79, 0.12); color: var(--catholic); }}
    .pill.ai {{ background: rgba(107, 90, 46, 0.14); color: var(--ai); }}
    .pill.pending {{ background: rgba(122, 122, 122, 0.14); color: var(--pending); }}
    .qnav {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.6rem;
      margin-bottom: 0.85rem;
    }}
    .qnav button {{
      font: inherit;
      font-size: 0.88rem;
      color: var(--accent);
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 0.3rem 0.7rem;
      cursor: pointer;
    }}
    .qnav button:disabled {{ opacity: 0.35; cursor: default; }}
    .pos {{ color: var(--muted); font-size: 0.85rem; font-variant-numeric: tabular-nums; }}
    .question {{
      font-size: clamp(1.1rem, 2vw, 1.35rem);
      font-weight: 600;
      line-height: 1.35;
      margin: 0 0 1.1rem;
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
      padding-top: 0.65rem;
    }}
    .answer.catholic {{ border-top-color: var(--catholic); }}
    .answer.breakaway {{ border-top-color: var(--break); }}
    .answer h3 {{
      margin: 0 0 0.4rem;
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .answer.catholic h3 {{ color: var(--catholic); }}
    .answer.breakaway h3 {{ color: var(--break); }}
    .answer p {{ margin: 0; line-height: 1.55; font-size: 0.96rem; }}
    .cite {{
      margin-top: 1.2rem;
      padding-top: 0.8rem;
      border-top: 1px solid var(--line);
      font-size: 0.84rem;
      color: var(--muted);
      line-height: 1.45;
    }}
    .empty {{
      color: var(--muted);
      line-height: 1.55;
      padding: 0.5rem 0 0.2rem;
    }}
    .empty code {{ font-size: 0.85em; }}
    footer {{
      margin-top: 1.25rem;
      color: var(--muted);
      font-size: 0.8rem;
    }}
  </style>
</head>
<body>
  <main>
    <h1>{data["title"]}</h1>
    <p class="lede">{data["description"]}</p>
    <div class="stats">
      <div class="stat"><strong id="stat-groups">0</strong><span>breakaway groups</span></div>
      <div class="stat"><strong id="stat-q">0</strong><span>questions</span></div>
      <div class="stat"><strong id="stat-strict">0</strong><span>with strict rows</span></div>
      <div class="stat"><strong id="stat-ai">0</strong><span>AI-only</span></div>
      <div class="stat"><strong id="stat-pending">0</strong><span>pending</span></div>
    </div>
    <div class="controls">
      <label>Status
        <select id="filter-status">
          <option value="">All</option>
          <option value="strict">Has strict</option>
          <option value="ai">AI-only</option>
          <option value="pending">Pending</option>
        </select>
      </label>
      <label>Council
        <select id="filter-council">
          <option value="">All councils</option>
        </select>
      </label>
      <label>Search
        <input type="search" id="filter-search" placeholder="Group, council, question…" />
      </label>
    </div>
    <div class="layout">
      <nav class="toc" id="toc" aria-label="Breakaway groups"></nav>
      <section class="viewer" id="viewer" aria-live="polite"></section>
    </div>
    <footer>
      Source: <code>denomination_council_matches_50y.json</code> +
      <code>contrast.jsonl</code> / <code>contrast_ai.jsonl</code>.
      Regenerate: <code>python3 scripts/step1/export_match_contrast_viz.py</code>
    </footer>
  </main>
  <script>
    const DATA = {payload};

    const elToc = document.getElementById("toc");
    const elViewer = document.getElementById("viewer");
    const elStatus = document.getElementById("filter-status");
    const elCouncil = document.getElementById("filter-council");
    const elSearch = document.getElementById("filter-search");

    document.getElementById("stat-groups").textContent = DATA.n_groups;
    document.getElementById("stat-q").textContent = DATA.n_questions;
    document.getElementById("stat-strict").textContent = DATA.n_groups_strict;
    document.getElementById("stat-ai").textContent = DATA.n_groups_ai_only;
    document.getElementById("stat-pending").textContent = DATA.n_pending;

    const councils = [...new Set(DATA.groups.map(g => g.primary_council))].sort();
    for (const c of councils) {{
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      elCouncil.appendChild(opt);
    }}

    let filtered = DATA.groups.slice();
    let gIndex = 0;
    let qIndex = 0;

    function applyFilter() {{
      const st = elStatus.value;
      const council = elCouncil.value;
      const q = elSearch.value.trim().toLowerCase();
      filtered = DATA.groups.filter(g => {{
        if (st && g.status !== st) return false;
        if (council && g.primary_council !== council) return false;
        if (!q) return true;
        const blob = [
          g.group_name, g.primary_council, g.group_id,
          ...g.questions.map(r => r.question + " " + r.breakaway_answer)
        ].join(" ").toLowerCase();
        return blob.includes(q);
      }});
      gIndex = 0;
      qIndex = 0;
      renderToc();
      render();
    }}

    function renderToc() {{
      elToc.innerHTML = "";
      filtered.forEach((g, i) => {{
        const b = document.createElement("button");
        b.type = "button";
        b.innerHTML =
          `<span class="dot ${{g.status}}"></span>${{escapeHtml(g.group_name)}}` +
          `<span class="sub">${{g.start_year}} · ${{escapeHtml(g.primary_council)}} · ${{g.n_questions}} q</span>`;
        if (i === gIndex) b.classList.add("active");
        b.addEventListener("click", () => {{ gIndex = i; qIndex = 0; renderToc(); render(); }});
        elToc.appendChild(b);
      }});
    }}

    function escapeHtml(s) {{
      return String(s)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }}

    function render() {{
      if (!filtered.length) {{
        elViewer.innerHTML = `<p class="empty">No groups match these filters.</p>`;
        return;
      }}
      const g = filtered[Math.max(0, Math.min(gIndex, filtered.length - 1))];
      const qs = g.questions || [];
      const statusPill = `<span class="pill ${{g.status}}">${{g.status}}</span>`;

      let body = "";
      if (!qs.length) {{
        body = `
          <p class="empty">
            No disagreement question yet for this breakaway.
            Primary council pairing is <strong>${{escapeHtml(g.primary_council)}}</strong>
            (${{escapeHtml(g.primary_reason || "paired")}}).
            Rows appear here after a strict or AI contrast draft is linked to this group.
          </p>`;
      }} else {{
        qIndex = Math.max(0, Math.min(qIndex, qs.length - 1));
        const r = qs[qIndex];
        body = `
          <div class="qnav">
            <button type="button" id="prev-q" ${{qIndex === 0 ? "disabled" : ""}}>← Prev Q</button>
            <span class="pos">Question ${{qIndex + 1}} / ${{qs.length}} · ${{r.tier}}</span>
            <button type="button" id="next-q" ${{qIndex >= qs.length - 1 ? "disabled" : ""}}>Next Q →</button>
          </div>
          <p class="question">${{escapeHtml(r.question)}}</p>
          <div class="answers">
            <div class="answer catholic">
              <h3>Catholic</h3>
              <p>${{escapeHtml(r.catholic_answer)}}</p>
            </div>
            <div class="answer breakaway">
              <h3>${{escapeHtml(g.group_name)}}</h3>
              <p>${{escapeHtml(r.breakaway_answer)}}</p>
            </div>
          </div>
          <div class="cite">
            <div><strong>Council locus:</strong> ${{escapeHtml(r.council || g.primary_council)}}</div>
            <div><strong>Citation:</strong> ${{escapeHtml(r.canonical_citation || "—")}}</div>
            <div><strong>Entry:</strong> <code>${{escapeHtml(r.source_entry_id || r.id)}}</code>
              · confidence ${{escapeHtml(r.confidence || "")}}</div>
          </div>`;
      }}

      elViewer.innerHTML = `
        <div class="group-head">
          <h2>${{escapeHtml(g.group_name)}}</h2>
          <div class="meta-row">
            ${{statusPill}}
            <span class="pill">${{g.start_year}}</span>
            <span>${{escapeHtml(g.primary_council)}}</span>
            <span>${{escapeHtml(g.primary_reason)}}</span>
            ${{g.primary_distance_years != null ? `<span>Δ ${{g.primary_distance_years}}y</span>` : ""}}
            ${{g.differs_from_doctrinal && g.doctrinal_council ? `<span>doctrinal alt: ${{escapeHtml(g.doctrinal_council)}}</span>` : ""}}
            <span>${{g.n_questions}} question${{g.n_questions === 1 ? "" : "s"}}</span>
          </div>
        </div>
        ${{body}}`;

      const prev = document.getElementById("prev-q");
      const next = document.getElementById("next-q");
      if (prev) prev.addEventListener("click", () => {{ qIndex -= 1; render(); }});
      if (next) next.addEventListener("click", () => {{ qIndex += 1; render(); }});

      const active = elToc.querySelector("button.active");
      if (active) active.scrollIntoView({{ block: "nearest" }});
    }}

    elStatus.addEventListener("change", applyFilter);
    elCouncil.addEventListener("change", applyFilter);
    elSearch.addEventListener("input", applyFilter);
    document.addEventListener("keydown", (e) => {{
      if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "SELECT")) return;
      const g = filtered[gIndex];
      if (!g) return;
      if (e.key === "ArrowUp" && gIndex > 0) {{ gIndex -= 1; qIndex = 0; renderToc(); render(); }}
      if (e.key === "ArrowDown" && gIndex < filtered.length - 1) {{ gIndex += 1; qIndex = 0; renderToc(); render(); }}
      if (e.key === "ArrowLeft" && qIndex > 0) {{ qIndex -= 1; render(); }}
      if (e.key === "ArrowRight" && g.questions && qIndex < g.questions.length - 1) {{ qIndex += 1; render(); }}
    }});

    applyFilter();
  </script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--mode",
        choices=("doctrinal", "temporal", "both"),
        default="both",
    )
    ap.add_argument("--out-html", type=Path, default=None)
    ap.add_argument("--out-json", type=Path, default=None)
    args = ap.parse_args()

    modes = ["doctrinal", "temporal"] if args.mode == "both" else [args.mode]
    results = []
    for mode in modes:
        paths = MODE_PATHS[mode]
        if not paths["matches"].exists():
            print(f"skip {mode}: missing {paths['matches']}")
            continue
        data = build_payload(mode)
        out_json = args.out_json or paths["json"]
        out_html = args.out_html or paths["html"]
        # When both modes, ignore single out overrides after first
        if args.mode == "both":
            out_json = paths["json"]
            out_html = paths["html"]
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        out_html.write_text(build_html(data), encoding="utf-8")
        results.append(
            {
                "mode": mode,
                "wrote_html": str(out_html),
                "wrote_json": str(out_json),
                "n_groups": data["n_groups"],
                "n_questions": data["n_questions"],
                "n_with_questions": data["n_with_questions"],
                "n_pending": data["n_pending"],
                "by_primary_council": data.get("by_primary_council"),
            }
        )

    # README pointers
    readme = OUT_DIR / "README.md"
    if readme.exists():
        body = readme.read_text(encoding="utf-8")
        additions = []
        if "| `match_contrast.html`" not in body:
            additions.append(
                "| `match_contrast.html` | Match-list Q&A viewer (**doctrinal**) |"
            )
        if "| `match_contrast_temporal.html`" not in body:
            additions.append(
                "| `match_contrast_temporal.html` | Match-list Q&A viewer (**temporal / nearest**) |"
            )
        if "| `denomination_council_matches_temporal.md`" not in body:
            additions.append(
                "| `denomination_council_matches_temporal.md` | Temporal nearest-council match list |"
            )
        if additions:
            anchor = (
                "| `denomination_council_matches_50y.md` | **Authoritative** breakaway↔council list (viz group basis) |"
            )
            if anchor in body:
                body = body.replace(anchor, anchor + "\n" + "\n".join(additions))
                readme.write_text(body, encoding="utf-8")

    print(json.dumps(results if len(results) > 1 else (results[0] if results else {}), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
