# Requirements Document

## Introduction

The Operator is the sandboxing and fix execution component of DevReady CLI responsible for safely applying environment fixes without breaking existing projects. It acts as the execution layer that receives fix recommendations from The Architect and executes them in isolated Docker containers to verify they work before applying changes to the host system. The Operator implements strict project isolation, ensuring fixes never affect other projects on the developer's machine.

The Operator uses python-on-whales for Docker integration, GitPython for git hook management, and implements intelligent fallback logic to generate project-specific isolation configs (mise.toml, devcontainer.json) when global fixes are unsafe. It supports multiple package managers (npm, pip, cargo, go, maven) and completes dry-run validations in under 10 seconds per fix.

## Glossary

- **Operator**: The sandboxing and fix execution component responsible for safe fix application
- **Docker_Manager**: The python-on-whales wrapper that manages ephemeral containers
- **Fix_Command**: A shell command that installs, updates, or configures a tool or dependency
- **Dry_Run**: Execution of a Fix_Command in an isolated Docker container to verify it works
- **Isolation_Config**: A project-specific configuration file (mise.toml, devcontainer.json) that isolates dependencies
- **Hook_Manager**: The GitPython-based component that installs and manages git hooks
- **Sandbox_Container**: An ephemeral Docker container with the workspace mounted for fix validation
- **Exit_Code**: The integer return code from a Fix_Command execution (0 = success, non-zero = failure)
- **Project_Isolation**: The guarantee that fixes applied to one project never affect other projects
- **Global_Fix**: A fix that installs or updates tools at the system level (affects all projects)
- **Local_Fix**: A fix that modifies only project-specific files or configs
- **Fallback_Strategy**: The logic to generate Isolation_Config when Global_Fix is unsafe
- **Package_Manager**: A tool that manages dependencies (npm, pip, cargo, go, maven, gradle, etc.)
- **Workspace_Mount**: The read-write binding of the project directory into Sandbox_Container
- **Fix_Verification**: The process of checking Exit_Code and output to confirm a fix succeeded

## Requirements

### Requirement 1: Docker Integration with python-on-whales

**User Story:** As The Operator, I want to manage Docker containers using python-on-whales, so that I can execute fixes in isolated environments with a Pythonic API.

#### Acceptance Criteria

1. THE Docker_Manager SHALL use python-on-whales to interact with the Docker daemon
2. THE Docker_Manager SHALL verify Docker is installed and running before attempting container operations
3. WHEN Docker is not available, THE Docker_Manager SHALL return an error message with installation instructions
4. THE Docker_Manager SHALL support Docker Desktop on macOS and Windows, and Docker Engine on Linux
5. THE Docker_Manager SHALL handle Docker daemon connection errors gracefully without crashing
6. THE Docker_Manager SHALL log all Docker operations at debug level
7. WHEN Docker version is below 20.10, THE Docker_Manager SHALL log a warning about potential compatibility issues

### Requirement 2: Ephemeral Sandbox Container Creation

**User Story:** As The Operator, I want to spin up ephemeral Docker containers for fix validation, so that I can test fixes without affecting the host system.

#### Acceptance Criteria

1. THE Docker_Manager SHALL create Sandbox_Container instances with base images matching the project's Tech_Stack
2. WHEN Tech_Stack is Node.js, THE Docker_Manager SHALL use node:lts-alpine as the base image
3. WHEN Tech_Stack is Python, THE Docker_Manager SHALL use python:3.11-slim as the base image
4. WHEN Tech_Stack is Go, THE Docker_Manager SHALL use golang:1.21-alpine as the base image
5. WHEN Tech_Stack is Rust, THE Docker_Manager SHALL use rust:1.75-slim as the base image
6. WHEN Tech_Stack is Java, THE Docker_Manager SHALL use eclipse-temurin:17-jdk-alpine as the base image
7. THE Docker_Manager SHALL mount the project workspace as a read-write volume at /workspace
8. THE Docker_Manager SHALL set the working directory to /workspace in the container
9. THE Docker_Manager SHALL configure containers to auto-remove after execution
10. THE Docker_Manager SHALL complete container creation within 3 seconds

