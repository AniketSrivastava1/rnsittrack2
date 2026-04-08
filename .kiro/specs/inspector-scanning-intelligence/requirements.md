# Requirements Document

## Introduction

The Inspector is the scanning and intelligence component of DevReady CLI responsible for collecting system state, dependency information, and configuration data. It acts as the data collection layer that feeds The Architect's API with accurate, structured environment information. The Inspector executes local scans using osquery for system state, syft for dependency SBOMs, and custom parsers for AI agent configuration files.

The Inspector operates 100% offline, completing full environment scans in under 8 seconds while supporting multiple tech stacks (Node.js, Python, Go, Rust, Java, etc.). It returns data as dictionaries matching The Architect's Pydantic schemas, ensuring type safety and validation across the system.

## Glossary

- **Inspector**: The scanning and intelligence component responsible for data collection
- **System_Scanner**: The osquery-python wrapper that queries OS-level state
- **Dependency_Scanner**: The syft wrapper that generates Software Bill of Materials
- **Config_Parser**: The component that parses AI agent configuration files
- **Policy_Checker**: The Checkov-based component that validates scanned data against team policies
- **Scan_Result**: A dictionary containing all collected data, conforming to The Architect's EnvironmentSnapshot schema
- **SBOM**: Software Bill of Materials - structured JSON inventory of project dependencies
- **AI_Agent_Config**: Configuration files like CLAUDE.md, .cursorrules, or .copilot that define AI coding assistant behavior
- **Tool_Version**: A detected software tool with name, version, installation path, and package manager
- **Project_Root**: The directory containing project markers (.git, package.json, pyproject.toml, Cargo.toml, go.mod)
- **Tech_Stack**: The detected programming language ecosystem (Node.js, Python, Go, Rust, Java, etc.)

## Requirements

### Requirement 1: System State Scanner with osquery

**User Story:** As The Architect, I want to query system-level state including installed tools, running processes, and open ports, so that I can build a complete environment snapshot.

#### Acceptance Criteria

1. THE System_Scanner SHALL use osquery-python to query installed software packages
2. WHEN querying installed tools, THE System_Scanner SHALL return a list of Tool_Version dictionaries with fields: name, version, path, manager
3. THE System_Scanner SHALL detect package managers including: brew, apt, yum, dnf, pacman, chocolatey, winget, scoop
4. THE System_Scanner SHALL query listening network ports and return port number, process name, and PID
5. THE System_Scanner SHALL detect OS version and architecture (macOS, Windows, Linux; x86_64, arm64)
6. THE System_Scanner SHALL complete system queries within 2 seconds
7. WHEN osquery is not available, THE System_Scanner SHALL log an error and return an empty result set
8. THE System_Scanner SHALL handle osquery errors gracefully without crashing

### Requirement 2: Dependency Scanner with syft

**User Story:** As The Architect, I want to generate Software Bill of Materials for project directories, so that I can track all project-specific dependencies and detect outdated packages.

#### Acceptance Criteria

1. THE Dependency_Scanner SHALL execute syft as a subprocess to generate JSON SBOM output
2. WHEN scanning a project directory, THE Dependency_Scanner SHALL pass the Project_Root path to syft
3. THE Dependency_Scanner SHALL parse syft's JSON output into a structured dictionary
4. THE Dependency_Scanner SHALL extract package name, version, type, and location from SBOM artifacts
5. THE Dependency_Scanner SHALL support multiple package ecosystems: npm, pip, cargo, go modules, maven, gradle
6. THE Dependency_Scanner SHALL complete SBOM generation within 4 seconds for typical projects
7. WHEN syft is not installed, THE Dependency_Scanner SHALL return an error message with installation instructions
8. WHEN syft execution fails, THE Dependency_Scanner SHALL capture stderr and return it in the error details

### Requirement 3: AI Agent Configuration Parser

