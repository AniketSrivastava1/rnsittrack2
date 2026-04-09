"""Unit tests for the AI Agent Config File Drift Checker (PRD Feature #6)."""
from __future__ import annotations

import os
import tempfile
import textwrap
from pathlib import Path

import pytest

from devready.inspector.ai_parser import AIParser
from devready.inspector.config_parser import ConfigParser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(files: dict[str, str]) -> str:
    """Create a temp project directory with given file paths and contents."""
    d = tempfile.mkdtemp()
    for rel_path, content in files.items():
        full = Path(d) / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
    return d


# ---------------------------------------------------------------------------
# ConfigParser tests
# ---------------------------------------------------------------------------

class TestConfigParser:
    def test_finds_claude_md(self):
        proj = _make_project({"CLAUDE.md": "# Instructions\nALWAYS use type hints."})
        configs = ConfigParser().find_configs(proj)
        names = [c["filename"] for c in configs]
        assert "CLAUDE.md" in names

    def test_finds_cursorrules(self):
        proj = _make_project({".cursorrules": '{"rules": "Use PEP8."}'})
        configs = ConfigParser().find_configs(proj)
        names = [c["filename"] for c in configs]
        assert ".cursorrules" in names

    def test_finds_copilot_instructions(self):
        proj = _make_project({".github/copilot-instructions.md": "NEVER use eval."})
        configs = ConfigParser().find_configs(proj)
        names = [c["filename"] for c in configs]
        assert ".github/copilot-instructions.md" in names

    def test_finds_codex_md(self):
        proj = _make_project({"codex.md": "# Codex Rules\nAlways add docstrings."})
        configs = ConfigParser().find_configs(proj)
        names = [c["filename"] for c in configs]
        assert "codex.md" in names

    def test_finds_windsurfrules(self):
        proj = _make_project({".windsurfrules": "prefer functional style"})
        configs = ConfigParser().find_configs(proj)
        names = [c["filename"] for c in configs]
        assert ".windsurfrules" in names

    def test_no_configs_returns_empty(self):
        proj = _make_project({"README.md": "just a readme"})
        configs = ConfigParser().find_configs(proj)
        assert configs == []

    def test_parse_markdown_extracts_sections(self):
        proj = _make_project({"CLAUDE.md": "# Instructions\nALWAYS use type hints.\n# Stack\nPython"})
        parsed = ConfigParser().find_configs(proj)
        assert parsed
        content = parsed[0]["content"]
        # Should have 'instructions' section
        assert "instructions" in content
        assert "type hints" in content["instructions"].lower()


# ---------------------------------------------------------------------------
# AIParser tests
# ---------------------------------------------------------------------------

class TestAIParser:
    def test_merge_plain_copilot(self):
        proj = _make_project({
            ".github/copilot-instructions.md": "ALWAYS use type hints.\nNEVER use eval."
        })
        result = AIParser().parse_project_configs(proj)
        assert "always use type hints" in result["instructions"].lower()
        assert "never use eval" in result["instructions"].lower()

    def test_merge_cursorrules_json(self):
        proj = _make_project({".cursorrules": '{"rules": "Use semantic commits."}'})
        result = AIParser().parse_project_configs(proj)
        assert "semantic commits" in result["instructions"].lower()

    def test_cursorrules_plain_text(self):
        proj = _make_project({".cursorrules": "Always write tests."})
        result = AIParser().parse_project_configs(proj)
        assert "always write tests" in result["instructions"].lower()

    def test_codex_md_parsed(self):
        proj = _make_project({"codex.md": "# Codex Rules\nPrefer immutability."})
        result = AIParser().parse_project_configs(proj)
        assert "prefer immutability" in result["instructions"].lower()

    def test_windsurfrules_parsed(self):
        proj = _make_project({".windsurfrules": "prefer functional style"})
        result = AIParser().parse_project_configs(proj)
        assert "functional style" in result["instructions"].lower()

    def test_multiple_files_merged(self):
        proj = _make_project({
            "CLAUDE.md": "# Instructions\nALWAYS add type hints.",
            ".cursorrules": "Use semantic commits.",
        })
        result = AIParser().parse_project_configs(proj)
        assert "always add type hints" in result["instructions"].lower()
        assert "semantic commits" in result["instructions"].lower()

    def test_files_found_list(self):
        proj = _make_project({
            "CLAUDE.md": "# Instructions\nALWAYS use type hints.",
            ".github/copilot-instructions.md": "NEVER use eval.",
        })
        result = AIParser().parse_project_configs(proj)
        assert len(result["files_found"]) == 2

    def test_empty_project_returns_empty_instructions(self):
        proj = _make_project({"README.md": "no ai configs here"})
        result = AIParser().parse_project_configs(proj)
        assert result["instructions"].strip() == ""
        assert result["files_found"] == []


