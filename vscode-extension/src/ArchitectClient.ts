import * as http from 'http';

export interface FixRecommendation {
    violation: any;
    strategy: string;
    command?: string;
    description: string;
    risk_level: string;
}

export class ArchitectClient {
    constructor(private baseUrl: string) {}

    public async getLatestSnapshot(projectPath: string): Promise<any> {
        return this.get(`/api/v1/snapshots/latest?project_path=${encodeURIComponent(projectPath)}`);
    }

    public async getFixRecommendations(snapshotId: string, policy: any): Promise<FixRecommendation[]> {
        return this.post('/api/v1/fixes/recommendations', { snapshot_id: snapshotId, team_policy: policy });
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
            const options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            const req = http.request(url, options, (res) => {
                let body = '';
                res.on('data', (chunk) => body += chunk);
                res.on('end', () => {
                    if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                        resolve(JSON.parse(body));
                    } else {
                        reject(new Error(`API Error: ${res.statusCode} - ${body}`));
                    }
                });
            });

            req.on('error', (err) => reject(err));
            req.write(JSON.stringify(data));
            req.end();
        });
    }
}