### Requirement 3: Fix Command Execution in Sandbox

**User Story:** As The Operator, I want to execute Fix_Command instances in Sandbox_Container environments, so that I can verify fixes work before applying them to the host.

#### Acceptance Criteria

1. THE Docker_Manager SHALL execute Fix_Command as a shell command inside Sandbox_Container
2. THE Docker_Manager SHALL capture stdout, stderr, and Exit_Code from Fix_Command execution
3. THE Docker_Manager SHALL set a timeout of 60 seconds for Fix_Command execution
4. WHEN Fix_Command times out, THE Docker_Manager SHALL terminate the container and return a timeout error
5. WHEN Exit_Code is 0, THE Docker_Manager SHALL mark the fix as verified
6. WHEN Exit_Code is non-zero, THE Docker_Manager SHALL mark the fix as failed and include stderr in the error details
7. THE Docker_Manager SHALL complete fix execution and verification within 10 seconds for typical commands
8. THE Docker_Manager SHALL log Fix_Command, Exit_Code, and execution duration

### Requirement 4: Workspace Mounting and File Access

**User Story:** As The Operator, I want to mount the project workspace into containers, so that fixes can access and modify project files during validation.

#### Acceptance Criteria

1. THE Docker_Manager SHALL mount the Project_Root as a read-write volume
2. THE Docker_Manager SHALL preserve file permissions when mounting the workspace
3. THE Docker_Manager SHALL handle Windows path formats correctly when mounting volumes
4. THE Docker_Manager SHALL validate that Project_Root exists before attempting to mount
5. WHEN mounting fails, THE Docker_Manager SHALL return a descriptive error message
6. THE Docker_Manager SHALL support mounting additional directories specified in fix metadata
7. THE Docker_Manager SHALL ensure mounted files are accessible to the container user

### Requirement 5: Global Fix Detection and Risk Assessment

**User Story:** As The Operator, I want to detect when a fix would affect the global system, so that I can assess risk and apply appropriate isolation strategies.

#### Acceptance Criteria

1. THE Risk_Assessor SHALL classify fixes as Global_Fix or Local_Fix based on their target scope
2. THE Risk_Assessor SHALL identify Global_Fix by detecting system-level package manager commands (brew install, apt install, choco install)
3. THE Risk_Assessor SHALL identify Global_Fix by detecting version manager commands (nvm install, pyenv install, rustup install)
4. THE Risk_Assessor SHALL classify fixes modifying only project files as Local_Fix
5. THE Risk_Assessor SHALL assign risk levels: low (Local_Fix), medium (Global_Fix with isolation), high (Global_Fix without isolation)
6. THE Risk_Assessor SHALL return a risk assessment with fields: level, reason, isolation_recommended
7. WHEN a fix is classified as high risk, THE Risk_Assessor SHALL recommend generating an Isolation_Config

### Requirement 6: Fallback to Isolation Config Generation

**User Story:** As The Operator, I want to generate project-specific isolation configs when global fixes are unsafe, so that I can provide working solutions without breaking other projects.

#### Acceptance Criteria

1. THE Config_Generator SHALL generate mise.toml files for tool version isolation
2. THE Config_Generator SHALL generate devcontainer.json files for full environment isolation
3. WHEN a Global_Fix would conflict with other projects, THE Config_Generator SHALL create a mise.toml specifying project-local tool versions
4. WHEN multiple tools need isolation, THE Config_Generator SHALL create a devcontainer.json with all required tools
5. THE Config_Generator SHALL include comments in generated configs explaining why isolation was needed
6. THE Config_Generator SHALL validate generated configs for syntax correctness
7. THE Config_Generator SHALL write generated configs to the Project_Root
8. WHEN a config file already exists, THE Config_Generator SHALL merge new settings with existing ones

### Requirement 7: mise.toml Generation for Tool Isolation

