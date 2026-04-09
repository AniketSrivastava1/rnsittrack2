"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.DashboardViewProvider = void 0;
const vscode = __importStar(require("vscode"));
class DashboardViewProvider {
    constructor(_extensionUri, _client, _registry) {
        this._extensionUri = _extensionUri;
        this._client = _client;
        this._registry = _registry;
    }
    resolveWebviewView(webviewView, _context, _token) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'fix':
                    await this.applyFix(data.value);
                    break;
                case 'scan':
                    await this.refresh();
                    break;
                case 'visualize':
                    this.openVisualization(data.snapshotId);
                    break;
                case 'visualizeTeam':
                    this.openTeamDashboard();
                    break;
            }
        });
        this.refresh();
    }
    async refresh() {
        if (!this._view)
            return;
        const projectPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!projectPath) {
            vscode.window.showErrorMessage('DevReady: No workspace folder open.');
            return;
        }
        try {
            // Run the actual scan (same as `devready scan`)
            const snapshot = await this._client.scan(projectPath);
            // Persist to machine-wide registry
            this._registry.upsert(snapshot);
            const policy = { required_tools: [], forbidden_tools: [], version_constraints: {}, env_var_requirements: [] };
            const recommendations = await this._client.getFixRecommendations(snapshot.snapshot_id, policy);
            this._view.webview.postMessage({ type: 'update', snapshot, recommendations });
        }
        catch (error) {
            this._view.webview.postMessage({ type: 'update', snapshot: { health_score: '--' }, recommendations: [] });
            const msg = error?.message ?? String(error);
            if (msg.includes('ECONNREFUSED') || msg.includes('connect')) {
                vscode.window.showErrorMessage('DevReady: Daemon not running. Start it with: uvicorn devready.daemon.main:app --host 127.0.0.1 --port 8443');
            }
            else {
                vscode.window.showErrorMessage(`DevReady: Scan failed. ${msg}`);
            }
        }
    }
    async openVisualization(snapshotId) {
        if (!snapshotId)
            return;
        const panel = vscode.window.createWebviewPanel('devready.dependencyGraph', 'Dependency Graph', vscode.ViewColumn.One, { enableScripts: true });
        try {
            const html = await this._client.getVisualizationHtml(snapshotId);
            panel.webview.html = html;
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to load dependency graph: ${error}`);
            panel.dispose();
        }
    }
    async openTeamDashboard() {
        const panel = vscode.window.createWebviewPanel('devready.teamDashboard', 'Team Dashboard', vscode.ViewColumn.One, { enableScripts: true });
        try {
            const html = await this._client.getTeamVisualizationHtml();
            panel.webview.html = html;
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to load team dashboard: ${error}`);
            panel.dispose();
        }
    }
    async applyFix(recommendation) {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Applying Fix: ${recommendation.description}`,
            cancellable: false
        }, async () => {
            const result = await this._client.applyFix(recommendation);
            if (result.success) {
                vscode.window.showInformationMessage(result.message);
                await this.refresh();
            }
            else {
                vscode.window.showErrorMessage(result.message);
            }
        });
    }
    _getHtmlForWebview(_webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg-color: #020617;
            --text-color: #f8fafc;
            --card-bg: #0f172a;
            --card-border: #1e293b;
            --accent-primary: #1e3a8a;
            --accent-hover: #1e40af;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --desc-color: #94a3b8;
            --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        body { 
            font-family: var(--font-family); 
            padding: 24px; 
            color: var(--text-color); 
            background: var(--bg-color);
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .header {
            text-align: center;
            margin-bottom: 20px;
            animation: fadeIn 0.5s ease-out;
            position: relative;
            z-index: 10;
        }

        .geo {
            position: fixed;
            z-index: 0;
            pointer-events: none;
            border-radius: 50%;
        }
        
        .geo-1 {
            width: 350px;
            height: 350px;
            background: radial-gradient(circle, rgba(30, 58, 138, 0.45) 0%, transparent 60%);
            top: -100px;
            left: -100px;
        }

        .geo-2 {
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, transparent 60%);
            bottom: -200px;
            right: -200px;
        }

        .geo-3 {
            width: 180px;
            height: 180px;
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.08) 0%, transparent 100%);
            top: 40px;
            right: 10px;
            border-radius: 24px;
            transform: rotate(30deg);
        }

        .content-container {
            position: relative;
            z-index: 10;
        }

        .title {
            font-size: 1.2rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--desc-color);
            margin-bottom: 12px;
        }

        .dashboard-controls {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
            margin-top: 24px;
            flex-wrap: wrap;
        }

        .control-panel {
            display: flex;
            flex-direction: column;
            gap: 12px;
            flex: 1;
            min-width: 130px;
        }
        
        .control-panel.left { align-items: flex-end; }
        .control-panel.right { align-items: flex-start; }

        .score-container { 
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            flex-shrink: 0;
        }

        .score-circle {
            width: 220px;
            height: 220px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            background: conic-gradient(var(--success-color) 0%, var(--card-bg) 0%);
            position: relative;
            box-shadow: 0 12px 40px rgba(0,0,0,0.5);
            transition: background 1s ease-out;
        }

        .score-circle::before {
            content: '';
            position: absolute;
            inset: 12px;
            border-radius: 50%;
            background: var(--bg-color);
        }

        .score { 
            position: relative;
            font-size: 5rem; 
            font-weight: 800; 
            z-index: 10;
            text-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--card-border);
        }

        #issues-list {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .issue-card { 
            background: var(--card-bg); 
            border: 1px solid var(--card-border);
            padding: 16px; 
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            animation: slideUp 0.4s ease-out forwards;
            opacity: 0;
            transform: translateY(10px);
        }

        .issue-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        }

        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }

        .issue-title { 
            font-weight: 600; 
            font-size: 1.05rem;
            line-height: 1.4;
        }

        .risk-badge {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 8px;
            border-radius: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .risk-high { background: rgba(248, 113, 113, 0.2); color: var(--error-color); }
        .risk-medium { background: rgba(250, 204, 21, 0.2); color: var(--warning-color); }
        .risk-low { background: rgba(74, 222, 128, 0.2); color: var(--success-color); }

        .issue-desc {
            font-size: 0.9rem;
            color: var(--desc-color);
            line-height: 1.5;
            margin-bottom: 16px;
        }

        .fix-button { 
            background: var(--accent-primary);
            color: #ffffff;
            border: none; 
            padding: 8px 16px; 
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer; 
            border-radius: 6px;
            width: 100%;
            transition: background 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
        }

        .shadow-btn {
            box-shadow: 0 4px 14px rgba(30, 58, 138, 0.5);
        }
        
        .shadow-btn:hover {
            box-shadow: 0 6px 20px rgba(30, 58, 138, 0.7);
        }

        .btn-icon {
            display: inline-block;
            vertical-align: middle;
            margin-right: 2px;
        }

        .fix-button:hover { 
            background: var(--accent-hover); 
        }

        .fix-button:active {
            transform: scale(0.98);
        }
        
        .loading {
            text-align: center;
            color: var(--desc-color);
            font-style: italic;
            padding: 20px;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="geo geo-1"></div>
    <div class="geo geo-2"></div>
    <div class="geo geo-3"></div>

    <div class="content-container">
        <div class="header">
            <div class="title">Environment Health</div>
            
            <div class="dashboard-controls">
                <div class="control-panel left">
                    <button id="scan-button" class="fix-button shadow-btn">
                        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" class="btn-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        Scan Env
                    </button>
                </div>
                
                <div class="score-container">
                    <div class="score-circle" id="score-circle">
                        <div id="score" class="score">--</div>
                    </div>
                </div>
                
                <div class="control-panel right">
                    <button id="team-button" class="fix-button shadow-btn">
                        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" class="btn-icon"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        Team Board
                    </button>
                    <button id="graph-button" class="fix-button shadow-btn" style="display: none; background: #0f172a; border: 1px solid rgba(255,255,255,0.1);">
                        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" class="btn-icon"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                        Graph
                    </button>
                </div>
            </div>
        </div>
        
        <div>
            <div class="section-title">Actionable Fixes</div>
            <div id="issues-list">
                <div class="loading">Analyzing environment...</div>
            </div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const scoreEl = document.getElementById('score');
        const scoreCircleEl = document.getElementById('score-circle');
        const listEl = document.getElementById('issues-list');
        const scanBtn = document.getElementById('scan-button');
        const graphBtn = document.getElementById('graph-button');
        const teamBtn = document.getElementById('team-button');

        let currentSnapshotId = null;

        scanBtn.onclick = () => {
            listEl.innerHTML = '<div class="loading">Mapping dependency graph...</div>';
            scanBtn.disabled = true;
            scanBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" class="btn-icon"><polyline points="12 2 12 12 18 12"></polyline><circle cx="12" cy="12" r="10"></circle></svg> Mapping...';
            
            setTimeout(() => {
                document.body.innerHTML = 
                '<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; background: #020617;">' +
                    '<div style="padding: 20px; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; z-index: 10;">' +
                        '<h2 style="margin: 0; color: #f8fafc; font-size: 1.2rem;">Mock Service Dependency Graph</h2>' +
                        '<button onclick="location.reload()" style="background: #334155; color: #f8fafc; border: 1px solid #475569; padding: 8px 16px; border-radius: 6px; cursor: pointer;">&larr; Back to Dashboard</button>' +
                    '</div>' +
                    '<div id="d3-graph-container" style="flex: 1; overflow: hidden; position: relative; display: flex; justify-content: center; align-items: center;">' +
                    '</div>' +
                '</div>';
                
                const container = document.getElementById('d3-graph-container');
                const cx = window.innerWidth / 2;
                const cy = (window.innerHeight - 70) / 2;
                let svgHtml = '<svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">';
                
                const nodes = [
                    { id: "Core App", group: 0, val: 24, fill: "url(#coreGrad)", str: "#fff" },
                    { id: "Auth Service", group: 1, val: 14, fill: "#10b981", str: "#1e293b" },
                    { id: "Payment API", group: 1, val: 14, fill: "#3b82f6", str: "#1e293b" },
                    { id: "Database Cluster", group: 1, val: 18, fill: "#f59e0b", str: "#1e293b" },
                    { id: "Redis Cache", group: 2, val: 12, fill: "#8b5cf6", str: "#1e293b" },
                    { id: "Python 3.12 Backend", group: 2, val: 16, fill: "#ef4444", str: "#1e293b" },
                    { id: "React Frontend", group: 2, val: 16, fill: "#06b6d4", str: "#1e293b" }
                ];
                
                const links = [
                    { source: 0, target: 1 }, { source: 0, target: 2 }, { source: 0, target: 5 }, { source: 0, target: 6 },
                    { source: 5, target: 3 }, { source: 5, target: 4 }, { source: 2, target: 3 }, { source: 1, target: 4 }
                ];
                
                const positions = [
                    {x: cx, y: cy},
                    {x: cx - 180, y: cy - 120},
                    {x: cx + 180, y: cy - 120},
                    {x: cx, y: cy + 180},
                    {x: cx - 180, y: cy + 120},
                    {x: cx - 180, y: cy},
                    {x: cx + 180, y: cy}
                ];
                
                links.forEach(l => {
                    const p1 = positions[l.source];
                    const p2 = positions[l.target];
                    svgHtml += '<line x1="' + p1.x + '" y1="' + p1.y + '" x2="' + p2.x + '" y2="' + p2.y + '" stroke="#334155" stroke-width="2" />';
                });
                
                nodes.forEach((n, i) => {
                    const p = positions[i];
                    svgHtml += '<circle cx="' + p.x + '" cy="' + p.y + '" r="' + n.val + '" fill="' + n.fill + '" stroke="' + n.str + '" stroke-width="2" style="filter:drop-shadow(0 4px 6px rgba(0,0,0,0.5));" />';
                    svgHtml += '<text x="' + p.x + '" y="' + (p.y + n.val + 16) + '" text-anchor="middle" fill="#94a3b8" font-size="12px" font-weight="bold" font-family="sans-serif">' + n.id + '</text>';
                });
                
                svgHtml += '<defs><linearGradient id="coreGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#38bdf8" /><stop offset="100%" stop-color="#818cf8" /></linearGradient></defs>';
                svgHtml += '</svg>';
                
                container.innerHTML = svgHtml;
            }, 800);
        };

        graphBtn.onclick = () => {
            if (currentSnapshotId) {
                vscode.postMessage({ type: 'visualize', snapshotId: currentSnapshotId });
            }
        };

        teamBtn.onclick = () => {
            vscode.postMessage({ type: 'visualizeTeam' });
        };

        function updateScoreVisuals(scoreStr) {
            const score = parseInt(scoreStr) || 0;
            const color = score >= 80 ? 'var(--success-color)' : 
                          score >= 50 ? 'var(--warning-color)' : 
                          'var(--error-color)';
            
            scoreEl.style.color = color;
            // Animate conic gradient
            setTimeout(() => {
                scoreCircleEl.style.background = \`conic-gradient(\${color} \${score}%, var(--card-bg) \${score}%)\`;
            }, 100);
        }

        window.addEventListener('message', event => {
            const message = event.data;
            if (message.type === 'update') {
                scanBtn.disabled = false;
                scanBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" class="btn-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Scan Environment';
                
                scoreEl.innerText = message.snapshot.health_score;
                updateScoreVisuals(message.snapshot.health_score);
                
                currentSnapshotId = message.snapshot.snapshot_id;
                if (currentSnapshotId) {
                    graphBtn.style.display = 'flex';
                } else {
                    graphBtn.style.display = 'none';
                }
                
                listEl.innerHTML = '';
                
                if (!message.recommendations || message.recommendations.length === 0) {
                    listEl.innerHTML = \`
                        <div style="text-align: center; padding: 32px; background: rgba(74, 222, 128, 0.1); border-radius: 12px; border: 1px dashed var(--success-color);">
                            <div style="display: flex; justify-content: center;"><svg viewBox="0 0 24 24" width="32" height="32" stroke="var(--success-color)" stroke-width="1.5" fill="none" style="margin-bottom: 8px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg></div>
                            <div style="font-weight: 600; color: var(--success-color);">All systems go!</div>
                            <div style="font-size: 0.9rem; color: var(--desc-color); margin-top: 4px;">Your environment complies with all policies.</div>
                        </div>\`;
                } else {
                    message.recommendations.forEach((rec, index) => {
                        const card = document.createElement('div');
                        card.className = 'issue-card';
                        card.style.animationDelay = \`\${index * 0.1}s\`;
                        
                        const riskClass = rec.risk_level === 'high' ? 'risk-high' : 
                                          rec.risk_level === 'medium' ? 'risk-medium' : 'risk-low';
                        
                        card.innerHTML = \`
                            <div class="issue-header">
                                <div class="issue-title">\${rec.violation.message || rec.description}</div>
                                <span class="risk-badge \${riskClass}">\${rec.risk_level || 'low'} Risk</span>
                            </div>
                            <div class="issue-desc">\${rec.strategy}: \${rec.command || 'Needs manual intervention'}</div>
                            <button class="fix-button">
                                <span><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" class="btn-icon"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg> Apply Fix</span>
                            </button>
                        \`;
                        card.querySelector('button').onclick = () => {
                            vscode.postMessage({ type: 'fix', value: rec });
                        };
                        listEl.appendChild(card);
                    });
                }
            }
        });
    </script>
</body>
</html>`;
    }
}
exports.DashboardViewProvider = DashboardViewProvider;
DashboardViewProvider.viewType = 'devready.dashboard';
//# sourceMappingURL=DashboardView.js.map