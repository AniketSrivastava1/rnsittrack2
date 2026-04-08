import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages in-memory caching for scan results."""

    def __init__(self):
        # Format: {key: {"data": data, "expiry": timestamp}}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {"hits": 0, "misses": 0}

    def get(self, key: str) -> Optional[Any]:
        """Retrieves data from cache if not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry["expiry"]:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {key}")
                return entry["data"]
            else:
                logger.debug(f"Cache expired: {key}")
                del self._cache[key]
        
        self.stats["misses"] += 1
        return None

    def set(self, key: str, data: Any, ttl_seconds: int) -> None:
        """Stores data in cache with a TTL."""
        self._cache[key] = {
            "data": data,
            "expiry": time.time() + ttl_seconds
        }
        logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")

    def invalidate(self, key: str) -> None:
        """Removes a specific key from the cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache invalidated: {key}")

    def clear(self) -> None:
        """Clears the entire cache."""
        self._cache.clear()
        logger.info("Cache cleared.")

    def get_stats(self) -> Dict[str, int]:
        """Returns cache hit/miss statistics."""
        return self.stats
