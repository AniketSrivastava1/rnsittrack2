import time
import logging
import psutil
import json
from typing import Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitors scan execution time and resource usage."""

    def __init__(self, total_budget_seconds: float = 8.0):
        self.total_budget = total_budget_seconds
        self.timings: Dict[str, float] = {}
        self.start_time: float = 0
        self.memory_snap: float = 0

    def start_total_timer(self):
        """Starts the total scan timer."""
        self.start_time = time.perf_counter()
        self.memory_snap = psutil.Process().memory_info().rss / (1024 * 1024)

    @contextmanager
    def measure(self, component_name: str, budget_seconds: Optional[float] = None):
        """Context manager to measure a component's execution time."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - start)
            self.timings[component_name] = round(duration * 1000, 2) # in ms
            
            if budget_seconds and duration > budget_seconds:
                logger.warning(
                    f"Performance violation: component '{component_name}' "
                    f"took {duration:.2f}s (Budget: {budget_seconds}s)"
                )

    def get_summary(self) -> Dict[str, Any]:
        """Returns a summary of performance metrics."""
        total_duration = time.perf_counter() - self.start_time
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        summary = {
            "total_duration_ms": round(total_duration * 1000, 2),
            "component_timings_ms": self.timings,
            "memory_usage_mb": round(final_memory, 2),
            "memory_increase_mb": round(final_memory - self.memory_snap, 2),
            "within_budget": total_duration <= self.total_budget
        }
        
        if not summary["within_budget"]:
            logger.error(
                f"Total scan duration ({total_duration:.2f}s) exceeded budget "
                f"({self.total_budget}s)!"
            )
            
        return summary

    def to_json(self) -> str:
        """Exports timing data in JSON format."""
        return json.dumps(self.get_summary(), indent=2)
