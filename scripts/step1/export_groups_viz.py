#!/usr/bin/env python3
"""Export an interactive HTML lineage visualization of groups_catalog.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "outputs" / "step1" / "breakaways" / "groups_catalog.json"
DEFAULT_OUT = ROOT / "outputs" / "step1" / "breakaways" / "groups_lineage.html"
PASSAGES_BREAKAWAY = ROOT / "outputs" / "step1" / "breakaways" / "passages.jsonl"
COUNCIL_DOCS = ROOT / "data" / "councils" / "documents"


def _collect_locus_record_ids(catalog: dict) -> set[str]:
    ids: set[str] = set()
    for g in catalog.get("groups", []):
        d = g.get("disagreement") or {}
        if d.get("kind") != "council_locus":
            continue
        rid = d.get("record_id")
        if rid:
            ids.add(rid)
        for rel in d.get("related_loci") or []:
            rrid = rel.get("record_id")
            if rrid:
                ids.add(rrid)
    return ids


def load_locus_texts(record_ids: set[str]) -> dict[str, dict]:
    """Resolve full passage text for disagreement loci (breakaway passages, then council docs)."""
    out: dict[str, dict] = {}
    if not record_ids:
        return out

    if PASSAGES_BREAKAWAY.exists():
        for line in PASSAGES_BREAKAWAY.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            p = json.loads(line)
            rid = p.get("record_id")
            if rid in record_ids and p.get("text"):
                out[rid] = {
                    "record_id": rid,
                    "canonical_citation": p.get("canonical_citation"),
                    "council": p.get("council"),
                    "text": p["text"],
                    "text_status": p.get("text_status"),
                    "source_url": p.get("source_url"),
                }

    still = record_ids - set(out)
    if still and COUNCIL_DOCS.exists():
        for path in COUNCIL_DOCS.rglob("*.jsonl"):
            if not still:
                break
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                if "record_id" not in line:
                    continue
                doc = json.loads(line)
                rid = doc.get("record_id")
                if rid in still and doc.get("text"):
                    out[rid] = {
                        "record_id": rid,
                        "canonical_citation": doc.get("canonical_citation"),
                        "council": doc.get("council"),
                        "text": doc["text"],
                        "text_status": doc.get("text_status"),
                        "source_url": doc.get("source_url"),
                    }
                    still.discard(rid)
                    if not still:
                        break
    return out


def build_html(catalog: dict) -> str:
    locus_ids = _collect_locus_record_ids(catalog)
    loci_texts = load_locus_texts(locus_ids)

    payload = {
        "root": catalog.get("root"),
        "stats": catalog.get("stats"),
        "loci_texts": loci_texts,
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
                "disagreement": g.get("disagreement"),
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
      --accent: #2a5f7a;
      --accent2: #8a4b2f;
      --paper: #f7f5f1;
      --step1: #2f6b4f;
      --edge: #9aa8b5;
      --edge-hot: #2a5f7a;
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
      max-width: 1360px;
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
      max-width: 46rem;
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
      grid-template-columns: minmax(0, 1.7fr) minmax(17rem, 0.9fr);
      gap: 1.25rem;
      align-items: start;
    }}
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
    }}
    .panel {{
      background: rgba(255,255,255,0.55);
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
      min-width: 0;
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
    .graph-wrap {{
      position: relative;
      background: #fffef9;
      overflow: hidden;
      height: min(78vh, 920px);
      touch-action: none;
    }}
    .graph-toolbar {{
      position: absolute;
      top: 0.65rem;
      right: 0.65rem;
      z-index: 2;
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
      justify-content: flex-end;
      max-width: calc(100% - 1.2rem);
    }}
    .graph-toolbar button {{
      font: inherit;
      font-size: 0.8rem;
      color: var(--ink);
      background: rgba(255,255,255,0.92);
      border: 1px solid var(--line);
      border-radius: 3px;
      padding: 0.28rem 0.5rem;
      cursor: pointer;
      box-shadow: 0 1px 2px rgba(28,36,48,0.06);
    }}
    .graph-toolbar button:hover {{ border-color: var(--accent); color: var(--accent); }}
    .graph-toolbar .zoom-readout {{
      font-size: 0.78rem;
      color: var(--muted);
      background: rgba(255,255,255,0.92);
      border: 1px solid var(--line);
      border-radius: 3px;
      padding: 0.28rem 0.5rem;
      min-width: 3.2rem;
      text-align: center;
      font-variant-numeric: tabular-nums;
    }}
    .graph-hint {{
      position: absolute;
      left: 0.65rem;
      bottom: 0.55rem;
      z-index: 2;
      font-size: 0.75rem;
      color: var(--muted);
      background: rgba(255,254,249,0.9);
      padding: 0.2rem 0.4rem;
      border-radius: 3px;
      pointer-events: none;
    }}
    #graph {{
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
    }}
    #graph.panning {{ cursor: grabbing; }}
    #graph .edge {{
      fill: none;
      stroke: var(--edge);
      stroke-width: 1.35;
    }}
    #graph .edge.hot {{
      stroke: var(--edge-hot);
      stroke-width: 2.1;
    }}
    #graph .edge.dim {{
      stroke: #d5dde5;
      stroke-width: 1;
      opacity: 0.55;
    }}
    #graph .node {{ cursor: pointer; }}
    #graph .node circle.node-dot {{
      stroke: #fff;
      stroke-width: 1.5;
    }}
    #graph .node.step1 circle.node-dot {{
      stroke: var(--step1);
      stroke-width: 2.4;
    }}
    #graph .node.selected circle.node-dot {{
      stroke: var(--accent2);
      stroke-width: 3;
    }}
    #graph .node.dim {{ opacity: 0.35; }}
    #graph .node text.label {{
      font-size: 11px;
      fill: var(--ink);
      paint-order: stroke;
      stroke: #fffef9;
      stroke-width: 3px;
      stroke-linejoin: round;
    }}
    #graph .twist {{
      cursor: pointer;
    }}
    #graph .twist rect {{
      fill: #fff;
      stroke: var(--edge);
      stroke-width: 1;
    }}
    #graph .twist:hover rect {{ stroke: var(--accent); }}
    #graph .twist text {{
      font-size: 9px;
      fill: var(--muted);
      text-anchor: middle;
      dominant-baseline: central;
      pointer-events: none;
    }}
    #graph .collapsed-count {{
      font-size: 9px;
      fill: var(--accent2);
      paint-order: stroke;
      stroke: #fffef9;
      stroke-width: 2px;
    }}
    #graph .col-label {{
      fill: var(--muted);
      font-size: 11px;
    }}
    .detail {{
      padding: 0.9rem 1rem 1.2rem;
      font-size: 0.95rem;
      line-height: 1.45;
      max-height: min(78vh, 920px);
      overflow: auto;
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
    .path {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.2rem 0.15rem;
      margin: 0 0 0.85rem;
      padding: 0.55rem 0.65rem;
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--line);
      border-radius: 4px;
      font-size: 0.86rem;
      line-height: 1.35;
    }}
    .path button {{
      font: inherit;
      font-size: inherit;
      color: var(--accent);
      background: none;
      border: none;
      padding: 0;
      cursor: pointer;
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .path button.current {{
      color: var(--ink);
      font-weight: 600;
      text-decoration: none;
      cursor: default;
    }}
    .path .sep {{ color: #c5ced8; padding: 0 0.15rem; }}
    .spawned {{ margin: 0.85rem 0 0.25rem; }}
    .spawned h3 {{
      margin: 0 0 0.35rem;
      font-size: 0.78rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
    }}
    .spawned ul {{ margin: 0; padding: 0; list-style: none; }}
    .spawned li {{ margin: 0.15rem 0; }}
    .spawned button {{
      font: inherit;
      font-size: 0.9rem;
      color: var(--accent);
      background: none;
      border: none;
      padding: 0;
      cursor: pointer;
      text-align: left;
    }}
    .spawned button:hover {{ text-decoration: underline; }}
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
    .pill.locus {{ border-color: var(--accent); color: var(--accent); }}
    .locus-block {{
      margin: 0.75rem 0 0.35rem;
      padding: 0.65rem 0.7rem;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: rgba(255,255,255,0.75);
    }}
    .locus-block > p {{ margin: 0 0 0.45rem; }}
    .locus-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin: 0.35rem 0 0.15rem;
    }}
    button.locus-toggle {{
      font: inherit;
      font-size: 0.82rem;
      color: var(--accent);
      background: #fff;
      border: 1px solid var(--accent);
      border-radius: 3px;
      padding: 0.28rem 0.55rem;
      cursor: pointer;
    }}
    button.locus-toggle:hover {{ background: #eef5f8; }}
    button.locus-toggle[aria-expanded="true"] {{
      background: var(--accent);
      color: #fff;
    }}
    .locus-text {{
      display: none;
      margin-top: 0.55rem;
      padding-top: 0.55rem;
      border-top: 1px solid var(--line);
      max-height: min(42vh, 28rem);
      overflow: auto;
      font-size: 0.88rem;
      line-height: 1.5;
      white-space: pre-wrap;
      color: var(--ink);
    }}
    .locus-text.open {{ display: block; }}
    .locus-text .cite {{
      color: var(--muted);
      font-size: 0.78rem;
      margin-bottom: 0.45rem;
    }}
    .locus-text a {{ color: var(--accent); }}
    .related-loci {{
      margin-top: 0.55rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}
    .related-loci .locus-block {{ margin: 0; padding: 0.5rem 0.6rem; }}
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
      Graph of who broke from whom. Branches are laid out as a tidy tree
      with orthogonal edges. Collapse a node’s branch with the ▸ control;
      scroll to zoom, drag to pan.
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
        <div class="graph-wrap" id="graphWrap">
          <div class="graph-toolbar">
            <button type="button" id="zoomOut" title="Zoom out">−</button>
            <span class="zoom-readout" id="zoomReadout">100%</span>
            <button type="button" id="zoomIn" title="Zoom in">+</button>
            <button type="button" id="zoomFit" title="Fit whole graph">Fit</button>
            <button type="button" id="zoomSelection" title="Zoom to selected branch">Focus</button>
            <button type="button" id="expandAll" title="Expand all branches">Expand all</button>
            <button type="button" id="collapseDeep" title="Collapse deeper branches">Collapse deep</button>
          </div>
          <svg id="graph" role="img" aria-label="Breakaway lineage graph"></svg>
          <div class="graph-hint">▸ collapse branch · scroll zoom · drag pan</div>
        </div>
      </div>
      <div class="panel">
        <h2>Selected group</h2>
        <div class="detail" id="detail">
          <p class="meta">Click a node to inspect its parent chain and forks.</p>
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
      name: (DATA.root && DATA.root.name) || "Catholic Church",
      separation_degree: 0,
      status: "in_communion",
      confidence: "established",
      summary: "Root node for lineage distance.",
      broke_from: null,
      lineage: ["catholic-church"],
      in_step1_breakaways: false,
      approx_rupture: "—",
      region: "Global",
      disagreement: null,
    }};

    const childrenOf = {{}};
    for (const g of DATA.groups) {{
      const p = g.broke_from || "catholic-church";
      (childrenOf[p] ||= []).push(g.id);
    }}
    for (const ids of Object.values(childrenOf)) {{
      ids.sort((a, b) => {{
        const ga = byId[a], gb = byId[b];
        const ya = ga.rupture_year ?? 9999, yb = gb.rupture_year ?? 9999;
        if (ya !== yb) return ya - yb;
        return ga.name.localeCompare(gb.name);
      }});
    }}

    let selectedId = "catholic-church";
    const collapsed = new Set();

    // Camera: content is drawn in world coords inside #scene; pan/zoom via transform.
    const camera = {{ x: 0, y: 0, k: 1 }};
    let contentBounds = {{ width: 800, height: 600 }};
    let lastLayout = null;

    function escapeHtml(s) {{
      return String(s ?? "").replace(/[&<>"']/g, c => ({{
        "&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"
      }})[c]);
    }}

    function initCollapseDefaults() {{
      collapsed.clear();
      for (const g of DATA.groups) {{
        const kids = childrenOf[g.id] || [];
        if (kids.length && (g.separation_degree ?? 0) >= 2) collapsed.add(g.id);
      }}
    }}

    function descendantCount(id) {{
      let n = 0;
      for (const cid of childrenOf[id] || []) {{
        if (!includeInGraph(cid)) continue;
        n += 1 + descendantCount(cid);
      }}
      return n;
    }}

    function applyCamera() {{
      const scene = document.getElementById("scene");
      if (scene) {{
        scene.setAttribute(
          "transform",
          `translate(${{camera.x}},${{camera.y}}) scale(${{camera.k}})`
        );
      }}
      const readout = document.getElementById("zoomReadout");
      if (readout) readout.textContent = `${{Math.round(camera.k * 100)}}%`;
    }}

    function fitCamera(padding = 28) {{
      const wrap = document.getElementById("graphWrap");
      const w = wrap.clientWidth || 800;
      const h = wrap.clientHeight || 600;
      const bw = Math.max(contentBounds.width, 1);
      const bh = Math.max(contentBounds.height, 1);
      const k = Math.min((w - padding * 2) / bw, (h - padding * 2) / bh, 1.35);
      camera.k = Math.max(0.15, k);
      camera.x = (w - bw * camera.k) / 2;
      camera.y = (h - bh * camera.k) / 2;
      applyCamera();
    }}

    function focusCameraOnIds(ids, padding = 48) {{
      if (!lastLayout) return;
      const pts = ids.map(id => lastLayout.pos[id]).filter(Boolean);
      if (!pts.length) return fitCamera();
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (const p of pts) {{
        minX = Math.min(minX, p.x - 20);
        maxX = Math.max(maxX, p.x + 150);
        minY = Math.min(minY, p.y - 16);
        maxY = Math.max(maxY, p.y + 16);
      }}
      const wrap = document.getElementById("graphWrap");
      const w = wrap.clientWidth || 800;
      const h = wrap.clientHeight || 600;
      const bw = Math.max(maxX - minX, 80);
      const bh = Math.max(maxY - minY, 80);
      const k = Math.min((w - padding * 2) / bw, (h - padding * 2) / bh, 2.4);
      camera.k = Math.max(0.2, k);
      camera.x = -minX * camera.k + (w - bw * camera.k) / 2;
      camera.y = -minY * camera.k + (h - bh * camera.k) / 2;
      applyCamera();
    }}

    function zoomAt(clientX, clientY, factor) {{
      const wrap = document.getElementById("graphWrap");
      const rect = wrap.getBoundingClientRect();
      const mx = clientX - rect.left;
      const my = clientY - rect.top;
      const worldX = (mx - camera.x) / camera.k;
      const worldY = (my - camera.y) / camera.k;
      const next = Math.min(3.5, Math.max(0.12, camera.k * factor));
      camera.k = next;
      camera.x = mx - worldX * camera.k;
      camera.y = my - worldY * camera.k;
      applyCamera();
    }}

    function wireViewport() {{
      const svg = document.getElementById("graph");
      const wrap = document.getElementById("graphWrap");
      let dragging = false;
      let lastX = 0, lastY = 0;

      wrap.addEventListener("wheel", (e) => {{
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
        zoomAt(e.clientX, e.clientY, factor);
      }}, {{ passive: false }});

      svg.addEventListener("pointerdown", (e) => {{
        if (e.button !== 0) return;
        // Don't start pan when clicking controls/nodes (nodes stopPropagation).
        if (e.target.closest && e.target.closest(".node, .twist")) return;
        dragging = true;
        lastX = e.clientX;
        lastY = e.clientY;
        svg.classList.add("panning");
        svg.setPointerCapture(e.pointerId);
      }});
      svg.addEventListener("pointermove", (e) => {{
        if (!dragging) return;
        camera.x += e.clientX - lastX;
        camera.y += e.clientY - lastY;
        lastX = e.clientX;
        lastY = e.clientY;
        applyCamera();
      }});
      const endPan = (e) => {{
        if (!dragging) return;
        dragging = false;
        svg.classList.remove("panning");
        try {{ svg.releasePointerCapture(e.pointerId); }} catch (_) {{}}
      }};
      svg.addEventListener("pointerup", endPan);
      svg.addEventListener("pointercancel", endPan);

      document.getElementById("zoomIn").addEventListener("click", () => {{
        const r = wrap.getBoundingClientRect();
        zoomAt(r.left + r.width / 2, r.top + r.height / 2, 1.2);
      }});
      document.getElementById("zoomOut").addEventListener("click", () => {{
        const r = wrap.getBoundingClientRect();
        zoomAt(r.left + r.width / 2, r.top + r.height / 2, 1 / 1.2);
      }});
      document.getElementById("zoomFit").addEventListener("click", () => fitCamera());
      document.getElementById("zoomSelection").addEventListener("click", () => {{
        const ids = [...selectedPathSet(selectedId)];
        // include collapsed parent itself even if kids hidden
        ids.push(selectedId);
        focusCameraOnIds(ids);
      }});
      document.getElementById("expandAll").addEventListener("click", () => {{
        collapsed.clear();
        draw({{ keepCamera: true }});
      }});
      document.getElementById("collapseDeep").addEventListener("click", () => {{
        initCollapseDefaults();
        draw({{ keepCamera: true }});
      }});
    }}

    function renderStats() {{
      const s = DATA.stats;
      const deg = s.by_degree || {{}};
      const maxDeg = Math.max(...Object.keys(deg).map(Number), 1);
      const maxCount = Math.max(...Object.values(deg), 1);
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

    function matchesFilters(g) {{
      if (!g || g.id === "catholic-church") return true;
      const maxD = Number(document.getElementById("maxDegree").value);
      const status = document.getElementById("statusFilter").value;
      const step1 = document.getElementById("step1Only").checked;
      if ((g.separation_degree ?? 0) > maxD) return false;
      if (step1 && !g.in_step1_breakaways) return false;
      if (status === "extant" && g.status !== "extant") return false;
      if (status === "historical" && g.status !== "historical") return false;
      if (status === "real" && (g.status === "synthetic" || g.status === "in_communion")) return false;
      return true;
    }}

    function searchBlob(g) {{
      const d = g.disagreement || {{}};
      return (
        g.name + " " + g.id + " " + (g.summary || "") + " " +
        (d.summary || "") + " " + (d.canonical_citation || "")
      ).toLowerCase();
    }}

    function searchQuery() {{
      return document.getElementById("search").value.trim().toLowerCase();
    }}

    function isDirectMatch(id) {{
      const g = byId[id];
      if (!g || id === "catholic-church") return id === "catholic-church";
      const q = searchQuery();
      return matchesFilters(g) && (!q || searchBlob(g).includes(q));
    }}

    /** Include node if it matches, or is an ancestor of a match (keeps forks connected). */
    function includeInGraph(id) {{
      if (id === "catholic-church") {{
        return (childrenOf[id] || []).some(cid => includeInGraph(cid));
      }}
      if (isDirectMatch(id)) return true;
      return (childrenOf[id] || []).some(cid => includeInGraph(cid));
    }}

    function filterChildren(id) {{
      return (childrenOf[id] || []).filter(cid => includeInGraph(cid));
    }}

    function visibleChildren(id) {{
      if (collapsed.has(id)) return [];
      return filterChildren(id);
    }}

    function hasCollapsibleChildren(id) {{
      return filterChildren(id).length > 0;
    }}

    function lineageNodes(id) {{
      const g = byId[id];
      const ids = (g && g.lineage && g.lineage.length)
        ? g.lineage
        : (() => {{
            const chain = [];
            let cur = g;
            while (cur) {{
              chain.unshift(cur.id);
              cur = cur.broke_from ? byId[cur.broke_from] : null;
            }}
            if (!chain.includes("catholic-church")) chain.unshift("catholic-church");
            return chain;
          }})();
      return ids.map(i => byId[i]).filter(Boolean);
    }}

    function selectedPathSet(id) {{
      const set = new Set();
      for (const n of lineageNodes(id)) set.add(n.id);
      for (const cid of (childrenOf[id] || [])) set.add(cid);
      return set;
    }}

    /**
     * Tidy tree: each subtree gets a contiguous vertical band under its parent.
     * X = tree depth (not mixed same-degree columns), so sibling forks stay local.
     */
    function layoutTree(rootId) {{
      const rowGap = 28;
      const colGap = 176;
      const padX = 44;
      const padY = 36;
      const labelW = 140;

      const subtreeLeaves = {{}};
      function measure(id) {{
        const kids = visibleChildren(id);
        if (!kids.length) {{
          subtreeLeaves[id] = 1;
          return 1;
        }}
        let sum = 0;
        for (const k of kids) sum += measure(k);
        subtreeLeaves[id] = Math.max(1, sum);
        return subtreeLeaves[id];
      }}
      measure(rootId);

      const pos = {{}};
      let maxDepth = 0;
      function place(id, depth, yStart) {{
        maxDepth = Math.max(maxDepth, depth);
        const kids = visibleChildren(id);
        if (!kids.length) {{
          pos[id] = {{
            x: padX + depth * colGap,
            y: yStart + rowGap / 2,
            depth,
            g: byId[id],
          }};
          return;
        }}
        let y = yStart;
        for (const k of kids) {{
          const kh = (subtreeLeaves[k] || 1) * rowGap;
          place(k, depth + 1, y);
          y += kh;
        }}
        const first = pos[kids[0]];
        const last = pos[kids[kids.length - 1]];
        pos[id] = {{
          x: padX + depth * colGap,
          y: (first.y + last.y) / 2,
          depth,
          g: byId[id],
        }};
      }}
      place(rootId, 0, padY);

      const width = padX + maxDepth * colGap + labelW + 48;
      const height = padY * 2 + (subtreeLeaves[rootId] || 1) * rowGap;
      return {{ pos, width, height, maxDepth, colGap, padX }};
    }}

    function elbowPath(a, b) {{
      const midX = (a.x + b.x) / 2;
      return `M${{a.x}},${{a.y}} H${{midX}} V${{b.y}} H${{b.x}}`;
    }}

    function toggleCollapse(id) {{
      if (!hasCollapsibleChildren(id)) return;
      if (collapsed.has(id)) {{
        collapsed.delete(id);
      }} else {{
        collapsed.add(id);
        // If selection sits inside the collapsed branch, keep the parent selected.
        const chain = lineageNodes(selectedId).map(n => n.id);
        if (selectedId !== id && chain.includes(id)) selectedId = id;
      }}
      draw({{ keepCamera: true }});
      showDetail(selectedId);
    }}

    function draw(opts = {{}}) {{
      const keepCamera = !!opts.keepCamera;
      const svg = document.getElementById("graph");
      const wrap = document.getElementById("graphWrap");
      const vw = wrap.clientWidth || 800;
      const vh = wrap.clientHeight || 600;

      svg.setAttribute("width", vw);
      svg.setAttribute("height", vh);
      svg.setAttribute("viewBox", `0 0 ${{vw}} ${{vh}}`);

      if (!includeInGraph("catholic-church") && !DATA.groups.some(g => isDirectMatch(g.id))) {{
        svg.innerHTML = `<text x="24" y="56" fill="#5c6b7a" font-size="14">No groups match the current filters.</text>`;
        lastLayout = null;
        return;
      }}

      const layout = layoutTree("catholic-church");
      lastLayout = layout;
      contentBounds = {{ width: layout.width, height: layout.height }};
      const {{ pos, maxDepth, colGap, padX }} = layout;
      const pathSet = selectedPathSet(selectedId);

      svg.innerHTML = "";
      const scene = document.createElementNS("http://www.w3.org/2000/svg", "g");
      scene.setAttribute("id", "scene");
      svg.appendChild(scene);

      const gLab = document.createElementNS("http://www.w3.org/2000/svg", "g");
      for (let d = 0; d <= maxDepth; d++) {{
        const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
        t.setAttribute("class", "col-label");
        t.setAttribute("x", padX + d * colGap);
        t.setAttribute("y", 16);
        t.setAttribute("text-anchor", "middle");
        t.textContent = d === 0 ? "Catholic" : `depth ${{d}}`;
        gLab.appendChild(t);
      }}
      scene.appendChild(gLab);

      const gEdges = document.createElementNS("http://www.w3.org/2000/svg", "g");
      for (const id of Object.keys(pos)) {{
        const node = pos[id];
        const parentId = node.g.broke_from;
        if (!parentId || !pos[parentId]) continue;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", elbowPath(pos[parentId], node));
        const onPath = pathSet.has(id) && pathSet.has(parentId);
        const dim = !isDirectMatch(id) && id !== "catholic-church";
        path.setAttribute("class", `edge${{onPath ? " hot" : ""}}${{dim && !onPath ? " dim" : ""}}`);
        gEdges.appendChild(path);
      }}
      scene.appendChild(gEdges);

      const gNodes = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const ordered = Object.keys(pos).sort((a, b) => pos[a].depth - pos[b].depth || pos[a].y - pos[b].y);
      for (const id of ordered) {{
        const p = pos[id];
        const g = p.g;
        const direct = id === "catholic-church" || isDirectMatch(id);
        const gNode = document.createElementNS("http://www.w3.org/2000/svg", "g");
        gNode.setAttribute(
          "class",
          `node${{g.in_step1_breakaways ? " step1" : ""}}${{selectedId === id ? " selected" : ""}}${{direct ? "" : " dim"}}`
        );

        const canCollapse = hasCollapsibleChildren(id);
        const isCollapsed = collapsed.has(id);
        let dotX = p.x;
        if (canCollapse) {{
          const twist = document.createElementNS("http://www.w3.org/2000/svg", "g");
          twist.setAttribute("class", "twist");
          twist.setAttribute("transform", `translate(${{p.x - 18}}, ${{p.y - 7}})`);
          const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          r.setAttribute("width", 14);
          r.setAttribute("height", 14);
          r.setAttribute("rx", 2);
          twist.appendChild(r);
          const tx = document.createElementNS("http://www.w3.org/2000/svg", "text");
          tx.setAttribute("x", 7);
          tx.setAttribute("y", 7);
          tx.textContent = isCollapsed ? "▸" : "▾";
          twist.appendChild(tx);
          twist.addEventListener("click", (e) => {{
            e.stopPropagation();
            toggleCollapse(id);
          }});
          twist.addEventListener("pointerdown", (e) => e.stopPropagation());
          gNode.appendChild(twist);
        }}

        const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        c.setAttribute("class", "node-dot");
        c.setAttribute("cx", dotX);
        c.setAttribute("cy", p.y);
        c.setAttribute("r", id === "catholic-church" ? 7 : 5);
        c.setAttribute("fill", degColors[g.separation_degree] || "#2a5f7a");
        gNode.appendChild(c);

        const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
        t.setAttribute("class", "label");
        t.setAttribute("x", p.x + 10);
        t.setAttribute("y", p.y + 4);
        const label = g.name.length > 30 ? g.name.slice(0, 28) + "…" : g.name;
        t.textContent = label;
        gNode.appendChild(t);

        if (isCollapsed) {{
          const hidden = descendantCount(id);
          if (hidden > 0) {{
            const ct = document.createElementNS("http://www.w3.org/2000/svg", "text");
            ct.setAttribute("class", "collapsed-count");
            ct.setAttribute("x", p.x + 10);
            ct.setAttribute("y", p.y + 16);
            ct.textContent = `+${{hidden}} hidden`;
            gNode.appendChild(ct);
          }}
        }}

        gNode.addEventListener("click", (e) => {{
          e.stopPropagation();
          selectGroup(id);
        }});
        gNode.addEventListener("pointerdown", (e) => e.stopPropagation());
        gNodes.appendChild(gNode);
      }}
      scene.appendChild(gNodes);

      if (!keepCamera) fitCamera();
      else applyCamera();
    }}

    function selectGroup(id) {{
      selectedId = id;
      // Expanding ancestors so the selected node stays reachable after collapses
      let cur = byId[id];
      while (cur && cur.broke_from) {{
        collapsed.delete(cur.broke_from);
        cur = byId[cur.broke_from];
      }}
      showDetail(id);
      draw({{ keepCamera: true }});
    }}

    function showDetail(id) {{
      const g = byId[id];
      if (!g) return;
      const deg = g.separation_degree ?? 0;
      const pills = [
        id === "catholic-church" ? "" : `<span class="pill ${{deg <= 1 ? "d1" : "dhigh"}}">degree ${{deg}}</span>`,
        `<span class="pill">${{escapeHtml(g.status || "—")}}</span>`,
        g.confidence ? `<span class="pill">${{escapeHtml(g.confidence)}}</span>` : "",
        g.in_step1_breakaways ? `<span class="pill step1">Step 1</span>` : "",
      ].join("");

      const chain = lineageNodes(id);
      const pathHtml = chain.map((node, i) => {{
        const isLast = i === chain.length - 1;
        const btn = isLast
          ? `<button type="button" class="current">${{escapeHtml(node.name)}}</button>`
          : `<button type="button" data-jump="${{escapeHtml(node.id)}}">${{escapeHtml(node.name)}}</button>`;
        return btn + (isLast ? "" : `<span class="sep">→</span>`);
      }}).join("");

      const parent = g.broke_from ? byId[g.broke_from] : null;
      const parentLine = parent
        ? `<p><strong>Broke from:</strong> <button type="button" data-jump="${{escapeHtml(parent.id)}}" style="font:inherit;color:var(--accent);background:none;border:none;padding:0;cursor:pointer;text-decoration:underline">${{escapeHtml(parent.name)}}</button></p>`
        : `<p><strong>Broke from:</strong> —</p>`;

      const kids = (childrenOf[id] || []).filter(cid => byId[cid]);
      const canCollapse = hasCollapsibleChildren(id);
      const branchBtn = canCollapse
        ? `<p><button type="button" id="detailCollapse" style="font:inherit;font-size:0.85rem;color:var(--accent);background:#fff;border:1px solid var(--accent);border-radius:3px;padding:0.28rem 0.55rem;cursor:pointer">${{
            collapsed.has(id) ? "Expand branch on graph" : "Collapse branch on graph"
          }}</button></p>`
        : "";
      const spawned = kids.length
        ? `<div class="spawned"><h3>Broke into (${{kids.length}})</h3><ul>${{
            kids.map(cid => {{
              const c = byId[cid];
              const yr = c.approx_rupture && c.approx_rupture !== "—" ? ` · ${{escapeHtml(c.approx_rupture)}}` : "";
              return `<li><button type="button" data-jump="${{escapeHtml(cid)}}">${{escapeHtml(c.name)}}</button><span class="meta" style="margin:0 0 0 0.35rem">${{yr}}</span></li>`;
            }}).join("")
          }}</ul></div>`
        : `<div class="spawned"><h3>Broke into</h3><p class="meta">No catalogued descendant groups.</p></div>`;

      const d = g.disagreement || {{}};
      const kindPill = d.kind
        ? `<span class="pill ${{d.kind === "council_locus" ? "locus" : ""}}">${{escapeHtml(d.kind)}}</span>`
        : "";
      let disagreeHtml = "";
      if (d.kind === "council_locus") disagreeHtml = locusExpandHtml(d, "primary");
      else if (d.summary) disagreeHtml = `<p><strong>Disagreement:</strong> ${{escapeHtml(d.summary)}}</p>`;
      if (d.vs_parent) {{
        disagreeHtml += `<p class="meta"><strong>Vs parent:</strong> ${{escapeHtml(d.vs_parent)}}</p>`;
      }}

      document.getElementById("detail").innerHTML = `
        <p class="name">${{escapeHtml(g.name)}}</p>
        <div>${{pills}}${{kindPill}}</div>
        <p class="meta">${{escapeHtml(g.approx_rupture || "—")}} · ${{escapeHtml(g.region || "—")}}</p>
        <div class="path" aria-label="Lineage path">${{pathHtml}}</div>
        ${{parentLine}}
        ${{branchBtn}}
        <p>${{escapeHtml(g.summary || "")}}</p>
        ${{disagreeHtml}}
        ${{spawned}}`;

      document.getElementById("detail").querySelectorAll("[data-jump]").forEach(btn => {{
        btn.addEventListener("click", () => selectGroup(btn.getAttribute("data-jump")));
      }});
      const collapseBtn = document.getElementById("detailCollapse");
      if (collapseBtn) {{
        collapseBtn.addEventListener("click", () => toggleCollapse(id));
      }}
      wireLocusToggles(document.getElementById("detail"));
    }}

    function locusPayload(recordId) {{
      return (DATA.loci_texts || {{}})[recordId] || null;
    }}

    function locusExpandHtml(d, role) {{
      const rid = d.record_id || "";
      const payload = rid ? locusPayload(rid) : null;
      const cite = d.canonical_citation || (payload && payload.canonical_citation) || rid || "";
      const label = role === "primary" ? "Disagreement locus" : "Related locus";
      let body = `
        <div class="locus-block" data-record-id="${{escapeHtml(rid)}}">
          <p><strong>${{label}}:</strong> ${{escapeHtml(cite)}}</p>
          ${{d.summary ? `<p>${{escapeHtml(d.summary)}}</p>` : ""}}`;
      if (payload && payload.text) {{
        const src = payload.source_url
          ? `<div class="cite"><a href="${{escapeHtml(payload.source_url)}}" target="_blank" rel="noopener">Source</a>${{payload.text_status ? " · " + escapeHtml(payload.text_status) : ""}}</div>`
          : (payload.text_status ? `<div class="cite">${{escapeHtml(payload.text_status)}}</div>` : "");
        body += `
          <div class="locus-actions">
            <button type="button" class="locus-toggle" aria-expanded="false">Read locus</button>
          </div>
          <div class="locus-text" hidden>
            ${{src}}
            ${{escapeHtml(payload.text)}}
          </div>`;
      }} else if (rid) {{
        body += `<p class="meta">Full text not embedded for this locus.</p>`;
      }}
      if (role === "primary" && Array.isArray(d.related_loci) && d.related_loci.length) {{
        const related = d.related_loci
          .filter(r => r.record_id || r.canonical_citation || r.note)
          .map(r => {{
            if (r.record_id) return locusExpandHtml(r, "related");
            if (r.note) return `<div class="locus-block"><p class="meta">${{escapeHtml(r.note)}}</p></div>`;
            return `<div class="locus-block"><p>${{escapeHtml(r.canonical_citation || "")}}</p></div>`;
          }})
          .join("");
        if (related) body += `<div class="related-loci">${{related}}</div>`;
      }}
      body += `</div>`;
      return body;
    }}

    function wireLocusToggles(root) {{
      root.querySelectorAll("button.locus-toggle").forEach(btn => {{
        btn.addEventListener("click", () => {{
          const block = btn.closest(".locus-block");
          const panel = block && block.querySelector(".locus-text");
          if (!panel) return;
          const open = panel.classList.toggle("open");
          panel.hidden = !open;
          btn.setAttribute("aria-expanded", open ? "true" : "false");
          btn.textContent = open ? "Hide locus" : "Read locus";
        }});
      }});
    }}

    function redraw() {{
      draw({{ keepCamera: false }});
      showDetail(selectedId);
    }}

    renderStats();
    initCollapseDefaults();
    wireViewport();
    ["maxDegree","statusFilter","step1Only","search"].forEach(id => {{
      document.getElementById(id).addEventListener("input", redraw);
      document.getElementById(id).addEventListener("change", redraw);
    }});
    window.addEventListener("resize", () => draw({{ keepCamera: true }}));
    redraw();
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
    locus_ids = _collect_locus_record_ids(catalog)
    texts = load_locus_texts(locus_ids)
    html = build_html(catalog)
    args.out.write_text(html, encoding="utf-8")
    missing = sorted(locus_ids - set(texts))
    print(
        f"wrote lineage viz ({catalog['stats']['group_count']} groups, "
        f"{len(texts)}/{len(locus_ids)} loci texts) -> {args.out}"
    )
    if missing:
        print("missing locus texts:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
