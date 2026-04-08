# Requirements Document

## Introduction

The Architect is the foundational API and data state management component of DevReady CLI. It provides a local FastAPI daemon server that acts as the single source of truth for all environment scanning, snapshot management, and drift detection operations. This component establishes the core data models, persistence layer, and REST/WebSocket endpoints that enable the CLI, VS Code extension, and desktop agent to function cohesively.

The Architect runs as a lightweight background service on localhost:8443, maintaining < 2% CPU and < 150 MB RAM when idle, while supporting sub-8-second full environment scans. It operates 100% offline for core functionality, storing all environment state locally in SQLite.

## Glossary

- **Daemon**: The background FastAPI server process running on localhost:8443
- **Environment_Snapshot**: A point-in-time capture of all detected tools, versions, dependencies, and configurations
- **Drift**: The difference between two Environment_Snapshots or between current state and team policy
- **Scanner_Client**: Any component (CLI, VS Code extension, desktop agent) that communicates with the Daemon
- **Database**: The local SQLite database managed by SQLModel for persistence
- **API_Endpoint**: A REST or WebSocket route exposed by the Daemon
- **Health_Score**: A calculated metric (0-100) representing environment compliance and readiness
- **Team_Policy**: A Pydantic schema defining required tools, versions, and configurations
- **Project_Context**: The current working directory and associated configuration files
- **SBOM**: Software Bill of Materials - a structured inventory of dependencies

## Requirements

### Requirement 1: FastAPI Daemon Server

**User Story:** As a Scanner_Client, I want to communicate with a local API server, so that I can request scans and retrieve environment state without managing the scanning logic myself.

#### Acceptance Criteria

1. THE Daemon SHALL listen on localhost:8443 for HTTP requests
2. WHEN the Daemon starts, THE Daemon SHALL initialize within 2 seconds
3. WHILE the Daemon is idle, THE Daemon SHALL consume less than 2% CPU
4. WHILE the Daemon is idle, THE Daemon SHALL consume less than 150 MB RAM
5. THE Daemon SHALL support graceful shutdown without data loss
6. WHEN a Scanner_Client requests an invalid endpoint, THE Daemon SHALL return HTTP 404 with a descriptive error message
7. THE Daemon SHALL log all requests with timestamps to a local log file
8. THE Daemon SHALL support CORS for localhost origins only

### Requirement 2: Pydantic Data Models

**User Story:** As a developer, I want strongly-typed data models for environment state, so that all components share a consistent schema and validation rules.

#### Acceptance Criteria

1. THE Schema_Validator SHALL define a ToolVersion model with fields: name, version, path, manager
2. THE Schema_Validator SHALL define an EnvironmentSnapshot model with fields: id, timestamp, tools, dependencies, env_vars, health_score, project_path
3. THE Schema_Validator SHALL define a DriftReport model with fields: snapshot_a_id, snapshot_b_id, added_tools, removed_tools, version_changes, timestamp
4. THE Schema_Validator SHALL define a TeamPolicy model with fields: required_tools, forbidden_tools, version_constraints, env_var_requirements
5. WHEN invalid data is provided to any model, THE Schema_Validator SHALL raise a validation error with specific field details
6. THE Schema_Validator SHALL serialize all models to JSON for API responses
7. THE Schema_Validator SHALL deserialize JSON payloads into validated model instances

### Requirement 3: SQLModel Database Layer

**User Story:** As the Daemon, I want to persist environment snapshots and historical data, so that I can support drift detection and trend analysis over time.

#### Acceptance Criteria

1. THE Database SHALL store Environment_Snapshots in a local SQLite file at ~/.devready/state.db
2. WHEN the Daemon starts, THE Database SHALL create all required tables if they do not exist
3. THE Database SHALL support inserting new Environment_Snapshots with automatic timestamp generation
4. THE Database SHALL support querying Environment_Snapshots by id, timestamp range, or project_path
5. THE Database SHALL support retrieving the most recent Environment_Snapshot for a given project_path
6. THE Database SHALL support deleting Environment_Snapshots older than a configurable retention period
7. THE Database SHALL maintain referential integrity between snapshots and drift reports
8. WHEN a database operation fails, THE Database SHALL log the error and return a descriptive error message

