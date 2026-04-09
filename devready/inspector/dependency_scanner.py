import json
import logging
import os
import shutil
from typing import Any, Dict, List, Optional

from devready.inspector.subprocess_wrapper import SubprocessWrapper
from devready.inspector.sbom_parser import SBOMParser

logger = logging.getLogger(__name__)

# Dependency files to scan per language when syft is unavailable
_MANIFEST_PARSERS = {
    "python": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.cfg"],
    "node": ["package.json"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "ruby": ["Gemfile"],
    "java": ["pom.xml", "build.gradle"],
    "php": ["composer.json"],
}


class DependencyScanner:
    """Scans projects for dependencies using Syft, with a file-based fallback."""

    def __init__(self, wrapper: Optional[SubprocessWrapper] = None, parser: Optional[SBOMParser] = None):
        self.wrapper = wrapper or SubprocessWrapper()
        self.parser = parser or SBOMParser()

    def scan(self, project_path: str) -> Dict[str, Any]:
        if shutil.which("syft"):
            return self._scan_with_syft(project_path)
        logger.info("syft not found, using manifest fallback for %s", project_path)
        return self._scan_manifests(project_path)

    def _scan_with_syft(self, project_path: str) -> Dict[str, Any]:
        try:
            result = self.wrapper.execute(["syft", project_path, "-o", "json"], timeout_seconds=4.0)
            if result.exit_code == 0:
                parsed = self.parser.parse(result.stdout)
                dependencies = parsed.get("dependencies", [])
                graph = parsed.get("graph", {"nodes": [], "links": []})
                return {"success": True, "dependencies": dependencies, "count": len(dependencies), "graph": graph}
            return {"success": False, "dependencies": [], "error": result.stderr, "graph": {"nodes": [], "links": []}}
        except Exception as e:
            return {"success": False, "dependencies": [], "error": str(e), "graph": {"nodes": [], "links": []}}

    def _scan_manifests(self, project_path: str) -> Dict[str, Any]:
        """Parse dependency manifests directly without syft."""
        dependencies: List[Dict[str, Any]] = []
        nodes: List[Dict[str, Any]] = []
        links: List[Dict[str, Any]] = []

        # Root node
        project_name = os.path.basename(project_path)
        root_id = f"project:{project_name}"
        nodes.append({"id": root_id, "name": project_name, "version": "0.1.0", "type": "project"})

        for lang, files in _MANIFEST_PARSERS.items():
            for filename in files:
                filepath = os.path.join(project_path, filename)
                if not os.path.exists(filepath):
                    continue
                try:
                    deps = self._parse_manifest(filepath, lang)
                    for d in deps:
                        dep_id = f"{lang}:{d['name']}"
                        d["id"] = dep_id
                        dependencies.append(d)
                        nodes.append({
                            "id": dep_id,
                            "name": d["name"],
                            "version": d["version"],
                            "type": d["type"]
                        })
                        links.append({"source": root_id, "target": dep_id, "type": "dependsOn"})
                except Exception as e:
                    logger.debug("Failed to parse %s: %s", filepath, e)
                break  # only parse first matching file per lang

        return {
            "success": True, 
            "dependencies": dependencies, 
            "count": len(dependencies),
            "graph": {"nodes": nodes, "links": links}
        }

    def _parse_manifest(self, filepath: str, lang: str) -> List[Dict[str, Any]]:
        filename = os.path.basename(filepath)
        deps = []

        if filename == "requirements.txt":
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    name, _, version = line.partition("==")
                    name2, _, version2 = name.partition(">=")
                    deps.append({"name": name2.strip() or name.strip(),
                                 "version": version.strip() or version2.strip() or "unknown",
                                 "type": lang, "location": filepath})

        elif filename == "package.json":
            with open(filepath) as f:
                data = json.load(f)
            for section in ("dependencies", "devDependencies"):
                for name, ver in data.get(section, {}).items():
                    deps.append({"name": name, "version": ver.lstrip("^~"),
                                 "type": lang, "location": filepath})

        elif filename == "go.mod":
            with open(filepath) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[0] not in ("module", "go", "require", "//"):
                        deps.append({"name": parts[0], "version": parts[1],
                                     "type": lang, "location": filepath})

        elif filename == "Cargo.toml":
            import re
            with open(filepath) as f:
                content = f.read()
            for m in re.finditer(r'^(\S+)\s*=\s*["\{]([^"}\n]+)', content, re.MULTILINE):
                deps.append({"name": m.group(1), "version": m.group(2).strip(),
                             "type": lang, "location": filepath})

        elif filename == "pyproject.toml":
            import re
            with open(filepath) as f:
                content = f.read()
            for m in re.finditer(r'"([a-zA-Z0-9_\-]+)([>=<!][^"]*)?"', content):
                deps.append({"name": m.group(1), "version": (m.group(2) or "").strip(),
                             "type": lang, "location": filepath})

        else:
            # Generic: just record the manifest file itself
            deps.append({"name": filename, "version": "unknown",
                         "type": lang, "location": filepath})

        return deps