**User Story:** As The Operator, I want to generate mise.toml files, so that I can isolate tool versions to specific projects without affecting global installations.

#### Acceptance Criteria

1. THE Mise_Generator SHALL create mise.toml files with tool version specifications
2. THE Mise_Generator SHALL support specifying versions for: node, python, go, rust, java, ruby
3. THE Mise_Generator SHALL use semantic version format (e.g., node = "20.11.0")
4. THE Mise_Generator SHALL include installation instructions in comments
5. THE Mise_Generator SHALL validate that specified versions are available in mise
6. WHEN mise is not installed, THE Mise_Generator SHALL include mise installation instructions in comments
7. THE Mise_Generator SHALL preserve existing mise.toml settings when adding new tools

### Requirement 8: devcontainer.json Generation for Full Isolation

**User Story:** As The Operator, I want to generate devcontainer.json files, so that I can provide full environment isolation when multiple tools or complex dependencies are needed.

#### Acceptance Criteria

1. THE Devcontainer_Generator SHALL create devcontainer.json files with base image and feature specifications
2. THE Devcontainer_Generator SHALL select base images matching the project's Tech_Stack
3. THE Devcontainer_Generator SHALL include features for required tools (node, python, go, rust, docker-in-docker)
4. THE Devcontainer_Generator SHALL configure port forwarding for common development ports (3000, 8000, 8080, 5173)
5. THE Devcontainer_Generator SHALL set up volume mounts for package manager caches
6. THE Devcontainer_Generator SHALL include postCreateCommand for dependency installation
7. THE Devcontainer_Generator SHALL validate generated JSON for syntax correctness
8. THE Devcontainer_Generator SHALL include comments explaining the isolation strategy

### Requirement 9: Git Hook Installation with GitPython

**User Story:** As The Operator, I want to install git hooks that trigger scans on pull/merge/commit, so that environment issues are detected automatically during development workflows.

#### Acceptance Criteria

1. THE Hook_Manager SHALL use GitPython to access the project's .git directory
2. THE Hook_Manager SHALL install post-merge hooks that trigger `devready scan`
3. THE Hook_Manager SHALL install post-checkout hooks that trigger scans when switching branches
4. THE Hook_Manager SHALL install pre-commit hooks that validate environment compliance
5. THE Hook_Manager SHALL preserve existing hooks by chaining them with new hooks
6. WHEN .git directory does not exist, THE Hook_Manager SHALL return an error indicating the project is not a git repository
7. THE Hook_Manager SHALL make hook scripts executable on Unix-like systems
8. THE Hook_Manager SHALL handle Windows hook execution using bash or sh if available

### Requirement 10: Post-Merge Hook for Environment Validation

**User Story:** As a developer, I want automatic environment scans after git pull or merge, so that I'm immediately notified of new dependencies or tool version changes.

#### Acceptance Criteria

1. THE Post_Merge_Hook SHALL execute `devready scan --quick` after successful merges
2. THE Post_Merge_Hook SHALL detect changes to dependency files (package.json, requirements.txt, Cargo.toml, go.mod)
3. WHEN dependency files changed, THE Post_Merge_Hook SHALL trigger a full scan instead of quick scan
4. THE Post_Merge_Hook SHALL display scan results in the terminal
5. WHEN scan detects issues, THE Post_Merge_Hook SHALL offer to run `devready fix`
6. THE Post_Merge_Hook SHALL complete within 5 seconds to avoid blocking the developer
7. THE Post_Merge_Hook SHALL support a --skip-scan flag to bypass scanning when needed

### Requirement 11: Pre-Commit Hook for Compliance Validation

**User Story:** As a developer, I want automatic compliance checks before commits, so that I don't commit code that requires tools or dependencies I don't have installed.

#### Acceptance Criteria

