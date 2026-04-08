import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class WorkspaceMounter:
    def format_path_for_docker(self, path: str) -> str:
        """Handle Windows path formatting if necessary."""
        return os.path.abspath(path).replace('\\', '/')

    def mount_workspace(self, project_root: str, additional_dirs: List[str] = None) -> List[Tuple[str, str, str]]:
        """
        Validate and prepare mount configurations for a workspace.
        """
        if not os.path.exists(project_root):
            error_msg = f"Mount failure: Project root '{project_root}' does not exist."
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if not os.path.isdir(project_root):
            error_msg = f"Mount failure: Project root '{project_root}' is not a directory."
            logger.error(error_msg)
            raise ValueError(error_msg)

        formatted_root = self.format_path_for_docker(project_root)
        
        # Volumes expected by python_on_whales: list of tuple (host_path, container_path, mode)
        mounts = [(formatted_root, "/workspace", "rw")]
        
        if additional_dirs:
            for idx, d in enumerate(additional_dirs):
                if not os.path.exists(d):
                    logger.warning(f"Additional mount directory '{d}' does not exist, skipping.")
                    continue
                formatted_dir = self.format_path_for_docker(d)
                mounts.append((formatted_dir, f"/additional_{idx}", "rw"))
                
        logger.debug(f"Prepared mounts: {mounts}")
        return mounts
