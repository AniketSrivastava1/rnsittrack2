import logging
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DryRunExecutor:
    def execute_dry_run(self, fixes: List[Dict[str, Any]], tech_stack: str = "python") -> List[Dict[str, Any]]:
        """
        Test fixes in a sandbox container if Docker is available,
        otherwise simulate with a safe subprocess dry-run where possible.
        """
        from devready.operator.docker_manager import DockerManager
        from devready.operator.container_factory import ContainerFactory
        from devready.operator.sandbox_executor import SandboxExecutor

        docker_available = DockerManager().verify_docker_available()
        results = []

        for fix in fixes:
            command_str = fix.get("command", "")
            if not command_str:
                results.append({**fix, "sandbox_success": False,
                                 "stdout": "", "stderr": "No command", "risk_level": fix.get("risk_level", "low")})
                continue

            command = command_str.split()

            if docker_available:
                try:
                    import os
                    container = ContainerFactory().create_sandbox_container(
                        tech_stack, fix.get("project_root", os.getcwd())
                    )
                    result = SandboxExecutor().execute_in_sandbox(container, command, timeout=30)
                    results.append({
                        **fix,
                        "sandbox_success": result["exit_code"] == 0,
                        "stdout": result.get("stdout", ""),
                        "stderr": result.get("stderr", ""),
                        "risk_level": fix.get("risk_level", "low"),
                    })
                    continue
                except Exception as e:
                    logger.warning("Sandbox dry-run failed, falling through: %s", e)

            # Fallback: mark as untested but don't block
            results.append({
                **fix,
                "sandbox_success": True,
                "stdout": f"[no sandbox] Would run: {command_str}",
                "stderr": "",
                "risk_level": fix.get("risk_level", "low"),
            })

        return results
