from .adapter import PackageManagerAdapter, registry
from typing import List, Optional

class NpmAdapter(PackageManagerAdapter):
    name = "npm"
    lock_files = ["package-lock.json"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pkg_str = f"{package}@{version}" if version else package
        if action == "install":
            return ["npm", "install", pkg_str]
        return ["npm", action, pkg_str]

class YarnAdapter(PackageManagerAdapter):
    name = "yarn"
    lock_files = ["yarn.lock"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pkg_str = f"{package}@{version}" if version else package
        if action == "install":
            return ["yarn", "add", pkg_str]
        return ["yarn", action, pkg_str]

class PnpmAdapter(PackageManagerAdapter):
    name = "pnpm"
    lock_files = ["pnpm-lock.yaml"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pkg_str = f"{package}@{version}" if version else package
        if action == "install":
            return ["pnpm", "add", pkg_str]
        return ["pnpm", action, pkg_str]

class BunAdapter(PackageManagerAdapter):
    name = "bun"
    lock_files = ["bun.lockb"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pkg_str = f"{package}@{version}" if version else package
        if action == "install":
            return ["bun", "add", pkg_str]
        return ["bun", action, pkg_str]

registry.register("nodejs", PnpmAdapter)
registry.register("nodejs", YarnAdapter)
registry.register("nodejs", BunAdapter)
registry.register("nodejs", NpmAdapter)
