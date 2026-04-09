import { mockSnapshot, mockTeamSummary, mockDriftReport } from './mockData';

export interface Tool {
    name: string;
    version: string;
    path: string;
    manager: string;
    status: 'ok' | 'warning' | 'error';
}

export interface Snapshot {
    health_score: number;
    status: string;
    last_scan: string;
    tools: Tool[];
}

export interface TeamMember {
    name: string;
    score: number;
    status: string;
    last_scan: string;
}

export interface TeamSummary {
    members: TeamMember[];
}

export interface DriftReport {
    drift_score: number;
    version_changes: any[];
    added_tools: any[];
    removed_tools: any[];
}

export class ApiService {
    private baseUrl: string;
    private useMock: boolean = false;

    constructor(baseUrl: string = 'http://localhost:8443') {
        this.baseUrl = baseUrl;
        this.checkDaemon();
    }

    private async checkDaemon() {
        try {
            const resp = await fetch(`${this.baseUrl}/api/version`);
            this.useMock = !resp.ok;
        } catch (e) {
            this.useMock = true;
            console.warn("Daemon not reachable, using mock data.");
        }
    }

    async getLatestSnapshot(): Promise<Snapshot> {
        if (this.useMock) return mockSnapshot;
        const resp = await fetch(`${this.baseUrl}/api/v1/snapshots?limit=1`);
        const data = await resp.json();
        return data[0] || mockSnapshot;
    }

    async getTeamSummary(): Promise<TeamSummary> {
        if (this.useMock) return mockTeamSummary;
        const resp = await fetch(`${this.baseUrl}/api/v1/team/summary`);
        return await resp.json();
    }

    async compareWithMember(name: string): Promise<DriftReport> {
        if (this.useMock) return mockDriftReport;
        const resp = await fetch(`${this.baseUrl}/api/v1/team/compare/${name}`);
        return await resp.json();
    }

    async scan(): Promise<void> {
        if (this.useMock) {
            return new Promise(resolve => setTimeout(resolve, 2000));
        }
        await fetch(`${this.baseUrl}/api/v1/scan`, { method: 'POST' });
    }

    connectWebSocket(onProgress: (p: number) => void, onComplete: () => void) {
        if (this.useMock) return;
        // Using the /ws/scan endpoint as required by the latest daemon version
        const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws/scan';
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'scan_progress') {
                onProgress(data.progress);
            } else if (data.type === 'scan_complete') {
                onComplete();
            }
        };

        ws.onclose = () => {
            setTimeout(() => this.connectWebSocket(onProgress, onComplete), 5000);
        };
    }
}
