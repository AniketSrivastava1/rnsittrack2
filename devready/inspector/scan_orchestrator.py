import logging
import datetime
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from devready.inspector.system_scanner import SystemScanner
from devready.inspector.dependency_scanner import DependencyScanner
from devready.inspector.tool_detector import ToolDetector
from devready.inspector.ai_parser import AIParser
from devready.inspector.root_detector import RootDetector
from devready.inspector.stack_detector import StackDetector
from devready.inspector.env_collector import EnvCollector
from devready.inspector.cache_manager import CacheManager
from devready.inspector.performance_monitor import PerformanceMonitor
from devready.inspector.policy_checker import PolicyChecker
from devready.inspector.freshness_analyzer import FreshnessAnalyzer
from devready.inspector.error_handler import ErrorHandler
from devready.inspector.result_validator import ResultValidator

logger = logging.getLogger(__name__)

class ScanOrchestrator:
    """Orchestrates all scanners to produce a complete environment snapshot."""

    def __init__(self):
        self.system_scanner = SystemScanner()
        self.dependency_scanner = DependencyScanner()
        self.tool_detector = ToolDetector()
        self.ai_parser = AIParser()
        self.root_detector = RootDetector()
        self.stack_detector = StackDetector()
        self.env_collector = EnvCollector()
        self.cache_manager = CacheManager()
        self.performance_monitor = PerformanceMonitor()
        self.policy_checker = PolicyChecker()
        self.freshness_analyzer = FreshnessAnalyzer()
        self.error_handler = ErrorHandler()
        self.validator = ResultValidator()

    def run_scan(self, project_path: Optional[str] = None, scan_scope: str = "full", force_refresh: bool = False) -> Dict[str, Any]:
        """
        Executes a scan of the environment.
        
        Args:
            project_path: Override project detection.
            scan_scope: one of 'full', 'system_only', 'dependencies_only', 'configs_only'.
            force_refresh: bypass cache.
        """
        self.performance_monitor.start_total_timer()
        
        # 1. Detect project root if not provided
        with self.performance_monitor.measure("root_detection", budget_seconds=0.1):
            root = project_path or self.root_detector.detect()
            if not root:
                root = "."
            project_name = self.root_detector.get_project_name(root)

        # 2. Parallel scan setup
        results = {}
        
        # Determine which scans to run
        run_system = scan_scope in ["full", "system_only"]
        run_deps = scan_scope in ["full", "dependencies_only"]
        run_configs = scan_scope in ["full", "configs_only"]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # We wrap scanner calls to handle errors locally
            def safe_scan(name, func, *args):
                with self.performance_monitor.measure(name):
                    try:
                        return func(*args)
                    except Exception as e:
                        self.error_handler.handle(name, e)
                        return None

            # Launch scans conditionally
            futures = {}
            if run_system:
                futures["system"] = executor.submit(safe_scan, "system", self.system_scanner.scan)
                futures["tools"] = executor.submit(safe_scan, "tools", self.tool_detector.detect_all)
            
            if run_configs:
                futures["env"] = executor.submit(safe_scan, "env", self.env_collector.collect, root)
                futures["ai_configs"] = executor.submit(safe_scan, "ai_configs", self.ai_parser.parse_project_configs, root)
                futures["stack"] = executor.submit(safe_scan, "stack", self.stack_detector.detect, root)
            
            if run_deps:
                futures["dependencies"] = executor.submit(safe_scan, "dependencies", self.dependency_scanner.scan, root)

            # Collect results
            sys_info = futures["system"].result() if "system" in futures else {}
            tool_info = futures["tools"].result() if "tools" in futures else {"tools": {}, "version_managers": {}}
            env_info = futures["env"].result() if "env" in futures else {}
            ai_info = futures["ai_configs"].result() if "ai_configs" in futures else {}
            stack_info = futures["stack"].result() if "stack" in futures else ["unknown"]
            dep_res = futures["dependencies"].result() if "dependencies" in futures else {"dependencies": []}

        # 3. Post-processing
        freshness = {"freshness_score": 100.0}
        if run_deps:
            with self.performance_monitor.measure("freshness_analysis"):
                freshness = self.freshness_analyzer.analyze(dep_res.get("dependencies", []))
            
        # 4. Assemble snapshot
        snapshot_data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "project_path": root,
            "project_name": project_name,
            "tech_stack": stack_info,
            "tools": tool_info.get("tools", {}),
            "dependencies": dep_res.get("dependencies", []),
            "env_vars": self.env_collector.get_filtered_env(env_info),
            "ai_configs": ai_info,
            "freshness_score": freshness.get("freshness_score", 100.0),
            "performance": self.performance_monitor.get_summary(),
            "success": not self.error_handler.has_errors(),
            "errors": self.error_handler.get_errors()
        }

        # 5. Validate
        try:
            validated_snapshot = self.validator.validate(snapshot_data)
            return validated_snapshot.model_dump()
        except Exception:
            # Return raw data if validation fails but we still want to see results
            return snapshot_data
