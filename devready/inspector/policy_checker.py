import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PolicyChecker:
    """Checks scan results against team policies."""

    def check(self, policy: Dict[str, Any], scan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validates the scan result against the provided team policy.
        
        Args:
            policy: Dictionary containing rules for required tools and versions.
            scan_result: The result of a full environment scan.
            
        Returns:
            A list of policy violations.
        """
        violations = []
        
        # 1. Check required tools and versions
        required_tools = policy.get("required_tools", {})
        detected_tools = scan_result.get("tools", {})
        
        for tool, constraint in required_tools.items():
            if tool not in detected_tools or detected_tools[tool] is None:
                violations.append({
                    "rule_id": "missing_tool",
                    "severity": "high",
                    "message": f"Required tool '{tool}' is missing from your environment.",
                    "affected_component": tool
                })
            else:
                detected_version = detected_tools[tool]
                if not self._check_version(detected_version, constraint):
                    violations.append({
                        "rule_id": "version_mismatch",
                        "severity": "medium",
                        "message": f"Tool '{tool}' version {detected_version} does not meet policy requirement: {constraint}.",
                        "affected_component": tool
                    })
        
        # 2. Check forbidden tools
        forbidden_tools = policy.get("forbidden_tools", [])
        for tool in forbidden_tools:
            if tool in detected_tools and detected_tools[tool] is not None:
                violations.append({
                    "rule_id": "forbidden_tool",
                    "severity": "high",
                    "message": f"Tool '{tool}' is forbidden by team policy and should be removed.",
                    "affected_component": tool
                })
        
        # 3. Check for vulnerabilities (simplified placeholder logic)
        vulnerabilities = scan_result.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            violations.append({
                "rule_id": "vulnerability",
                "severity": vuln.get("severity", "medium"),
                "message": f"Security vulnerability found in {vuln.get('package')}: {vuln.get('id')}",
                "affected_component": vuln.get("package")
            })

        return violations

    def _check_version(self, actual: str, constraint: str) -> bool:
        """
        Simple version constraint checker.
        Supports exact matches and '>=X.Y.Z'.
        """
        if not constraint:
            return True
            
        if constraint.startswith(">="):
            min_version = constraint[2:].strip()
            return self._compare_versions(actual, min_version) >= 0
        
        return actual == constraint

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compares two semantic version strings."""
        def parse(v):
            return [int(x) for x in re.findall(r"\d+", v)]
            
        import re
        try:
            p1 = parse(v1)
            p2 = parse(v2)
            for i in range(max(len(p1), len(p2))):
                i1 = p1[i] if i < len(p1) else 0
                i2 = p2[i] if i < len(p2) else 0
                if i1 > i2:
                    return 1
                if i1 < i2:
                    return -1
            return 0
        except Exception:
            return 0
