import * as http from 'http';

export interface FixRecommendation {
    violation: any;
    strategy: string;
    command?: string;
    description: string;
    risk_level: string;
}

export class ArchitectClient {
    constructor(public baseUrl: string) {}

    public async scan(projectPath: string, scope: string = 'full'): Promise<any> {
        return this.post('/api/v1/scan', { project_path: projectPath, scope });
    }

    public async getLatestSnapshot(projectPath: string): Promise<any> {
        return this.get(`/api/v1/snapshots/latest?project_path=${encodeURIComponent(projectPath)}`);
    }

    public async getVisualizationHtml(snapshotId: string): Promise<string> {
        const url = new URL(`/api/v1/visualize/dependencies/${snapshotId}`, this.baseUrl);
        return new Promise((resolve, reject) => {
            const req = http.get(url, (res) => {
                let body = '';
                res.on('data', (chunk) => body += chunk);
                res.on('end', () => resolve(body));
            });
            req.on('error', (err) => reject(err));
        });
    }

    public async getTeamVisualizationHtml(): Promise<string> {
        const url = new URL(`/api/v1/visualize/team`, this.baseUrl);
        return new Promise((resolve, reject) => {
            const req = http.get(url, (res) => {
                let body = '';
                res.on('data', (chunk) => body += chunk);
                res.on('end', () => resolve(body));
            });
            req.on('error', (err) => reject(err));
        });
    }

    public async getFixRecommendations(snapshotId: string, _policy: any): Promise<FixRecommendation[]> {
        return this.get(`/api/v1/fixes?snapshot_id=${encodeURIComponent(snapshotId)}`);
    }
    }

    public async applyFix(recommendation: FixRecommendation): Promise<any> {
        return this.post('/api/v1/fixes/apply', recommendation);
    }

    private get(path: string): Promise<any> {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseUrl);
            const options = {
                method: 'GET',
            };

            const req = http.request(url, options, (res) => {
                let body = '';
                res.on('data', (chunk) => body += chunk);
                res.on('end', () => {
                    if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                        resolve(JSON.parse(body));
                    } else if (res.statusCode === 404) {
                        resolve(null);
                    } else {
                        reject(new Error(`API Error: ${res.statusCode} - ${body}`));
                    }
                });
            });

            req.on('error', (err) => reject(err));
            req.end();
        });
    }

    private post(path: string, data: any): Promise<any> {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseUrl);
            const body = JSON.stringify(data);
            console.log('[DevReady] POST', url.href, body);
            const options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(body),
                }
            };

            const req = http.request(url, options, (res) => {
                let raw = '';
                res.on('data', (chunk) => raw += chunk);
                res.on('end', () => {
                    console.log('[DevReady] POST', url.href, '->', res.statusCode, raw.slice(0, 200));
                    if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                        resolve(JSON.parse(raw));
                    } else {
                        reject(new Error(`API Error: ${res.statusCode} - ${raw}`));
                    }
                });
            });

            req.on('error', (err) => reject(err));
            req.write(body);
            req.end();
        });
    }
}
