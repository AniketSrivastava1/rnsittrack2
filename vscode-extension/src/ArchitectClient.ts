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
        return this.getRaw(`/api/v1/visualize/dependencies/${snapshotId}`);
    }

    public async getTeamVisualizationHtml(): Promise<string> {
        return this.getRaw(`/api/v1/visualize/team`);
    }

    public async getFixRecommendations(snapshotId: string, _policy: any): Promise<FixRecommendation[]> {
        return this.get(`/api/v1/fixes?snapshot_id=${encodeURIComponent(snapshotId)}`);
    }

    public async applyFix(recommendation: FixRecommendation): Promise<any> {
        return this.post('/api/v1/fixes/apply', recommendation);
    }

    private async getRaw(path: string): Promise<string> {
        return this.withRetry(async () => {
            const url = new URL(path, this.baseUrl);
            return new Promise((resolve, reject) => {
                const req = http.get(url, (res) => {
                    let body = '';
                    res.on('data', (chunk) => body += chunk);
                    res.on('end', () => resolve(body));
                });
                req.on('error', (err) => reject(err));
                req.setTimeout(5000, () => { req.destroy(); reject(new Error('Request timeout')); });
            });
        });
    }

    private async get(path: string): Promise<any> {
        return this.withRetry(async () => {
            return new Promise((resolve, reject) => {
                const url = new URL(path, this.baseUrl);
                const options = { method: 'GET' };

                const req = http.request(url, options, (res) => {
                    let body = '';
                    res.on('data', (chunk) => body += chunk);
                    res.on('end', () => {
                        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                            try { resolve(JSON.parse(body)); } catch (e) { resolve(body); }
                        } else if (res.statusCode === 404) {
                            resolve(null);
                        } else {
                            reject(new Error(`API Error: ${res.statusCode} - ${body}`));
                        }
                    });
                });

                req.on('error', (err) => reject(err));
                req.setTimeout(5000, () => { req.destroy(); reject(new Error('Request timeout')); });
                req.end();
            });
        });
    }

    private async post(path: string, data: any): Promise<any> {
        return this.withRetry(async () => {
            return new Promise((resolve, reject) => {
                const url = new URL(path, this.baseUrl);
                const body = JSON.stringify(data);
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
                        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                            try { resolve(JSON.parse(raw)); } catch (e) { resolve(raw); }
                        } else {
                            reject(new Error(`API Error: ${res.statusCode} - ${raw}`));
                        }
                    });
                });

                req.on('error', (err) => reject(err));
                req.setTimeout(5000, () => { req.destroy(); reject(new Error('Request timeout')); });
                req.write(body);
                req.end();
            });
        });
    }

    private async withRetry<T>(fn: () => Promise<T>, retries: number = 5, delay: number = 1000): Promise<T> {
        let lastError: any;
        for (let i = 0; i < retries; i++) {
            try {
                return await fn();
            } catch (err: any) {
                lastError = err;
                if (err.code === 'ECONNREFUSED' || err.message === 'Request timeout') {
                    console.log(`[DevReady] Connection failed, retrying (${i + 1}/${retries})...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    continue;
                }
                throw err;
            }
        }
        throw lastError;
    }
}

