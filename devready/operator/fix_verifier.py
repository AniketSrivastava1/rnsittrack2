import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FixVerifier:
    def __init__(self, inspector_client):
        self.inspector = inspector_client

    def verify_resolution(self, project_dir: str, pre_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Re-run scans to verify issue resolution."""
        logger.info(f"Verifying fixes in {project_dir}")
        
        post_issues = self.inspector.scan(project_dir).get("issues", [])
        
        resolved = []
        remaining = []
        new_issues = []
        
        pre_ids = {i.get("id") for i in pre_issues}
        post_ids = {i.get("id") for i in post_issues}
        
        for p in pre_issues:
            if p.get("id") in post_ids:
                remaining.append(p)
            else:
                resolved.append(p)
                
        for p in post_issues:
            if p.get("id") not in pre_ids:
                new_issues.append(p)
                
        if new_issues:
            logger.warning(f"Detected {len(new_issues)} new issues after fix application.")
            
        return {
            "resolved": resolved,
            "remaining": remaining,
            "new_issues": new_issues,
            "success": len(remaining) == 0 and len(new_issues) == 0
        }