**User Story:** As The Architect, I want to parse AI agent configuration files and extract their settings, so that I can detect drift from team standards and identify security risks.

#### Acceptance Criteria

1. THE Config_Parser SHALL search for AI agent config files: CLAUDE.md, .cursorrules, .copilot, AGENTS.md, .aider.conf.yml
2. WHEN a config file is found, THE Config_Parser SHALL parse its contents and extract key-value settings
3. THE Config_Parser SHALL identify referenced dependencies, API endpoints, and custom instructions
4. THE Config_Parser SHALL detect model names, temperature settings, and context window configurations
5. THE Config_Parser SHALL return a dictionary with fields: file_path, agent_type, settings, dependencies, last_modified
6. WHEN multiple config files exist, THE Config_Parser SHALL parse all and return a list
7. WHEN no config files are found, THE Config_Parser SHALL return an empty list
8. THE Config_Parser SHALL handle malformed config files and log parsing errors without crashing

### Requirement 4: Project Root Detection

**User Story:** As The Inspector, I want to automatically detect the project root directory, so that scans are scoped correctly without requiring manual path specification.

#### Acceptance Criteria

1. THE Root_Detector SHALL search for project markers: .git, package.json, pyproject.toml, Cargo.toml, go.mod, pom.xml, build.gradle
2. WHEN multiple markers exist, THE Root_Detector SHALL use .git as the highest priority indicator
3. THE Root_Detector SHALL traverse up the directory tree from the current working directory until a marker is found
4. WHEN no markers are found within 10 parent directories, THE Root_Detector SHALL use the current working directory
5. THE Root_Detector SHALL return the absolute path to the detected Project_Root
6. THE Root_Detector SHALL extract the project name from the root directory name or primary package manifest
7. THE Root_Detector SHALL complete detection within 100ms

### Requirement 5: Tech Stack Detection

**User Story:** As The Inspector, I want to identify the programming language ecosystem of a project, so that I can apply stack-specific scanning logic and validation rules.

#### Acceptance Criteria

1. THE Stack_Detector SHALL identify Node.js projects by presence of package.json or node_modules
2. THE Stack_Detector SHALL identify Python projects by presence of pyproject.toml, setup.py, requirements.txt, or Pipfile
3. THE Stack_Detector SHALL identify Go projects by presence of go.mod or go.sum
4. THE Stack_Detector SHALL identify Rust projects by presence of Cargo.toml or Cargo.lock
5. THE Stack_Detector SHALL identify Java projects by presence of pom.xml, build.gradle, or build.gradle.kts
6. THE Stack_Detector SHALL support detecting multiple stacks in monorepo projects
7. WHEN no stack markers are found, THE Stack_Detector SHALL return "unknown" as the Tech_Stack

### Requirement 6: Policy Validation with Checkov

**User Story:** As The Architect, I want to validate scanned data against team policies, so that I can identify compliance violations and security risks.

#### Acceptance Criteria

1. THE Policy_Checker SHALL accept a Team_Policy dictionary and a Scan_Result dictionary as inputs
2. THE Policy_Checker SHALL validate that all required tools from Team_Policy are present in Scan_Result
3. THE Policy_Checker SHALL validate that tool versions meet Team_Policy version constraints
4. THE Policy_Checker SHALL identify forbidden tools present in Scan_Result
5. THE Policy_Checker SHALL check dependencies against known CVE databases for security vulnerabilities
6. THE Policy_Checker SHALL return a list of violations with fields: rule_id, severity, message, affected_component
7. WHEN no violations are found, THE Policy_Checker SHALL return an empty violations list

### Requirement 7: Scan Orchestration and Result Assembly

**User Story:** As The Architect, I want a single scan function that orchestrates all scanning components and returns a complete Scan_Result, so that I can trigger comprehensive scans with one call.

#### Acceptance Criteria