### Requirement 4: Environment Snapshot REST Endpoints

**User Story:** As a Scanner_Client, I want to create and retrieve environment snapshots via REST API, so that I can capture and review environment state on demand.

#### Acceptance Criteria

1. WHEN a POST request is sent to /api/v1/snapshots with valid snapshot data, THE Daemon SHALL store the snapshot and return HTTP 201 with the snapshot id
2. WHEN a GET request is sent to /api/v1/snapshots/{id}, THE Daemon SHALL return HTTP 200 with the snapshot data
3. WHEN a GET request is sent to /api/v1/snapshots with query parameter project_path, THE Daemon SHALL return all snapshots for that project
4. WHEN a GET request is sent to /api/v1/snapshots/latest with query parameter project_path, THE Daemon SHALL return the most recent snapshot
5. WHEN a DELETE request is sent to /api/v1/snapshots/{id}, THE Daemon SHALL delete the snapshot and return HTTP 204
6. WHEN a snapshot id does not exist, THE Daemon SHALL return HTTP 404
7. THE Daemon SHALL complete all snapshot operations within 500ms excluding scan time

### Requirement 5: Drift Detection REST Endpoints

**User Story:** As a Scanner_Client, I want to compare environment snapshots and detect drift, so that I can identify changes over time or deviations from team policy.

#### Acceptance Criteria

1. WHEN a POST request is sent to /api/v1/drift/compare with snapshot_a_id and snapshot_b_id, THE Daemon SHALL return a DriftReport
2. WHEN a POST request is sent to /api/v1/drift/policy with snapshot_id and team_policy, THE Daemon SHALL return policy violations
3. THE Drift_Detector SHALL identify added tools not present in the baseline snapshot
4. THE Drift_Detector SHALL identify removed tools present in the baseline but missing in current
5. THE Drift_Detector SHALL identify version changes for tools present in both snapshots
6. THE Drift_Detector SHALL calculate a drift_score representing the magnitude of changes
7. WHEN comparing identical snapshots, THE Drift_Detector SHALL return an empty DriftReport with drift_score of 0

### Requirement 6: Health Score Calculation

**User Story:** As a Scanner_Client, I want a computed health score for each environment snapshot, so that I can quickly assess environment readiness without analyzing raw data.

#### Acceptance Criteria

1. THE Health_Calculator SHALL compute a score from 0 to 100 for each Environment_Snapshot
2. THE Health_Calculator SHALL deduct points for missing required tools defined in Team_Policy
3. THE Health_Calculator SHALL deduct points for version mismatches with Team_Policy
4. THE Health_Calculator SHALL deduct points for outdated dependencies with known CVEs
5. THE Health_Calculator SHALL award full points when all Team_Policy requirements are met
6. WHEN no Team_Policy is provided, THE Health_Calculator SHALL compute a baseline score based on tool freshness
7. THE Health_Calculator SHALL store the computed score in the Environment_Snapshot model

### Requirement 7: WebSocket Real-Time Updates

**User Story:** As a Scanner_Client, I want to receive real-time scan progress updates, so that I can display live feedback during long-running operations.

#### Acceptance Criteria

1. THE Daemon SHALL expose a WebSocket endpoint at /ws/scan
2. WHEN a scan is initiated, THE Daemon SHALL broadcast progress updates to all connected WebSocket clients
3. THE Daemon SHALL send progress messages with fields: stage, percent_complete, current_tool, message
4. WHEN a scan completes, THE Daemon SHALL send a final message with the snapshot_id
5. WHEN a scan fails, THE Daemon SHALL send an error message with details
6. THE Daemon SHALL support multiple concurrent WebSocket connections
7. WHEN a WebSocket client disconnects, THE Daemon SHALL clean up resources without affecting other clients

