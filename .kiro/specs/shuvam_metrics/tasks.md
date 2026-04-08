# Implementation Plan: Metrics & Visualisation (The Lens)

## Overview

The Lens is implemented as a FastAPI router plugin + Textual widgets + Typer sub-app. It mounts into The Architect's daemon and The Face's CLI with minimal integration surface. Build order: models → aggregator (pure logic) → contract → router → widgets → CLI.

## Tasks

- [ ] 1. Project structure and shared dependencies
  - Create `devready/lens/` directory with `__init__.py`
  - Add `devready.lens` to the existing `pyproject.toml` — no new packages needed (httpx, textual, pydantic, pyyaml already declared)
  - Export `router` and `metrics_app` from `devready/lens/__init__.py`
  - _Requirements: 1.1, 1.2_

- [ ] 2. Pydantic response models (`devready/lens/models.py`)
  - Implement `HealthTrendEntry`, `HealthTrendSummary`, `HealthTrendResponse`
  - Implement `IssueEntry`, `TopIssuesResponse`
  - Implement `TimeSavedBreakdownEntry`, `TimeSavedResponse`
  - Implement `ComplianceResponse`
  - All models include `api_version: str = "v1"` field
  - _Requirements: 1.7, 2.1, 3.1, 4.4, 5.1_

- [ ] 3. Pure aggregation functions (`devready/lens/aggregator.py`)
  - Implement `compute_health_trend(snapshots, days) -> HealthTrendResult`
  - Implement `compute_top_issues(violations, limit) -> list[IssueEntry]`
  - Implement `compute_time_saved(snapshots) -> TimeSavedResult` with fixed estimation table
  - Implement `compute_compliance(snapshots, threshold) -> ComplianceResult`
  - Implement `_trend_direction(current, week_ago) -> str`
  - Implement fix-event detection: violation in snapshot[N] absent in snapshot[N+1]
  - _Requirements: 2.3, 2.4, 3.2, 4.2, 4.3, 5.3_

- [ ] 4. Unit tests for aggregator (`tests/lens/unit/test_aggregator.py`)
  - Test empty snapshot list → all zero/null results
  - Test single snapshot → trend_direction = "stable"
  - Test fix-event detection across consecutive snapshots
  - Test compliance_score = 100 when all snapshots health_score >= 90
  - Test time-saved estimation table values
  - _Requirements: 2.5, 4.5, 5.3_

- [ ] 5. `.devready.yml` contract (`devready/lens/contract.py`)
  - Define `EnvContract` Pydantic model matching the file format
  - Implement `load_contract(project_path: str) -> EnvContract`
  - Implement `contract_to_team_policy(contract: EnvContract) -> TeamPolicy` — imports `TeamPolicy` from `devready.daemon.models`
  - Implement `validate_snapshot_against_contract(snapshot, contract) -> list[PolicyViolation]` — imports `PolicyViolation` from `devready.daemon.models`
  - Raise `ContractParseError` (subclass of `ValueError`) on malformed YAML
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.9_

- [ ] 6. Unit tests for contract (`tests/lens/unit/test_contract.py`)
  - Test valid `.devready.yml` parses correctly
  - Test malformed YAML raises `ContractParseError`
  - Test `contract_to_team_policy` produces valid `TeamPolicy`
  - Test missing `.devready.yml` raises `FileNotFoundError`
  - _Requirements: 6.5, 6.8_

- [ ] 7. Analytics FastAPI router (`devready/lens/router.py`)
  - Implement `GET /api/v1/analytics/trends/health` → calls `compute_health_trend`
  - Implement `GET /api/v1/analytics/issues/top` → calls `compute_top_issues`
  - Implement `GET /api/v1/analytics/time-saved` → calls `compute_time_saved`
  - Implement `GET /api/v1/analytics/compliance` → calls `compute_compliance`, loads contract if present
  - Implement `GET /api/v1/analytics/contract` → calls `load_contract`, returns 404 if missing
  - Implement `POST /api/v1/analytics/contract/validate` → loads snapshot via `get_session`, validates against contract
  - All handlers use `Depends(get_session)` from `devready.daemon.database`
  - All error responses use `{error_code, message, details}` format
  - _Requirements: 1.1, 1.3, 1.4, 1.6, 2.1, 3.1, 4.1, 5.1, 6.6, 6.7_

- [ ] 8. Integration tests for router (`tests/lens/integration/test_router.py`)
  - Use FastAPI `TestClient` with in-memory SQLite (same pattern as The Architect's tests)
  - Test each endpoint returns correct shape with seeded snapshot data
  - Test 404 on missing contract
  - Test 400 on malformed contract in `validate` endpoint
  - _Requirements: 1.6, 2.5, 5.5, 6.8_

- [ ] 9. Textual widgets (`devready/lens/widgets/`)
  - Implement `HealthTrendWidget` — ASCII sparkline using `▁▂▃▄▅▆▇█` characters
  - Implement `TopIssuesWidget` — ranked list with violation counts
  - Implement `TimeSavedWidget` — single counter display
  - Implement `ComplianceWidget` — percentage bar
  - All widgets: `daemon_url` + `project_path` constructor params, 60s auto-refresh, loading/error states, async httpx fetch
  - Export all four from `devready/lens/widgets/__init__.py`
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

- [ ] 10. Typer CLI sub-app (`devready/lens/cli.py`)
  - Implement `metrics_app = typer.Typer(...)`
  - Implement default `metrics()` command: 7-day sparkline, top 3 issues, time saved, compliance score
  - Implement `--full` flag: 30-day trend, top 10 issues, full breakdown
  - Implement `--json` flag: single JSON object to stdout
  - Implement `--project` option: scopes all metrics to a project path
  - Use Rich `Console` for output — same style as The Face
  - Exit code 1 when daemon unreachable
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 11. Checkpoint — verify integration surface
  - Confirm `from devready.lens import router, metrics_app` works
  - Confirm `from devready.lens.widgets import HealthTrendWidget, TopIssuesWidget, TimeSavedWidget, ComplianceWidget` works
  - Confirm `from devready.daemon.models import TeamPolicy, PolicyViolation` is importable (dependency on Shuvam's work)
  - Confirm `from devready.daemon.database import get_session` is importable (dependency on Shuvam's work)
  - Document any import that depends on a teammate's code with a `# DEPENDS: shuvam/architect` comment

## Notes

- Tasks 3 and 5 have zero dependencies on teammates — build and test these first
- Tasks 7–10 depend on Shuvam's `get_session`, `EnvironmentSnapshot`, `TeamPolicy`, `PolicyViolation` exports — use `TYPE_CHECKING` guards and mock these in tests until his code is merged
- The Lens never writes to the DB — if a test needs snapshot data, seed it using The Architect's `db_operations.insert_snapshot()` or directly via SQLModel in test fixtures
- Widget tests can use `httpx.MockTransport` to avoid needing a live daemon
