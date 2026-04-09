# Requirements Document

## Introduction

The Metrics & Visualisation component (codename: **The Lens**) is the analytics and reporting layer of DevReady. It aggregates historical environment snapshot data stored by The Architect, computes trends and statistics, and exposes both API endpoints and Textual/Rich UI widgets that The Face can embed directly into the interactive dashboard.

The Lens is a pure read layer — it never writes to the database directly. It reads from The Architect's existing SQLite database (via The Architect's own API endpoints) and exposes its own `/api/v1/analytics/*` routes as a FastAPI router that is mounted into The Architect's daemon at startup. This means no separate process, no separate port — The Lens is a plugin router inside the existing daemon.

It also owns the `.devready.yml` environment contract file format — the human-readable, git-committable spec that defines what a team's required environment looks like. The Lens reads this file to power compliance scoring and team-level metrics.

## Glossary

- **Lens**: This component — the analytics and visualisation layer
- **Snapshot_History**: The ordered time-series of Environment_Snapshots for a project
- **Health_Trend**: The sequence of health_score values over time for a project
- **Top_Issues**: The ranked list of most frequently occurring policy violations
- **Time_Saved**: An estimated duration recovered per fix, accumulated over all fixes
- **Compliance_Score**: The percentage of team members whose latest snapshot meets the `.devready.yml` contract
- **Env_Contract**: The `.devready.yml` file committed to a project repo defining required tools and versions
- **Analytics_Router**: The FastAPI APIRouter mounted at /api/v1/analytics inside The Architect's daemon
- **Trend_Widget**: A Textual widget that renders a sparkline of health scores over time
- **Issues_Widget**: A Textual widget that renders a ranked bar chart of top violations
- **TimeSaved_Widget**: A Textual widget that displays cumulative time recovered
- **Compliance_Widget**: A Textual widget that displays team compliance score as a gauge

## Requirements

### Requirement 1: Analytics FastAPI Router

**User Story:** As The Architect daemon, I want to mount the analytics router at startup, so that all analytics endpoints are available on the same localhost:8443 server without a separate process.

#### Acceptance Criteria

1. THE Analytics_Router SHALL be implemented as a FastAPI `APIRouter` with prefix `/api/v1/analytics`
2. THE Analytics_Router SHALL be importable and mountable by The Architect's `main.py` with a single `app.include_router()` call
3. THE Analytics_Router SHALL share The Architect's existing database session dependency (`get_session`) without reimplementing database access
4. THE Analytics_Router SHALL share The Architect's existing logging configuration
5. WHEN The Architect daemon starts, THE Analytics_Router SHALL be available within the same 2-second startup window
6. THE Analytics_Router SHALL follow the same error response format as The Architect: `{error_code, message, details}`
7. THE Analytics_Router SHALL include `api_version` in all JSON responses, consistent with Requirement 11 of The Architect

### Requirement 2: Health Score Trend Endpoint

**User Story:** As a developer, I want to see how my environment health score has changed over time, so that I can understand whether my setup is improving or degrading.

#### Acceptance Criteria

1. WHEN a GET request is sent to `/api/v1/analytics/trends/health` with optional `project_path` and `days` (default: 30) parameters, THE Lens SHALL return a time-ordered list of `{timestamp, health_score, snapshot_id}` entries
2. WHEN `project_path` is omitted, THE Lens SHALL aggregate across all projects and return the average health score per day
3. THE response SHALL include a `summary` object with fields: `current_score`, `score_7d_ago`, `score_30d_ago`, `trend_direction` (one of: "improving", "degrading", "stable")
4. `trend_direction` SHALL be "improving" if current_score > score_7d_ago by more than 2 points, "degrading" if lower by more than 2 points, and "stable" otherwise
5. WHEN no snapshots exist for the requested window, THE Lens SHALL return an empty data list with a 200 response and null summary fields
6. THE endpoint SHALL complete within 500ms for up to 1000 snapshots

### Requirement 3: Top Issues Endpoint

**User Story:** As a developer, I want to know which environment issues recur most often, so that I can prioritise fixing the root cause rather than symptoms.

#### Acceptance Criteria

1. WHEN a GET request is sent to `/api/v1/analytics/issues/top` with optional `project_path` and `days` (default: 30) parameters, THE Lens SHALL return a ranked list of the most frequently occurring policy violations
2. Each entry in the response SHALL include: `violation_type`, `tool_or_var_name`, `count`, `last_seen`, `severity`
3. THE response SHALL be sorted by `count` descending, with a maximum of 20 entries
4. WHEN `project_path` is omitted, THE Lens SHALL aggregate violations across all projects
5. THE endpoint SHALL complete within 500ms for up to 1000 snapshots

### Requirement 4: Time Saved Endpoint

**User Story:** As a developer, I want to see how much debugging time DevReady has saved me, so that I can justify using it and share the impact with my team.

#### Acceptance Criteria

1. WHEN a GET request is sent to `/api/v1/analytics/time-saved`, THE Lens SHALL return a cumulative time-saved estimate in minutes
2. THE time-saved estimate SHALL be computed as: for each fix event recorded in snapshots (a violation present in snapshot N but absent in snapshot N+1), add the estimated debug minutes for that violation type
3. THE Lens SHALL use a fixed estimation table: `missing_tool` = 30 min, `version_mismatch` = 20 min, `missing_env_var` = 25 min, `forbidden_tool` = 10 min
4. THE response SHALL include: `total_minutes_saved`, `total_hours_saved` (rounded to 1 decimal), `fix_count`, `breakdown_by_type` (list of `{violation_type, fix_count, minutes_saved}`)
5. WHEN no fix events are detected, THE Lens SHALL return zeros for all fields with a 200 response
6. THE endpoint SHALL accept an optional `project_path` parameter to scope the calculation