1. THE Scan_Orchestrator SHALL execute System_Scanner, Dependency_Scanner, Config_Parser, and Stack_Detector in parallel
2. THE Scan_Orchestrator SHALL assemble results into a dictionary matching The Architect's EnvironmentSnapshot schema
3. THE Scan_Orchestrator SHALL include fields: timestamp, tools, dependencies, env_vars, project_path, tech_stack, ai_configs
4. THE Scan_Orchestrator SHALL complete full scans within 8 seconds
5. WHEN any scanner component fails, THE Scan_Orchestrator SHALL include partial results and log the failure
6. THE Scan_Orchestrator SHALL accept an optional project_path parameter to override automatic detection
7. THE Scan_Orchestrator SHALL return scan duration in milliseconds as metadata

### Requirement 8: Environment Variable Collection

**User Story:** As The Architect, I want to collect relevant environment variables, so that I can detect missing or misconfigured variables required by the project.

#### Acceptance Criteria

1. THE Env_Collector SHALL read environment variables from the current process environment
2. THE Env_Collector SHALL filter variables to include only development-relevant keys: PATH, NODE_ENV, PYTHON_PATH, GOPATH, CARGO_HOME, JAVA_HOME
3. THE Env_Collector SHALL redact sensitive values containing: token, key, secret, password, api
4. THE Env_Collector SHALL return a dictionary of variable names to values (or "[REDACTED]" for sensitive ones)
5. THE Env_Collector SHALL detect .env files in the Project_Root and parse their contents
6. WHEN .env files contain syntax errors, THE Env_Collector SHALL log a warning and skip malformed lines
7. THE Env_Collector SHALL never log or return actual sensitive values

### Requirement 9: Installed Tool Version Detection

**User Story:** As The Architect, I want to detect versions of common development tools, so that I can verify they meet project requirements.

#### Acceptance Criteria

1. THE Tool_Detector SHALL execute version commands for common tools: node, python, go, rustc, java, docker, git
2. WHEN executing version commands, THE Tool_Detector SHALL parse stdout to extract semantic version numbers
3. THE Tool_Detector SHALL handle tools not in PATH by returning null for version
4. THE Tool_Detector SHALL detect version managers: nvm, pyenv, asdf, mise, rustup, sdkman
5. THE Tool_Detector SHALL identify which version manager controls each detected tool
6. THE Tool_Detector SHALL complete tool detection within 3 seconds
7. WHEN a tool command hangs, THE Tool_Detector SHALL timeout after 1 second and mark the tool as unresponsive

### Requirement 10: Dependency Freshness Analysis

**User Story:** As The Architect, I want to identify outdated dependencies, so that I can recommend updates and flag security risks.

#### Acceptance Criteria

1. THE Freshness_Analyzer SHALL compare detected dependency versions against latest stable versions
2. THE Freshness_Analyzer SHALL categorize dependencies as: current, minor_update_available, major_update_available, deprecated
3. THE Freshness_Analyzer SHALL identify dependencies with known security vulnerabilities
4. THE Freshness_Analyzer SHALL return a freshness_score from 0 to 100 based on update recency
5. THE Freshness_Analyzer SHALL use local caching to avoid repeated network requests for version lookups
6. WHEN operating offline, THE Freshness_Analyzer SHALL use cached data and mark results as potentially stale
7. THE Freshness_Analyzer SHALL complete analysis within 2 seconds using cached data

### Requirement 11: Parser for CLAUDE.md and .cursorrules

**User Story:** As The Architect, I want to parse CLAUDE.md and .cursorrules files specifically, so that I can extract AI agent instructions and detect configuration drift.

#### Acceptance Criteria

1. THE AI_Parser SHALL parse CLAUDE.md files and extract markdown sections as structured data
2. THE AI_Parser SHALL parse .cursorrules files and extract JSON or YAML configuration
3. THE AI_Parser SHALL identify custom instructions, system prompts, and tool configurations
4. THE AI_Parser SHALL extract referenced file paths, API endpoints, and external dependencies
5. THE AI_Parser SHALL detect model preferences and parameter settings (temperature, max_tokens, etc.)
6. THE AI_Parser SHALL return a normalized dictionary regardless of source file format
7. WHEN both CLAUDE.md and .cursorrules exist, THE AI_Parser SHALL merge their configurations with .cursorrules taking precedence

