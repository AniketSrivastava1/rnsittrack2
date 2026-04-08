# Implementation Plan: Scanning & Intelligence (Inspector)

## Overview

This implementation plan covers the development of the Inspector component - the scanning and intelligence layer that collects environment data. The implementation follows a bottom-up approach: subprocess wrapper → scanners → parsers → orchestration → caching → testing.

The component will be implemented in Python using osquery-python, syft (via subprocess), and custom parsers, with comprehensive testing for accuracy and performance.

## Tasks

- [x] 1. Project setup and dependencies
  - Create project directory structure: `devready/inspector/`
  - Set up `pyproject.toml` with dependencies: osquery-python 3.0+, sh 2.0+, PyYAML 6.0+, toml 0.10+, psutil
  - Configure development dependencies: pytest, hypothesis, pytest-asyncio, ruff, mypy
  - Create `.gitignore` for Python project
  - Initialize Git repository on branch `aniket/feature-inspector-scanning`
  - _Requirements: All (foundation for implementation)_

- [x] 2. Implement subprocess wrapper
  - [x] 2.1 Create subprocess wrapper module (`devready/inspector/subprocess_wrapper.py`)
    - Implement `SubprocessWrapper` class
    - Implement `execute()` with configurable timeout (default 5s)
    - Capture stdout, stderr, and exit code
    - Return ExecutionResult with duration
    - Terminate process on timeout
    - Include stderr in error details on failure
    - Sanitize command arguments to prevent shell injection
    - Log all executed commands for debugging
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

  - [x]* 2.2 Write property test for subprocess execution
    - **Property: Timeout Enforcement**
    - **Validates: Requirements 12.4**
    - Test that long-running commands are terminated after timeout

  - [x]* 2.3 Write unit tests for command sanitization
    - Test dangerous character detection
    - Test shell injection prevention
    - _Requirements: 12.6_

- [x] 3. Implement path handler
  - [x] 3.1 Create path handler module (`devready/inspector/path_handler.py`)
    - Implement `PathHandler` class using pathlib
    - Normalize paths to use forward slashes
    - Expand ~ to user home directory on all platforms
    - Handle Windows drive letters correctly
    - Resolve symlinks to actual targets
    - Validate paths exist before scanning
    - Return clear error for non-existent paths
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

  - [x]* 3.2 Write property test for cross-platform paths
    - **Property 8: Cross-Platform Path Handling**
    - **Validates: Requirements 17.1-17.7**
    - Test path normalization on Windows, macOS, Linux

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement system scanner
  - [x] 5.1 Create system scanner module (`devready/inspector/system_scanner.py`)
    - Implement `SystemScanner` class using osquery-python
    - Query installed software packages
    - Return list of ToolVersion dictionaries
    - Detect package managers: brew, apt, yum, dnf, pacman, chocolatey, winget, scoop
    - Query listening network ports with process info
    - Detect OS version and architecture
    - Complete system queries within 2 seconds
    - Return empty result set if osquery unavailable
    - Handle osquery errors gracefully
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [x]* 5.2 Write unit tests for system scanner
    - Test package query parsing
    - Test error handling when osquery unavailable
    - _Requirements: 1.7, 1.8_

- [x] 6. Implement tool detector
  - [x] 6.1 Create tool detector module (`devready/inspector/tool_detector.py`)
    - Implement `ToolDetector` class
    - Execute version commands for common tools: node, python, go, rustc, java, docker, git
    - Parse stdout to extract semantic version numbers
    - Return null for tools not in PATH
    - Detect version managers: nvm, pyenv, asdf, mise, rustup, sdkman
    - Identify which version manager controls each tool
    - Complete tool detection within 3 seconds
    - Timeout individual tool checks after 1 second
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x]* 6.2 Write property test for tool detection
    - **Property 3: Tool Detection Accuracy**
    - **Validates: Requirements 9.1, 9.2**
    - Test that detected versions match actual installations

