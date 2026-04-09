# Implementation Plan: Sandboxing & Fixes (Operator)

## Overview

This implementation plan covers the development of the Operator component - the sandboxing and fix execution layer that safely applies environment fixes using Docker containers for validation. The implementation follows a bottom-up approach: Docker integration → risk assessment → fix execution → git hooks → config generation → testing.

The component will be implemented in Python using python-on-whales, GitPython, and subprocess management, with comprehensive testing including property-based tests for isolation guarantees.

## Tasks

- [x] 1. Project setup and dependencies
  - Create project directory structure: `devready/operator/`
  - Set up `pyproject.toml` with dependencies: python-on-whales 0.70+, GitPython 3.1+, sh 2.0+, toml 0.10+, psutil
  - Configure development dependencies: pytest, hypothesis, pytest-asyncio, docker (for testing)
  - Create `.gitignore` for Python project
  - Initialize Git repository on branch `reythem/feature-operator-sandboxing`
  - _Requirements: All (foundation for implementation)_

- [x] 2. Implement Docker Manager
  - [x] 2.1 Create Docker manager module (`devready/operator/docker_manager.py`)
    - Implement `DockerManager` class using python-on-whales
    - Implement `verify_docker_available()` to check Docker is running
    - Implement `get_docker_version()` and log warning if < 20.10
    - Handle Docker daemon connection errors gracefully
    - Log all Docker operations at debug level
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x] 2.2 Implement container factory (`devready/operator/container_factory.py`)
    - Define base image mappings for tech stacks (Node.js → node:lts-alpine, etc.)
    - Implement `create_sandbox_container()` with workspace mounting
    - Set working directory to /workspace
    - Configure auto-remove after execution
    - Complete container creation within 3 seconds
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x]* 2.3 Write property test for Docker availability
    - **Property 1: Docker Availability Check**
    - **Validates: Requirements 1.2, 1.3**
    - Test that Docker availability is correctly detected

  - [x]* 2.4 Write unit tests for container creation
    - Test correct base image selection for each tech stack
    - Test workspace mounting configuration
    - _Requirements: 2.1-2.6_

- [x] 3. Implement fix command execution in sandbox
  - [x] 3.1 Create sandbox executor (`devready/operator/sandbox_executor.py`)
    - Implement `execute_in_sandbox()` method
    - Execute fix command inside container
    - Capture stdout, stderr, and exit code
    - Set timeout of 60 seconds
    - Terminate container on timeout
    - Mark fix as verified if exit code is 0
    - Log command, exit code, and duration
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [x]* 3.2 Write property test for sandbox isolation
    - **Property 1: Sandbox Isolation**
    - **Validates: Requirements 3.1, 3.5, 3.6**
    - Test that failed sandbox executions don't affect host

  - [x]* 3.3 Write property test for timeout enforcement
    - **Property 9: Timeout Enforcement**
    - **Validates: Requirements 3.3, 3.4**
    - Test that long-running commands are terminated

- [x] 4. Implement workspace mounting and file access
  - [x] 4.1 Create workspace mounter (`devready/operator/workspace_mounter.py`)
    - Implement `mount_workspace()` with read-write volume
    - Preserve file permissions when mounting
    - Handle Windows path formats correctly
    - Validate project root exists before mounting
    - Return descriptive error on mount failure
    - Support mounting additional directories
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x]* 4.2 Write property test for path handling
    - **Property 8: Platform Compatibility**
    - **Validates: Requirements 4.3, 23.3**
    - Test that Windows paths are correctly converted for Docker

  - [x]* 4.3 Write unit tests for mount validation
    - Test error handling for non-existent paths
    - Test permission preservation
    - _Requirements: 4.4, 4.2_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement risk assessment
  - [x] 6.1 Create risk assessor (`devready/operator/risk_assessor.py`)
    - Implement `RiskAssessor` class
    - Implement `classify_fix()` to detect global vs local fixes
    - Detect system-level package manager commands (brew, apt, choco)
    - Detect version manager commands (nvm, pyenv, rustup)
    - Classify project-only fixes as local
    - Assign risk levels: low, medium, high
    - Return risk assessment with isolation recommendation
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x]* 6.2 Write property test for risk classification
    - **Property 6: Risk Assessment Accuracy**
    - **Validates: Requirements 5.2, 5.3**
    - Test that global fixes are correctly identified

  - [x]* 6.3 Write unit tests for risk levels
    - Test risk level assignment logic
    - Test isolation recommendations
    - _Requirements: 5.5, 5.6, 5.7_

