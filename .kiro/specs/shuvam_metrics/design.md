# Design Document: Metrics & Visualisation (The Lens)

## Overview

The Lens is the analytics and reporting layer of DevReady. It is implemented as a FastAPI `APIRouter` that mounts directly into The Architect's existing daemon — no new process, no new port. It reads historical snapshot data via The Architect's shared database session, computes aggregations in-process, and exposes both REST endpoints and Textual UI widgets.

The Lens also owns the `.devready.yml` environment contract format — the git-committable file that defines a team's required environment. This contract is the input to compliance scoring and is a strict superset of The Architect's `TeamPolicy` Pydantic model, ensuring zero friction when The Architect's drift/policy endpoints consume it.

## Architecture

### Position in the System

```
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Daemon (localhost:8443)          │
│                                                           │
│  ┌─────────────────┐    ┌──────────────────────────────┐ │
│  │  The Architect  │    │       The Lens               │ │
│  │  /api/v1/       │    │  /api/v1/analytics/          │ │
│  │  snapshots      │    │  trends/health               │ │
│  │  drift          │    │  issues/top                  │ │
│  │  metrics        │    │  time-saved                  │ │
│  │  ...            │    │  compliance                  │ │
│  └────────┬────────┘    │  contract                    │ │
│           │             └──────────────┬───────────────┘ │
│           └──────────────────┬─────────┘                 │
│                              │                           │
│                    Shared DB Session                      │
│                    (get_session)                          │
│                              │                           │
│                    ~/.devready/state.db                   │
└─────────────────────────────────────────────────────────┘

         ↑ consumed by
┌────────────────────────────────────────────────────────┐
│                    The Face (CLI + Dashboard)            │
│                                                          │
│  devready metrics          Textual Dashboard             │
│  (Typer sub-app)           ┌──────────┬──────────────┐  │
│                            │ Trend    │ Top Issues   │  │
│                            │ Widget   │ Widget       │  │
│                            ├──────────┼──────────────┤  │
│                            │ Time     │ Compliance   │  │
│                            │ Saved    │ Widget       │  │
│                            └──────────┴──────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Directory Structure

```
devready/
└── lens/
    ├── __init__.py          # exports: router, metrics_app
    ├── router.py            # FastAPI APIRouter — all /api/v1/analytics/* endpoints
    ├── aggregator.py        # pure functions: compute_trends, compute_top_issues, compute_time_saved, compute_compliance
    ├── contract.py          # .devready.yml loader, validator, TeamPolicy converter
    ├── models.py            # Pydantic response models for all analytics endpoints
    ├── cli.py               # Typer sub-app (metrics_app) for `devready metrics`
    └── widgets/
        ├── __init__.py      # exports: HealthTrendWidget, TopIssuesWidget, TimeSavedWidget, ComplianceWidget
        ├── health_trend.py
        ├── top_issues.py
        ├── time_saved.py
        └── compliance.py
```

### Integration Points

**Into The Architect (`devready/daemon/main.py`)** — one line added:
```python
from devready.lens import router as lens_router
app.include_router(lens_router)
```

**Into The Face (`devready/face/cli.py`)** — one line added:
```python
from devready.lens import metrics_app
app.add_typer(metrics_app, name="metrics")
```

**Into The Face dashboard (`devready/face/dashboard.py`)** — four imports:
```python
from devready.lens.widgets import (
    HealthTrendWidget, TopIssuesWidget, TimeSavedWidget, ComplianceWidget
)
```

## Components

### 1. `router.py` — Analytics FastAPI Router

Mounts at `/api/v1/analytics`. All handlers are thin: they call `aggregator.py` functions and return Pydantic response models.

**Endpoints:**

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/analytics/trends/health` | `get_health_trend` | Health score over time |
| GET | `/api/v1/analytics/issues/top` | `get_top_issues` | Most frequent violations |
| GET | `/api/v1/analytics/time-saved` | `get_time_saved` | Cumulative time recovered |
| GET | `/api/v1/analytics/compliance` | `get_compliance` | Team compliance score |
| GET | `/api/v1/analytics/contract` | `get_contract` | Read .devready.yml |
| POST | `/api/v1/analytics/contract/validate` | `validate_contract` | Validate snapshot vs contract |

All endpoints share the same query parameter pattern:
- `project_path: Optional[str] = None`
- `days: int = 30` (where applicable)

All endpoints use `Depends(get_session)` from The Architect — no new DB connection.

### 2. `aggregator.py` — Pure Computation Functions

All functions are pure (no I/O side effects) and take raw snapshot data as input. This makes them trivially testable without a running daemon.

