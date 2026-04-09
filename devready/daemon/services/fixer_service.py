import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from devready.daemon.models import PolicyViolation
from devready.inspector.subprocess_wrapper import SubprocessWrapper, SubprocessError

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
        return [r for r in (_create_recommendation(v) for v in violations) if r is not None]

    async def apply_fix(self, recommendation: FixRecommendation) -> FixResult:
        """Executes the recommended fix."""
        if not recommendation.command:
            return FixResult(success=False, message="No command provided for this fix.")
        logger.info("Applying fix: %s", recommendation.description)
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: self.wrapper.execute(recommendation.command.split(), timeout_seconds=60.0)
            )
            return FixResult(
                success=True,
                message=f"Successfully applied fix: {recommendation.description}",
                details={"stdout": result.stdout, "stderr": result.stderr, "duration_ms": result.duration_ms},
            )
        except SubprocessError as e:
            logger.error("Fix command failed: %s", e)
            return FixResult(success=False, message=str(e), details={"stderr": e.result.stderr})
        except Exception as e:
            logger.error("Failed to apply fix: %s", e)
            return FixResult(success=False, message=f"Failed to apply fix: {e}")


def _create_recommendation(v: PolicyViolation) -> Optional[FixRecommendation]:
    """Maps a violation to a fix recommendation."""
    if v.violation_type == "missing_tool":
        version_suffix = f"@{v.expected}" if v.expected else ""
        return FixRecommendation(
            violation=v,
            strategy="install_tool",
            description=f"Install {v.tool_or_var_name} using mise.",
            command=f"mise install {v.tool_or_var_name}{version_suffix}",
            risk_level="medium",
        )
    if v.violation_type == "version_mismatch":
        return FixRecommendation(
            violation=v,
            strategy="update_tool",
            description=f"Update {v.tool_or_var_name} to {v.expected}.",
            command=f"mise use {v.tool_or_var_name}@{v.expected or 'latest'}",
            risk_level="medium",
        )
    if v.violation_type == "missing_env_var":
        return FixRecommendation(
            violation=v,
            strategy="set_env_var",
            description=f"Set missing environment variable: {v.tool_or_var_name}.",
            command=f"export {v.tool_or_var_name}=<value>",
            risk_level="low",
        )
    return None
