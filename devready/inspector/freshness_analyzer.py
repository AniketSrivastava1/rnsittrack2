import logging
import re
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class FreshnessAnalyzer:
    """Analyzes dependencies for freshness. Version data loaded from a JSON file if present."""

    _BUILTIN_VERSIONS = {
        "fastapi": "0.115.0", "pydantic": "2.7.0", "requests": "2.32.0",
        "uvicorn": "0.30.0", "sqlalchemy": "2.0.30", "httpx": "0.27.0",
        "typer": "0.12.0", "rich": "13.7.0",
        "node": "22.0.0", "python": "3.12.3", "go": "1.22.0",
        "rust": "1.78.0", "docker": "26.0.0",
    }

    def __init__(self, latest_versions_cache: dict | None = None):
        import json, os
        self.latest_versions = dict(self._BUILTIN_VERSIONS)
        # Allow override via ~/.devready/versions.json
        versions_file = os.path.expanduser("~/.devready/versions.json")
        if os.path.exists(versions_file):
            try:
                with open(versions_file) as f:
                    self.latest_versions.update(json.load(f))
            except Exception:
                pass
        if latest_versions_cache:
            self.latest_versions.update(latest_versions_cache)

    def analyze(self, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes a list of dependencies and returns freshness info.
        """
        results = []
        scores = []
        
        for dep in dependencies:
            name = dep.get("name")
            current_version = dep.get("version")
            latest_version = self.latest_versions.get(name)
            
            if not latest_version:
                results.append(self._create_entry(dep, "unknown"))
                scores.append(100) # Neutral score for unknown
                continue
                
            status = self._get_status(current_version, latest_version)
            results.append(self._create_entry(dep, status, latest_version))
            
            # Scoring logic
            if status == "current":
                scores.append(100)
            elif status == "minor_update_available":
                scores.append(80)
            elif status == "major_update_available":
                scores.append(40)
            elif status == "deprecated":
                scores.append(0)
            
        freshness_score = sum(scores) / len(scores) if scores else 100
        
        return {
            "freshness_score": round(freshness_score, 1),
            "analysis": results,
            "timestamp": time.time()
        }

    def _get_status(self, current: str, latest: str) -> str:
        """Categorizes the update status based on semver comparison."""
        try:
            c_parts = [int(x) for x in re.findall(r"\d+", current)]
            l_parts = [int(x) for x in re.findall(r"\d+", latest)]
            
            if c_parts == l_parts:
                return "current"
                
            if len(c_parts) >= 1 and len(l_parts) >= 1:
                if c_parts[0] < l_parts[0]:
                    return "major_update_available"
                if len(c_parts) >= 2 and len(l_parts) >= 2:
                    if c_parts[1] < l_parts[1]:
                        return "minor_update_available"
            
            return "current" # Or patch_update_available if we want more detail
        except Exception:
            return "unknown"

    def _create_entry(self, dep: Dict[str, Any], status: str, latest: Optional[str] = None) -> Dict[str, Any]:
        return {
            "name": dep.get("name"),
            "current_version": dep.get("version"),
            "latest_version": latest,
            "status": status,
            "affected_component": dep.get("name")
        }
