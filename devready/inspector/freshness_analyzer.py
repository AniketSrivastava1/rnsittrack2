import logging
import re
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class FreshnessAnalyzer:
    """Analyzes dependencies for freshness and security updates."""

    def __init__(self, latest_versions_cache: Optional[Dict[str, str]] = None):
        # In a real app, this would be backed by a local DB or network fetcher
        self.latest_versions = latest_versions_cache or {
            "fastapi": "0.109.0",
            "pydantic": "2.6.0",
            "requests": "2.31.0",
            "node": "20.11.0",
            "python": "3.12.1"
        }

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