# ---------------------------------------------------------------------------
# Central drift tests
# ---------------------------------------------------------------------------

class TestCentralConfigDrift:
    def test_no_drift_when_agent_contains_all_central_rules(self):
        proj = _make_project({
            "CLAUDE.md": "# Instructions\nALWAYS use type hints.\nNEVER use eval.",
            ".github/copilot-instructions.md": "ALWAYS use type hints.\nNEVER use eval.",
        })
        drift = AIParser().get_central_drift(proj)
        # copilot file has both rules -> no drift
        assert drift == []

    def test_drift_detected_when_rule_missing_from_agent(self):
        proj = _make_project({
            "CLAUDE.md": "# Instructions\nALWAYS use type hints.\nNEVER use eval.",
            ".github/copilot-instructions.md": "ALWAYS use type hints.",
        })
        drift = AIParser().get_central_drift(proj)
        assert len(drift) == 1
        assert "never use eval" in drift[0]["missing_rules"][0]
        assert "copilot-instructions.md" in drift[0]["agent_file"]

    def test_no_central_file_means_no_drift(self):
        proj = _make_project({
            ".github/copilot-instructions.md": "ALWAYS use type hints.",
        })
        drift = AIParser().get_central_drift(proj)
        assert drift == []

    def test_no_agent_files_means_no_drift(self):
        proj = _make_project({
            "CLAUDE.md": "# Instructions\nALWAYS use type hints.",
        })
        drift = AIParser().get_central_drift(proj)
        assert drift == []

    def test_multiple_agent_files_checked_independently(self):
        claude_content = "# Instructions\nALWAYS use type hints.\nNEVER use eval."
        proj = _make_project({
            "CLAUDE.md": claude_content,
            ".cursorrules": "ALWAYS use type hints.",              # missing NEVER use eval
            ".github/copilot-instructions.md": "NEVER use eval.", # missing ALWAYS use type hints
        })
        drift = AIParser().get_central_drift(proj)
        agent_files = {d["agent_file"] for d in drift}
        assert ".cursorrules" in agent_files
        assert "copilot-instructions.md" in agent_files


# ---------------------------------------------------------------------------
# Policy violation (via DriftDetectionService)
# ---------------------------------------------------------------------------

class TestAIConfigPolicyViolations:
    def _make_snap(self, instructions: str, project_path: str = ""):
        from devready.daemon.models import EnvironmentSnapshot
        return EnvironmentSnapshot(
            project_path=project_path,
            project_name="test",
            tools=[],
            dependencies={},
            env_vars={},
            health_score=100,
            scan_duration_seconds=0.0,
            ai_configs={"instructions": instructions},
        )

    def _policy(self, required: list[str]):
        from devready.daemon.models import TeamPolicy
        return TeamPolicy(ai_instructions_must_contain=required)

    def test_no_violation_when_rule_present(self):
        from devready.daemon.services.drift_service import DriftDetectionService
        snap = self._make_snap("ALWAYS use type hints. NEVER use eval.")
        policy = self._policy(["ALWAYS use type hints", "NEVER use eval"])
        violations = DriftDetectionService().check_policy_compliance(snap, policy)
        ai_v = [v for v in violations if v.violation_type == "ai_config_drift"]
        assert ai_v == []

    def test_violation_when_rule_missing(self):
        from devready.daemon.services.drift_service import DriftDetectionService
        snap = self._make_snap("ALWAYS use type hints.")
        policy = self._policy(["ALWAYS use type hints", "NEVER use eval"])
        violations = DriftDetectionService().check_policy_compliance(snap, policy)
        ai_v = [v for v in violations if v.violation_type == "ai_config_drift"]
        assert len(ai_v) == 1
        assert "never use eval" in ai_v[0].message.lower()

    def test_case_insensitive_matching(self):
        from devready.daemon.services.drift_service import DriftDetectionService
        snap = self._make_snap("always use TYPE HINTS.")
        policy = self._policy(["ALWAYS use type hints"])
        violations = DriftDetectionService().check_policy_compliance(snap, policy)
        ai_v = [v for v in violations if v.violation_type == "ai_config_drift"]
        assert ai_v == []