- [x] 7. Implement dependency scanner
  - [x] 7.1 Create dependency scanner module (`devready/inspector/dependency_scanner.py`)
    - Implement `DependencyScanner` class
    - Execute syft as subprocess to generate SBOM
    - Pass project root path to syft
    - Parse syft JSON output into structured dictionary
    - Extract package name, version, type, location from artifacts
    - Support ecosystems: npm, pip, cargo, go modules, maven, gradle
    - Complete SBOM generation within 4 seconds
    - Return error with installation instructions if syft not installed
    - Capture stderr and return in error details on failure
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 7.2 Create SBOM parser (`devready/inspector/sbom_parser.py`)
    - Implement `SBOMParser` class
    - Parse syft JSON output into dependencies dict
    - Extract artifacts, relationships, metadata
    - Implement pretty printer for human-readable output
    - Include package names, versions, types, locations
    - Support output formats: text, markdown, json
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.6, 20.7_

  - [x]* 7.3 Write property test for SBOM parsing
    - **Property 4: SBOM Parsing Round-Trip**
    - **Validates: Requirements 20.5**
    - Test that parse → pretty print → parse produces equivalent structure

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement config parser
  - [x] 9.1 Create config parser module (`devready/inspector/config_parser.py`)
    - Implement `ConfigParser` class
    - Search for AI agent config files: CLAUDE.md, .cursorrules, .copilot, AGENTS.md, .aider.conf.yml
    - Parse contents and extract key-value settings
    - Identify referenced dependencies, API endpoints, custom instructions
    - Detect model names, temperature, context window configs
    - Return dict with: file_path, agent_type, settings, dependencies, last_modified
    - Parse all found configs and return list
    - Return empty list if no configs found
    - Handle malformed configs and log errors without crashing
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [x] 9.2 Create AI parser (`devready/inspector/ai_parser.py`)
    - Implement `AIParser` class
    - Parse CLAUDE.md files and extract markdown sections
    - Parse .cursorrules files (JSON or YAML)
    - Identify custom instructions, system prompts, tool configs
    - Extract referenced file paths, API endpoints, dependencies
    - Detect model preferences and parameters
    - Return normalized dict regardless of source format
    - Merge configs when both CLAUDE.md and .cursorrules exist (.cursorrules precedence)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

  - [x]* 9.3 Write unit tests for config parsing
    - Test markdown parsing
    - Test JSON/YAML parsing
    - Test malformed config handling
    - _Requirements: 3.8, 11.1-11.7_

- [x] 10. Implement project detection
  - [x] 10.1 Create root detector module (`devready/inspector/root_detector.py`)
    - Implement `RootDetector` class
    - Search for project markers: .git, pyproject.toml, package.json, Cargo.toml, go.mod, pom.xml, build.gradle
    - Use .git as highest priority when multiple markers exist
    - Traverse up directory tree from current working directory
    - Stop after 10 parent directories if no marker found
    - Return absolute path to detected project root
    - Extract project name from root directory or package manifest
    - Complete detection within 100ms
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 10.2 Create stack detector (`devready/inspector/stack_detector.py`)
    - Implement `StackDetector` class
    - Identify Node.js by package.json or node_modules
    - Identify Python by pyproject.toml, setup.py, requirements.txt, Pipfile
    - Identify Go by go.mod or go.sum
    - Identify Rust by Cargo.toml or Cargo.lock
    - Identify Java by pom.xml, build.gradle, build.gradle.kts
    - Support detecting multiple stacks in monorepos
    - Return "unknown" if no stack markers found
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x]* 10.3 Write unit tests for project detection
    - Test marker priority
    - Test multi-stack detection
    - _Requirements: 4.2, 5.6_

- [x] 11. Implement environment variable collection
  - [x] 11.1 Create env collector module (`devready/inspector/env_collector.py`)
    - Implement `EnvCollector` class
    - Read environment variables from current process
    - Filter to development-relevant keys: PATH, NODE_ENV, PYTHON_PATH, GOPATH, CARGO_HOME, JAVA_HOME
    - Redact sensitive values containing: token, key, secret, password, api
    - Return dict of variable names to values (or "[REDACTED]")
    - Detect .env files in project root and parse contents
    - Log warning and skip malformed lines in .env files
    - Never log or return actual sensitive values
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x]* 11.2 Write unit tests for env collection
    - Test sensitive data redaction
    - Test .env file parsing
    - _Requirements: 8.3, 8.7_

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement policy checker
  - [x] 13.1 Create policy checker module (`devready/inspector/policy_checker.py`)
    - Implement `PolicyChecker` class
    - Accept TeamPolicy dict and ScanResult dict as inputs
    - Validate all required tools from policy are present
    - Validate tool versions meet policy version constraints
    - Identify forbidden tools present in scan result
    - Check dependencies against known CVE databases
    - Return list of violations with: rule_id, severity, message, affected_component
    - Return empty list when no violations found
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [x]* 13.2 Write property test for policy validation
    - **Property: Policy Validation**
    - **Validates: Requirements 6.2, 6.3, 6.4**
    - Test that violations are correctly identified

