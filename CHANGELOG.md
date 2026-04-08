# Changelog

## [1.0.0] - 2026-04-08

### Added
- FastAPI daemon server on localhost:8443
- Pydantic/SQLModel data models: ToolVersion, EnvironmentSnapshot, DriftReport, TeamPolicy, PolicyViolation
- Async SQLite database layer with retry logic (3 attempts, exponential backoff)
- Configuration management via ~/.devready/config.yaml with env var overrides
- Rotating file logging with sensitive data redaction
- Project context detection (git, pyproject.toml, package.json, Cargo.toml, go.mod, pom.xml)
- Health score calculator (0-100 based on policy compliance)
- Drift detection service (added/removed/changed tools, drift score)
- Snapshot service with CRUD operations
- Background metrics collector (CPU, memory, scan stats via psutil)
- REST endpoints: POST/GET/DELETE /api/v1/snapshots, POST /api/v1/drift/compare, POST /api/v1/drift/policy, GET /api/v1/metrics, GET /api/version
- WebSocket endpoint at /ws/scan for real-time scan progress
- Rate limiting middleware (100 req/min)
- Security middleware (path sanitization, 10 MB request size limit)
- CORS for localhost origins only
- Database migration manager with backup/rollback
- Initial schema migration (001_initial_schema)
- Comprehensive test suite: unit, property-based (Hypothesis), and integration tests