1. THE Pre_Commit_Hook SHALL execute `devready validate` before allowing commits
2. THE Pre_Commit_Hook SHALL check that all required tools are installed and meet version requirements
3. THE Pre_Commit_Hook SHALL validate that project dependencies are installed
4. WHEN validation fails, THE Pre_Commit_Hook SHALL block the commit and display errors
5. WHEN validation passes, THE Pre_Commit_Hook SHALL allow the commit to proceed
6. THE Pre_Commit_Hook SHALL support a --no-verify flag to bypass validation in emergencies
7. THE Pre_Commit_Hook SHALL complete validation within 3 seconds

### Requirement 12: Terminal Error Detection Hook

**User Story:** As a developer, I want automatic scans when terminal commands fail, so that I can quickly identify if the failure was due to environment issues.

#### Acceptance Criteria

1. THE Error_Hook SHALL integrate with shell history to detect failed commands
2. THE Error_Hook SHALL trigger scans when commands fail with "command not found" errors
3. THE Error_Hook SHALL trigger scans when commands fail with "module not found" or "package not found" errors
4. THE Error_Hook SHALL parse error messages to identify missing tools or dependencies
5. THE Error_Hook SHALL offer to install missing tools automatically
6. THE Error_Hook SHALL support bash, zsh, and fish shells
7. WHEN a scan is triggered by an error, THE Error_Hook SHALL focus on the specific missing component

### Requirement 13: Multi-Package Manager Support

**User Story:** As The Operator, I want to support multiple package managers, so that I can apply fixes across diverse tech stacks and project configurations.

#### Acceptance Criteria

1. THE Package_Manager_Adapter SHALL support npm, yarn, pnpm, and bun for Node.js projects
2. THE Package_Manager_Adapter SHALL support pip, poetry, and pipenv for Python projects
3. THE Package_Manager_Adapter SHALL support cargo for Rust projects
4. THE Package_Manager_Adapter SHALL support go modules for Go projects
5. THE Package_Manager_Adapter SHALL support maven and gradle for Java projects
6. THE Package_Manager_Adapter SHALL detect which package manager a project uses
7. THE Package_Manager_Adapter SHALL generate Fix_Command instances using the detected package manager
8. WHEN multiple package managers are detected, THE Package_Manager_Adapter SHALL use the one specified in project config or default to the most common

### Requirement 14: Fix Application to Host System

**User Story:** As The Operator, I want to apply verified fixes to the host system, so that developers can actually resolve environment issues after validation succeeds.

#### Acceptance Criteria

1. THE Fix_Applicator SHALL execute verified Fix_Command instances on the host system
2. THE Fix_Applicator SHALL require explicit user confirmation before applying Global_Fix instances
3. THE Fix_Applicator SHALL apply Local_Fix instances automatically without confirmation
4. THE Fix_Applicator SHALL capture stdout, stderr, and Exit_Code from host execution
5. WHEN host execution fails, THE Fix_Applicator SHALL rollback changes if possible
6. THE Fix_Applicator SHALL log all applied fixes with timestamps
7. THE Fix_Applicator SHALL update The Architect's state after successful fix application
8. THE Fix_Applicator SHALL re-run scans after applying fixes to verify the issue is resolved

### Requirement 15: Rollback Support for Failed Fixes

**User Story:** As The Operator, I want to rollback failed fixes, so that developers don't end up in a worse state than before attempting the fix.

#### Acceptance Criteria

1. THE Rollback_Manager SHALL create snapshots before applying Global_Fix instances
2. THE Rollback_Manager SHALL store snapshots including: installed packages, tool versions, config files
3. WHEN a fix fails on the host, THE Rollback_Manager SHALL restore the previous state
4. THE Rollback_Manager SHALL support manual rollback via `devready rollback` command
5. THE Rollback_Manager SHALL keep the last 5 snapshots
6. THE Rollback_Manager SHALL clean up old snapshots automatically
7. WHEN rollback fails, THE Rollback_Manager SHALL provide manual recovery instructions

### Requirement 16: Project Isolation Verification

**User Story:** As The Operator, I want to verify that fixes maintain project isolation, so that I can guarantee fixes never break other projects.

#### Acceptance Criteria

