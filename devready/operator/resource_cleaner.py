import logging
import time
import python_on_whales
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ResourceCleaner:
    def __init__(self):
        self.client = python_on_whales.DockerClient()

    def cleanup_sandbox(self, container_id: str):
        """Remove a sandbox container immediately after execution."""
        try:
            self.client.container.remove(container_id, force=True)
            logger.debug(f"Removed sandbox container {container_id}")
        except Exception as e:
            logger.warning(f"Failed to remove sandbox container {container_id}: {e}")

    def cleanup_all(self):
        """Clean up all dangling images and unused volumes."""
        start_time = time.time()
        logger.info("Starting cleanup of Docker resources...")
        try:
            self.client.image.prune(all=False)
            self.client.volume.prune()
            
            # Disk space could be monitored via system.df()
            # but omitted for simple mock
            
            duration = time.time() - start_time
            if duration > 2:
                logger.warning(f"Cleanup took {duration:.2f}s, exceeding 2s target.")
            logger.info("Cleanup complete.")
        except Exception as e:
            logger.warning(f"Cleanup failed, but execution can continue: {e}")