### Requirement 12: Subprocess Execution Wrapper

**User Story:** As The Inspector, I want a safe subprocess wrapper for executing external tools, so that I can handle errors, timeouts, and output parsing consistently.

#### Acceptance Criteria

1. THE Subprocess_Wrapper SHALL execute commands with configurable timeout (default: 5 seconds)
2. THE Subprocess_Wrapper SHALL capture both stdout and stderr
3. THE Subprocess_Wrapper SHALL return exit code, stdout, stderr, and execution duration
4. WHEN a command times out, THE Subprocess_Wrapper SHALL terminate the process and return a timeout error
5. WHEN a command fails, THE Subprocess_Wrapper SHALL include stderr in the error details
6. THE Subprocess_Wrapper SHALL sanitize command arguments to prevent shell injection
7. THE Subprocess_Wrapper SHALL log all executed commands for debugging purposes

### Requirement 13: Scan Result Validation

**User Story:** As The Inspector, I want to validate scan results against The Architect's schemas before returning them, so that I catch data quality issues early.

#### Acceptance Criteria

1. THE Result_Validator SHALL validate Scan_Result dictionaries against The Architect's EnvironmentSnapshot Pydantic model
2. WHEN validation fails, THE Result_Validator SHALL return detailed error messages indicating which fields are invalid
3. THE Result_Validator SHALL coerce compatible types (e.g., string to int) when possible
4. THE Result_Validator SHALL reject results with missing required fields
5. THE Result_Validator SHALL validate that timestamps are in ISO 8601 format
6. THE Result_Validator SHALL validate that version strings follow semantic versioning
7. WHEN validation succeeds, THE Result_Validator SHALL return the validated dictionary

### Requirement 14: Incremental Scanning Support

**User Story:** As The Architect, I want to perform incremental scans that only check specific components, so that I can optimize scan performance for targeted checks.

#### Acceptance Criteria

1. THE Scan_Orchestrator SHALL accept a scan_scope parameter with values: full, system_only, dependencies_only, configs_only
2. WHEN scan_scope is system_only, THE Scan_Orchestrator SHALL execute only System_Scanner and Tool_Detector
3. WHEN scan_scope is dependencies_only, THE Scan_Orchestrator SHALL execute only Dependency_Scanner
4. WHEN scan_scope is configs_only, THE Scan_Orchestrator SHALL execute only Config_Parser and AI_Parser
5. THE Scan_Orchestrator SHALL complete incremental scans in under 3 seconds
6. THE Scan_Orchestrator SHALL return partial Scan_Result dictionaries with only requested data populated
7. WHEN scan_scope is full or not specified, THE Scan_Orchestrator SHALL execute all scanning components

### Requirement 15: Error Recovery and Partial Results

**User Story:** As The Architect, I want The Inspector to return partial results when some scanners fail, so that I can still provide value even when individual components encounter errors.

#### Acceptance Criteria

1. WHEN System_Scanner fails, THE Scan_Orchestrator SHALL continue with other scanners and include an error field in the result
2. WHEN Dependency_Scanner fails, THE Scan_Orchestrator SHALL return system state and config data with a warning
3. THE Scan_Orchestrator SHALL never crash due to individual scanner failures
4. THE Scan_Orchestrator SHALL include an errors list in Scan_Result with fields: component, error_message, timestamp
5. THE Scan_Orchestrator SHALL log all errors to The Architect's logging system
6. WHEN all scanners fail, THE Scan_Orchestrator SHALL return a minimal result with error details
7. THE Scan_Orchestrator SHALL set a success flag to false when any scanner fails