- [x] 7. Implement config generation
  - [x] 7.1 Create config generator base (`devready/operator/config_generator.py`)
    - Implement `ConfigGenerator` base class
    - Implement `generate_isolation_config()` method
    - Validate generated configs for syntax
    - Write configs to project root
    - Merge with existing configs when present
    - _Requirements: 6.1, 6.2, 6.5, 6.6, 6.7, 6.8_

  - [x] 7.2 Create mise.toml generator (`devready/operator/mise_generator.py`)
    - Implement `MiseGenerator` class
    - Support tool versions: node, python, go, rust, java, ruby
    - Use semantic version format
    - Include installation instructions in comments
    - Validate versions are available in mise
    - Include mise installation instructions if not installed
    - Preserve existing mise.toml settings
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [x] 7.3 Create devcontainer.json generator (`devready/operator/devcontainer_generator.py`)
    - Implement `DevcontainerGenerator` class
    - Select base images matching tech stack
    - Include features for required tools
    - Configure port forwarding (3000, 8000, 8080, 5173)
    - Set up volume mounts for package manager caches
    - Include postCreateCommand for dependency installation
    - Validate generated JSON syntax
    - Include comments explaining isolation strategy
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

  - [x]* 7.4 Write property test for config generation
    - **Property: Config Generation Correctness**
    - **Validates: Requirements 6.6, 7.4, 8.7**
    - Test that generated configs are syntactically valid

  - [x]* 7.5 Write unit tests for config merging
    - Test merging with existing configs
    - Test preservation of existing settings
    - _Requirements: 6.8, 7.7_

- [x] 8. Implement git hook management
  - [x] 8.1 Create hook manager (`devready/operator/hook_manager.py`)
    - Implement `HookManager` class using GitPython
    - Implement `install_post_merge_hook()` to trigger scans
    - Implement `install_post_checkout_hook()` for branch switches
    - Implement `install_pre_commit_hook()` for validation
    - Preserve existing hooks by chaining
    - Return error if .git directory doesn't exist
    - Make hook scripts executable on Unix
    - Handle Windows hook execution with bash/sh
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

  - [x] 8.2 Create post-merge hook (`devready/operator/hooks/post_merge.py`)
    - Execute `devready scan --quick` after merges
    - Detect changes to dependency files
    - Trigger full scan if dependency files changed
    - Display scan results in terminal
    - Offer to run `devready fix` if issues found
    - Complete within 5 seconds
    - Support --skip-scan flag
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 8.3 Create pre-commit hook (`devready/operator/hooks/pre_commit.py`)
    - Execute `devready validate` before commits
    - Check required tools are installed
    - Validate project dependencies are installed
    - Block commit if validation fails
    - Allow commit if validation passes
    - Support --no-verify flag
    - Complete validation within 3 seconds
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

  - [x]* 8.4 Write property test for hook preservation
    - **Property 7: Hook Preservation**
    - **Validates: Requirements 9.5**
    - Test that existing hooks are preserved after installation

  - [x]* 8.5 Write unit tests for hook execution
    - Test post-merge hook triggers scan
    - Test pre-commit hook blocks on failure
    - _Requirements: 10.1, 11.4_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement package manager adapters
  - [x] 10.1 Create package manager adapter base (`devready/operator/package_managers/adapter.py`)
    - Implement `PackageManagerAdapter` base class
    - Implement `detect_package_manager()` for each tech stack
    - Implement `generate_fix_command()` using detected manager
    - Handle multiple package managers per tech stack
    - _Requirements: 13.6, 13.7, 13.8_

  - [x] 10.2 Create Node.js adapters (`devready/operator/package_managers/nodejs.py`)
    - Implement adapters for npm, yarn, pnpm, bun
    - Detect based on lock files (pnpm-lock.yaml, yarn.lock, bun.lockb)
    - _Requirements: 13.1_

  - [x] 10.3 Create Python adapters (`devready/operator/package_managers/python.py`)
    - Implement adapters for pip, poetry, pipenv
    - Detect based on lock files (poetry.lock, Pipfile.lock)
    - _Requirements: 13.2_

  - [x] 10.4 Create other language adapters
    - Implement Cargo adapter for Rust
    - Implement Go modules adapter
    - Implement Maven and Gradle adapters for Java
    - _Requirements: 13.3, 13.4, 13.5_

  - [x]* 10.5 Write property test for package manager detection
    - **Property: Package Manager Detection**
    - **Validates: Requirements 13.6**
    - Test that correct package manager is detected for each project type

