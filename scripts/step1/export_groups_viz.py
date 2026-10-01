#!/usr/bin/env python3
"""Export an interactive HTML lineage visualization of groups_catalog.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "outputs" / "step1" / "breakaways" / "groups_catalog.json"
DEFAULT_OUT = ROOT / "outputs" / "step1" / "breakaways" / "groups_lineage.html"


def build_html(catalog: dict) -> str:
    # Embed compact payload for the browser
    payload = {
        "root": catalog.get("root"),
        "stats": catalog.get("stats"),
        "groups": [
            {
                "id": g["id"],
                "name": g["name"],
                "approx_rupture": g.get("approx_rupture"),
                "rupture_year": g.get("rupture_year"),
                "broke_from": g.get("broke_from"),
                "separation_degree": g.get("separation_degree"),
                "confidence": g.get("confidence"),
                "status": g.get("status"),
                "summary": g.get("summary"),
                "in_step1_breakaways": g.get("in_step1_breakaways"),
                "lineage": g.get("lineage") or [],
                "region": g.get("region"),
            }
            for g in catalog.get("groups", [])
        ],
    }
    data_json = json.dumps(payload, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Breakaway lineage — groups catalog</title>
  <style>
    :root {{
      --ink: #1c2430;
      --muted: #5c6b7a;
      --line: #d5dde5;
      --fill: #e8eef4;
      --accent: #2a5f7a;
      --accent2: #8a4b2f;
      --paper: #f7f5f1;
      --step1: #2f6b4f;
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
      max-width: 1280px;
      margin: 0 auto;
      padding: 2rem 1.25rem 3.5rem;
    }}
    h1 {{
      font-size: clamp(1.7rem, 3vw, 2.3rem);
      font-weight: 600;
      letter-spacing: -0.02em;
      margin: 0 0 0.35rem;
    }}
    .lede {{
      color: var(--muted);
      max-width: 42rem;
      line-height: 1.5;
      margin: 0 0 1.5rem;
    }}
    .stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem 1.75rem;
      margin-bottom: 1.25rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid var(--line);
    }}
    .stat strong {{
      display: block;
      font-size: 1.55rem;
      color: var(--accent);
      font-variant-numeric: tabular-nums;
    }}
    .stat span {{ color: var(--muted); font-size: 0.88rem; }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem 1.25rem;
      align-items: end;
      margin-bottom: 1.25rem;
    }}
    label {{
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      font-size: 0.8rem;
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
      min-width: 10rem;
    }}
    .check {{
      flex-direction: row;
      align-items: center;
      gap: 0.4rem;
      text-transform: none;
      letter-spacing: 0;
      font-size: 0.95rem;
      color: var(--ink);
      padding-bottom: 0.35rem;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(16rem, 0.9fr);
      gap: 1.25rem;
    }}
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
    }}
    .panel {{
      background: rgba(255,255,255,0.55);
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
    }}
    .panel h2 {{
      margin: 0;
      padding: 0.7rem 0.9rem;
      font-size: 0.78rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,0.7);
    }}
    #graph {{
      width: 100%;
      height: min(72vh, 820px);
      display: block;
      background: #fffef9;
    }}
    .detail {{
      padding: 0.9rem 1rem 1.2rem;
      font-size: 0.95rem;
      line-height: 1.45;
    }}
    .detail .name {{
      font-size: 1.2rem;
      font-weight: 600;
      margin: 0 0 0.35rem;
    }}
    .detail .meta {{
      color: var(--muted);
      font-size: 0.88rem;
      margin-bottom: 0.75rem;
    }}
    .pill {{
      display: inline-block;
      font-size: 0.75rem;
      padding: 0.12rem 0.45rem;
      border-radius: 3px;
      border: 1px solid var(--line);
      margin-right: 0.3rem;
      color: var(--muted);
    }}
    .pill.step1 {{ border-color: var(--step1); color: var(--step1); }}
    .pill.d1 {{ border-color: var(--accent); color: var(--accent); }}
    .pill.dhigh {{ border-color: var(--accent2); color: var(--accent2); }}
    .lineage {{
      font-family: ui-monospace, Menlo, Consolas, monospace;
      font-size: 0.78rem;
      color: var(--muted);
      word-break: break-word;
    }}
    .bars {{
      display: flex;
      gap: 0.35rem;
      align-items: flex-end;
      height: 3.2rem;
      margin: 0.75rem 0 0.25rem;
    }}
    .bars .b {{
      flex: 1;
      background: var(--accent);
      border-radius: 2px 2px 0 0;
      min-width: 0;
      opacity: 0.85;
    }}
    .bars .b.hot {{ background: var(--accent2); }}
    .bar-labels {{
      display: flex;
      gap: 0.35rem;
      font-size: 0.72rem;
      color: var(--muted);
      font-variant-numeric: tabular-nums;
    }}
    .bar-labels span {{ flex: 1; text-align: center; }}
    footer {{
      margin-top: 1.5rem;
      color: var(--muted);
      font-size: 0.85rem;
    }}
    code {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 0.86em; }}
  </style>
</head>
<body>
  <main>
    <h1>Breakaway lineage</h1>
    <p class="lede">
      Separation distance from the Catholic Church across the groups catalog.
      Columns are degree (0 = Catholic root). Edges follow <code>broke_from</code>.
    </p>
    <div class="stats" id="stats"></div>
    <div class="controls">
      <label>Max degree
        <select id="maxDegree"></select>
      </label>
      <label>Status
        <select id="statusFilter">
          <option value="all">All</option>
          <option value="extant" selected>Extant</option>
          <option value="historical">Historical</option>
          <option value="real">Hide synthetic / sentinels</option>
        </select>
      </label>
      <label>Search
        <input id="search" type="search" placeholder="Name or id" />
      </label>
      <label class="check"><input type="checkbox" id="step1Only" /> Step 1 tagged only</label>
    </div>
    <div class="layout">
      <div class="panel">
        <h2>Lineage graph</h2>
        <svg id="graph" role="img" aria-label="Breakaway lineage graph by separation degree"></svg>
      </div>
      <div class="panel">
        <h2>Selected group</h2>
        <div class="detail" id="detail">
          <p class="meta">Click a node to inspect lineage, region, and notes.</p>
        </div>
      </div>
    </div>
    <footer>
      Source: <code>outputs/step1/breakaways/groups_catalog.json</code>
      · regenerate with <code>python scripts/step1/export_groups_viz.py</code>
    </footer>
  </main>
  <script>
    const DATA = {data_json};

    const degColors = {{
      0: "#5c6b7a",
      1: "#2a5f7a",
      2: "#3d7a96",
      3: "#8a4b2f",
      4: "#a65d3a",
      5: "#b8734d",
      6: "#c98961",
    }};

    const byId = Object.fromEntries(DATA.groups.map(g => [g.id, g]));
    byId["catholic-church"] = {{
      id: "catholic-church",
      name: DATA.root.name,
      separation_degree: 0,
      status: "in_communion",
      confidence: "established",
      summary: "Root node for lineage distance.",
      broke_from: null,
      lineage: ["catholic-church"],
      in_step1_breakaways: false,
      approx_rupture: "—",
      region: "Global",
    }};

    function renderStats() {{
      const s = DATA.stats;
      const deg = s.by_degree || {{}};
      const maxDeg = Math.max(...Object.keys(deg).map(Number));
      const maxCount = Math.max(...Object.values(deg));
      const bars = [];
      const labels = [];
      for (let d = 0; d <= maxDeg; d++) {{
        const n = deg[String(d)] || deg[d] || 0;
        const h = Math.max(4, Math.round(48 * n / maxCount));
        bars.push(`<div class="b${{d >= 3 ? " hot" : ""}}" style="height:${{h}}px" title="degree ${{d}}: ${{n}}"></div>`);
        labels.push(`<span>d${{d}}<br>${{n}}</span>`);
      }}
      document.getElementById("stats").innerHTML = `
        <div class="stat"><strong>${{s.group_count}}</strong><span>groups in catalog</span></div>
        <div class="stat"><strong>${{s.in_step1_true}}</strong><span>tagged in Step 1</span></div>
        <div class="stat"><strong>${{s.extant}}</strong><span>extant</span></div>
        <div class="stat" style="min-width:14rem">
          <span>Groups by separation degree</span>
          <div class="bars">${{bars.join("")}}</div>
          <div class="bar-labels">${{labels.join("")}}</div>
        </div>`;
      const sel = document.getElementById("maxDegree");
      sel.innerHTML = "";
      for (let d = 1; d <= maxDeg; d++) {{
        const opt = document.createElement("option");
        opt.value = d;
        opt.textContent = String(d);
        if (d === Math.min(4, maxDeg)) opt.selected = true;
        sel.appendChild(opt);
      }}
    }}

    function visibleGroups() {{
      const maxD = Number(document.getElementById("maxDegree").value);
      const status = document.getElementById("statusFilter").value;
      const step1 = document.getElementById("step1Only").checked;
      const q = document.getElementById("search").value.trim().toLowerCase();
      return DATA.groups.filter(g => {{
        if (g.separation_degree > maxD) return false;
        if (step1 && !g.in_step1_breakaways) return false;
        if (status === "extant" && g.status !== "extant") return false;
        if (status === "historical" && g.status !== "historical") return false;
        if (status === "real" && (g.status === "synthetic" || g.status === "in_communion")) return false;
        if (q) {{
          const blob = (g.name + " " + g.id + " " + (g.summary || "")).toLowerCase();
          if (!blob.includes(q)) return false;
        }}
        return true;
      }});
    }}

    function showDetail(id) {{
      const g = byId[id];
      if (!g) return;
      const deg = g.separation_degree;
      const pills = [
        `<span class="pill ${{deg <= 1 ? "d1" : "dhigh"}}">degree ${{deg}}</span>`,
        `<span class="pill">${{g.status || "—"}}</span>`,
        `<span class="pill">${{g.confidence || "—"}}</span>`,
        g.in_step1_breakaways ? `<span class="pill step1">Step 1</span>` : "",
      ].join("");
      const parent = g.broke_from ? (byId[g.broke_from]?.name || g.broke_from) : "—";
      document.getElementById("detail").innerHTML = `
        <p class="name">${{escapeHtml(g.name)}}</p>
        <div>${{pills}}</div>
        <p class="meta">${{escapeHtml(g.approx_rupture || "—")}} · ${{escapeHtml(g.region || "—")}}</p>
        <p><strong>Broke from:</strong> ${{escapeHtml(parent)}}</p>
        <p>${{escapeHtml(g.summary || "")}}</p>
        <p class="lineage">${{escapeHtml((g.lineage || []).join(" → "))}}</p>`;
    }}

    function escapeHtml(s) {{
      return String(s).replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[c]));
    }}

    function draw() {{
      const svg = document.getElementById("graph");
      const groups = visibleGroups();
      const width = svg.clientWidth || 800;
      const height = svg.clientHeight || 600;
      svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);
      svg.innerHTML = "";

      const maxD = Number(document.getElementById("maxDegree").value);
      const nodes = [byId["catholic-church"], ...groups];
      // Ensure parents of visible nodes are present for edges even if filtered out
      const needed = new Set(nodes.map(n => n.id));
      for (const g of groups) {{
        let p = g.broke_from;
        while (p && !needed.has(p)) {{
          if (byId[p]) {{
            nodes.push(byId[p]);
            needed.add(p);
            p = byId[p].broke_from;
          }} else break;
        }}
      }}
      const uniq = [];
      const seen = new Set();
      for (const n of nodes) {{
        if (seen.has(n.id)) continue;
        seen.add(n.id);
        if ((n.separation_degree ?? 0) > maxD && n.id !== "catholic-church") continue;
        uniq.push(n);
      }}

      const byDeg = {{}};
      for (const n of uniq) {{
        const d = n.separation_degree ?? 0;
        (byDeg[d] ||= []).push(n);
      }}
      const degrees = Object.keys(byDeg).map(Number).sort((a,b)=>a-b);
      const pos = {{}};
      const padX = 40, padY = 28;
      const usableW = width - padX * 2;
      const usableH = height - padY * 2;
      const colW = degrees.length > 1 ? usableW / (degrees.length - 1 || 1) : 0;

      for (let i = 0; i < degrees.length; i++) {{
        const d = degrees[i];
        const col = byDeg[d];
        col.sort((a,b) => (a.rupture_year||9999) - (b.rupture_year||9999) || a.name.localeCompare(b.name));
        const x = padX + (degrees.length === 1 ? usableW / 2 : i * (usableW / (degrees.length - 1)));
        for (let j = 0; j < col.length; j++) {{
          const y = padY + (col.length === 1 ? usableH / 2 : j * (usableH / Math.max(col.length - 1, 1)));
          pos[col[j].id] = {{ x, y, n: col[j] }};
        }}
      }}

      // edges
      const gEdges = document.createElementNS("http://www.w3.org/2000/svg", "g");
      for (const n of uniq) {{
        if (!n.broke_from || !pos[n.id] || !pos[n.broke_from]) continue;
        const a = pos[n.broke_from], b = pos[n.id];
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        const mx = (a.x + b.x) / 2;
        path.setAttribute("d", `M${{a.x}},${{a.y}} C${{mx}},${{a.y}} ${{mx}},${{b.y}} ${{b.x}},${{b.y}}`);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", "#c5ced8");
        path.setAttribute("stroke-width", "1.2");
        gEdges.appendChild(path);
      }}
      svg.appendChild(gEdges);

      // column labels
      const gLab = document.createElementNS("http://www.w3.org/2000/svg", "g");
      for (let i = 0; i < degrees.length; i++) {{
        const d = degrees[i];
        const x = padX + (degrees.length === 1 ? usableW / 2 : i * (usableW / (degrees.length - 1)));
        const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
        t.setAttribute("x", x);
        t.setAttribute("y", 14);
        t.setAttribute("text-anchor", "middle");
        t.setAttribute("fill", "#5c6b7a");
        t.setAttribute("font-size", "11");
        t.textContent = d === 0 ? "Catholic" : `degree ${{d}}`;
        gLab.appendChild(t);
      }}
      svg.appendChild(gLab);

      const gNodes = document.createElementNS("http://www.w3.org/2000/svg", "g");
      for (const n of uniq) {{
        const p = pos[n.id];
        if (!p) continue;
        const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        c.setAttribute("cx", p.x);
        c.setAttribute("cy", p.y);
        c.setAttribute("r", n.id === "catholic-church" ? 7 : 5);
        c.setAttribute("fill", degColors[n.separation_degree] || "#2a5f7a");
        c.setAttribute("stroke", n.in_step1_breakaways ? "#2f6b4f" : "#fff");
        c.setAttribute("stroke-width", n.in_step1_breakaways ? 2.5 : 1);
        c.style.cursor = "pointer";
        c.addEventListener("click", () => showDetail(n.id));
        gNodes.appendChild(c);

        const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
        t.setAttribute("x", p.x + 8);
        t.setAttribute("y", p.y + 3);
        t.setAttribute("fill", "#1c2430");
        t.setAttribute("font-size", "10");
        t.textContent = n.name.length > 28 ? n.name.slice(0, 26) + "…" : n.name;
        t.style.cursor = "pointer";
        t.addEventListener("click", () => showDetail(n.id));
        gNodes.appendChild(t);
      }}
      svg.appendChild(gNodes);
    }}

    renderStats();
    ["maxDegree","statusFilter","step1Only","search"].forEach(id => {{
      document.getElementById(id).addEventListener("input", draw);
      document.getElementById(id).addEventListener("change", draw);
    }});
    window.addEventListener("resize", draw);
    draw();
    showDetail("catholic-church");
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_html(catalog), encoding="utf-8")
    print(f"wrote lineage viz ({catalog['stats']['group_count']} groups) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
