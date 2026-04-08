import logging
import time
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.metrics = []
        
    def record_execution(self, fix_id: str, sandbox_time: float, host_time: float, docker_startup: float):
        total = sandbox_time + host_time + docker_startup
        
        if total > 30:
            logger.warning(f"Fix {fix_id} took {total:.2f}s, exceeding 30s warning threshold.")
        if total > 60:
            logger.error(f"Performance violation: Fix {fix_id} took {total:.2f}s, exceeding 60s max.")
            
        metric = {
            "fix_id": fix_id,
            "sandbox_time": sandbox_time,
            "host_time": host_time,
            "docker_startup": docker_startup,
            "total_time": total,
            "timestamp": time.time()
        }
        self.metrics.append(metric)
        return metric
        
    def export_json(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.metrics, f, indent=2)
