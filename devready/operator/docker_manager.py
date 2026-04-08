import logging
import python_on_whales

logger = logging.getLogger(__name__)

class DockerManager:
    def __init__(self):
        self.client = python_on_whales.DockerClient()

    def verify_docker_available(self) -> bool:
        """Check if Docker is running and available."""
        try:
            self.client.info()
            logger.debug("Docker is available and reachable.")
            return True
        except python_on_whales.exceptions.DockerException as e:
            logger.debug(f"Docker daemon connection error: {e}")
            return False

    def get_docker_version(self) -> str:
        """Get Docker engine version, warning if < 20.10."""
        try:
            version_info = self.client.version()
            version = version_info.server.version
            logger.debug(f"Docker version: {version}")
            
            parts = version.split('.')
            if len(parts) >= 2:
                try:
                    major = int(parts[0])
                    minor = int(parts[1])
                    if major < 20 or (major == 20 and minor < 10):
                        logger.warning(f"Docker version {version} is older than 20.10")
                except ValueError:
                    pass
            return version
        except python_on_whales.exceptions.DockerException as e:
            logger.debug(f"Failed to get docker version: {e}")
            return "unknown"
