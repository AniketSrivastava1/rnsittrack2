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
    constructor(_extensionUri, _client) {
        this._extensionUri = _extensionUri;
        this._client = _client;
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
            }
        });
        this.refresh();
    }
    async refresh() {
        if (!this._view)
            return;
        try {
            const projectPath = vscode.workspace.workspaceFolders?.[0].uri.fsPath || "";
            const snapshot = await this._client.getLatestSnapshot(projectPath);
            if (!snapshot) {
                this._view.webview.postMessage({
                    type: 'update',
                    snapshot: { health_score: '--' },
                    recommendations: []
                });
                return;
            }
            // For now, use a dummy policy or fetch one
            const policy = { required_tools: [], forbidden_tools: [], version_constraints: {}, env_var_requirements: [] };
            const recommendations = await this._client.getFixRecommendations(snapshot.snapshot_id, policy);
            this._view.webview.postMessage({
                type: 'update',
                snapshot: snapshot,
                recommendations: recommendations
            });
        }
        catch (error) {
            vscode.window.showErrorMessage(`DevReady: Refresh failed. ${error}`);
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
            --bg-color: var(--vscode-editor-background);
            --text-color: var(--vscode-editor-foreground);
            --card-bg: var(--vscode-sideBar-background);
            --card-border: var(--vscode-widget-border);
            --accent-primary: var(--vscode-button-background);
            --accent-hover: var(--vscode-button-hoverBackground);
            --success-color: #4ade80;
            --warning-color: #facc15;
            --error-color: #f87171;
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
        }

        .title {
            font-size: 1.2rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 12px;
        }

        .score-container { 
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }

        .score-circle {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            background: conic-gradient(var(--success-color) 0%, var(--card-bg) 0%);
            position: relative;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            transition: background 1s ease-out;
        }

        .score-circle::before {
            content: '';
            position: absolute;
            inset: 8px;
            border-radius: 50%;
            background: var(--bg-color);
        }

        .score { 
            position: relative;
            font-size: 3.5rem; 
            font-weight: 800; 
            z-index: 10;
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
            color: var(--vscode-descriptionForeground);
            line-height: 1.5;
            margin-bottom: 16px;
        }

        .fix-button { 
            background: var(--accent-primary);
            color: var(--vscode-button-foreground);
            border: none; 
            padding: 8px 16px; 
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer; 
            border-radius: 6px;
            width: 100%;
            transition: background 0.2s ease, transform 0.1s ease;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
        }

        .fix-button:hover { 
            background: var(--accent-hover); 
        }

        .fix-button:active {
            transform: scale(0.98);
        }
        
        .loading {
            text-align: center;
            color: var(--vscode-descriptionForeground);
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
    <div class="header">
        <div class="title">Environment Health</div>
        <div class="score-container">
            <div class="score-circle" id="score-circle">
                <div id="score" class="score">--</div>
            </div>
        </div>
        <button id="scan-button" class="fix-button" style="margin-top: 24px; max-width: 250px; margin-inline: auto;">
            🔍 Scan Environment
        </button>
    </div>
    
    <div>
        <div class="section-title">Actionable Fixes</div>
        <div id="issues-list">
            <div class="loading">Analyzing environment...</div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const scoreEl = document.getElementById('score');
        const scoreCircleEl = document.getElementById('score-circle');
        const listEl = document.getElementById('issues-list');
        const scanBtn = document.getElementById('scan-button');

        scanBtn.onclick = () => {
            listEl.innerHTML = '<div class="loading">Scanning environment...</div>';
            scanBtn.disabled = true;
            scanBtn.innerText = '⏳ Scanning...';
            vscode.postMessage({ type: 'scan' });
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
                scanBtn.innerText = '🔍 Scan Environment';
                
                scoreEl.innerText = message.snapshot.health_score;
                updateScoreVisuals(message.snapshot.health_score);
                
                listEl.innerHTML = '';
                
                if (!message.recommendations || message.recommendations.length === 0) {
                    listEl.innerHTML = \`
                        <div style="text-align: center; padding: 32px; background: rgba(74, 222, 128, 0.1); border-radius: 12px; border: 1px dashed var(--success-color);">
                            <div style="font-size: 2rem; margin-bottom: 8px;">✨</div>
                            <div style="font-weight: 600; color: var(--success-color);">All systems go!</div>
                            <div style="font-size: 0.9rem; color: var(--vscode-descriptionForeground); margin-top: 4px;">Your environment complies with all policies.</div>
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
                                <span>🛠️ Apply Fix</span>
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