- [x] 14. Implement dependency freshness analyzer
  - [x] 14.1 Create freshness analyzer module (`devready/inspector/freshness_analyzer.py`)
    - Implement `FreshnessAnalyzer` class
    - Compare detected versions against latest stable versions
    - Categorize as: current, minor_update_available, major_update_available, deprecated
    - Identify dependencies with known security vulnerabilities
    - Return freshness_score from 0 to 100 based on recency
    - Use local caching to avoid repeated network requests
    - Use cached data when offline and mark as potentially stale
    - Complete analysis within 2 seconds using cached data
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x]* 14.2 Write property test for freshness analysis
    - **Property 5: Cache Correctness**
    - **Validates: Requirements 10.6**
    - Test that cached results match fresh scans within TTL

- [x] 15. Implement cache manager
  - [x] 15.1 Create cache manager module (`devready/inspector/cache_manager.py`)
    - Implement `CacheManager` class
    - Cache tool versions for 5 minutes
    - Cache SBOM results for 1 minute per project
    - Invalidate caches when project files are modified
    - Store caches in memory (not disk)
    - Return cached data within 10ms on cache hit
    - Include cache hit/miss statistics in scan metadata
    - Support force-refresh to bypass caches
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_

  - [x]* 15.2 Write property test for caching
    - **Property 5: Cache Correctness**
    - **Validates: Requirements 18.2, 18.5**
    - Test that cached and fresh results are equivalent

- [x] 16. Implement performance monitor
  - [x] 16.1 Create performance monitor module (`devready/inspector/performance_monitor.py`)
    - Implement `PerformanceMonitor` class
    - Measure execution time for each scanner component
    - Include timing data in scan result metadata
    - Log warnings when components exceed time budget
    - Track memory usage during scans
    - Log performance violation when total > 8 seconds
    - Support exporting timing data in JSON format
    - Measure subprocess execution time separately from parsing
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_

  - [x]* 16.2 Write property test for performance
    - **Property 2: Scan Performance**
    - **Validates: Requirements 16.5**
    - Test that full scans complete within 8 seconds

- [x] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Implement scan orchestrator
  - [x] 18.1 Create scan orchestrator module (`devready/inspector/scan_orchestrator.py`)
    - Implement `ScanOrchestrator` class
    - Execute SystemScanner, DependencyScanner, ConfigParser, StackDetector in parallel
    - Assemble results into dict matching EnvironmentSnapshot schema
    - Include fields: timestamp, tools, dependencies, env_vars, project_path, tech_stack, ai_configs
    - Complete full scans within 8 seconds
    - Include partial results and log failure when scanner fails
    - Accept optional project_path parameter to override detection
    - Return scan duration in milliseconds as metadata
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [x] 18.2 Implement incremental scanning
    - Accept scan_scope parameter: full, system_only, dependencies_only, configs_only
    - Execute only SystemScanner and ToolDetector for system_only
    - Execute only DependencyScanner for dependencies_only
    - Execute only ConfigParser and AIParser for configs_only
    - Complete incremental scans in under 3 seconds
    - Return partial ScanResult dicts with only requested data
    - Execute all scanners for full or unspecified scope
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [x]* 18.3 Write property test for scan completeness
    - **Property 1: Scan Completeness**
    - **Validates: Requirements 7.3**
    - Test that full scans include all required fields

- [x] 19. Implement result validator
  - [x] 19.1 Create result validator module (`devready/inspector/result_validator.py`)
    - Implement `ResultValidator` class
    - Validate ScanResult dicts against EnvironmentSnapshot Pydantic model
    - Return detailed error messages for invalid fields
    - Coerce compatible types when possible
    - Reject results with missing required fields
    - Validate timestamps are in ISO 8601 format
    - Validate version strings follow semantic versioning
    - Return validated dictionary on success
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [x]* 19.2 Write property test for validation
    - **Property: Validation Correctness**
    - **Validates: Requirements 13.1, 13.2**
    - Test that invalid data is rejected with clear errors

