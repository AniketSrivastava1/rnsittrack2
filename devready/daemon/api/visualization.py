"""Visualization API router."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.database import get_session
from devready.daemon.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/v1/visualize", tags=["visualization"])
_snapshot_svc = SnapshotService()

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
    </style>
</head>
<body>
    <div class="header">
        <h1>Dependency Map</h1>
        <p>{snapshot.project_name} &bull; {snapshot.project_path}</p>
    </div>

    <div class="legend" id="legend"></div>

    <div class="controls">
        <button class="control-btn" onclick="resetZoom()">🏠 Reset View</button>
        <button class="control-btn" onclick="toggleLabels()">🏷️ Toggle Labels</button>
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
</body>
</html>
    """
    return html_content