- [x] 11. Implement fix application to host
  - [x] 11.1 Create fix applicator (`devready/operator/fix_applicator.py`)
    - Implement `FixApplicator` class
    - Execute verified fix commands on host
    - Require user confirmation for global fixes
    - Apply local fixes automatically
    - Capture stdout, stderr, exit code from host execution
    - Rollback on host execution failure
    - Log all applied fixes with timestamps
    - Update Architect's state after successful application
    - Re-run scans to verify issue resolution
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

  - [x]* 11.2 Write property test for fix application
    - **Property 4: Fix Verification**
    - **Validates: Requirements 14.8, 25.3**
    - Test that applied fixes resolve reported issues

- [x] 12. Implement rollback support
  - [x] 12.1 Create rollback manager (`devready/operator/rollback_manager.py`)
    - Implement `RollbackManager` class
    - Create snapshots before global fixes
    - Store installed packages, tool versions, config files
    - Restore previous state on host failure
    - Support manual rollback via `devready rollback` command
    - Keep last 5 snapshots
    - Clean up old snapshots automatically
    - Provide manual recovery instructions on rollback failure
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

  - [x]* 12.2 Write property test for rollback correctness
    - **Property 3: Rollback Correctness**
    - **Validates: Requirements 15.3**
    - Test that rollback restores exact previous state

- [x] 13. Implement project isolation verification
  - [x] 13.1 Create isolation verifier (`devready/operator/isolation_verifier.py`)
    - Implement `IsolationVerifier` class
    - Scan all projects before and after fixes
    - Detect changes to global tool versions
    - Verify other projects still work after global fixes
    - Run quick health checks on other projects
    - Trigger automatic rollback if another project breaks
    - Log isolation verification results
    - Complete verification within 15 seconds
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_

  - [x]* 13.2 Write property test for project isolation
    - **Property 2: Project Isolation**
    - **Validates: Requirements 16.1, 16.4**
    - Test that fixes don't affect other projects

- [x] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Implement dry-run execution
  - [x] 15.1 Create dry-run executor (`devready/operator/dry_run_executor.py`)
    - Implement `DryRunExecutor` class
    - Execute all fixes in sandbox before offering to apply
    - Display fix command, expected changes, risk level
    - Show stdout and stderr from sandbox execution
    - Indicate whether fix succeeded in sandbox
    - Don't offer to apply if sandbox execution failed
    - Support --dry-run-only flag
    - Complete dry-runs within 10 seconds per fix
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

  - [x]* 15.2 Write property test for dry-run safety
    - **Property: Dry-Run Safety**
    - **Validates: Requirements 17.1, 17.5**
    - Test that dry-runs never modify host system

- [x] 16. Implement concurrent fix execution
  - [x] 16.1 Create concurrent executor (`devready/operator/concurrent_executor.py`)
    - Implement `ConcurrentExecutor` class
    - Identify independent fixes that can run in parallel
    - Execute independent fixes concurrently (max 3)
    - Execute dependent fixes sequentially
    - Skip dependent fixes if dependency fails
    - Aggregate results from all executions
    - Complete faster than sequential execution
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_

  - [x]* 16.2 Write property test for concurrent execution
    - **Property 5: Concurrent Execution Safety**
    - **Validates: Requirements 18.1, 18.6**
    - Test that concurrent execution produces same results as sequential

