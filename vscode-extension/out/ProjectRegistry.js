"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProjectRegistry = void 0;
const KEY = 'devready.projectRegistry';
class ProjectRegistry {
    constructor(ctx) {
        this.ctx = ctx;
    }
    getAll() {
        return this.ctx.globalState.get(KEY, []);
    }
    upsert(snapshot) {
        const records = this.getAll();
        const now = new Date().toISOString();
        const idx = records.findIndex(r => r.project_path === snapshot.project_path);
        const entry = {
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
        if (idx >= 0) {
            records[idx] = entry;
        }
        else {
            records.push(entry);
        }
        this.ctx.globalState.update(KEY, records);
    }
}
exports.ProjectRegistry = ProjectRegistry;
//# sourceMappingURL=ProjectRegistry.js.map