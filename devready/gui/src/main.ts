import { ApiService, Snapshot, TeamSummary, DriftReport } from './api';

class App {
    private api: ApiService;
    private currentTab: string = 'my-env';
    private scanning: boolean = false;

    constructor() {
        this.api = new ApiService();
        this.setupEventListeners();
        this.init();
    }

    private async init() {
        await this.refreshAll();
        this.api.connectWebSocket(
            (progress) => this.updateScanProgress(progress),
            () => {
                this.updateScanProgress(0);
                this.refreshAll();
                this.notify('Scan complete!', 'success');
            }
        );
    }

    private setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.nav-links li').forEach(li => {
            li.addEventListener('click', () => {
                const tab = li.getAttribute('data-tab');
                if (tab) this.switchTab(tab);
            });
        });

        // Search (local filtering)
        const searchInput = document.querySelector('.search-bar input') as HTMLInputElement;
        searchInput?.addEventListener('input', (e) => {
            const query = (e.target as HTMLInputElement).value.toLowerCase();
            this.filterTables(query);
        });

        // Global Actions
        document.getElementById('btn-refresh')?.addEventListener('click', () => this.refreshAll());
        document.getElementById('btn-scan')?.addEventListener('click', () => this.runScan());

        // Modal Close
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        // Outside modal click
        window.addEventListener('click', (e) => {
            if (e.target === document.getElementById('comparison-modal')) {
                this.closeModal();
            }
        });
    }

    private async refreshAll() {
        try {
            const [snapshot, team] = await Promise.all([
                this.api.getLatestSnapshot(),
                this.api.getTeamSummary()
            ]);
            this.renderMyEnv(snapshot);
            this.renderTeamEnv(team);
        } catch (e) {
            this.notify('Failed to refresh data', 'error');
        }
    }

    private switchTab(tabId: string) {
        this.currentTab = tabId;
        
        // UI Update
        document.querySelectorAll('.nav-links li').forEach(li => {
            li.classList.toggle('active', li.getAttribute('data-tab') === tabId);
        });
        
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === tabId);
        });
    }

    private renderMyEnv(snapshot: Snapshot) {
        // Health Score
        const ring = document.getElementById('health-progress') as SVGPathElement;
        const text = document.getElementById('health-score-text');
        const desc = document.getElementById('health-status-desc');
        
        if (ring && text) {
            const score = snapshot.health_score;
            ring.setAttribute('stroke-dasharray', `${score}, 100`);
            text.textContent = `${score}%`;
            
            // Color logic
            ring.classList.remove('green', 'yellow', 'red');
            if (score >= 90) ring.classList.add('green');
            else if (score >= 70) ring.classList.add('yellow');
            else ring.classList.add('red');
        }

        // Table
        const tbody = document.querySelector('#tools-table tbody');
        if (tbody) {
            tbody.innerHTML = snapshot.tools.map(tool => `
                <tr>
                    <td><span class="tool-name">${tool.name}</span></td>
                    <td><span class="version-tag">${tool.version}</span></td>
                    <td>${tool.manager}</td>
                    <td class="text-secondary">${tool.path}</td>
                    <td><span class="status-tag status-${tool.status === 'ok' ? 'ok' : tool.status === 'warning' ? 'warn' : 'error'}">${tool.status}</span></td>
                </tr>
            `).join('');
        }
    }

    private renderTeamEnv(summary: TeamSummary) {
        const tbody = document.querySelector('#team-table tbody');
        if (tbody) {
            tbody.innerHTML = summary.members.map(member => `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--bg-deep); display: flex; align-items: center; justify-content: center; font-weight: bold; border: 1px solid var(--border);">
                                ${member.name[0]}
                            </div>
                            ${member.name}
                        </div>
                    </td>
                    <td>
                        <div style="font-weight: 600; color: ${member.score >= 90 ? 'var(--success)' : member.score >= 70 ? 'var(--warning)' : 'var(--danger)'}">
                            ${member.score}%
                        </div>
                    </td>
                    <td>${100 - member.score}% Divergent</td>
                    <td><span class="status-tag ${member.status === 'Active' ? 'status-ok' : 'status-warn'}">${member.status}</span></td>
                    <td class="text-secondary">${member.last_scan}</td>
                    <td>
                        <button class="btn-secondary btn-sm compare-btn" data-member="${member.name}">Compare</button>
                    </td>
                </tr>
            `).join('');

            // Add events to compare buttons
            tbody.querySelectorAll('.compare-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const memberName = btn.getAttribute('data-member');
                    if (memberName) this.showComparison(memberName);
                });
            });
        }
    }

    private async showComparison(memberName: string) {
        try {
            const report = await this.api.compareWithMember(memberName);
            this.renderComparisonModal(memberName, report);
            document.getElementById('comparison-modal')!.style.display = 'flex';
        } catch (e) {
            this.notify('Comparison failed', 'error');
        }
    }

    private renderComparisonModal(name: string, report: DriftReport) {
        document.getElementById('modal-title')!.textContent = `Comparison: Me vs ${name}`;
        document.getElementById('drift-score-val')!.textContent = report.drift_score.toString();
        
        const tbody = document.querySelector('#comparison-table tbody');
        if (tbody) {
            let html = '';
            
            report.version_changes.forEach(c => {
                html += `
                    <tr>
                        <td>${c.tool_name}</td>
                        <td class="text-secondary">${c.old_version}</td>
                        <td class="text-primary">${c.new_version}</td>
                        <td><span class="status-tag status-warn">Divergent</span></td>
                    </tr>
                `;
            });

            report.added_tools.forEach(t => {
                html += `
                    <tr>
                        <td>${t.name}</td>
                        <td class="text-secondary">Missing</td>
                        <td class="text-primary">${t.version}</td>
                        <td><span class="status-tag status-error">[+] Added</span></td>
                    </tr>
                `;
            });

            tbody.innerHTML = html || '<tr><td colspan="4" style="text-align: center; padding: 40px;">No divergence detected. Environment is perfectly aligned.</td></tr>';
        }
    }

    private closeModal() {
        document.getElementById('comparison-modal')!.style.display = 'none';
    }

    private async runScan() {
        if (this.scanning) return;
        this.scanning = true;
        this.updateScanProgress(10);
        document.getElementById('scan-status-text')!.textContent = 'Scanning...';
        
        try {
            await this.api.scan();
            this.notify('Scan initiated', 'info');
        } catch (e) {
            this.notify('Scan failed to start', 'error');
            this.scanning = false;
            this.updateScanProgress(0);
        }
    }

    private updateScanProgress(percent: number) {
        const bar = document.getElementById('scan-progress-inner');
        const text = document.getElementById('scan-percent');
        const label = document.getElementById('scan-status-text');
        
        if (bar && text && label) {
            bar.style.width = `${percent}%`;
            text.textContent = `${percent}%`;
            if (percent === 0) {
                label.textContent = 'Idle';
                this.scanning = false;
            } else if (percent === 100) {
                label.textContent = 'Complete';
            }
        }
    }

    private filterTables(query: string) {
        const rows = document.querySelectorAll('table tbody tr');
        rows.forEach(row => {
            const text = row.textContent?.toLowerCase() || '';
            (row as HTMLElement).style.display = text.includes(query) ? '' : 'none';
        });
    }

    private notify(message: string, type: 'success' | 'error' | 'info') {
        const area = document.getElementById('notification-area');
        if (!area) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        area.appendChild(toast);

        // Styling via script for quick injection
        Object.assign(toast.style, {
            backgroundColor: type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : 'var(--accent-blue)',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '8px',
            marginBottom: '10px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            animation: 'fadeInRight 0.3s ease'
        });

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Global fade in right animation for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    #notification-area {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 2000;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }
`;
document.head.appendChild(style);

new App();