### Requirement 8: Performance Monitoring Endpoints

**User Story:** As a developer, I want to monitor daemon performance metrics, so that I can verify compliance with PRD performance requirements.

#### Acceptance Criteria

1. WHEN a GET request is sent to /api/v1/metrics, THE Daemon SHALL return current CPU usage percentage
2. WHEN a GET request is sent to /api/v1/metrics, THE Daemon SHALL return current memory usage in MB
3. WHEN a GET request is sent to /api/v1/metrics, THE Daemon SHALL return total scan count since startup
4. WHEN a GET request is sent to /api/v1/metrics, THE Daemon SHALL return average scan duration in seconds
5. THE Daemon SHALL update metrics every 5 seconds
6. THE Daemon SHALL expose metrics in JSON format compatible with monitoring tools
7. WHEN metrics exceed thresholds (2% CPU, 150 MB RAM), THE Daemon SHALL log a warning

### Requirement 9: Configuration Management

**User Story:** As a user, I want to configure daemon behavior via a local config file, so that I can customize retention periods, ports, and logging levels without code changes.

#### Acceptance Criteria

1. THE Daemon SHALL read configuration from ~/.devready/config.yaml on startup
2. THE Config_Manager SHALL support configuring the server port (default: 8443)
3. THE Config_Manager SHALL support configuring snapshot retention days (default: 90)
4. THE Config_Manager SHALL support configuring log level (debug, info, warn, error)
5. THE Config_Manager SHALL support configuring database path (default: ~/.devready/state.db)
6. WHEN the config file does not exist, THE Daemon SHALL create it with default values
7. WHEN the config file contains invalid YAML, THE Daemon SHALL log an error and use default values
8. THE Daemon SHALL validate all configuration values against allowed ranges

### Requirement 10: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error handling and logging, so that I can diagnose issues and ensure system reliability.

#### Acceptance Criteria

1. WHEN any API endpoint encounters an error, THE Daemon SHALL return a JSON error response with fields: error_code, message, details
2. THE Daemon SHALL log all errors to ~/.devready/logs/daemon.log with timestamps
3. THE Daemon SHALL rotate log files when they exceed 10 MB
4. THE Daemon SHALL maintain up to 5 historical log files
5. WHEN the database is locked, THE Daemon SHALL retry operations up to 3 times with exponential backoff
6. WHEN a critical error occurs, THE Daemon SHALL log a stack trace for debugging
7. THE Daemon SHALL never expose internal stack traces in API responses to Scanner_Clients

### Requirement 11: API Versioning and Compatibility

**User Story:** As a Scanner_Client developer, I want API versioning, so that I can rely on stable endpoints while new features are added.

#### Acceptance Criteria

1. THE Daemon SHALL prefix all REST endpoints with /api/v1/
2. THE Daemon SHALL include an API version field in all JSON responses
3. WHEN a GET request is sent to /api/version, THE Daemon SHALL return the current API version and daemon build number
4. THE Daemon SHALL maintain backward compatibility within major versions
5. WHEN breaking changes are required, THE Daemon SHALL increment the major version number
6. THE Daemon SHALL document all endpoint changes in a CHANGELOG.md file
7. THE Daemon SHALL support content negotiation for JSON responses only

### Requirement 12: Database Schema Migrations

**User Story:** As a developer, I want automated database migrations, so that schema changes can be deployed without manual intervention or data loss.

#### Acceptance Criteria

1. THE Migration_Manager SHALL detect schema version mismatches on Daemon startup
2. WHEN a schema upgrade is required, THE Migration_Manager SHALL apply migrations automatically
3. THE Migration_Manager SHALL create a backup of the database before applying migrations
4. WHEN a migration fails, THE Migration_Manager SHALL restore from backup and log the error
5. THE Migration_Manager SHALL store the current schema version in a migrations table
6. THE Migration_Manager SHALL support rollback to the previous schema version
7. THE Migration_Manager SHALL log all migration operations with timestamps