```python
def compute_health_trend(
    snapshots: list[SnapshotRow],
    days: int
) -> HealthTrendResult: ...

def compute_top_issues(
    violations: list[ViolationRow],
    limit: int = 20
) -> list[IssueEntry]: ...

def compute_time_saved(
    snapshots: list[SnapshotRow]
) -> TimeSavedResult: ...

def compute_compliance(
    snapshots: list[SnapshotRow],
    threshold: int = 90
) -> ComplianceResult: ...
```

**Time-saved estimation table** (fixed constants, not configurable):
```python
TIME_SAVED_MINUTES: dict[str, int] = {
    "missing_tool": 30,
    "version_mismatch": 20,
    "missing_env_var": 25,
    "forbidden_tool": 10,
}
```

A "fix event" is detected by comparing consecutive snapshots for the same project: if violation V is present in snapshot[N] but absent in snapshot[N+1], it counts as one fix.

**Trend direction logic:**
```python
def _trend_direction(current: int, week_ago: int) -> str:
    delta = current - week_ago
    if delta > 2: return "improving"
    if delta < -2: return "degrading"
    return "stable"
```

### 3. `contract.py` — `.devready.yml` Contract

**File format** (`.devready.yml`):
```yaml
version: "1.0"
min_health_score: 90

required_tools:
  - name: node
    min_version: "20.0.0"
    allowed_managers: [nvm, mise, asdf]
  - name: python
    min_version: "3.11.0"

forbidden_tools:
  - python2

env_vars:
  - name: DATABASE_URL
    required: true
  - name: API_KEY
    required: true
    pattern: "^[A-Za-z0-9]{32}$"
```

**Key functions:**
```python
def load_contract(project_path: str) -> EnvContract: ...
    # Reads .devready.yml, validates schema, raises ContractParseError if malformed

def contract_to_team_policy(contract: EnvContract) -> TeamPolicy: ...
    # Converts EnvContract → The Architect's TeamPolicy Pydantic model
    # This is the bridge that lets The Architect's /drift/policy endpoint
    # consume a .devready.yml without any changes to The Architect's code

def validate_snapshot_against_contract(
    snapshot: EnvironmentSnapshot,
    contract: EnvContract
) -> list[PolicyViolation]: ...
    # Reuses The Architect's PolicyViolation model directly
```

`EnvContract` is a Pydantic model. Its fields map 1:1 to `TeamPolicy` fields, with `min_health_score` as the only addition. `contract_to_team_policy()` drops `min_health_score` and returns a valid `TeamPolicy`.

### 4. `models.py` — Response Pydantic Models

```python
class HealthTrendEntry(BaseModel):
    timestamp: datetime
    health_score: int
    snapshot_id: str

class HealthTrendSummary(BaseModel):
    current_score: Optional[int]
    score_7d_ago: Optional[int]
    score_30d_ago: Optional[int]
    trend_direction: Optional[Literal["improving", "degrading", "stable"]]

class HealthTrendResponse(BaseModel):
    data: list[HealthTrendEntry]
    summary: HealthTrendSummary
    api_version: str = "v1"

class IssueEntry(BaseModel):
    violation_type: str
    tool_or_var_name: str
    count: int
    last_seen: datetime
    severity: Literal["error", "warning"]

class TopIssuesResponse(BaseModel):
    issues: list[IssueEntry]
    api_version: str = "v1"

class TimeSavedBreakdownEntry(BaseModel):
    violation_type: str
    fix_count: int
    minutes_saved: int

class TimeSavedResponse(BaseModel):
    total_minutes_saved: int
    total_hours_saved: float
    fix_count: int
    breakdown_by_type: list[TimeSavedBreakdownEntry]
    api_version: str = "v1"

class ComplianceResponse(BaseModel):
    compliance_score: float
    compliant_count: int
    total_count: int
    violations_summary: list[IssueEntry]
    contract_missing: bool = False
    api_version: str = "v1"
```

All models use The Architect's existing `PolicyViolation` type where violations are returned — no new violation schema.

### 5. `widgets/` — Textual Widgets

Each widget follows the same pattern:

```python
class HealthTrendWidget(Widget):
    def __init__(self, daemon_url: str = "http://localhost:8443", project_path: Optional[str] = None):
        ...

    def on_mount(self) -> None:
        self.set_interval(60, self.refresh_data)
        self.run_worker(self.fetch_data(), exclusive=True)

    async def fetch_data(self) -> None:
        async with httpx.AsyncClient() as client:
            # fetch from /api/v1/analytics/trends/health
            ...

    def render(self) -> RenderableType:
        # uses Rich's Sparkline or a simple ASCII bar
        ...
```

Widgets have three render states:
- **Loading**: `Text("Loading...", style="dim")`
- **Error**: `Text("⚠ Daemon unreachable", style="red")`
- **Data**: the actual visualisation

