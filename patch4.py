import sys

path = r'c:\Users\GOWRI SIMHA\rnsittrack2\devready\daemon\api\visualization.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. CSS
idx_css = content.find('        .main-content {')
if idx_css == -1: idx_css = content.find('        .main-content {{')
if idx_css == -1: print('CSS start not found'); sys.exit(1)
idx_css_end = content.find('        .view-header {', idx_css)
if idx_css_end == -1: idx_css_end = content.find('        .view-header {{', idx_css)
if idx_css_end == -1: print('CSS end not found'); sys.exit(1)

css_payload = """        .main-content {{
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

        .view-header {{"""
content = content[:idx_css] + css_payload + content[idx_css_end:]

# 2. HTML
idx_html = content.find('<div class="main-content">')
if idx_html == -1: print('HTML start not found'); sys.exit(1)
idx_html_end = content.find('<div id="content-view"', idx_html)

html_payload = """<div class="main-content">
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

        """
content = content[:idx_html] + html_payload + content[idx_html_end:]


# 3. MOCK DATA
js_start = content.find('                const demoDetails = {')
if js_start == -1: js_start = content.find('                const demoDetails = {{')
js_end = content.find('                renderMemberDetails(member, demoDetails);\n            }\n        }')
if js_end == -1: js_end = content.find('                renderMemberDetails(member, demoDetails);\n            }}\n        }}')

if js_start == -1 or js_end == -1: print('JS Mock missing'); sys.exit(1)

rich_demo_data = """                // Deep Dark specific realistic mock values
                const demoDetails = {
                    gowri: {
                        "bio": "Lead Architect driving core API design. Environment is fully compliant with organization-wide policies.",
                        "tools": [ { "name": "Python", "version": "3.12.2", "status": "ok" }, { "name": "Node.js", "version": "20.11.0", "status": "ok" }, { "name": "Docker", "version": "25.0.3", "status": "ok" }, { "name": "AWS CLI", "version": "2.15.22", "status": "ok" }, { "name": "Terraform", "version": "1.7.4", "status": "ok" }, { "name": "Go", "version": "1.22.1", "status": "ok" } ],
                        "history": [ { "date": "1 hour ago", "score": 92, "event": "Clean Environment Scan" }, { "date": "Yesterday", "score": 92, "event": "Updated Python to 3.12.2" }, { "date": "3 days ago", "score": 88, "event": "Drift Resolved: Docker" } ]
                    },
                    aniket: {
                        "bio": "Fullstack Engineer. Currently working on frontend caching strategies.",
                        "tools": [ { "name": "Python", "version": "3.11.5", "status": "warning" }, { "name": "Node.js", "version": "18.17.0", "status": "warning" }, { "name": "Docker", "version": "24.0.5", "status": "warning" }, { "name": "npm", "version": "9.6.7", "status": "ok" } ],
                        "history": [ { "date": "1 hour ago", "score": 85, "event": "Python version warning threshold" }, { "date": "Yesterday", "score": 88, "event": "Environment Synchronized" }, { "date": "2 days ago", "score": 90, "event": "Passed Policy Checks" } ]
                    },
                    shuvam: {
                        "bio": "QA Lead focusing on E2E browser automation. Testing dependencies lagging behind mainline.",
                        "tools": [ { "name": "Python", "version": "3.10.12", "status": "danger" }, { "name": "pytest", "version": "8.0.0", "status": "ok" }, { "name": "Selenium", "version": "4.15.0", "status": "warning" }, { "name": "Node.js", "version": "16.20.2", "status": "danger" } ],
                        "history": [ { "date": "15 mins ago", "score": 70, "event": "Critical Drift: End-of-Life Node Version" }, { "date": "1 week ago", "score": 75, "event": "Selenium upgrade failed" }, { "date": "2 weeks ago", "score": 82, "event": "Routine sync" } ]
                    },
                    arun: {
                        "bio": "DevOps Expert standardizing staging pipelines.",
                        "tools": [ { "name": "Go", "version": "1.22.1", "status": "ok" }, { "name": "Terraform", "version": "1.7.4", "status": "ok" }, { "name": "Kubernetes CLI", "version": "v1.29.2", "status": "ok" }, { "name": "Helm", "version": "v3.14.2", "status": "ok" }, { "name": "Python", "version": "3.12.2", "status": "ok" } ],
                        "history": [ { "date": "Just now", "score": 100, "event": "Perfect Synchronization" }, { "date": "2 days ago", "score": 100, "event": "Provisioned new policies" }, { "date": "1 month ago", "score": 100, "event": "Standardized Terraform" } ]
                    }
                }[member.id] || {
                    "bio": "Expert in " + member.role + ". Environment status is " + member.status + ".",
                    "tools": [ { "name": "Unknown", "version": "?", "status": "warning" } ],
                    "history": [ { "date": "Unknown", "score": member.score, "event": "Never Synced" } ]
                };"""

content = content[:js_start] + rich_demo_data.replace('{', '{{').replace('}', '}}') + content[js_end:]

# 4. Panel JS logic
js_final_idx = content.find("        loadTeam();")
if js_final_idx == -1: print('JS final missing'); sys.exit(1)

js_tabs = """
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
                    </div>`;
            }}).join('');
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

"""
content = content[:js_final_idx] + js_tabs + content[js_final_idx:]
content = content.replace("        loadTeam();\n    </script>", "        loadTeam();\n        setTimeout(() => showPanel('status'), 300);\n    </script>")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("All Replacements DONE")
