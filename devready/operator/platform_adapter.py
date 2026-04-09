import platform
import os
import logging
import subprocess

logger = logging.getLogger(__name__)

class PlatformAdapter:
    def __init__(self):
        self.os_name = platform.system().lower()
        self.is_windows = self.os_name == 'windows'
        self.is_mac = self.os_name == 'darwin'
        self.is_linux = self.os_name == 'linux'
        self.is_wsl = self._detect_wsl()

    def _detect_wsl(self) -> bool:
        if self.is_linux:
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        return True
            except Exception:
                pass
        return False

    def normalize_path(self, path: str) -> str:
        if self.is_windows and not self.is_wsl:
            return os.path.abspath(path).replace('\\', '/')
        return os.path.abspath(path)

    def get_shell_cmd(self, command: str) -> list[str]:
        if self.is_windows and not self.is_wsl:
            return ["powershell", "-Command", command]
        return ["bash", "-c", command]

    def validate_docker(self) -> bool:
        try:
            subprocess.run(["docker", "info"], check=True, capture_output=True)
            return True
        except Exception:
            if self.is_windows or self.is_mac:
                logger.error("Docker Desktop is not running.")
            return False
