from .adapter import PackageManagerAdapter, registry
from typing import List, Optional

class CargoAdapter(PackageManagerAdapter):
    name = "cargo"
    lock_files = ["Cargo.lock"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        cmd = ["cargo", action if action != "install" else "add", package]
        if version:
            cmd.extend(["@", version])
        return cmd

class GoModulesAdapter(PackageManagerAdapter):
    name = "go"
    lock_files = ["go.sum", "go.mod"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pkg_str = f"{package}@{version}" if version else package
        return ["go", "get", pkg_str]

class MavenAdapter(PackageManagerAdapter):
    name = "maven"
    lock_files = ["pom.xml"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        return ["mvn", "dependency:resolve"]

class GradleAdapter(PackageManagerAdapter):
    name = "gradle"
    lock_files = ["build.gradle", "build.gradle.kts"]
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        return ["./gradlew", "dependencies"]

registry.register("rust", CargoAdapter)
registry.register("go", GoModulesAdapter)
registry.register("java", MavenAdapter)
registry.register("java", GradleAdapter)
