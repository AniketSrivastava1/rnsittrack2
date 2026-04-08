import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import datetime

logger = logging.getLogger(__name__)

class ToolVersion(BaseModel):
    name: str
    version: Optional[str] = None
    manager: Optional[str] = None

class Dependency(BaseModel):
    name: str
    version: str
    type: str
    location: str

class EnvironmentSnapshot(BaseModel):
    timestamp: str
    project_path: str
    project_name: str
    tech_stack: List[str]
    tools: Dict[str, Optional[str]]
    dependencies: List[Dependency]
    env_vars: Dict[str, str]
    ai_configs: Dict[str, Any]
    freshness_score: float
    performance: Dict[str, Any]
    success: bool = True
    errors: List[Dict[str, str]] = Field(default_factory=list)

    from pydantic import field_validator
    
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        try:
            datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError("Timestamp must be in ISO 8601 format")

class ResultValidator:
    """Validates scan results against the EnvironmentSnapshot schema."""

    def validate(self, data: Dict[str, Any]) -> EnvironmentSnapshot:
        """
        Validates the data and returns an EnvironmentSnapshot instance.
        
        Raises:
            pydantic.ValidationError: If the data is invalid.
        """
        try:
            return EnvironmentSnapshot(**data)
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
