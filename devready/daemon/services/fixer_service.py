import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from devready.daemon.models import PolicyViolation
from devready.inspector.subprocess_wrapper import SubprocessWrapper

logger = logging.getLogger(__name__)

class FixRecommendation(BaseModel):
    """Represents a recommended fix for a policy violation."""
    violation: PolicyViolation
    strategy: str
    command: Optional[str] = None
    description: str
    risk_level: str = "low"  # low, medium, high

class FixResult(BaseModel):
    """Result of applying a fix."""
    success: bool
    message: str
    details: Dict[str, Any] = {}

class FixerService:
    """Service for recommending and applying environment fixes."""

    def __init__(self):
        self.wrapper = SubprocessWrapper()

    def get_recommendations(self, violations: List[PolicyViolation]) -> List[FixRecommendation]:
        """Analyzes violations and returns fix recommendations."""
        recommendations = []
        for v in violations:
            rec = self._create_recommendation(v)
            if rec:
                recommendations.append(rec)
        return recommendations

    def _create_recommendation(self, v: PolicyViolation) -> Optional[FixRecommendation]:
        """Maps a violation to a fix recommendation."""
        if v.violation_type == "missing_tool":
            return FixRecommendation(
                violation=v,
                strategy="install_tool",
                description=f"Install {v.tool_or_var_name} using standard package manager.",
                command=self._get_install_command(v.tool_or_var_name),
                risk_level="medium"
            )
        elif v.violation_type == "version_mismatch":
            return FixRecommendation(
                violation=v,
                strategy="update_tool",
                description=f"Update {v.tool_or_var_name} to {v.expected}.",
                command=self._get_update_command(v.tool_or_var_name, v.expected),
                risk_level="medium"
            )
        elif v.violation_type == "missing_env_var":
            return FixRecommendation(
                violation=v,
                strategy="set_env_var",
                description=f"Set missing environment variable: {v.tool_or_var_name}.",
                command=f"export {v.tool_or_var_name}=<value>",
                risk_level="low"
            )
        # TODO: Add more strategies (AI configs, etc.)
        return None

    def _get_install_command(self, tool: str) -> Optional[str]:
        """Returns the best guess for an install command."""
        # Simple heuristic for common tools
        if tool.lower() in ["node", "npm"]:
            return "nvm install node"
        elif tool.lower() == "python":
            return "pyenv install 3.11"
        return f"brew install {tool}"

    def _get_update_command(self, tool: str, version: str) -> Optional[str]:
        """Returns the best guess for an update command."""
        if tool.lower() == "node":
            return f"nvm install {version}"
        return f"brew upgrade {tool}"

    async def apply_fix(self, recommendation: FixRecommendation) -> FixResult:
        """Executes the recommended fix."""
        if not recommendation.command:
            return FixResult(success=False, message="No command provided for this fix.")

        logger.info(f"Applying fix: {recommendation.description}")
        try:
            # We split the command for SubprocessWrapper
            args = recommendation.command.split(" ")
            result = self.wrapper.execute(args, timeout_seconds=60.0)
            
            return FixResult(
                success=True,
                message=f"Successfully applied fix: {recommendation.description}",
                details={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "duration_ms": result.duration_ms
                }
            )
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            return FixResult(
                success=False,
                message=f"Failed to apply fix: {str(e)}",
                details={"error": str(e)}
            )
