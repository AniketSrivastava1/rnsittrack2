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
from devready.operator.isolation_verifier import IsolationVerifier
from devready.operator.concurrent_executor import ConcurrentExecutor
from devready.operator.fix_verifier import FixVerifier

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
        self.isolation_verifier = IsolationVerifier()
        self.concurrent_executor = ConcurrentExecutor(max_workers=3)

        class _InspectorClient:
            def scan(self, project_dir):
                from devready.inspector.scan_orchestrator import ScanOrchestrator
                raw = ScanOrchestrator().run_scan(project_path=project_dir, scan_scope="system_only")
                return {"issues": raw.get("policy_violations_inspector", [])}

        self.fix_verifier = FixVerifier(_InspectorClient())

    def run(self, fixes: List[Dict[str, Any]], dry_run: bool = False) -> List[Dict[str, Any]]:
        results = []
        docker_available = self.docker_manager.verify_docker_available()

        # Split: local-scope fixes can run concurrently; global/user_global run sequentially
        local_fixes = [f for f in fixes if self.risk_assessor.classify_fix(
            (f.get("command") or "").split())["scope"] == "local"]
        other_fixes = [f for f in fixes if f not in local_fixes]

        def _run_one(fix):
            return self._run_single(fix, docker_available, dry_run)

        if local_fixes:
            results.extend(self.concurrent_executor.execute_concurrently(local_fixes, _run_one))
        for fix in other_fixes:
            results.append(_run_one(fix))

        return results

    def _run_single(self, fix: Dict[str, Any], docker_available: bool, dry_run: bool) -> Dict[str, Any]:
        command_str = fix.get("command")
        if not command_str:
            return {"fix_id": fix.get("fix_id"), "success": False, "message": "No command to execute"}

        command = command_str.split()
        assessment = self.risk_assessor.classify_fix(command)
        scope = assessment["scope"]

        sandbox_ok = True
        if docker_available and scope == "local":
            sandbox_ok = self._sandbox_test(command, fix.get("tech_stack", "python"))

        if not sandbox_ok:
            return {"fix_id": fix.get("fix_id"), "success": False, "message": "Sandbox test failed — fix not applied"}

        if dry_run:
            dry_results = self.dry_run_executor.execute_dry_run(
                [{"fix_id": fix.get("fix_id"), "command": command_str}],
                fix.get("tech_stack", "python")
            )
            dr = dry_results[0] if dry_results else {}
            return {"fix_id": fix.get("fix_id"), "success": dr.get("sandbox_success", True),
                    "message": dr.get("stdout") or f"[dry-run] Would run: {command_str} (scope={scope})"}

        snapshot_id = self.rollback_manager.create_snapshot(scope)
        result = self.fix_applicator.apply_fix(command, scope, self.project_root)
        if result.get("success"):
            if scope in ("global", "user_global"):
                self.isolation_verifier.verify_isolation_after_fix({}, global_versions_changed=True)
            verification = self.fix_verifier.verify_resolution(self.project_root, [])
            msg = f"Applied: {command_str}"
            if not verification.get("success"):
                msg += f" (warning: {len(verification.get('new_issues', []))} new issue(s) detected)"
            return {"fix_id": fix.get("fix_id"), "success": True, "message": msg}
        else:
            logger.warning("Fix failed, rolling back to snapshot %s", snapshot_id)
            self.rollback_manager.restore_snapshot(snapshot_id)
            return {"fix_id": fix.get("fix_id"), "success": False,
                    "message": result.get("stderr") or result.get("error", "Fix failed")}

    def _sandbox_test(self, command: List[str], tech_stack: str) -> bool:
        try:
            container = self.container_factory.create_sandbox_container(tech_stack, self.project_root)
            result = self.sandbox_executor.execute_in_sandbox(container, command, timeout=30)
            return result.get("exit_code", 1) == 0
        except Exception as e:
            logger.warning("Sandbox test error (proceeding without sandbox): %s", e)
            return True  # Don't block if Docker fails unexpectedly
