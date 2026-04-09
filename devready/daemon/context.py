"""Project context detection - finds project root and name."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

import tomllib  # Python 3.11+

logger = logging.getLogger(__name__)

_MARKERS = [".git", "pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml"]


def _find_project_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for directory in [current, *current.parents]:
        for marker in _MARKERS:
            if (directory / marker).exists():
                return directory
    return None


def _extract_project_name(root: Path) -> str:
    # Try pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text())
            name = data.get("project", {}).get("name") or data.get("tool", {}).get("poetry", {}).get("name")
            if name:
                return str(name)
        except Exception:
            pass

    # Try package.json
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            if data.get("name"):
                return str(data["name"])
        except Exception:
            pass

    # Try Cargo.toml
    cargo = root / "Cargo.toml"
    if cargo.exists():
        try:
            data = tomllib.loads(cargo.read_text())
            name = data.get("package", {}).get("name")
            if name:
                return str(name)
        except Exception:
            pass

    return root.name


class ContextDetector:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[str, str]] = {}

    def detect(self, working_directory: Optional[str] = None) -> Tuple[str, str]:
        """Return (project_path, project_name) for the given directory."""
        wd = working_directory or str(Path.cwd())
        if wd not in self._cache:
            start = Path(wd)
            root = _find_project_root(start)
            if root is None:
                self._cache[wd] = (str(start.resolve()), start.resolve().name)
            else:
                self._cache[wd] = (str(root), _extract_project_name(root))
        return self._cache[wd]

    def invalidate(self, working_directory: str) -> None:
        """Clear cached result for a path (call after fixes that may rename/change project)."""
        self._cache.pop(working_directory, None)