- [x] 20. Implement error recovery
  - [x] 20.1 Create error handling module (`devready/inspector/error_handler.py`)
    - Continue with other scanners when SystemScanner fails
    - Return system state and config data with warning when DependencyScanner fails
    - Never crash due to individual scanner failures
    - Include errors list in ScanResult with: component, error_message, timestamp
    - Log all errors to Architect's logging system
    - Return minimal result with error details when all scanners fail
    - Set success flag to false when any scanner fails
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

  - [x]* 20.2 Write property test for error recovery
    - **Property 7: Error Recovery**
    - **Validates: Requirements 15.1, 15.2, 15.3**
    - Test that partial results are returned on scanner failures

- [x] 21. Implement logging
  - [x] 21.1 Create logging configuration (`devready/inspector/logging_config.py`)
    - Log all scanner executions with timestamps and durations
    - Log detected tools, versions, paths at debug level
    - Log errors and warnings at appropriate severity levels
    - Include context in log messages (project path, scanner component, operation)
    - Support configurable log levels: debug, info, warn, error
    - Never log sensitive data (API keys, tokens, passwords)
    - Write logs to Architect's logging system
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7_

  - [x]* 21.2 Write unit tests for logging
    - Test sensitive data redaction
    - Test log level filtering
    - _Requirements: 19.6_

- [x] 22. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 23. Create comprehensive test suite
  - [x] 23.1 Set up test infrastructure (`tests/conftest.py`)
    - Create pytest fixtures for mock osquery
    - Create fixture for mock syft output
    - Create fixture for temporary project directories
    - Set up Hypothesis strategies for scan results
    - Configure test logging

  - [x] 23.2 Create Hypothesis strategies (`tests/strategies.py`)
    - Implement `tool_version_strategy()` for ToolVersion generation
    - Implement `scan_result_strategy()` for ScanResult generation
    - Implement `sbom_strategy()` for SBOM generation

  - [x]* 23.3 Write integration tests (`tests/integration/`)
    - Test full scan workflow: orchestrate → scanners → assemble → validate
    - Test incremental scan workflow: scope → targeted scanners → partial result
    - Test error recovery workflow: scanner failure → partial result → continue
    - Test caching workflow: scan → cache → scan → cache hit
    - Test offline workflow: disable network → scan → verify no network calls

- [x] 24. Performance validation
  - [x] 24.1 Create performance tests (`tests/performance/`)
    - Test full scan < 8 seconds
    - Test system scan < 2 seconds
    - Test dependency scan < 4 seconds
    - Test config scan < 1 second
    - Test tool detection < 3 seconds
    - Test cache hit < 10ms
    - Test project root detection < 100ms
    - _Requirements: Performance requirements from design_

  - [x]* 24.2 Run performance tests and validate
    - Execute all performance tests
    - Document results
    - Optimize if targets are missed

- [x] 25. Offline operation validation
  - [x]* 25.1 Write property test for offline operation
    - **Property 6: Offline Operation**
    - **Validates: All requirements**
    - Test that all scanning works without network access

- [x] 26. Documentation
  - [x] 26.1 Create component documentation
    - Document scanner architecture and data flow
    - Document osquery integration
    - Document syft SBOM generation
    - Document caching strategy
    - Document error handling

  - [x] 26.2 Create developer documentation
    - Write README.md with setup instructions
    - Document how to add new scanners
    - Document testing strategy
    - Create troubleshooting guide

- [x] 27. Git workflow and pull request
  - [x] 27.1 Finalize Git workflow
    - Ensure all code is committed on branch `aniket/feature-inspector-scanning`
    - Write comprehensive commit messages
    - Push branch to remote repository
    - Create pull request linking to requirements and design docs
    - _Requirements: All (delivery)_

  - [x] 27.2 Pre-PR checklist
    - All tests passing (unit, property, integration, performance)
    - Code linting passes
    - Type checking passes
    - Test coverage meets 85% target
    - Documentation is complete
    - All scans complete within 8 seconds
    - Offline operation verified

## Notes

- Tasks marked with `*` are optional property tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties
- Integration tests validate end-to-end workflows
- Performance tests validate timing requirements
- The implementation uses Python with osquery-python, syft, and custom parsers
- All scanning must work 100% offline
- Performance is critical: full scans must complete in < 8 seconds
- Caching is essential for responsiveness
- Error recovery ensures partial results are always available
