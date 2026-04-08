# Implementation Plan: Core API & Data State (Architect)

## Overview

This implementation plan covers the development of the Architect component - a FastAPI daemon server that provides the foundational API and data state management for DevReady CLI. The implementation follows a bottom-up approach: data models → database layer → business logic → API endpoints → WebSocket → configuration → testing.

The component will be implemented in Python using FastAPI, Pydantic, SQLModel, and SQLite, with comprehensive unit and property-based testing using Hypothesis.

## Tasks

- [x] 1. Project setup and dependencies
  - Create project directory structure: `devready/daemon/`
  - Set up `pyproject.toml` with dependencies: FastAPI 0.110+, Pydantic 2.6+, SQLModel 0.0.16+, uvicorn, aiosqlite, PyYAML 6.0+, psutil
  - Configure development dependencies: pytest, hypothesis, pytest-asyncio, httpx, ruff, mypy
  - Create `.gitignore` for Python project
  - Initialize Git repository on branch `unichronicles39/feature-architect-core-api`
  - _Requirements: All (foundation for implementation)_

- [x] 2. Implement Pydantic data models
  - [x] 2.1 Create core data models module (`devready/daemon/models.py`)
    - Implement `ToolVersion` model with fields: name, version, path, manager (frozen=True)
    - Implement `EnvironmentSnapshot` SQLModel with fields: id, timestamp, project_path, project_name, tools, dependencies, env_vars, health_score, scan_duration_seconds
    - Implement `DriftReport` model with fields: snapshot_a_id, snapshot_b_id, timestamp, added_tools, removed_tools, version_changes, drift_score
    - Implement `VersionChange` model with fields: tool_name, old_version, new_version, severity
    - Implement `TeamPolicy` model with fields: required_tools, forbidden_tools, version_constraints, env_var_requirements
    - Implement `ToolRequirement` and `EnvVarRequirement` models
    - Implement `PolicyViolation` model with fields: violation_type, tool_or_var_name, expected, actual, severity, message
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x]* 2.2 Write property test for data model serialization
    - **Property 6: Model Serialization Round-Trip**
    - **Validates: Requirements 2.7**
    - Test that all models can serialize to JSON and deserialize back to equivalent objects

  - [x]* 2.3 Write property test for model validation
    - **Property 5: Invalid Model Data Raises Validation Errors**
    - **Validates: Requirements 2.5**
    - Test that invalid data raises validation errors with field details

- [x] 3. Implement database layer with SQLModel
  - [x] 3.1 Create database module (`devready/daemon/database.py`)
    - Implement async SQLite engine creation with aiosqlite
    - Implement `get_session()` dependency injection function
    - Implement `init_db()` function to create tables on startup
    - Create indexes for project_path and timestamp fields
    - Implement connection pooling configuration
    - _Requirements: 3.1, 3.2_

  - [x] 3.2 Create database operations module (`devready/daemon/db_operations.py`)
    - Implement `insert_snapshot()` with automatic timestamp generation
    - Implement `get_snapshot_by_id()` query
    - Implement `list_snapshots()` with project_path filter, pagination
    - Implement `get_latest_snapshot()` for project_path
    - Implement `delete_snapshot()` operation
    - Implement `delete_old_snapshots()` with retention period
    - Add retry logic for database lock errors (3 attempts, exponential backoff)
    - _Requirements: 3.3, 3.4, 3.5, 3.6, 3.8_

  - [x]* 3.3 Write property test for snapshot CRUD operations
    - **Property 10: Snapshot Creation and Retrieval Round-Trip**
    - **Validates: Requirements 4.1, 4.2**
    - Test that creating and retrieving snapshots preserves data integrity

  - [x]* 3.4 Write unit tests for database error handling
    - Test database lock retry logic
    - Test error logging on database failures
    - _Requirements: 3.8_

- [x] 4. Implement configuration management
  - [x] 4.1 Create configuration module (`devready/daemon/config.py`)
    - Implement `ConfigManager` class to load from `~/.devready/config.yaml`
    - Define default configuration values (port: 8443, retention_days: 90, log_level: INFO)
    - Implement configuration validation with allowed ranges
    - Implement environment variable overrides (DEVREADY_PORT, etc.)
    - Create default config file if missing
    - Handle invalid YAML gracefully with fallback to defaults
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

  - [x]* 4.2 Write property test for configuration validation
    - **Property 32: Config Validation Enforces Ranges**
    - **Validates: Requirements 9.8**
    - Test that invalid config values are rejected or use defaults

  - [x]* 4.3 Write unit tests for config file handling
    - Test default config creation
    - Test invalid YAML handling
    - _Requirements: 9.6, 9.7_