### Requirement 5: Team Compliance Endpoint

**User Story:** As a team lead, I want to see what percentage of my team's machines meet the environment contract, so that I can identify who needs help before it causes incidents.

#### Acceptance Criteria

1. WHEN a GET request is sent to `/api/v1/analytics/compliance` with an optional `project_path` parameter, THE Lens SHALL return a compliance summary
2. THE compliance summary SHALL include: `compliance_score` (0-100), `compliant_count`, `total_count`, `violations_summary` (list of top 5 violations across the team)
3. THE compliance score SHALL be calculated as `(compliant_count / total_count) * 100`, where a machine is "compliant" if its latest snapshot health_score >= 90
4. WHEN no `.devready.yml` contract file is found in the project root, THE Lens SHALL return compliance based on health_score >= 90 as the default threshold and include a `contract_missing: true` field in the response
5. WHEN a `.devready.yml` contract file exists, THE Lens SHALL load it and use its `min_health_score` field (if present) as the compliance threshold instead of the default 90
6. THE endpoint SHALL complete within 500ms

### Requirement 6: `.devready.yml` Environment Contract

**User Story:** As a team, I want to commit a single file to our repository that defines our required environment, so that DevReady can validate every developer's machine against a shared standard.

#### Acceptance Criteria

1. THE Lens SHALL define and own the `.devready.yml` file format as the authoritative environment contract schema
2. THE `.devready.yml` file SHALL support the following top-level fields: `version` (string), `min_health_score` (integer, default: 90), `required_tools` (list), `forbidden_tools` (list), `env_vars` (list)
3. Each entry in `required_tools` SHALL support fields: `name` (required), `min_version` (optional semver string), `max_version` (optional semver string), `allowed_managers` (optional list of strings)
4. Each entry in `env_vars` SHALL support fields: `name` (required), `required` (boolean), `pattern` (optional regex string for value validation)
5. WHEN THE Lens reads a `.devready.yml` file, it SHALL validate it against the schema and return a `400` error with details if the file is malformed
6. THE Lens SHALL expose a `GET /api/v1/analytics/contract` endpoint that reads the `.devready.yml` from the `project_path` query parameter directory and returns the parsed contract as JSON
7. THE Lens SHALL expose a `POST /api/v1/analytics/contract/validate` endpoint that accepts a snapshot_id and validates the snapshot against the contract found in the snapshot's project_path, returning a list of contract violations
8. WHEN no `.devready.yml` is found, THE `GET /api/v1/analytics/contract` endpoint SHALL return HTTP 404 with error_code `CONTRACT_NOT_FOUND`
9. THE `.devready.yml` format SHALL be a strict superset of The Architect's `TeamPolicy` Pydantic model — meaning any valid `.devready.yml` can be deserialized into a `TeamPolicy` instance without data loss

### Requirement 7: Textual Dashboard Widgets

**User Story:** As The Face component, I want to import pre-built Textual widgets from The Lens, so that I can embed analytics panels into the interactive dashboard without reimplementing data fetching or rendering logic.

#### Acceptance Criteria

1. THE Lens SHALL export a `HealthTrendWidget` Textual widget that renders a sparkline of health scores over the last 30 days using data from `/api/v1/analytics/trends/health`
2. THE Lens SHALL export a `TopIssuesWidget` Textual widget that renders a ranked list of top 5 violations using data from `/api/v1/analytics/issues/top`
3. THE Lens SHALL export a `TimeSavedWidget` Textual widget that renders the cumulative time-saved counter using data from `/api/v1/analytics/time-saved`
4. THE Lens SHALL export a `ComplianceWidget` Textual widget that renders the team compliance score as a percentage bar using data from `/api/v1/analytics/compliance`
5. ALL widgets SHALL accept a `daemon_url: str` constructor parameter (default: `"http://localhost:8443"`) and a `project_path: Optional[str]` parameter
6. ALL widgets SHALL fetch data asynchronously using httpx and SHALL NOT block the Textual event loop
7. ALL widgets SHALL display a loading state while data is being fetched and an error state if the daemon is unreachable
8. ALL widgets SHALL auto-refresh every 60 seconds
9. THE widgets module SHALL be importable as `from devready.lens.widgets import HealthTrendWidget, TopIssuesWidget, TimeSavedWidget, ComplianceWidget`

### Requirement 8: `devready metrics` CLI Command

**User Story:** As a developer, I want a single CLI command that shows me all my metrics at once, so that I can get a full picture of my environment health history without opening the dashboard.

#### Acceptance Criteria

1. THE Lens SHALL expose its CLI integration as a Typer sub-application that The Face can mount with `app.add_typer(metrics_app, name="metrics")`
2. WHEN a user runs `devready metrics`, THE CLI SHALL display: current health score trend (last 7 days as ASCII sparkline), top 3 recurring issues, total time saved, and compliance score
3. WHEN a user runs `devready metrics --full`, THE CLI SHALL display the complete 30-day trend, top 10 issues, full time-saved breakdown, and compliance details
4. WHEN a user runs `devready metrics --json`, THE CLI SHALL output all metrics as a single JSON object to stdout
5. THE command SHALL complete within 2 seconds excluding network time
6. WHEN the daemon is unreachable, THE CLI SHALL display a clear error message and exit with code 1