### Requirement 16: Performance Monitoring and Profiling

**User Story:** As a developer, I want to measure Inspector performance, so that I can verify compliance with the 8-second scan requirement and identify bottlenecks.

#### Acceptance Criteria

1. THE Performance_Monitor SHALL measure execution time for each scanner component
2. THE Performance_Monitor SHALL include timing data in Scan_Result metadata
3. THE Performance_Monitor SHALL log warnings when any component exceeds its time budget
4. THE Performance_Monitor SHALL track memory usage during scans
5. WHEN total scan time exceeds 8 seconds, THE Performance_Monitor SHALL log a performance violation
6. THE Performance_Monitor SHALL support exporting timing data in JSON format for analysis
7. THE Performance_Monitor SHALL measure time spent in subprocess execution separately from parsing

### Requirement 17: Cross-Platform Path Handling

**User Story:** As The Inspector, I want to handle file paths correctly across Windows, macOS, and Linux, so that scans work consistently on all supported platforms.

#### Acceptance Criteria

1. THE Path_Handler SHALL use pathlib for all path operations
2. THE Path_Handler SHALL normalize paths to use forward slashes in stored data
3. THE Path_Handler SHALL expand ~ to the user's home directory on all platforms
4. THE Path_Handler SHALL handle Windows drive letters correctly (C:\, D:\, etc.)
5. THE Path_Handler SHALL resolve symlinks to their actual targets
6. THE Path_Handler SHALL validate that paths exist before attempting to scan them
7. WHEN a path does not exist, THE Path_Handler SHALL return a clear error message

### Requirement 18: Caching for Performance Optimization

**User Story:** As The Inspector, I want to cache expensive operations, so that repeated scans complete faster and reduce system load.

#### Acceptance Criteria

1. THE Cache_Manager SHALL cache system tool versions for 5 minutes
2. THE Cache_Manager SHALL cache SBOM results for 1 minute per project
3. THE Cache_Manager SHALL invalidate caches when project files are modified
4. THE Cache_Manager SHALL store caches in memory, not on disk
5. WHEN a cache hit occurs, THE Cache_Manager SHALL return cached data within 10ms
6. THE Cache_Manager SHALL include cache hit/miss statistics in scan metadata
7. THE Cache_Manager SHALL support force-refresh to bypass caches

### Requirement 19: Logging and Debugging Support

**User Story:** As a developer, I want comprehensive logging from The Inspector, so that I can diagnose scanning issues and understand what data was collected.

#### Acceptance Criteria

1. THE Inspector SHALL log all scanner executions with timestamps and durations
2. THE Inspector SHALL log detected tools, versions, and paths at debug level
3. THE Inspector SHALL log errors and warnings at appropriate severity levels
4. THE Inspector SHALL include context in log messages (project path, scanner component, operation)
5. THE Inspector SHALL support configurable log levels: debug, info, warn, error
6. THE Inspector SHALL never log sensitive data (API keys, tokens, passwords)
7. THE Inspector SHALL write logs to The Architect's logging system

### Requirement 20: Syft SBOM Parser and Pretty Printer

**User Story:** As The Inspector, I want to parse syft's JSON SBOM output and provide a pretty printer, so that I can validate round-trip parsing and provide human-readable output.

#### Acceptance Criteria

1. THE SBOM_Parser SHALL parse syft JSON output into a structured dictionary
2. THE SBOM_Parser SHALL extract artifacts, relationships, and metadata from the SBOM
3. THE Pretty_Printer SHALL format SBOM dictionaries into human-readable text output
4. THE Pretty_Printer SHALL include package names, versions, types, and locations
5. FOR ALL valid SBOM dictionaries, parsing syft output then pretty printing then parsing SHALL produce an equivalent structure (round-trip property)
6. WHEN syft output is malformed, THE SBOM_Parser SHALL return a descriptive error
7. THE Pretty_Printer SHALL support output formats: text, markdown, json