- [x] 5. Implement logging system
  - [x] 5.1 Create logging module (`devready/daemon/logging_config.py`)
    - Configure Python logging with rotating file handler
    - Set log file path to `~/.devready/logs/daemon.log`
    - Implement log rotation (max 10 MB, keep 5 files)
    - Define log format with timestamp, level, module, message
    - Implement log level configuration from config file
    - Add sensitive data redaction for env vars, tokens, passwords
    - _Requirements: 1.7, 10.2, 10.3, 10.4, 10.6, 15.7_

  - [x]* 5.2 Write unit tests for logging
    - Test log rotation at size threshold
    - Test sensitive data redaction
    - _Requirements: 10.3, 15.7_

- [x] 6. Implement project context detection
  - [x] 6.1 Create context detector module (`devready/daemon/context.py`)
    - Implement `ContextDetector` class with `detect_project_context()` method
    - Search upward for project markers: .git, pyproject.toml, package.json, Cargo.toml, go.mod, pom.xml
    - Extract project name from Git remote, package manifest, or directory name
    - Implement caching to avoid repeated filesystem scans
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x]* 6.2 Write property test for project context detection
    - **Property 42: Working Directory Parameter Used**
    - **Property 43: Project Root Detection**
    - **Validates: Requirements 13.1, 13.3**
    - Test that project markers are correctly identified

  - [x]* 6.3 Write unit tests for project name extraction
    - Test extraction from various manifest formats
    - Test fallback to directory name
    - _Requirements: 13.4_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement business logic services
  - [x] 8.1 Create snapshot service (`devready/daemon/services/snapshot_service.py`)
    - Implement `SnapshotService` class with async methods
    - Implement `create_snapshot()` with context detection and health score calculation
    - Implement `get_snapshot()` by ID
    - Implement `list_snapshots()` with filtering and pagination
    - Implement `get_latest_snapshot()` for project
    - Implement `delete_snapshot()` operation
    - Implement `cleanup_old_snapshots()` with retention period
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 3.6_

  - [x] 8.2 Create health score calculator (`devready/daemon/services/health_calculator.py`)
    - Implement `HealthScoreCalculator` class
    - Implement scoring algorithm: start at 100, deduct for violations
    - Deduct 10 points per missing required tool
    - Deduct 5 points per version mismatch
    - Deduct 3 points per CVE-affected dependency
    - Deduct 2 points per missing env var
    - Implement baseline score calculation without policy
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [x]* 8.3 Write property test for health score calculation
    - **Property 21: Health Score Within Valid Range**
    - **Property 22: Health Score Decreases with Policy Violations**
    - **Property 23: Perfect Compliance Yields Maximum Score**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
    - Test that health scores are always 0-100 and correlate with violations

  - [x] 8.4 Create drift detection service (`devready/daemon/services/drift_service.py`)
    - Implement `DriftDetectionService` class
    - Implement `compare_snapshots()` to generate DriftReport
    - Identify added tools (in B but not in A)
    - Identify removed tools (in A but not in B)
    - Identify version changes (same tool, different versions)
    - Implement `calculate_drift_score()` based on change magnitude
    - Implement `check_policy_compliance()` to generate PolicyViolations
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x]* 8.5 Write property tests for drift detection
    - **Property 17: Drift Detection Identifies Added Tools**
    - **Property 18: Drift Detection Identifies Removed Tools**
    - **Property 19: Drift Detection Identifies Version Changes**
    - **Property 20: Drift Score Correlates with Changes**
    - **Validates: Requirements 5.3, 5.4, 5.5, 5.6**
    - Test that drift detection correctly identifies all types of changes

  - [x]* 8.6 Write property test for policy compliance
    - **Property 16: Policy Check Returns Violations**
    - **Validates: Requirements 5.2**
    - Test that policy violations are correctly identified

- [x] 9. Implement metrics collection
  - [x] 9.1 Create metrics collector (`devready/daemon/services/metrics_collector.py`)
    - Implement `MetricsCollector` class with background task
    - Collect CPU percentage using psutil
    - Collect memory usage in MB using psutil
    - Track scan count and average duration
    - Store metrics in circular buffer (last 1000 samples)
    - Run collection every 5 seconds
    - Log warnings when CPU > 2% or memory > 150 MB
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.7_

  - [x]* 9.2 Write property test for metrics thresholds
    - **Property 31: Metrics Threshold Warnings**
    - **Validates: Requirements 8.7**
    - Test that warnings are logged when thresholds exceeded

