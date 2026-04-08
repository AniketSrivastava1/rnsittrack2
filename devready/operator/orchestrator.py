"""Orchestrates the full fix pipeline: assess → sandbox → apply → rollback."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from devready.operator.risk_assessor import RiskAssessor
from devready.operator.docker_manager import DockerManager
from devready.operator.container_factory import ContainerFactory
from devready.operator.sandbox_executor import SandboxExecutor
from devready.operator.dry_run_executor import DryRunExecutor
from devready.operator.fix_applicator import FixApplicator
from devready.operator.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)


class FixOrchestrator:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.risk_assessor = RiskAssessor()
        self.docker_manager = DockerManager()
        self.container_factory = ContainerFactory()
        self.sandbox_executor = SandboxExecutor()
        self.dry_run_executor = DryRunExecutor()
        self.fix_applicator = FixApplicator()
        self.rollback_manager = RollbackManager(project_root)

    def run(self, fixes: List[Dict[str, Any]], dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        For each fix:
          1. Assess risk/scope
          2. If Docker available and local scope → sandbox test first
          3. If dry_run → return sandbox results only
          4. Otherwise → apply on host with rollback on failure
        """
        results = []
        docker_available = self.docker_manager.verify_docker_available()

        for fix in fixes:
            command_str = fix.get("command")
            if not command_str:
                results.append({"fix_id": fix.get("fix_id"), "success": False,
                                 "message": "No command to execute"})
                continue

            command = command_str.split()
            assessment = self.risk_assessor.classify_fix(command)
            scope = assessment["scope"]

            # Sandbox test for local-scope fixes when Docker is available
            sandbox_ok = True
            if docker_available and scope == "local":
                sandbox_ok = self._sandbox_test(command, fix.get("tech_stack", "python"))

            if not sandbox_ok:
                results.append({"fix_id": fix.get("fix_id"), "success": False,
                                 "message": "Sandbox test failed — fix not applied"})
                continue

            if dry_run:
                results.append({"fix_id": fix.get("fix_id"), "success": True,
                                 "message": f"[dry-run] Would run: {command_str} (scope={scope})"})
                continue

            # Create rollback snapshot before applying
            snapshot_id = self.rollback_manager.create_snapshot(scope)

            result = self.fix_applicator.apply_fix(command, scope, self.project_root)
            if result.get("success"):
                results.append({"fix_id": fix.get("fix_id"), "success": True,
                                 "message": f"Applied: {command_str}"})
            else:
                logger.warning("Fix failed, rolling back to snapshot %s", snapshot_id)
                self.rollback_manager.restore_snapshot(snapshot_id)
                results.append({"fix_id": fix.get("fix_id"), "success": False,
                                 "message": result.get("stderr") or result.get("error", "Fix failed")})

        return results

    def _sandbox_test(self, command: List[str], tech_stack: str) -> bool:
        try:
            container = self.container_factory.create_sandbox_container(tech_stack, self.project_root)
            result = self.sandbox_executor.execute_in_sandbox(container, command, timeout=30)
            return result.get("exit_code", 1) == 0
        except Exception as e:
            logger.warning("Sandbox test error (proceeding without sandbox): %s", e)
            return True  # Don't block if Docker fails unexpectedly