- [x] 17. Implement fix command parser
  - [x] 17.1 Create fix parser (`devready/operator/fix_parser.py`)
    - Implement `FixParser` class
    - Parse fix command strings into structured dictionaries
    - Extract package_manager, action, target, version
    - Identify package manager from command prefix
    - Extract action (install, update, remove, configure)
    - Extract target package or tool name
    - _Requirements: 19.1, 19.2, 19.3, 19.4_

  - [x] 17.2 Create pretty printer (`devready/operator/pretty_printer.py`)
    - Implement `PrettyPrinter` class
    - Format fix command dictionaries into human-readable descriptions
    - Include risk level and isolation strategy
    - _Requirements: 19.5, 19.6_

  - [x]* 17.3 Write property test for round-trip parsing
    - **Property: Round-Trip Parsing**
    - **Validates: Requirements 19.7**
    - Test that parse → pretty print → parse produces equivalent structure

- [x] 18. Implement container cleanup
  - [x] 18.1 Create resource cleaner (`devready/operator/resource_cleaner.py`)
    - Implement `ResourceCleaner` class
    - Remove sandbox containers immediately after execution
    - Remove dangling images created during validation
    - Clean up unused volumes
    - Monitor disk space and warn when Docker > 10GB
    - Support `devready cleanup` command
    - Complete cleanup within 2 seconds
    - Log warnings on cleanup failure but don't block execution
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7_

  - [x]* 18.2 Write property test for resource cleanup
    - **Property 10: Resource Cleanup**
    - **Validates: Requirements 20.1**
    - Test that no orphaned containers remain after execution

- [x] 19. Implement error handling
  - [x] 19.1 Create error handling module (`devready/operator/errors.py`)
    - Define `OperatorError` base exception
    - Define `DockerNotAvailableError` with installation instructions
    - Define `FixExecutionError` with command and error details
    - Define other specific error types
    - _Requirements: 21.1, 21.2, 21.3_

  - [x] 19.2 Implement error recovery logic
    - Continue with remaining fixes if one fails
    - Never crash due to individual fix failures
    - Include errors list in results
    - Log all errors to Architect's logging system
    - Provide troubleshooting guidance when all fixes fail
    - _Requirements: 21.4, 21.5, 21.6, 21.7_

  - [x]* 19.3 Write unit tests for error handling
    - Test Docker not available error
    - Test fix execution error handling
    - Test error recovery and continuation
    - _Requirements: 21.1, 21.2, 21.4_

- [x] 20. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 21. Implement performance monitoring
  - [x] 21.1 Create performance monitor (`devready/operator/performance_monitor.py`)
    - Implement `PerformanceMonitor` class
    - Measure execution time for each fix (sandbox and host)
    - Include timing data in fix results
    - Log warnings when fixes exceed 30 seconds
    - Track Docker container startup time separately
    - Log performance violations when total > 60 seconds
    - Support exporting timing data in JSON format
    - Measure verification time separately
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7_

  - [x]* 21.2 Write property test for performance monitoring
    - **Property: Performance Monitoring**
    - **Validates: Requirements 22.1, 22.3**
    - Test that timing data is accurately captured

- [x] 22. Implement cross-platform support
  - [x] 22.1 Create platform adapter (`devready/operator/platform_adapter.py`)
    - Implement `PlatformAdapter` class
    - Detect host operating system
    - Use platform-specific package managers
    - Handle Windows path formats in Docker mounts
    - Use appropriate shell (bash on Unix, PowerShell on Windows)
    - Handle line ending differences (LF vs CRLF)
    - Validate Docker Desktop on macOS/Windows
    - Support WSL2 detection and prefer Linux-style execution
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7_

  - [x]* 22.2 Write property test for platform compatibility
    - **Property 8: Platform Compatibility**
    - **Validates: Requirements 23.1, 23.2, 23.3**
    - Test that fixes work on all platforms (requires multi-platform CI)