- [x] 10. Implement FastAPI application and REST endpoints
  - [x] 10.1 Create main FastAPI application (`devready/daemon/main.py`)
    - Initialize FastAPI app with title, version, docs URLs
    - Configure CORS middleware for localhost only
    - Add rate limiting middleware (100 requests/minute)
    - Implement startup hook: init database, load config, start metrics
    - Implement shutdown hook: close connections, flush logs
    - _Requirements: 1.1, 1.2, 1.5, 1.8, 15.5, 15.6_

  - [x] 10.2 Create snapshot REST endpoints (`devready/daemon/api/snapshots.py`)
    - Implement POST /api/v1/snapshots (create snapshot, return 201)
    - Implement GET /api/v1/snapshots/{id} (retrieve by ID, return 200 or 404)
    - Implement GET /api/v1/snapshots (list with project_path filter)
    - Implement GET /api/v1/snapshots/latest (get most recent for project)
    - Implement DELETE /api/v1/snapshots/{id} (delete, return 204 or 404)
    - Add request timeout of 30 seconds
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 14.6_

  - [x]* 10.3 Write property test for snapshot endpoints
    - **Property 11: Project Path Filtering**
    - **Property 12: Latest Snapshot Query Correctness**
    - **Property 13: Snapshot Deletion Removes Data**
    - **Property 14: Non-Existent Snapshot Returns 404**
    - **Validates: Requirements 4.3, 4.4, 4.5, 4.6**
    - Test that filtering, latest query, and deletion work correctly

  - [x] 10.4 Create drift REST endpoints (`devready/daemon/api/drift.py`)
    - Implement POST /api/v1/drift/compare (compare two snapshots)
    - Implement POST /api/v1/drift/policy (check policy compliance)
    - Return DriftReport and PolicyViolations respectively
    - _Requirements: 5.1, 5.2_

  - [x]* 10.5 Write property test for drift endpoints
    - **Property 15: Drift Comparison Returns Report**
    - **Validates: Requirements 5.1**
    - Test that drift comparison returns valid reports

  - [x] 10.6 Create metrics and version endpoints (`devready/daemon/api/system.py`)
    - Implement GET /api/v1/metrics (return CPU, memory, scan stats)
    - Implement GET /api/version (return API version, daemon version, build number)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6, 11.3_

  - [x] 10.7 Implement error handling middleware
    - Add exception handler for ValidationError (return 422)
    - Add exception handler for DatabaseError (return 500, log stack trace)
    - Add exception handler for generic exceptions (return 500)
    - Ensure all errors return structured JSON with error_code, message, details
    - Never expose stack traces in API responses
    - _Requirements: 10.1, 10.6, 10.7_

  - [x]* 10.8 Write property tests for error handling
    - **Property 2: Invalid Endpoints Return 404**
    - **Property 33: API Errors Return Structured JSON**
    - **Property 36: API Responses Never Expose Stack Traces**
    - **Property 49: Input Validation Before Processing**
    - **Validates: Requirements 1.6, 10.1, 10.7, 15.2**
    - Test that errors are handled consistently

  - [x]* 10.9 Write property test for API versioning
    - **Property 37: All JSON Responses Include API Version**
    - **Validates: Requirements 11.2**
    - Test that all responses include api_version field

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement WebSocket real-time updates
  - [x] 12.1 Create WebSocket manager (`devready/daemon/websocket/manager.py`)
    - Implement `WebSocketManager` class to manage connections
    - Maintain registry of active connections by project_path
    - Implement `connect()` to register new WebSocket client
    - Implement `disconnect()` to cleanup client connection
    - Implement `broadcast()` to send messages to all clients for a project
    - Handle send failures gracefully (log and continue)
    - _Requirements: 7.1, 7.6, 7.7_

  - [x] 12.2 Create WebSocket endpoint (`devready/daemon/api/websocket.py`)
    - Implement WebSocket endpoint at /ws/scan
    - Accept project_path as query parameter
    - Send progress messages with fields: type, stage, percent_complete, current_tool, message
    - Send completion message with snapshot_id on success
    - Send error message with details on failure
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x]* 12.3 Write property test for WebSocket broadcasts
    - **Property 26: WebSocket Broadcasts to All Clients**
    - **Property 27: Progress Messages Contain Required Fields**
    - **Property 30: WebSocket Disconnect Cleanup**
    - **Validates: Requirements 7.2, 7.3, 7.7**
    - Test that broadcasts reach all clients and cleanup works

  - [x]* 12.4 Write unit tests for WebSocket messages
    - Test completion message format
    - Test error message format
    - _Requirements: 7.4, 7.5_

