import * as vscode from 'vscode';

export interface ProjectRecord {
    project_path: string;
    project_name: string;
    first_scanned: string;
    last_scanned: string;
    last_health_score: number;
    last_snapshot_id: string;
    scan_count: number;
    last_tools: any[];
    last_dependencies: Record<string, string[]>;
    last_policy_violations: any[];
    last_freshness_score: number;
    last_scan_duration_seconds: number;
}

const KEY = 'devready.projectRegistry';

export class ProjectRegistry {
    constructor(private ctx: vscode.ExtensionContext) {}

    getAll(): ProjectRecord[] {
        return this.ctx.globalState.get<ProjectRecord[]>(KEY, []);
    }

    upsert(snapshot: any): void {
        const records = this.getAll();
        const now = new Date().toISOString();
        const idx = records.findIndex(r => r.project_path === snapshot.project_path);
        const entry: ProjectRecord = {
            project_path: snapshot.project_path,
            project_name: snapshot.project_name,
            first_scanned: idx >= 0 ? records[idx].first_scanned : now,
            last_scanned: now,
            last_health_score: snapshot.health_score,
            last_snapshot_id: snapshot.snapshot_id,
            scan_count: idx >= 0 ? records[idx].scan_count + 1 : 1,
            last_tools: snapshot.tools ?? [],
            last_dependencies: snapshot.dependencies ?? {},
            last_policy_violations: snapshot.policy_violations ?? [],
            last_freshness_score: snapshot.freshness_score ?? 100,
            last_scan_duration_seconds: snapshot.scan_duration_seconds ?? 0,
        };
        if (idx >= 0) { records[idx] = entry; } else { records.push(entry); }
        this.ctx.globalState.update(KEY, records);
    }
}
