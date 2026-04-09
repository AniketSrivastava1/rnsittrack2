import * as vscode from 'vscode';
import { ArchitectClient, PolicyViolation, FixRecommendation } from './ArchitectClient';
import { ProjectRegistry } from './ProjectRegistry';

export class DashboardViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'devready.dashboard';
    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly _client: ArchitectClient,
        private readonly _registry: ProjectRegistry
    ) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
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
                case 'openFile':
                    await this._openConfigFile(data.filename);
                    break;
            }
        });

        this.refresh();
    }

    public async refresh() {
        if (!this._view) { return; }

        const projectPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!projectPath) {
            vscode.window.showErrorMessage('DevReady: No workspace folder open.');
            return;
        }

        try {
            // Load team policy server-side (avoids bundling a YAML parser)
            const teamPolicy = await this._client.getTeamPolicy(projectPath);

            // Run actual scan — passes team policy so AI drift is evaluated
            const snapshot = await this._client.scan(projectPath, 'full', teamPolicy);

            // Persist to machine-wide registry
            this._registry.upsert(snapshot);

            // Get fix recommendations (includes ai_config_drift fixes)
            const recommendations = await this._client.getFixRecommendations(
                snapshot.snapshot_id, teamPolicy
            );

            // Separate AI config drift violations from the scan response
            const aiDriftViolations: PolicyViolation[] = (snapshot.policy_violations ?? [])
                .filter((v: PolicyViolation) => v.violation_type === 'ai_config_drift');

            // Match each AI drift violation to its fix recommendation's manual_steps
            const aiDriftWithFixes = aiDriftViolations.map((v: PolicyViolation) => {
                const fix = recommendations.find(
                    (r: FixRecommendation) => r.violation?.tool_or_var_name === v.tool_or_var_name
                );
                return { ...v, manual_steps: fix?.manual_steps ?? null };
            });

            // Non-AI fixes for the existing "Actionable Fixes" section
            const toolFixes = recommendations.filter(
                (r: FixRecommendation) => r.violation?.violation_type !== 'ai_config_drift'
            );

            this._view.webview.postMessage({
                type: 'update',
                snapshot,
                recommendations: toolFixes,
                aiDriftViolations: aiDriftWithFixes,
            });
        } catch (error: any) {
            this._view.webview.postMessage({
                type: 'update',
                snapshot: { health_score: '--' },
                recommendations: [],
                aiDriftViolations: [],
            });
            const msg = error?.message ?? String(error);
            if (msg.includes('ECONNREFUSED') || msg.includes('connect')) {
                vscode.window.showErrorMessage(
                    'DevReady: Daemon not running. Start it with: uvicorn devready.daemon.main:app --host 127.0.0.1 --port 8443'
                );
            } else {
                vscode.window.showErrorMessage(`DevReady: Scan failed. ${msg}`);
            }
        }
    }

    private async applyFix(recommendation: FixRecommendation) {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Applying Fix: ${recommendation.issue_description}`,
            cancellable: false
        }, async () => {
            try {
                const result = await this._client.applyFix(recommendation);
                if (result?.results?.[0]?.success) {
                    vscode.window.showInformationMessage(result.results[0].message ?? 'Fix applied.');
                    await this.refresh();
                } else {
                    const msg = result?.results?.[0]?.message ?? 'Fix could not be applied.';
                    vscode.window.showErrorMessage(msg);
                }
            } catch (err: any) {
                vscode.window.showErrorMessage(`Fix failed: ${err?.message}`);
            }
        });
    }

    /** Open an AI config file in the editor. Falls back to a search if file doesn't exist. */
    private async _openConfigFile(filename: string) {
        const projectPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!projectPath) { return; }

        // Resolve the file path — strip leading dots/slashes for safety
        const rel = filename.replace(/^\.\//, '');
        const uri = vscode.Uri.joinPath(
            vscode.workspace.workspaceFolders![0].uri,
            rel
        );

        try {
            await vscode.workspace.fs.stat(uri); // throws if not found
            const doc = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(doc, { preview: false });
        } catch {
            vscode.window.showWarningMessage(
                `DevReady: Could not open '${filename}'. Create it to fix the AI config drift.`,
                'Create File'
            ).then(async (choice) => {
                if (choice === 'Create File') {
                    await vscode.workspace.fs.writeFile(uri, Buffer.from('# AI Agent Instructions\n\n'));
                    const doc = await vscode.workspace.openTextDocument(uri);
                    await vscode.window.showTextDocument(doc, { preview: false });
                }
            });
        }
    }

    private _getHtmlForWebview(_webview: vscode.Webview) {
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
            --ai-color: #a78bfa;
            --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        body {
            font-family: var(--font-family);
            padding: 20px;
            color: var(--text-color);
            background: var(--bg-color);
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .header { text-align: center; animation: fadeIn 0.5s ease-out; }

        .title {
            font-size: 1.1rem;
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
        }

        .score-circle {
            width: 130px;
            height: 130px;
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
            font-size: 3rem;
            font-weight: 800;
            z-index: 10;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--card-border);
        }

        /* ── AI Drift Section ─────────────────────────────────── */
        .ai-drift-section { display: none; }
        .ai-drift-section.has-items { display: block; }

        .ai-drift-card {
            background: rgba(167, 139, 250, 0.08);
            border: 1px solid rgba(167, 139, 250, 0.35);
            padding: 14px 16px;
            border-radius: 10px;
            margin-bottom: 10px;
            animation: slideUp 0.35s ease-out forwards;
            opacity: 0;
        }

        .ai-drift-card:hover { background: rgba(167, 139, 250, 0.14); }

        .ai-drift-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }

        .ai-drift-name {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--ai-color);
            font-family: monospace;
        }

        .ai-badge {
            font-size: 0.7rem;
            font-weight: 700;
            padding: 3px 7px;
            border-radius: 10px;
            background: rgba(167, 139, 250, 0.2);
            color: var(--ai-color);
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }

        .ai-drift-msg {
            font-size: 0.85rem;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 10px;
            line-height: 1.4;
        }

        .ai-fix-hint {
            font-size: 0.8rem;
            color: var(--warning-color);
            background: rgba(250, 204, 21, 0.08);
            border-radius: 6px;
            padding: 6px 10px;
            margin-bottom: 10px;
            line-height: 1.4;
        }

        .open-file-btn {
            background: transparent;
            border: 1px solid var(--ai-color);
            color: var(--ai-color);
            padding: 6px 12px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 6px;
            transition: background 0.15s ease;
        }
        .open-file-btn:hover { background: rgba(167, 139, 250, 0.18); }

        /* ── Tool/Env Fix Cards ───────────────────────────────── */
        #issues-list {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .issue-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 14px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            animation: slideUp 0.4s ease-out forwards;
            opacity: 0;
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

        .issue-title { font-weight: 600; font-size: 1rem; line-height: 1.4; }

        .risk-badge {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 7px;
            border-radius: 10px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }

        .risk-high { background: rgba(248,113,113,0.2); color: var(--error-color); }
        .risk-medium { background: rgba(250,204,21,0.2); color: var(--warning-color); }
        .risk-low { background: rgba(74,222,128,0.2); color: var(--success-color); }

        .issue-desc {
            font-size: 0.88rem;
            color: var(--vscode-descriptionForeground);
            line-height: 1.5;
            margin-bottom: 14px;
        }

        .fix-button {
            background: var(--accent-primary);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            font-size: 0.88rem;
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
        .fix-button:hover { background: var(--accent-hover); }
        .fix-button:active { transform: scale(0.98); }

        .loading {
            text-align: center;
            color: var(--vscode-descriptionForeground);
            font-style: italic;
            padding: 20px;
        }

        .all-good {
            text-align: center;
            padding: 28px;
            background: rgba(74,222,128,0.08);
            border-radius: 10px;
            border: 1px dashed var(--success-color);
        }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
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
        <button id="scan-button" class="fix-button"
                style="margin-top: 20px; max-width: 240px; margin-inline: auto;">
            🔍 Scan Environment
        </button>
    </div>

    <!-- AI Agent Config Drift Section -->
    <div class="ai-drift-section" id="ai-drift-section">
        <div class="section-header">
            <span>🤖</span><span>AI Agent Config Drift</span>
        </div>
        <div id="ai-drift-list"></div>
    </div>

    <!-- Tool / Env Fixes Section -->
    <div>
        <div class="section-header">
            <span>🛠️</span><span>Actionable Fixes</span>
        </div>
        <div id="issues-list">
            <div class="loading">Analyzing environment...</div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const scoreEl = document.getElementById('score');
        const scoreCircleEl = document.getElementById('score-circle');
        const listEl = document.getElementById('issues-list');
        const aiDriftSection = document.getElementById('ai-drift-section');
        const aiDriftList = document.getElementById('ai-drift-list');
        const scanBtn = document.getElementById('scan-button');

        scanBtn.onclick = () => {
            listEl.innerHTML = '<div class="loading">Scanning environment...</div>';
            aiDriftList.innerHTML = '';
            aiDriftSection.classList.remove('has-items');
            scanBtn.disabled = true;
            scanBtn.innerText = '⏳ Scanning...';
            vscode.postMessage({ type: 'scan' });
        };

        function updateScoreVisuals(scoreStr) {
            const score = parseInt(scoreStr) || 0;
            const color = score >= 80 ? 'var(--success-color)'
                        : score >= 50 ? 'var(--warning-color)'
                        : 'var(--error-color)';
            scoreEl.style.color = color;
            setTimeout(() => {
                scoreCircleEl.style.background =
                    \`conic-gradient(\${color} \${score}%, var(--card-bg) \${score}%)\`;
            }, 100);
        }

        function renderAiDrift(violations) {
            aiDriftList.innerHTML = '';
            if (!violations || violations.length === 0) {
                aiDriftSection.classList.remove('has-items');
                return;
            }
            aiDriftSection.classList.add('has-items');
            violations.forEach((v, i) => {
                const card = document.createElement('div');
                card.className = 'ai-drift-card';
                card.style.animationDelay = \`\${i * 0.08}s\`;

                // Detect if it's a named agent file or a policy rule
                const isFileViolation = [
                    '.cursorrules', '.github', 'copilot', 'CLAUDE', 'AGENTS',
                    '.codex', 'codex.md', '.windsurfrules', '.aider'
                ].some(kw => v.tool_or_var_name.includes(kw));

                const filename = isFileViolation ? v.tool_or_var_name : null;
                const displayName = v.tool_or_var_name.replace('AI Config: ', '');

                card.innerHTML = \`
                    <div class="ai-drift-header">
                        <span class="ai-drift-name">\${escHtml(displayName)}</span>
                        <span class="ai-badge">AI Drift</span>
                    </div>
                    <div class="ai-drift-msg">\${escHtml(v.message)}</div>
                    \${v.manual_steps ? \`<div class="ai-fix-hint">💡 \${escHtml(v.manual_steps)}</div>\` : ''}
                    \${filename ? \`<button class="open-file-btn" data-file="\${escHtml(filename)}">📂 Open \${escHtml(filename)}</button>\` : ''}
                \`;

                const openBtn = card.querySelector('.open-file-btn');
                if (openBtn) {
                    openBtn.onclick = () => vscode.postMessage({ type: 'openFile', filename: openBtn.dataset.file });
                }
                aiDriftList.appendChild(card);
            });
        }

        function renderToolFixes(recommendations) {
            listEl.innerHTML = '';
            if (!recommendations || recommendations.length === 0) {
                listEl.innerHTML = \`
                    <div class="all-good">
                        <div style="font-size:2rem; margin-bottom:8px">✨</div>
                        <div style="font-weight:600; color:var(--success-color)">All systems go!</div>
                        <div style="font-size:0.88rem; color:var(--vscode-descriptionForeground); margin-top:4px">
                            Your environment complies with all policies.
                        </div>
                    </div>\`;
                return;
            }
            recommendations.forEach((rec, index) => {
                const card = document.createElement('div');
                card.className = 'issue-card';
                card.style.animationDelay = \`\${index * 0.1}s\`;

                const sev = rec.violation?.severity ?? rec.risk_level ?? 'low';
                const riskClass = sev === 'error' || sev === 'high' ? 'risk-high'
                                : sev === 'warning' || sev === 'medium' ? 'risk-medium'
                                : 'risk-low';
                const riskLabel = sev === 'error' ? 'High' : sev === 'warning' ? 'Medium' : 'Low';

                const desc = rec.manual_steps || rec.command || 'Needs manual intervention';

                card.innerHTML = \`
                    <div class="issue-header">
                        <div class="issue-title">\${escHtml(rec.issue_description || rec.description || '')}</div>
                        <span class="risk-badge \${riskClass}">\${riskLabel} Risk</span>
                    </div>
                    <div class="issue-desc">\${escHtml(desc)}</div>
                    \${rec.command ? \`<button class="fix-button"><span>🛠️ Apply Fix</span></button>\` : ''}
                \`;

                const btn = card.querySelector('button');
                if (btn) {
                    btn.onclick = () => vscode.postMessage({ type: 'fix', value: rec });
                }
                listEl.appendChild(card);
            });
        }

        function escHtml(s) {
            return String(s)
                .replace(/&/g,'&amp;').replace(/</g,'&lt;')
                .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        }

        window.addEventListener('message', event => {
            const message = event.data;
            if (message.type === 'update') {
                scanBtn.disabled = false;
                scanBtn.innerText = '🔍 Scan Environment';

                scoreEl.innerText = message.snapshot.health_score;
                updateScoreVisuals(message.snapshot.health_score);

                renderAiDrift(message.aiDriftViolations ?? []);
                renderToolFixes(message.recommendations ?? []);
            }
        });
    </script>
</body>
</html>`;
    }
}