- [x] 23. Implement logging
  - [x] 23.1 Create logging configuration (`devready/operator/logging_config.py`)
    - Log all fix executions with timestamps, commands, results
    - Log Docker operations at debug level
    - Log errors and warnings at appropriate levels
    - Include context in log messages (project path, fix type, risk level)
    - Support configurable log levels
    - Never log sensitive data
    - Write logs to Architect's logging system
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7_

  - [x]* 23.2 Write unit tests for logging
    - Test sensitive data redaction
    - Test log level filtering
    - _Requirements: 24.6_

- [x] 24. Implement fix verification
  - [x] 24.1 Create fix verifier (`devready/operator/fix_verifier.py`)
    - Implement `FixVerifier` class
    - Re-run Inspector's scans after applying fixes
    - Compare pre-fix and post-fix scan results
    - Confirm reported issues are no longer present
    - Report verification failure if issues persist
    - Detect new issues introduced by fixes
    - Trigger automatic rollback if new issues detected
    - Return verification report with fixed/remaining/new issues
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7_

  - [x]* 24.2 Write property test for fix verification
    - **Property 4: Fix Verification**
    - **Validates: Requirements 25.3, 25.5**
    - Test that verification correctly identifies resolved and new issues

- [x] 25. Create comprehensive test suite
  - [x] 25.1 Set up test infrastructure (`tests/conftest.py`)
    - Create pytest fixtures for Docker test environment
    - Create fixture for mock git repositories
    - Create fixture for temporary project directories
    - Set up Hypothesis strategies for fix commands
    - Configure test logging

  - [x] 25.2 Create Hypothesis strategies (`tests/strategies.py`)
    - Implement `fix_command_strategy()` for FixCommand generation
    - Implement `execution_result_strategy()` for ExecutionResult generation
    - Implement `risk_assessment_strategy()` for RiskAssessment generation

  - [x]* 25.3 Write integration tests (`tests/integration/`)
    - Test full fix workflow: dry-run → apply → verify
    - Test rollback workflow: snapshot → fail → restore
    - Test isolation workflow: global fix → verify other projects
    - Test hook workflow: install → trigger → scan
    - Test concurrent execution workflow: multiple fixes → parallel → aggregate

- [x] 26. Performance validation
  - [x] 26.1 Create performance tests (`tests/performance/`)
    - Test container creation < 3 seconds
    - Test fix execution in sandbox < 10 seconds
    - Test fix application to host < 5 seconds
    - Test rollback operation < 3 seconds
    - Test hook installation < 1 second
    - Test config generation < 500ms
    - Test concurrent execution faster than sequential
    - _Requirements: Performance requirements from design_

  - [x]* 26.2 Run performance tests and validate
    - Execute all performance tests
    - Document results
    - Optimize if targets are missed

- [x] 27. Documentation
  - [x] 27.1 Create component documentation
    - Document Docker integration and container management
    - Document risk assessment and isolation strategies
    - Document git hook installation and usage
    - Document package manager adapters
    - Document error handling and recovery

  - [x] 27.2 Create developer documentation
    - Write README.md with setup instructions
    - Document architecture and component interactions
    - Document testing strategy
    - Create troubleshooting guide

- [x] 28. Git workflow and pull request
  - [x] 28.1 Finalize Git workflow
    - Ensure all code is committed on branch `reythem/feature-operator-sandboxing`
    - Write comprehensive commit messages
    - Push branch to remote repository
    - Create pull request linking to requirements and design docs
    - _Requirements: All (delivery)_

  - [x] 28.2 Pre-PR checklist
    - All tests passing (unit, property, integration, performance)
    - Code linting passes
    - Type checking passes
    - Test coverage meets 85% target
    - Documentation is complete
    - Docker is properly cleaned up in all test scenarios

## Notes

- Tasks marked with `*` are optional property tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties (isolation, rollback, etc.)
- Integration tests validate end-to-end workflows
- Performance tests validate timing requirements
- The implementation uses Python with python-on-whales, GitPython, and subprocess
- All Docker operations must clean up resources properly
- Security is critical: sandbox isolation, user confirmation for global fixes
- Cross-platform support is essential: test on Windows, macOS, and Linux
