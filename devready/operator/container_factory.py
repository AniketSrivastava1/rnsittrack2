import logging
import time
from typing import List
import python_on_whales
from devready.operator.workspace_mounter import WorkspaceMounter

logger = logging.getLogger(__name__)

TECH_IMAGE_MAPPING = {
    "nodejs": "node:lts-alpine",
    "python": "python:3.11-slim",
    "go": "golang:1.21-alpine",
    "rust": "rust:1.75-slim",
    "java": "eclipse-temurin:21-jdk-alpine"
}

class ContainerFactory:
    def __init__(self):
        self.client = python_on_whales.DockerClient()
        self.workspace_mounter = WorkspaceMounter()

    def get_base_image(self, tech_stack: str) -> str:
        image = TECH_IMAGE_MAPPING.get(tech_stack.lower(), "ubuntu:22.04")
        logger.debug(f"Selected base image {image} for tech stack {tech_stack}")
        return image

    def create_sandbox_container(self, tech_stack: str, workspace_path: str, command: List[str] = None):
        """Create and start a sandbox container with workspace mounted."""
        start_time = time.time()
        image = self.get_base_image(tech_stack)
        mounts = self.workspace_mounter.mount_workspace(workspace_path)
        
        logger.debug(f"Creating sandbox container for {tech_stack} with workspace {workspace_path}")
        
        try:
            kwargs = {
                "volumes": mounts,
                "workdir": "/workspace",
                "remove": True,
                "detach": True,
                "tty": True
            }
            if command:
                container = self.client.run(image, command, **kwargs)
            else:
                container = self.client.run(image, ["tail", "-f", "/dev/null"], **kwargs)
                
            creation_time = time.time() - start_time
            if creation_time > 3.0:
                logger.warning(f"Container creation took {creation_time:.2f}s, exceeding 3s target")
                
            return container
        except python_on_whales.exceptions.DockerException as e:
            logger.error(f"Failed to create sandbox container: {e}")
            raise
