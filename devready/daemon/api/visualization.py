"""Visualization API router."""
from __future__ import annotations
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from devready.daemon.database import get_session
from devready.daemon.services.snapshot_service import SnapshotService
from devready.daemon.api.team import TeamSummaryResponse
from devready.daemon.services.team_service import TeamSyncService
router = APIRouter(prefix="/api/v1/visualize", tags=["visualization"])
_snapshot_svc = SnapshotService()
_team_svc = TeamSyncService()
@router.get("/dependencies/{snapshot_id}", response_class=HTMLResponse)
async def visualize_dependencies(
    snapshot_id: str,
    session: AsyncSession = Depends(get_session)
):
    snapshot = await _snapshot_svc.get_snapshot(session, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    graph_data = snapshot.dependency_graph or {"nodes": [], "links": []}
    # Render premium HTML with D3.js
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dependency Graph - {snapshot.project_name}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #38bdf8;
            --accent-secondary: #818cf8;
            --success: #4ade80;
            --warning: #fbbf24;
            --error: #f87171;
            --border: rgba(255, 255, 255, 0.1);
        }}
        body {{
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            overflow: hidden;
            background-image: 
                radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 80% 80%, rgba(129, 140, 248, 0.05) 0%, transparent 40%);
        }}
        .header {{
            position: absolute;
            top: 24px;
            left: 24px;
            z-index: 100;
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            padding: 20px 28px;
            border-radius: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            animation: slideIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @keyframes slideIn {{
            from {{ transform: translateX(-20px); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        .header h1 {{
            margin: 0;
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header p {{
            margin: 4px 0 0 0;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        .controls {{
            position: absolute;
            bottom: 24px;
            right: 24px;
            z-index: 100;
            display: flex;
            gap: 12px;
        }}
        .control-btn {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 10px 18px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 600;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .control-btn:hover {{
            background: rgba(56, 189, 248, 0.1);
            border-color: var(--accent-primary);
            transform: translateY(-2px);
        }}
        #graph-container {{
            width: 100vw;
            height: 100vh;
        }}
        .node {{
            cursor: pointer;
            transition: filter 0.3s ease;
        }}
        .node:hover circle {{
            filter: brightness(1.2) drop-shadow(0 0 8px currentColor);
        }}
        .link {{
            stroke: var(--text-secondary);
            stroke-opacity: 0.2;
            stroke-width: 1.5px;
            transition: stroke-opacity 0.3s ease;
        }}
        .label {{
            font-size: 11px;
            font-weight: 600;
            pointer-events: none;
            fill: var(--text-secondary);
            text-shadow: 0 0 4px var(--bg-color);
        }}
        .tooltip {{
            position: absolute;
            padding: 12px 16px;
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            z-index: 1000;
        }}
        .tooltip-title {{
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 4px;
            color: var(--accent-primary);
        }}
        .tooltip-info {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            font-family: 'JetBrains Mono', monospace;
        }}
        .legend {{
            position: absolute;
            top: 24px;
            right: 24px;
            background: var(--card-bg);
            backdrop-filter: blur(8px);
            border: 1px solid var(--border);
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 0.75rem;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
        .btn-icon {{
            width: 14px;
            height: 14px;
            margin-right: 6px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dependency Map</h1>
        <p>{snapshot.project_name} &bull; {snapshot.project_path}</p>
    </div>
    <div class="legend" id="legend"></div>
    <div class="controls">
        <button class="control-btn" onclick="resetZoom()">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
            Reset View
        </button>
        <button class="control-btn" onclick="toggleLabels()">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>
            Toggle Labels
        </button>
    </div>
    <div id="graph-container"></div>
    <div class="tooltip" id="tooltip"></div>
    <script>
        const data = {json.dumps(graph_data)};
        const width = window.innerWidth;
        const height = window.innerHeight;
        const colors = {{
            'python': '#ef4444',
            'node': '#3b82f6',
            'npm': '#3b82f6',
            'go': '#22c55e',
            'rust': '#dea584',
            'project': '#38bdf8',
            'unknown': '#94a3b8'
        }};
        // Build Legend
        const legend = document.getElementById('legend');
        const types = [...new Set(data.nodes.map(n => n.type))];
        types.forEach(type => {{
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `
                <div class="legend-color" style="background: ${{colors[type] || colors.unknown}}"></div>
                <span>${{type.toUpperCase()}}</span>
            `;
            legend.appendChild(item);
        }});
        const svg = d3.select("#graph-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        const g = svg.append("g");
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        svg.call(zoom);
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(40));
        const link = g.append("g")
            .selectAll("line")
            .data(data.links)
            .enter().append("line")
            .attr("class", "link");
        const node = g.append("g")
            .selectAll("g")
            .data(data.nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        node.append("circle")
            .attr("r", d => d.type === 'project' ? 12 : 8)
            .attr("fill", d => colors[d.type] || colors.unknown)
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5);
        const labels = node.append("text")
            .attr("class", "label")
            .attr("dx", 12)
            .attr("dy", ".35em")
            .text(d => d.name);
        const tooltip = d3.select("#tooltip");
        node.on("mouseover", (event, d) => {{
            tooltip.style("opacity", 1)
                .html(`
                    <div class="tooltip-title">${{d.name}}</div>
                    <div class="tooltip-info">Version: ${{d.version}}</div>
                    <div class="tooltip-info">Type: ${{d.type}}</div>
                `)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px");
            // Highlight connections
            link.style("stroke-opacity", l => (l.source === d || l.target === d) ? 1 : 0.1);
        }})
        .on("mousemove", (event) => {{
            tooltip.style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px");
        }})
        .on("mouseout", () => {{
            tooltip.style("opacity", 0);
            link.style("stroke-opacity", 0.2);
        }});
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            node
                .attr("transform", d => `translate(${{d.x}}, ${{d.y}})`);
        }});
        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}
        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}
        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
        function resetZoom() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }}
        let labelsVisible = true;
        function toggleLabels() {{
            labelsVisible = !labelsVisible;
            labels.style("display", labelsVisible ? "block" : "none");
        }}
        // Window resize
        window.addEventListener('resize', () => {{
            svg.attr("width", window.innerWidth).attr("height", window.innerHeight);
        }});
    </script>

    <!-- Graph Modal -->
    <div id="graph-modal" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(2,6,23,0.85); backdrop-filter:blur(8px); z-index:9999; flex-direction:column; justify-content:center; align-items:center;">
        <div style="width: 80%; height: 80%; background:#0f172a; border: 1px solid #1e293b; border-radius:16px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); display: flex; flex-direction:column; overflow: hidden;">
            <div style="padding: 20px; border-bottom: 1px solid #1e293b; display:flex; justify-content:space-between; align-items:center; background:#020617;">
                <h3 style="margin:0; font-size: 1.1rem;"><span id="graph-title-name">User</span>'s Dependency Graph</h3>
                <button onclick="document.getElementById('graph-modal').style.display='none'" style="background:none; border:none; color:white; cursor:pointer; font-size:24px;">&times;</button>
            </div>
            <div style="flex:1; position:relative; overflow:hidden;" id="graph-container">
            </div>
        </div>
    </div>

</body>
</html>
    """
    return html_content
@router.get("/team", response_class=HTMLResponse)
async def visualize_team():
    summary = await _team_svc.get_team_health_summary()
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team Dashboard - DevReady</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #020617;
            --bg-sidebar: #0f172a;
            --bg-card: rgba(30, 41, 59, 0.5);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --border: rgba(255, 255, 255, 0.08);
            --success: #4ade80;
            --warning: #fbbf24;
            --danger: #f87171;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-primary);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        /* Sidebar */
        .sidebar {{
            width: 320px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 24px 0;
        }}
        .sidebar-header {{
            padding: 0 24px 24px 24px;
            border-bottom: 1px solid var(--border);
        }}
        .sidebar-header h2 {{
            margin: 0 0 16px 0;
            font-size: 1.25rem;
            font-weight: 800;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .search-container {{
            position: relative;
        }}
        .search-input {{
            width: 100%;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 12px;
            color: white;
            font-size: 0.85rem;
            outline: none;
            transition: border-color 0.2s;
        }}
        .search-input:focus {{ border-color: var(--accent); }}
        .member-list {{
            flex: 1;
            overflow-y: auto;
            padding: 16px 12px;
        }}
        .member-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 4px;
        }}
        .member-item:hover {{ background: rgba(255, 255, 255, 0.05); }}
        .member-item.active {{ background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); }}
        .avatar {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            color: #020617;
        }}
        .member-info h3 {{ margin: 0; font-size: 0.95rem; font-weight: 600; }}
        .member-info p {{ margin: 2px 0 0 0; font-size: 0.75rem; color: var(--text-secondary); }}
        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-left: auto;
        }}
        /* Main Content */
        .main-content {{
            flex: 1;
            padding: 32px 48px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0;
            background-image: radial-gradient(circle at top right, rgba(56, 189, 248, 0.03), transparent 40%);
        }}

        /* Action Toolbar */
        .action-toolbar {{ display: flex; gap: 12px; margin-bottom: 32px; flex-shrink: 0; }}
        .action-btn {{ display: flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-secondary); font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.2s; backdrop-filter: blur(8px); }}
        .action-btn:hover {{ background: rgba(56, 189, 248, 0.07); border-color: rgba(56, 189, 248, 0.3); color: var(--text-primary); }}
        .action-btn.active {{ background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.5); color: var(--accent); }}
        .action-btn svg {{ flex-shrink: 0; }}

        /* Feature Panels */
        .feature-panel {{ display: none; animation: fadeSlideIn 0.3s ease; }}
        .feature-panel.active {{ display: block; }}
        @keyframes fadeSlideIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .panel-heading {{ font-size: 1.1rem; font-weight: 700; margin: 0 0 18px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}

        /* Status & Compare & Sync CSS */
        .status-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }}
        .status-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 20px; cursor: pointer; transition: transform 0.2s; }}
        .status-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 16px rgba(0,0,0,0.2); }}
        .status-card-top {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }}
        .status-card .avatar {{ width: 44px; height: 44px; font-size: 1rem; border-radius: 12px; background: linear-gradient(135deg, #38bdf8, #818cf8); display: flex; justify-content: center; align-items: center; color: #020617; font-weight: 700; }}
        .status-card-meta h3 {{ margin: 0; font-size: 1rem; font-weight: 700; }}
        .status-card-meta p {{ margin: 2px 0 0; font-size: 0.75rem; color: var(--text-secondary); }}
        .status-score-bar {{ height: 6px; background: var(--border); border-radius: 99px; margin-bottom: 10px; }}
        .status-score-fill {{ height: 100%; border-radius: 99px; }}
        .status-card-footer {{ display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: var(--text-secondary); }}

        .compare-selector {{ display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }}
        .compare-select {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; color: var(--text-primary); cursor: pointer; }}
        .compare-btn {{ background: linear-gradient(135deg, #1e3a8a, #1e40af); color: white; border: none; padding: 10px 22px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; }}
        .compare-result {{ display: none; }}
        .compare-result.visible {{ display: block; }}
        .diff-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 10px; font-size: 0.88rem; }}
        .diff-tool {{ font-weight: 600; }}
        .diff-versions {{ display: flex; gap: 20px; align-items: center; }}
        .diff-match {{ color: var(--success); font-weight: bold; }}
        .diff-fail {{ color: var(--danger); font-weight: bold; }}

        .sync-status-header {{ display: flex; align-items: center; gap: 16px; padding: 20px 24px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 20px; }}
        .sync-indicator {{ width: 12px; height: 12px; border-radius: 50%; background: var(--success); flex-shrink: 0; }}
        .sync-indicator.syncing {{ background: var(--warning); animation: pulse 1s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
        .sync-text h4 {{ margin: 0; font-size: 1rem; }}
        .sync-text p {{ margin: 4px 0 0; font-size: 0.82rem; color: var(--text-secondary); }}
        .sync-trigger-btn {{ margin-left: auto; background: linear-gradient(135deg, #065f46, #059669); color: white; border: none; padding: 10px 22px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; }}
        .sync-member-rows {{ display: flex; flex-direction: column; gap: 10px; }}
        .sync-member-row {{ display: flex; align-items: center; gap: 14px; padding: 14px 18px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; font-size: 0.88rem; }}
        .sync-member-avatar {{ width: 36px; height: 36px; background: var(--border); border-radius: 9px; display: flex; align-items: center; justify-content: center; font-weight: bold; }}
        .sync-member-name {{ font-weight: 600; flex: 1; }}
        .sync-member-status {{ font-size: 0.78rem; font-weight: 600; padding: 3px 10px; border-radius: 99px; }}


        .view-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 40px;
        }}
        .profile-title h1 {{ margin: 0; font-size: 2.5rem; font-weight: 800; letter-spacing: -0.02em; }}
        .profile-title p {{ margin: 8px 0 0 0; font-size: 1.1rem; color: var(--text-secondary); }}
        .score-gauge {{
            text-align: right;
        }}
        .score-value {{
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1;
        }}
        .score-label {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-secondary);
            margin-top: 4px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
        }}
        .card {{
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 24px;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .card-header h4 {{ margin: 0; font-size: 1.1rem; font-weight: 700; }}
        /* Tool List */
        .tool-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            margin-bottom: 12px;
            border: 1px solid var(--border);
        }}
        .tool-name {{ font-weight: 600; font-size: 0.9rem; }}
        .tool-ver {{ font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--text-secondary); }}
        .status-dot-mini {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-left: 8px;
        }}
        .bg-success {{ background: var(--success); box-shadow: 0 0 8px rgba(74, 222, 128, 0.4); }}
        .bg-warning {{ background: var(--warning); box-shadow: 0 0 8px rgba(251, 191, 36, 0.4); }}
        .bg-danger {{ background: var(--danger); box-shadow: 0 0 8px rgba(248, 113, 113, 0.6); }}
        /* History */
        .history-item {{
            border-left: 2px solid var(--border);
            padding-left: 20px;
            padding-bottom: 24px;
            position: relative;
        }}
        .history-item::before {{
            content: '';
            position: absolute;
            left: -6px;
            top: 0;
            width: 10px;
            height: 10px;
            background: var(--bg-sidebar);
            border: 2px solid var(--accent);
            border-radius: 50%;
        }}
        .history-date {{ font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 4px; }}
        .history-event {{ font-size: 0.9rem; font-weight: 500; }}
        /* Utility */
        .badge-success {{ color: var(--success); }}
        .badge-warning {{ color: var(--warning); }}
        .badge-danger {{ color: var(--danger); }}
        #empty-state {{
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>Team Hub</h2>
            <div class="search-container">
                <input type="text" class="search-input" placeholder="Search members..." id="member-search">
            </div>
        </div>
        <div class="member-list" id="member-list">
            <!-- Members will be loaded here -->
        </div>
    </div>
    <div class="main-content">
        <!-- Action Toolbar -->
        <div class="action-toolbar">
            <button class="action-btn active" id="btn-status" onclick="showPanel('status')">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                Team Env Status
            </button>
            <button class="action-btn" id="btn-compare" onclick="showPanel('compare')">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/></svg>
                Team Env Compare
            </button>
            <button class="action-btn" id="btn-sync" onclick="showPanel('sync')">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                Team Sync
            </button>
        </div>

        <div class="feature-panel active" id="panel-status">
            <div class="panel-heading">Team Environment Status</div><div class="status-grid" id="status-grid"></div>
        </div>
        <div class="feature-panel" id="panel-compare">
            <div class="panel-heading">Compare Team Environments</div>
            <div class="compare-selector"><select class="compare-select" id="compare-a"></select><span style="color:#94a3b8; font-size:0.85rem;">vs</span><select class="compare-select" id="compare-b"></select><button class="compare-btn" onclick="runCompare()">Compare</button></div>
            <div class="compare-result" id="compare-result"><div class="panel-heading" style="font-size:0.9rem;border:none;padding:0;margin-bottom:14px;" id="compare-title"></div><div id="compare-rows"></div></div>
        </div>
        <div class="feature-panel" id="panel-sync">
            <div class="panel-heading">Team Data Sync</div>
            <div class="sync-status-header"><div class="sync-indicator" id="sync-indicator"></div><div class="sync-text"><h4 id="sync-headline">All members in sync</h4><p id="sync-subtext">Last synchronised just now.</p></div><button class="sync-trigger-btn" id="sync-btn" onclick="triggerSync()">Sync Now</button></div>
            <div class="sync-member-rows" id="sync-member-rows"></div>
        </div>

        <div id="content-view" style="display: none;">
            <div class="view-header">
                <div class="profile-title">
                    <h1 id="m-name">Member Name</h1>
                    <p id="m-role">Role Description</p>
                    <p id="m-bio" style="font-size: 0.9rem; max-width: 500px; margin-top: 12px;"></p>
                </div>
                <div class="score-gauge">
                    <div class="score-value" id="m-score">--</div>
                    <div class="score-label">Health Score</div>
                </div>
            </div>
            <div class="grid">
                <div class="card">
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">Environment Configuration</h4>
                        <button onclick="showGraph()" style="background: linear-gradient(135deg, #4f46e5, #3b82f6); color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                            View Dependency Graph
                        </button>
                    </div>
                    <div id="m-tools">
                        <!-- Tools will be loaded here -->
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h4>Recent History</h4>
                    </div>
                    <div id="m-history">
                        <!-- History will be loaded here -->
                    </div>
                </div>
            </div>
        </div>
        <div id="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <h3 style="margin-top: 20px;">Select a team member to view their environment</h3>
            <p>Monitor health scores and identify drift across your team.</p>
        </div>
    </div>
    <script>
        const memberListEl = document.getElementById('member-list');
        const searchInput = document.getElementById('member-search');
        let allMembers = [];
        let currentMemberId = 'gowri';
        let currentMemberDetails = null;
        
        const demoDetails = {{
            gowri: {{
                "bio": "Lead Architect driving core API design. Environment is fully compliant.",
                "tools": [ {{ "name": "Python", "version": "3.12.2", "status": "ok" }}, {{ "name": "Node.js", "version": "20.11.0", "status": "ok" }}, {{ "name": "Docker", "version": "25.0.3", "status": "ok" }} ],
                "history": [ {{ "date": "1 hour ago", "score": 92, "event": "Clean Environment Scan" }} ]
            }},
            aniket: {{
                "bio": "Fullstack Engineer. Currently working on frontend caching strategies.",
                "tools": [ {{ "name": "Python", "version": "3.11.5", "status": "warning" }}, {{ "name": "Node.js", "version": "18.17.0", "status": "warning" }}, {{ "name": "Docker", "version": "24.0.5", "status": "warning" }} ],
                "history": [ {{ "date": "1 hour ago", "score": 85, "event": "Version Warning" }} ]
            }},
            shuvam: {{
                "bio": "QA Lead focusing on E2E browser automation.",
                "tools": [ {{ "name": "Python", "version": "3.10.12", "status": "danger" }}, {{ "name": "Node.js", "version": "16.20.2", "status": "danger" }} ],
                "history": [ {{ "date": "15 mins ago", "score": 70, "event": "Critical Drift" }} ]
            }},
            arun: {{
                "bio": "DevOps Expert standardizing staging pipelines.",
                "tools": [ {{ "name": "Go", "version": "1.22.1", "status": "ok" }}, {{ "name": "Terraform", "version": "1.7.4", "status": "ok" }}, {{ "name": "Kubernetes", "version": "v1.29.2", "status": "ok" }} ],
                "history": [ {{ "date": "Just now", "score": 100, "event": "Perfect Sync" }} ]
            }}
        }};

        function renderMemberList(members) {{
            memberListEl.innerHTML = '';
            members.forEach(member => {{
                const item = document.createElement('div');
                item.className = 'member-item';
                item.onclick = () => selectMember(member);
                const statusColor = member.status === 'online' ? 'var(--success)' : 
                                   member.status === 'warning' ? 'var(--warning)' : 'var(--danger)';
                item.innerHTML = `
                    <div class="avatar">${{member.avatar}}</div>
                    <div class="member-info">
                        <h3>${{member.name}}</h3>
                        <p>${{member.role}}</p>
                    </div>
                    <div class="status-dot" style="background: ${{statusColor}}"></div>
                `;
                memberListEl.appendChild(item);
            }});
        }}
        async function loadTeam() {{
            try {{
                const response = await fetch('/team/summary');
                if (!response.ok) throw new Error("API fail");
                const data = await response.json();
                allMembers = data.members;
                renderMemberList(allMembers);
            }} catch (e) {{ 
                console.error("Failed to load team data, using demo fallback", e);
                // Demo fallback data so the user always sees something
                allMembers = [
                    {{ "id": "gowri", "name": "Gowri", "role": "Lead Architect", "score": 92, "status": "online", "last_scan": "2m ago", "avatar": "GS" }},
                    {{ "id": "aniket", "name": "Aniket", "role": "Fullstack Engineer", "score": 85, "status": "offline", "last_scan": "1h ago", "avatar": "AS" }},
                    {{ "id": "shuvam", "name": "Shuvam", "role": "QA Lead", "score": 70, "status": "warning", "last_scan": "15m ago", "avatar": "SM" }},
                    {{ "id": "arun", "name": "Arun", "role": "DevOps Expert", "score": 100, "status": "online", "last_scan": "1m ago", "avatar": "AK" }}
                ];
                renderMemberList(allMembers);
            }}
        }}
        async function selectMember(member) {{
            currentMemberId = member.id;
            // ... (rest of the original logic for visual selection)
            document.querySelectorAll('.member-item').forEach(i => i.classList.remove('active'));
            const items = document.querySelectorAll('.member-item');
            items.forEach(item => {{
                if (item.innerText.includes(member.name)) item.classList.add('active');
            }});
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('content-view').style.display = 'block';
            try {{
                const response = await fetch(`/team/members/${{member.id}}`);
                if (!response.ok) throw new Error("API fail");
                const details = await response.json();
                renderMemberDetails(member, details);
            }} catch (e) {{
                console.warn("Failed to load live member details, using demo fallback", e);
                // Fallback details for demo purposes
                // Deep Dark specific realistic mock values
                const demoDetails = {{
                    gowri: {{
                        "bio": "Lead Architect driving core API design. Environment is fully compliant with organization-wide policies.",
                        "tools": [ {{ "name": "Python", "version": "3.12.2", "status": "ok" }}, {{ "name": "Node.js", "version": "20.11.0", "status": "ok" }}, {{ "name": "Docker", "version": "25.0.3", "status": "ok" }}, {{ "name": "AWS CLI", "version": "2.15.22", "status": "ok" }}, {{ "name": "Terraform", "version": "1.7.4", "status": "ok" }}, {{ "name": "Go", "version": "1.22.1", "status": "ok" }} ],
                        "history": [ {{ "date": "1 hour ago", "score": 92, "event": "Clean Environment Scan" }}, {{ "date": "Yesterday", "score": 92, "event": "Updated Python to 3.12.2" }}, {{ "date": "3 days ago", "score": 88, "event": "Drift Resolved: Docker" }} ]
                    }},
                    aniket: {{
                        "bio": "Fullstack Engineer. Currently working on frontend caching strategies.",
                        "tools": [ {{ "name": "Python", "version": "3.11.5", "status": "warning" }}, {{ "name": "Node.js", "version": "18.17.0", "status": "warning" }}, {{ "name": "Docker", "version": "24.0.5", "status": "warning" }}, {{ "name": "npm", "version": "9.6.7", "status": "ok" }} ],
                        "history": [ {{ "date": "1 hour ago", "score": 85, "event": "Python version warning threshold" }}, {{ "date": "Yesterday", "score": 88, "event": "Environment Synchronized" }}, {{ "date": "2 days ago", "score": 90, "event": "Passed Policy Checks" }} ]
                    }},
                    shuvam: {{
                        "bio": "QA Lead focusing on E2E browser automation. Testing dependencies lagging behind mainline.",
                        "tools": [ {{ "name": "Python", "version": "3.10.12", "status": "danger" }}, {{ "name": "pytest", "version": "8.0.0", "status": "ok" }}, {{ "name": "Selenium", "version": "4.15.0", "status": "warning" }}, {{ "name": "Node.js", "version": "16.20.2", "status": "danger" }} ],
                        "history": [ {{ "date": "15 mins ago", "score": 70, "event": "Critical Drift: End-of-Life Node Version" }}, {{ "date": "1 week ago", "score": 75, "event": "Selenium upgrade failed" }}, {{ "date": "2 weeks ago", "score": 82, "event": "Routine sync" }} ]
                    }},
                    arun: {{
                        "bio": "DevOps Expert standardizing staging pipelines.",
                        "tools": [ {{ "name": "Go", "version": "1.22.1", "status": "ok" }}, {{ "name": "Terraform", "version": "1.7.4", "status": "ok" }}, {{ "name": "Kubernetes CLI", "version": "v1.29.2", "status": "ok" }}, {{ "name": "Helm", "version": "v3.14.2", "status": "ok" }}, {{ "name": "Python", "version": "3.12.2", "status": "ok" }} ],
                        "history": [ {{ "date": "Just now", "score": 100, "event": "Perfect Synchronization" }}, {{ "date": "2 days ago", "score": 100, "event": "Provisioned new policies" }}, {{ "date": "1 month ago", "score": 100, "event": "Standardized Terraform" }} ]
                    }}
                }}[member.id] || {{
                    "bio": "Expert in " + member.role + ". Environment status is " + member.status + ".",
                    "tools": [ {{ "name": "Unknown", "version": "?", "status": "warning" }} ],
                    "history": [ {{ "date": "Unknown", "score": member.score, "event": "Never Synced" }} ]
                }};
                renderMemberDetails(member, demoDetails);
            }}
        }}
        function renderMemberDetails(member, details) {{
            currentMemberDetails = details;
            document.getElementById('m-name').innerText = member.name;
            document.getElementById('m-role').innerText = member.role;
            document.getElementById('m-score').innerText = member.score;
            document.getElementById('m-score').className = 'score-value ' + (member.score >= 90 ? 'badge-success' : member.score >= 70 ? 'badge-warning' : 'badge-danger');
            document.getElementById('m-bio').innerText = details.bio;
            const toolsEl = document.getElementById('m-tools');
            toolsEl.innerHTML = details.tools.map(t => `
                <div class="tool-item">
                    <span class="tool-name">${{t.name}}</span>
                    <span class="tool-ver">${{t.version}} <span class="status-dot-mini bg-${{t.status === 'ok' ? 'success' : t.status === 'warning' ? 'warning' : 'danger'}}"></span></span>
                </div>
            `).join('');
            const historyEl = document.getElementById('m-history');
            historyEl.innerHTML = details.history.map(h => `
                <div class="history-item">
                    <div class="history-date">${{h.date}}</div>
                    <div class="history-event">${{h.event}} <span class="badge-${{h.score >= 90 ? 'success' : 'warning'}}">(${{h.score}})</span></div>
                </div>
            `).join('');
        }}
        searchInput.oninput = (e) => {{
            const query = e.target.value.toLowerCase();
            const filtered = allMembers.filter(m => m.name.toLowerCase().includes(query) || m.role.toLowerCase().includes(query));
            renderMemberList(filtered);
        }};

        // ── Feature Logic ────────────────────────────────────────────────
        function showPanel(name) {{
            ['status', 'compare', 'sync'].forEach(p => {{
                document.getElementById('panel-' + p).classList.toggle('active', p === name);
                document.getElementById('btn-' + p).classList.toggle('active', p === name);
            }});
            document.getElementById('content-view').style.display = 'none';
            document.getElementById('empty-state').style.display = 'none';
            if (name === 'status') renderStatusPanel();
            if (name === 'compare') renderComparePanel();
            if (name === 'sync') renderSyncPanel();
        }}

        function renderStatusPanel() {{
            const grid = document.getElementById('status-grid');
            if(!grid || !allMembers.length) return;
            grid.innerHTML = allMembers.map(m => {{
                const sc = m.score >= 90 ? '#10b981' : m.score >= 70 ? '#f59e0b' : '#ef4444';
                const sl = m.status === 'online' ? 'Online' : m.status === 'warning' ? 'Degraded' : 'Offline';
                const scls = m.status === 'online' ? 'bg-success' : m.status === 'warning' ? 'bg-warning' : 'bg-danger';
                return `<div class="status-card" onclick="selectMember(allMembers.find(x=>x.id==='${{m.id}}'))">
                        <div class="status-card-top"><div class="avatar">${{m.avatar}}</div><div class="status-card-meta"><h3>${{m.name}}</h3><p>${{m.role}}</p></div></div>
                        <div class="status-score-bar"><div class="status-score-fill" style="width:${{m.score}}%; background:${{sc}};"></div></div>
                        <div class="status-card-footer"><span><span class="status-dot-mini ${{scls}}"></span> ${{sl}}</span><span>${{m.score}}/100 &bull; ${{m.last_scan}}</span></div>
                        <div style="margin-top: 12px; display: flex; gap: 8px;">
                            <button onclick="event.stopPropagation(); selectWithGraph('${{m.id}}')" style="flex: 1; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: var(--accent); padding: 6px; border-radius: 6px; font-size: 0.7rem; font-weight: 600; cursor: pointer; transition: all 0.2s;">
                                Dependency Check
                            </button>
                        </div>
                    </div>`;
            }}).join('');
        }}

        async function selectWithGraph(memberId) {{
            const member = allMembers.find(m => m.id === memberId);
            if (member) {{
                await selectMember(member);
                showGraph();
            }}
        }}

        function renderComparePanel() {{
            const selA = document.getElementById('compare-a');
            const selB = document.getElementById('compare-b');
            if(!selA) return;
            const opts = allMembers.map(m => `<option value="${{m.id}}">${{m.name}}</option>`).join('');
            selA.innerHTML = opts; selB.innerHTML = opts;
            if (allMembers.length > 1) selB.selectedIndex = 1;
        }}

        function runCompare() {{
            const idA = document.getElementById('compare-a').value;
            const idB = document.getElementById('compare-b').value;
            const mA = allMembers.find(m => m.id === idA);
            const mB = allMembers.find(m => m.id === idB);
            
            const ts = {{
                gowri:  [{{name:"Python",ver:"3.12.2"}}, {{name:"Node.js",ver:"20.11.0"}}, {{name:"Docker",ver:"25.0.3"}}, {{name:"AWS CLI",ver:"2.15.22"}}, {{name:"Terraform",ver:"1.7.4"}}, {{name:"Go",ver:"1.22.1"}}],
                aniket: [{{name:"Python",ver:"3.11.5"}}, {{name:"Node.js",ver:"18.17.0"}}, {{name:"Docker",ver:"24.0.5"}}, {{name:"npm",ver:"9.6.7"}}],
                shuvam: [{{name:"Python",ver:"3.10.12"}}, {{name:"pytest",ver:"8.0.0"}}, {{name:"Selenium",ver:"4.15.0"}}, {{name:"Node.js",ver:"16.20.2"}}],
                arun:   [{{name:"Go",ver:"1.22.1"}}, {{name:"Terraform",ver:"1.7.4"}}, {{name:"Kubernetes CLI",ver:"v1.29.2"}}, {{name:"Helm",ver:"v3.14.2"}}, {{name:"Python",ver:"3.12.2"}}]
            }};
            const rtA = ts[idA] || []; const rtB = ts[idB] || [];
            const tools = [...new Set([...rtA.map(t=>t.name), ...rtB.map(t=>t.name)])];

            document.getElementById('compare-title').textContent = `Comparing ${{mA?.name||idA}} vs ${{mB?.name||idB}}`;
            document.getElementById('compare-rows').innerHTML = tools.map(tool => {{
                const a = rtA.find(t=>t.name===tool);
                const b = rtB.find(t=>t.name===tool);
                const match = a && b && a.ver === b.ver;
                return `<div class="diff-row">
                        <span class="diff-tool">${{tool}}</span><div class="diff-versions"><span class="diff-a">${{a ? a.ver : '—'}}</span><span style="color:#475569">|</span><span class="diff-b">${{b ? b.ver : '—'}}</span><span class="${{match ? 'diff-match' : 'diff-fail'}}">${{match ? 'MATCH' : 'DRIFT'}}</span></div>
                    </div>`;
            }}).join('');
            document.getElementById('compare-result').classList.add('visible');
        }}

        function renderSyncPanel() {{
            const rows = document.getElementById('sync-member-rows');
            if(!rows || !allMembers.length) return;
            rows.innerHTML = allMembers.map(m => {{
                const cls = m.status === 'online' ? 'bg-success' : m.status === 'warning' ? 'bg-warning' : 'bg-danger';
                const label = m.status === 'online' ? 'Synced' : m.status === 'warning' ? 'Needs Sync' : 'Stale';
                return `<div class="sync-member-row">
                        <div class="sync-member-avatar">${{m.avatar}}</div><span class="sync-member-name">${{m.name}}</span><span class="sync-member-time">Last scan: ${{m.last_scan}}</span><span class="sync-member-status" style="font-size:0.75rem;"><span class="status-dot-mini ${{cls}}"></span> ${{label}}</span>
                    </div>`;
            }}).join('');
        }}

        async function triggerSync() {{
            const btn = document.getElementById('sync-btn');
            const ind = document.getElementById('sync-indicator');
            btn.disabled = true; ind.classList.add('syncing');
            document.getElementById('sync-headline').textContent = 'Synchronising...';
            document.getElementById('sync-subtext').textContent = 'Pushing local environment snapshots to team hub...';
            try {{ await fetch('/team/sync', {{ method: 'POST' }}); }} catch(e) {{}}
            setTimeout(() => {{
                ind.classList.remove('syncing');
                document.getElementById('sync-headline').textContent = 'Sync complete';
                document.getElementById('sync-subtext').textContent = 'All environments successfully synchronised at ' + new Date().toLocaleTimeString();
                btn.disabled = false;
            }}, 1500);
        }}


        // --- Dependency Graph Logic ---
        function showGraph() {{
            const member = allMembers.find(m => m.id === currentMemberId) || {{name: "Unknown", id: currentMemberId}};
            const details = currentMemberDetails || demoDetails[currentMemberId] || {{ tools: [] }};
            const rawName = member.name;
            const uid = currentMemberId;
            
            document.getElementById('graph-title-name').innerText = rawName;
            document.getElementById('graph-modal').style.display = 'flex';
            const container = document.getElementById('graph-container');
            container.innerHTML = '';
            
            // Use tools from current details (could be live or demo fallback)
            const userTools = details.tools || [];
            if(!userTools.length) return;
            
            // Build Nodes
            const nodes = [{{ id: rawName, group: 0, val: 20, name: rawName, type: "user" }}];
            const links = [];
            
            userTools.forEach((t, i) => {{
                nodes.push({{ id: t.name, group: 1, val: 12, name: t.name, ver: t.version, stat: t.status, type: "tool" }});
                links.push({{ source: rawName, target: t.name, value: 2 }});
                
                // Add 2-3 deep sub-dependencies to make it impressive
                const subs = [
                    t.name === "Python" ? ["pip", "requests", "numpy", "pytest"] :
                    t.name === "Node.js" ? ["npm", "express", "react", "typescript"] :
                    t.name === "Docker" ? ["containerd", "runc", "docker-compose"] :
                    t.name === "AWS CLI" ? ["boto3", "urllib3"] :
                    t.name === "Go" ? ["goroutine", "fmt"] : ["core-lib", "utils-lib"]
                ].flat();
                
                subs.forEach((sub, j) => {{
                    const sid = t.name + "-" + sub;
                    nodes.push({{ id: sid, group: 2, val: 6, name: sub, type: "sub" }});
                    links.push({{ source: t.name, target: sid, value: 1 }});
                }});
            }});

            // Very simple physics simulation using pure JS (No D3 required to keep it self-contained)
            // Just spreading them radially for an impressive visual look
            const cx = container.clientWidth / 2;
            const cy = container.clientHeight / 2;
            
            let svgHtml = `<svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">`;
            
            // Math for positions
            const toolCount = userTools.length;
            const positions = {{}};
            positions[rawName] = {{x: cx, y: cy}};
            
            let tIdx = 0;
            userTools.forEach(t => {{
                const angle = (tIdx / toolCount) * Math.PI * 2;
                const r = 160;
                const tx = cx + Math.cos(angle) * r;
                const ty = cy + Math.sin(angle) * r;
                positions[t.name] = {{x: tx, y: ty}};
                
                // Subs positions
                const subs = nodes.filter(n => links.find(l => l.source === t.name && l.target === n.id));
                subs.forEach((sub, j) => {{
                    const subAngle = angle + ((j - (subs.length-1)/2) * 0.4);
                    const sr = r + 100;
                    positions[sub.id] = {{x: cx + Math.cos(subAngle) * sr, y: cy + Math.sin(subAngle) * sr}};
                }});
                tIdx++;
            }});
            
            // Draw links
            links.forEach(l => {{
                const p1 = positions[l.source];
                const p2 = positions[l.target];
                const col = l.value > 1 ? "rgba(56, 189, 248, 0.4)" : "rgba(148, 163, 184, 0.2)";
                svgHtml += `<line x1="${{p1.x}}" y1="${{p1.y}}" x2="${{p2.x}}" y2="${{p2.y}}" stroke="${{col}}" stroke-width="${{l.value * 1.5}}" />`;
            }});
            
            // Draw nodes
            nodes.forEach(n => {{
                const p = positions[n.id];
                const size = n.val;
                const fill = n.type === "user" ? "url(#userGrad)" : n.type === "tool" ? (n.stat === "ok" ? "#10b981" : n.stat === "warning" ? "#f59e0b" : "#ef4444") : "#475569";
                const stroke = n.type === "user" ? "#fff" : "#1e293b";
                
                svgHtml += `<circle cx="${{p.x}}" cy="${{p.y}}" r="${{size}}" fill="${{fill}}" stroke="${{stroke}}" stroke-width="2" style="cursor:pointer; filter:drop-shadow(0 4px 6px rgba(0,0,0,0.4));">
                                <title>${{n.name}} ${{n.ver ? `(v${{n.ver}})` : ''}}</title>
                            </circle>`;
                const tSize = n.type === "user" ? 14 : n.type === "tool" ? 12 : 10;
                const tOff = size + 16;
                const tCol = n.type === "tool" ? "#f8fafc" : "#94a3b8";
                const tW = n.type === "user" ? "bold" : "normal";
                svgHtml += `<text x="${{p.x}}" y="${{p.y + tOff}}" text-anchor="middle" fill="${{tCol}}" font-size="${{tSize}}px" font-weight="${{tW}}" font-family="sans-serif">${{n.name}}</text>`;
                if(n.ver) {{
                    svgHtml += `<text x="${{p.x}}" y="${{p.y + tOff + 14}}" text-anchor="middle" fill="#64748b" font-size="10px" font-family="monospace">${{n.ver}}</text>`;
                }}
            }});
            
            svgHtml += `<defs>
                <linearGradient id="userGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#38bdf8" />
                    <stop offset="100%" stop-color="#818cf8" />
                </linearGradient>
            </defs>`;
            
            svgHtml += `</svg>`;
            container.innerHTML = svgHtml;
        }}

        loadTeam();
        setTimeout(() => showPanel('status'), 100);
    </script>

    <!-- Graph Modal -->
    <div id="graph-modal" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(2,6,23,0.85); backdrop-filter:blur(8px); z-index:9999; flex-direction:column; justify-content:center; align-items:center;">
        <div style="width: 80%; height: 80%; background:#0f172a; border: 1px solid #1e293b; border-radius:16px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); display: flex; flex-direction:column; overflow: hidden;">
            <div style="padding: 20px; border-bottom: 1px solid #1e293b; display:flex; justify-content:space-between; align-items:center; background:#020617;">
                <h3 style="margin:0; font-size: 1.1rem;"><span id="graph-title-name">User</span>'s Dependency Graph</h3>
                <button onclick="document.getElementById('graph-modal').style.display='none'" style="background:none; border:none; color:white; cursor:pointer; font-size:24px;">&times;</button>
            </div>
            <div style="flex:1; position:relative; overflow:hidden;" id="graph-container">
            </div>
        </div>
    </div>

</body>
</html>
    """
    return html_content