1. THE Isolation_Verifier SHALL scan all projects on the system before and after applying fixes
2. THE Isolation_Verifier SHALL detect changes to global tool versions
3. WHEN global changes are detected, THE Isolation_Verifier SHALL verify other projects still work
4. THE Isolation_Verifier SHALL run quick health checks on other projects after Global_Fix application
5. WHEN another project breaks, THE Isolation_Verifier SHALL trigger automatic rollback
6. THE Isolation_Verifier SHALL log isolation verification results
7. THE Isolation_Verifier SHALL complete verification within 15 seconds

### Requirement 17: Dry-Run Execution and Reporting

**User Story:** As a developer, I want to see what a fix will do before applying it, so that I can make informed decisions about environment changes.

#### Acceptance Criteria

1. THE Dry_Run_Executor SHALL execute all fixes in Sandbox_Container before offering to apply them
2. THE Dry_Run_Executor SHALL display Fix_Command, expected changes, and risk level
3. THE Dry_Run_Executor SHALL show stdout and stderr from sandbox execution
4. THE Dry_Run_Executor SHALL indicate whether the fix succeeded in the sandbox
5. WHEN a fix fails in the sandbox, THE Dry_Run_Executor SHALL not offer to apply it to the host
6. THE Dry_Run_Executor SHALL support `--dry-run-only` flag to validate without applying
7. THE Dry_Run_Executor SHALL complete dry-runs within 10 seconds per fix

### Requirement 18: Concurrent Fix Execution

**User Story:** As The Operator, I want to execute multiple independent fixes concurrently, so that I can reduce total fix time when multiple issues are detected.

#### Acceptance Criteria

1. THE Concurrent_Executor SHALL identify independent fixes that can run in parallel
2. THE Concurrent_Executor SHALL execute independent fixes concurrently using separate Sandbox_Container instances
3. THE Concurrent_Executor SHALL limit concurrent executions to 3 to avoid resource exhaustion
4. THE Concurrent_Executor SHALL execute dependent fixes sequentially in correct order
5. WHEN any fix in a dependency chain fails, THE Concurrent_Executor SHALL skip dependent fixes
6. THE Concurrent_Executor SHALL aggregate results from all concurrent executions
7. THE Concurrent_Executor SHALL complete multiple fixes faster than sequential execution

### Requirement 19: Fix Command Parser and Pretty Printer

**User Story:** As The Operator, I want to parse fix commands and provide a pretty printer, so that I can validate round-trip parsing and provide human-readable fix descriptions.

#### Acceptance Criteria

1. THE Fix_Parser SHALL parse Fix_Command strings into structured dictionaries with fields: package_manager, action, target, version
2. THE Fix_Parser SHALL identify package manager from command prefix (npm, pip, cargo, go, mvn)
3. THE Fix_Parser SHALL extract action (install, update, remove, configure)
4. THE Fix_Parser SHALL extract target package or tool name
5. THE Pretty_Printer SHALL format Fix_Command dictionaries into human-readable descriptions
6. THE Pretty_Printer SHALL include risk level and isolation strategy in output
7. FOR ALL valid Fix_Command dictionaries, parsing then pretty printing then parsing SHALL produce an equivalent structure (round-trip property)

### Requirement 20: Container Cleanup and Resource Management

**User Story:** As The Operator, I want to clean up Docker resources after fix execution, so that I don't leave orphaned containers or consume excessive disk space.

#### Acceptance Criteria

1. THE Docker_Manager SHALL remove Sandbox_Container instances immediately after execution
2. THE Docker_Manager SHALL remove dangling images created during fix validation
3. THE Docker_Manager SHALL clean up volumes that are no longer needed
4. THE Docker_Manager SHALL monitor disk space usage and warn when Docker consumes > 10GB
5. THE Docker_Manager SHALL support `devready cleanup` command to manually remove all DevReady containers and images
6. THE Docker_Manager SHALL complete cleanup within 2 seconds
7. WHEN cleanup fails, THE Docker_Manager SHALL log warnings but not block fix execution