### Requirement 13: Project Context Detection

**User Story:** As a Scanner_Client, I want the Daemon to detect project context automatically, so that snapshots are associated with the correct project without manual specification.

#### Acceptance Criteria

1. WHEN a scan request includes a working_directory parameter, THE Daemon SHALL use it as the Project_Context
2. WHEN no working_directory is provided, THE Daemon SHALL use the current working directory of the Scanner_Client
3. THE Context_Detector SHALL identify the project root by searching for .git, pyproject.toml, package.json, or Cargo.toml
4. THE Context_Detector SHALL extract the project name from the root directory name or package manifest
5. WHEN no project markers are found, THE Context_Detector SHALL use the directory path as the project identifier
6. THE Daemon SHALL store the detected Project_Context in each Environment_Snapshot
7. THE Daemon SHALL support filtering snapshots by Project_Context in query endpoints

### Requirement 14: Concurrent Request Handling

**User Story:** As a Scanner_Client, I want the Daemon to handle multiple concurrent requests, so that multiple clients or operations can run simultaneously without blocking.

#### Acceptance Criteria

1. THE Daemon SHALL support at least 10 concurrent HTTP requests
2. THE Daemon SHALL use async/await patterns for all I/O operations
3. WHEN multiple scan requests arrive simultaneously, THE Daemon SHALL queue them and process sequentially
4. THE Daemon SHALL support concurrent read operations on the Database without locking
5. WHEN a long-running scan is in progress, THE Daemon SHALL continue responding to health check and metrics requests
6. THE Daemon SHALL implement request timeouts of 30 seconds for all endpoints
7. WHEN a request times out, THE Daemon SHALL return HTTP 408 with a timeout message

### Requirement 15: Security and Access Control

**User Story:** As a user, I want the Daemon to be secure by default, so that my environment data is protected from unauthorized access.

#### Acceptance Criteria

1. THE Daemon SHALL bind only to localhost (127.0.0.1) and reject external connections
2. THE Daemon SHALL validate all input data against Pydantic schemas before processing
3. THE Daemon SHALL sanitize all file paths to prevent directory traversal attacks
4. THE Daemon SHALL reject requests with payloads larger than 10 MB
5. THE Daemon SHALL implement rate limiting of 100 requests per minute per client
6. WHEN rate limits are exceeded, THE Daemon SHALL return HTTP 429
7. THE Daemon SHALL never log sensitive data such as environment variable values or API tokens

### Requirement 16: Analytics Data Exposure for Metrics Layer

**User Story:** As the Metrics & Visualisation component, I want to query historical snapshot data in bulk, so that I can compute trends, aggregations, and time-saved estimates without re-implementing database access.

#### Acceptance Criteria

1. WHEN a GET request is sent to /api/v1/snapshots/history with query parameters project_path and days (default: 30), THE Daemon SHALL return all snapshots for that project within the specified time window, ordered by timestamp ascending
2. THE history response SHALL include for each snapshot: id, timestamp, health_score, scan_duration_seconds, tools (name + version only), and a policy_violations_count field
3. WHEN a GET request is sent to /api/v1/snapshots/history without project_path, THE Daemon SHALL return snapshots across all projects within the time window
4. THE Daemon SHALL support a limit query parameter (default: 200, max: 1000) on the history endpoint to prevent oversized responses
5. WHEN a GET request is sent to /api/v1/analytics/violations/summary with an optional project_path and days parameter, THE Daemon SHALL return a list of violation types with their occurrence counts, sorted by count descending
6. THE violations summary response SHALL include fields: violation_type, tool_or_var_name, count, last_seen timestamp
7. THE Daemon SHALL complete history and violations summary queries within 1 second for datasets up to 1000 snapshots
