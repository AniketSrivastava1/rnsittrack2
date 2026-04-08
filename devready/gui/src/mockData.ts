export const mockSnapshot = {
    health_score: 92,
    status: "Healthy",
    last_scan: "2026-04-09T00:45:00Z",
    tools: [
        { name: "python", version: "3.11.5", path: "/usr/bin/python3", manager: "system", status: "ok" },
        { name: "node", version: "20.5.1", path: "/usr/local/bin/node", manager: "nvm", status: "ok" },
        { name: "docker", version: "24.0.6", path: "/usr/bin/docker", manager: "system", status: "ok" },
        { name: "git", version: "2.42.0", path: "/usr/bin/git", manager: "system", status: "ok" },
        { name: "postgresql", version: "15.4", path: "/opt/homebrew/bin/psql", manager: "brew", status: "warning" },
    ]
};

export const mockTeamSummary = {
    members: [
        { name: "Alice", score: 95, status: "Active", last_scan: "2 mins ago" },
        { name: "Bob", score: 82, status: "Away", last_scan: "15 mins ago" },
        { name: "Charlie", score: 68, status: "Active", last_scan: "5 mins ago" },
        { name: "Diana", score: 91, status: "Active", last_scan: "1 min ago" },
    ]
};

export const mockDriftReport = {
    drift_score: 12,
    version_changes: [
        { tool_name: "node", old_version: "20.5.1", new_version: "18.17.0", severity: "medium" }
    ],
    added_tools: [
        { name: "redis", version: "7.2.1" }
    ],
    removed_tools: []
};
