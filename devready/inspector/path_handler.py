import os
from pathlib import Path
from typing import Union

class PathHandler:
    """Handles cross-platform path normalization and validation."""

    @staticmethod
    def normalize(path_str: Union[str, Path]) -> str:
        """
        Normalizes a path: expands ~, resolves symlinks, uses forward slashes.
        """
        # 1. Expand ~ and environment variables
        expanded_path = Path(os.path.expandvars(os.path.expanduser(str(path_str))))
        
        # 2. Resolve to absolute path and handle symlinks
        # If path doesn't exist, resolve() might not work as expected on all OSs, 
        # so we resolve the parent if the path itself doesn't exist yet.
        try:
            absolute_path = expanded_path.resolve()
        except (OSError, FileNotFoundError):
            absolute_path = expanded_path.absolute()

        # 3. Normalize to forward slashes regardless of OS
        return str(absolute_path).replace("\\", "/")

    @staticmethod
    def validate_exists(path_str: Union[str, Path]) -> Path:
        """
        Validates that a path exists and returns the Path object.
        
        Raises:
            FileNotFoundError: If the path does not exist.
        """
        path = Path(os.path.expanduser(str(path_str)))
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path_str}")
        return path

    @staticmethod
    def get_project_root_relative(path: Union[str, Path], root: Union[str, Path]) -> str:
        """
        Returns the path relative to the project root.
        """
        p = Path(path).resolve()
        r = Path(root).resolve()
        try:
            return str(p.relative_to(r)).replace("\\", "/")
        except ValueError:
            # Not a subpath of root, return normalized absolute path
            return PathHandler.normalize(p)
