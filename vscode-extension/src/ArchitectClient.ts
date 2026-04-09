import * as http from 'http';

export interface PolicyViolation {
    violation_type: string;
    tool_or_var_name: string;
    severity: string;
    message: string;
    expected?: string;
    actual?: string;
}

export interface FixRecommendation {
    fix_id: string;
    violation: PolicyViolation;
    issue_description: string;
    command?: string;
    manual_steps?: string;
    confidence: string;
    estimated_minutes: number;
    affects_global: boolean;
    // Legacy fields retained for backward compat
    strategy?: string;
    description?: string;
    risk_level?: string;
}

export class ArchitectClient {
    constructor(private baseUrl: string) {}

    /** Trigger a scan. Passes team_policy if provided so AI drift is checked. */
    public async scan(
        projectPath: string,
        scope: string = 'full',
        teamPolicy?: Record<string, any> | null
    ): Promise<any> {
        const payload: Record<string, any> = { project_path: projectPath, scope };
        if (teamPolicy) {
            payload.team_policy = teamPolicy;
        }
        return this.post('/api/v1/scan', payload);
    }

    /** Load the .devready-team.yaml for a project (parsed server-side). */
    public async getTeamPolicy(projectPath: string): Promise<Record<string, any> | null> {
        try {
            const result = await this.get(
                `/api/v1/team-policy?project_path=${encodeURIComponent(projectPath)}`
            );
            return result && Object.keys(result).length > 0 ? result : null;
        } catch {
            return null;
        }
    }

    public async getLatestSnapshot(projectPath: string): Promise<any> {
        return this.get(`/api/v1/snapshots/latest?project_path=${encodeURIComponent(projectPath)}`);
    }

    public async getFixRecommendations(snapshotId: string, _policy: any): Promise<FixRecommendation[]> {
        return this.get(`/api/v1/fixes?snapshot_id=${encodeURIComponent(snapshotId)}`);
    }

    public async applyFix(recommendation: FixRecommendation): Promise<any> {
        return this.post('/api/v1/fixes/apply', { fix_ids: [recommendation.fix_id] });
    }

    private get(path: string): Promise<any> {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseUrl);
            const req = http.request(url, { method: 'GET' }, (res) => {
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
