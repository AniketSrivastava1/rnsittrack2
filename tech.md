# Architecture & Tech Stack Document
**Product:** DevReady (v2.0)
**Stack Focus:** Python-First, High Developer Velocity, Modular, Test-Driven

## 1. Core Architecture Overview
DevReady operates on a local Client-Daemon architecture. The heavy lifting is done by a background Python daemon, which exposes a local API. Multiple lightweight clients (CLI, System Tray UI, VS Code Extension) interact with this single source of truth.

The final distributable will be packaged via **PyInstaller**, creating a single standalone executable. The end-user does *not* need Python installed on their machine.

## 2. The Core Stack
* **The Daemon (Background Engine):** **FastAPI**. Runs a lightweight, asynchronous local server (e.g., `localhost:8443`) handling all scan requests, sandbox executions, and webhook triggers.
* **The CLI (`devready`):** **Typer**. Native Python CLI framework that utilizes type hints for automatic help generation and robust argument parsing. Communicates with the FastAPI daemon.
* **Local State & Database:** **SQLModel + SQLite**. Stores environment snapshots, historical drift data, and cached dependencies. 
* **VS Code Extension:** **TypeScript + Node.js**. A lightweight "dumb" client that simply polls the FastAPI local daemon for the "Ready to Code" score and displays it in the editor status bar.
* **Desktop App / Tray:** **Pystray** (for the background OS tray icon) and **Textual** (for the terminal-based UI dashboard, avoiding the need for heavy Electron/web view wrappers).

## 3. Mapping Open Source Tools to PRD Features

### Feature 1 & 8: Smart Dependency Scanner & Multi-OS Support
* **Tool:** `osquery-python` + `sh` (wrapping `syft`).
* **Implementation:** `osquery` translates OS state (processes, ports, native packages) into queryable SQL. The daemon uses `syft` to instantly generate JSON Software Bill of Materials (SBOMs) for specific project directories.

### Feature 2, 4 & 6: Env Snapshots, Drift, Policy & AI Config Checker
* **Tool:** **Checkov** + **Pydantic**.
* **Implementation:** "Healthy" environments and team policies are defined as strict Pydantic schemas. The daemon compares the current `osquery`/`syft` output against these schemas. For AI agents, the tool parses `CLAUDE.md` or `.cursorrules`, extracts agent dependencies, and cross-references them against known CVE databases to prevent security drift.

### Feature 7 & 9: Sandboxed Dry-Run & Intelligent Isolation
* **Tool:** **python-on-whales**.
* **Implementation:** Provides a deeply integrated, Pythonic wrapper for the Docker CLI. When a missing dependency is found, the daemon spins up an ephemeral Docker container, mounts the workspace, executes the fix, and asserts the exit code to verify stability before altering host files or generating an isolated `mise.toml` config.

### Feature 3 & 5: Team Env Dashboard & Git Hooks
* **Tool:** **GitPython** + FastAPI endpoints.
* **Implementation:** Integrates directly with the `.git` directory to trigger scans on `git pull` or `git merge`. Team compliance JSONs are securely synced to authorized repositories, allowing the FastAPI dashboard to aggregate fleet health.

## 4. Data Flow (A Standard Execution)
1.  **Trigger:** Developer types `devready scan` (Typer CLI) OR opens VS Code (Extension API call).
2.  **Engine:** Typer sends a request to the FastAPI Daemon.
3.  **Inspect:** FastAPI queries `osquery` for global system state and runs `syft` on the current working directory.
4.  **Evaluate:** The retrieved state is passed through Pydantic validators against the `.devready-team.yaml` policy file.
5.  **Dry-Run (If Error):** If an outdated package is found, `python-on-whales` creates a hidden Docker container, attempts the fix, and returns a success/fail boolean.
6.  **Report:** FastAPI returns the JSON response, and Typer/Textual renders a beautiful, color-coded terminal output offering the verified fix.

## 5. Development Phases

* **Phase 1: The Scanner (CLI + Daemon)**
    * Setup Typer CLI and FastAPI daemon.
    * Integrate `syft` execution and `osquery` for basic package/version mapping.
* **Phase 2: The Sandbox (Docker Execution)**
    * Integrate `python-on-whales`.
    * Build the isolation logic: attempt fix in container -> read exit code -> apply/reject.
* **Phase 3: State & Sync**
    * Implement SQLModel/SQLite for local snapshots.
    * Integrate GitPython to enable team config sharing.
* **Phase 4: The UI Surfaces**
    * Build the TypeScript VS Code extension to read the Daemon's API.
    * Implement the Textual dashboard and Pystray agent.