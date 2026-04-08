import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ConcurrentExecutor:
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers

    def execute_concurrently(self, fixes: List[Dict[str, Any]], executor_func) -> List[Dict[str, Any]]:
        """
        Execute independent fixes concurrently.
        """
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for fix in fixes:
                futures.append(executor.submit(executor_func, fix))
                
            for future in futures:
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    logger.error(f"Concurrent execution error: {e}")
                    results.append({"success": False, "error": str(e)})
                    
        return results