- [x] 13. Implement database migrations
  - [x] 13.1 Create migration manager (`devready/daemon/migrations/manager.py`)
    - Implement `MigrationManager` class
    - Create schema_migrations table to track version
    - Implement `detect_pending_migrations()` on startup
    - Implement `apply_migrations()` automatically
    - Create database backup before migration
    - Implement rollback on migration failure
    - Log all migration operations with timestamps
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.7_

  - [x] 13.2 Create initial migration (`devready/daemon/migrations/001_initial_schema.py`)
    - Implement `upgrade()` function to create environmentsnapshot table
    - Implement `downgrade()` function to drop table
    - _Requirements: 12.2_

  - [x]* 13.3 Write property tests for migrations
    - **Property 38: Migrations Applied Automatically**
    - **Property 39: Migration Backup Created Before Upgrade**
    - **Property 40: Failed Migration Triggers Rollback**
    - **Property 41: Migration Operations Are Logged**
    - **Validates: Requirements 12.2, 12.3, 12.4, 12.7**
    - Test that migrations work correctly and handle failures

- [x] 14. Implement security and access control
  - [x] 14.1 Add security middleware (`devready/daemon/middleware/security.py`)
    - Implement localhost-only binding check (reject non-127.0.0.1)
    - Implement path sanitization to prevent directory traversal
    - Implement request size limit (10 MB max)
    - Implement rate limiting (100 requests/minute per client)
    - Return 429 when rate limit exceeded
    - _Requirements: 15.1, 15.3, 15.4, 15.5, 15.6_

  - [x]* 14.2 Write property test for security controls
    - **Property 50: Path Sanitization Prevents Traversal**
    - **Validates: Requirements 15.3**
    - Test that directory traversal attempts are blocked

- [x] 15. Implement concurrent request handling
  - [x] 15.1 Configure async request handling in main app
    - Ensure all I/O operations use async/await
    - Implement scan request queue (max 10 concurrent)
    - Return 503 if queue is full
    - Ensure read operations don't block during scans
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [x]* 15.2 Write property test for concurrent requests
    - **Property 47: Scan Requests Queued Sequentially**
    - **Property 48: Non-Blocking Health Checks During Scans**
    - **Validates: Requirements 14.3, 14.5**
    - Test that concurrent requests are handled correctly

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Create comprehensive test suite
  - [x] 17.1 Set up test infrastructure (`tests/conftest.py`)
    - Create pytest fixtures for test database (in-memory SQLite)
    - Create fixture for FastAPI test client
    - Create fixture for WebSocket test client
    - Set up Hypothesis strategies for all data models
    - Configure test logging

  - [x] 17.2 Create Hypothesis strategies (`tests/strategies.py`)
    - Implement `tool_version_strategy()` for ToolVersion generation
    - Implement `snapshot_strategy()` for EnvironmentSnapshot generation
    - Implement `team_policy_strategy()` for TeamPolicy generation
    - Implement `invalid_data_strategy()` for validation testing

  - [x]* 17.3 Write integration tests (`tests/integration/`)
    - Test full scan workflow: request → WebSocket updates → snapshot created → retrieve
    - Test drift detection workflow: baseline → current → compare → verify
    - Test policy compliance workflow: snapshot → policy → check → violations
    - Test migration workflow: old schema → startup → migrations → verify
    - Test multi-client workflow: concurrent clients → all succeed → no corruption

- [x] 18. Performance validation and optimization
  - [x] 18.1 Create performance tests (`tests/performance/`)
  - [x]* 18.2 Run performance tests and validate against requirements

- [x] 19. Documentation and API specification
  - [x] 19.1 Create API documentation
    - Document all REST endpoints with request/response examples
    - Document WebSocket protocol and message formats
    - Document error codes and meanings
    - Document configuration options
    - Create OpenAPI/Swagger documentation (auto-generated by FastAPI)

  - [x] 19.2 Create developer documentation
    - Write README.md with setup instructions
    - Document architecture and component interactions
    - Create CHANGELOG.md for version tracking
    - Document testing strategy and how to run tests

- [x] 20. Git workflow and pull request
  - [x] 20.1 Finalize Git workflow
    - Ensure all code is committed on branch `unichronicles39/feature-architect-core-api`
    - Write comprehensive commit messages
    - Push branch to remote repository
    - Create pull request with description linking to requirements and design docs
    - _Requirements: All (delivery)_

  - [x] 20.2 Pre-PR checklist
    - All tests passing (unit, property, integration, performance)
    - Code linting with ruff passes
    - Type checking with mypy passes
    - Test coverage meets 85% target
    - Documentation is complete
    - No sensitive data in code or logs

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Performance tests validate PRD requirements for startup time, resource usage, and response times
- The implementation uses Python with FastAPI, Pydantic, SQLModel, and SQLite as specified in the design
- All code should follow Python best practices: type hints, docstrings, async/await patterns
- Security is built-in: localhost-only, input validation, rate limiting, path sanitization
- The daemon is designed to be lightweight, fast, and 100% local-first