### Requirement 21: Error Handling and Recovery

**User Story:** As The Operator, I want robust error handling, so that failures in one fix don't prevent other fixes from being attempted.

#### Acceptance Criteria

1. WHEN Docker is not running, THE Operator SHALL return a clear error message with instructions to start Docker
2. WHEN a Sandbox_Container fails to start, THE Operator SHALL log the error and skip to the next fix
3. WHEN Fix_Command execution fails, THE Operator SHALL capture error details and continue with other fixes
4. THE Operator SHALL never crash due to individual fix failures
5. THE Operator SHALL include an errors list in results with fields: fix_id, error_message, timestamp
6. THE Operator SHALL log all errors to The Architect's logging system
7. WHEN all fixes fail, THE Operator SHALL provide troubleshooting guidance

### Requirement 22: Performance Monitoring for Fix Execution

**User Story:** As a developer, I want to see how long fixes take to execute, so that I can understand the performance impact of environment fixes.

#### Acceptance Criteria

1. THE Performance_Monitor SHALL measure execution time for each fix in sandbox and on host
2. THE Performance_Monitor SHALL include timing data in fix results
3. THE Performance_Monitor SHALL log warnings when any fix exceeds 30 seconds
4. THE Performance_Monitor SHALL track Docker container startup time separately from fix execution time
5. WHEN total fix time exceeds 60 seconds, THE Performance_Monitor SHALL log a performance violation
6. THE Performance_Monitor SHALL support exporting timing data in JSON format
7. THE Performance_Monitor SHALL measure time spent in verification separately from execution

### Requirement 23: Cross-Platform Fix Execution

**User Story:** As The Operator, I want to execute fixes correctly on Windows, macOS, and Linux, so that DevReady works consistently across all supported platforms.

#### Acceptance Criteria

1. THE Platform_Adapter SHALL detect the host operating system
2. THE Platform_Adapter SHALL use platform-specific package managers (brew on macOS, apt on Ubuntu, choco on Windows)
3. THE Platform_Adapter SHALL handle Windows path formats in Docker volume mounts
4. THE Platform_Adapter SHALL use appropriate shell (bash on Unix, PowerShell on Windows) for command execution
5. THE Platform_Adapter SHALL handle line ending differences (LF vs CRLF) in generated config files
6. THE Platform_Adapter SHALL validate that Docker Desktop is running on macOS and Windows
7. THE Platform_Adapter SHALL support WSL2 detection on Windows and prefer Linux-style execution when available

### Requirement 24: Logging and Debugging Support

**User Story:** As a developer, I want comprehensive logging from The Operator, so that I can diagnose fix failures and understand what changes were made.

#### Acceptance Criteria

1. THE Operator SHALL log all fix executions with timestamps, commands, and results
2. THE Operator SHALL log Docker operations at debug level
3. THE Operator SHALL log errors and warnings at appropriate severity levels
4. THE Operator SHALL include context in log messages (project path, fix type, risk level)
5. THE Operator SHALL support configurable log levels: debug, info, warn, error
6. THE Operator SHALL never log sensitive data (API keys, tokens, passwords)
7. THE Operator SHALL write logs to The Architect's logging system

### Requirement 25: Fix Verification and Health Check

**User Story:** As The Operator, I want to verify that applied fixes actually resolved the issues, so that I can confirm the environment is healthy after fix application.

#### Acceptance Criteria

1. THE Fix_Verifier SHALL re-run The Inspector's scans after applying fixes
2. THE Fix_Verifier SHALL compare pre-fix and post-fix scan results
3. THE Fix_Verifier SHALL confirm that reported issues are no longer present
4. WHEN issues persist after fixes, THE Fix_Verifier SHALL report verification failure
5. THE Fix_Verifier SHALL detect new issues introduced by fixes
6. WHEN new issues are detected, THE Fix_Verifier SHALL trigger automatic rollback
7. THE Fix_Verifier SHALL return a verification report with fields: fixed_issues, remaining_issues, new_issues
