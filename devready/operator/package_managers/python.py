from .adapter import PackageManagerAdapter, registry
from typing import List, Optional

class PipAdapter(PackageManagerAdapter):
    name = "pip"
    lock_files = ["requirements.txt"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pkg_str = f"{package}=={version}" if version else package
        return ["pip", action, pkg_str]

class PoetryAdapter(PackageManagerAdapter):
    name = "poetry"
    lock_files = ["poetry.lock"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pkg_str = f"{package}@{version}" if version else package
        if action == "install":
            return ["poetry", "add", pkg_str]
        return ["poetry", action, pkg_str]

class PipenvAdapter(PackageManagerAdapter):
    name = "pipenv"
    lock_files = ["Pipfile.lock"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pkg_str = f"{package}=={version}" if version else package
        if action == "install":
            return ["pipenv", "install", pkg_str]
        return ["pipenv", action, pkg_str]

registry.register("python", PoetryAdapter)
registry.register("python", PipenvAdapter)
registry.register("python", PipAdapter)