The sparkline for `HealthTrendWidget` uses Rich's built-in `rich.progress_bar` or a simple character-based sparkline (`▁▂▃▄▅▆▇█`) — no external charting library needed.

### 6. `cli.py` — Typer Sub-Application

```python
metrics_app = typer.Typer(name="metrics", help="View environment health metrics and trends.")

@metrics_app.callback(invoke_without_command=True)
def metrics(
    full: bool = typer.Option(False, "--full"),
    json_output: bool = typer.Option(False, "--json"),
    project_path: Optional[str] = typer.Option(None, "--project")
): ...
```

Output for `devready metrics` (default):
```
  Health Trend (7d)   ▃▄▅▅▆▇█  87 → 94  ↑ improving
  Top Issues          node version mismatch (×4), missing DATABASE_URL (×2), ...
  Time Saved          3.2 hrs recovered across 9 fixes
  Compliance          92% (11/12 machines compliant)
```

Uses Rich `Console` and `Table` — same as The Face's existing output style.

## Data Flow

### Health Trend Request

```
GET /api/v1/analytics/trends/health?project_path=/my/project&days=30

router.get_health_trend()
  └── session.execute(SELECT id, timestamp, health_score FROM environmentsnapshot
                      WHERE project_path = ? AND timestamp >= ?
                      ORDER BY timestamp ASC)
  └── aggregator.compute_health_trend(rows, days=30)
  └── return HealthTrendResponse
```

### Contract Validation Request

```
POST /api/v1/analytics/contract/validate
Body: { "snapshot_id": "abc123" }

router.validate_contract()
  └── session.get(EnvironmentSnapshot, snapshot_id)       # reuse Architect's model
  └── contract.load_contract(snapshot.project_path)       # read .devready.yml
  └── contract.validate_snapshot_against_contract(...)    # returns [PolicyViolation]
  └── return { violations: [...], api_version: "v1" }
```

## Integration Checklist for Teammates

### For Shuvam (The Architect)
- Add `Requirement 16` to your requirements (already done in your spec — see the updated requirements.md)
- In `main.py`, add two lines:
  ```python
  from devready.lens import router as lens_router
  app.include_router(lens_router)
  ```
- Ensure `get_session` is exported from `devready.daemon.database` (it already is per your design)
- Ensure `EnvironmentSnapshot`, `PolicyViolation`, `TeamPolicy` are exported from `devready.daemon.models` (they already are)
- Add migration `002_analytics_violations_cache.py` (The Lens will provide this file) that adds a `policy_violations` JSON column to `environmentsnapshot` — this is optional for MVP but needed for efficient `issues/top` queries

### For Gowri (The Face)
- In your dashboard Textual app, import and compose the four widgets:
  ```python
  from devready.lens.widgets import (
      HealthTrendWidget, TopIssuesWidget, TimeSavedWidget, ComplianceWidget
  )
  ```
- In your Typer app, mount the metrics sub-app:
  ```python
  from devready.lens import metrics_app
  app.add_typer(metrics_app, name="metrics")
  ```
- No other changes needed — widgets handle their own data fetching

### For Aniket (The Inspector)
- No changes needed. The Lens reads from snapshots that The Inspector populates via The Architect.
- Optional: when The Inspector records a fix event (violation resolved), it can include a `fixes` list in the snapshot payload. The Lens will detect fixes by comparing consecutive snapshots regardless, so this is not required.

### For Reythem (The Operator)
- No changes needed. The Lens is read-only.

## Non-Functional Properties

- **No new process**: The Lens runs inside The Architect's daemon. Zero additional RAM overhead beyond the router and aggregation logic.
- **No new database**: Reads from `~/.devready/state.db` via the shared session. No writes.
- **No new dependencies** beyond what's already in the stack: `httpx` (already used by The Face), `textual` (already used by The Face), `pydantic` (already used by The Architect), `pyyaml` (already used by The Architect).
- **Testable in isolation**: `aggregator.py` functions are pure — unit tests need no database or HTTP server.
- **Graceful degradation**: If no snapshots exist, all endpoints return empty/zero responses with 200 status. Widgets show "No data yet" state.

## Testing Strategy

```
tests/lens/
├── unit/
│   ├── test_aggregator.py       # pure function tests, no DB needed
│   ├── test_contract.py         # .devready.yml parsing and validation
│   └── test_models.py           # Pydantic model serialization
├── integration/
│   ├── test_router.py           # FastAPI TestClient against in-memory DB
│   └── test_widgets.py          # Textual widget rendering with mock data
└── fixtures/
    ├── sample_contract.yml
    └── sample_snapshots.json
```

Key unit test cases for `aggregator.py`:
- Empty snapshot list → all zero/null results
- Single snapshot → trend direction is "stable"
- Violation present in N, absent in N+1 → counted as one fix
- All snapshots health_score >= 90 → compliance_score = 100
