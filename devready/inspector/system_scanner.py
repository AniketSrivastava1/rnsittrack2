import platform
import logging
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)

# Try to import osquery
try:
    import osquery
    OSQUERY_AVAILABLE = True
except ImportError:
    OSQUERY_AVAILABLE = False
    logger.warning("osquery package is not installed.")

class SystemScanner:
    """Scans the local system for packages, ports, and OS info using osquery."""

    def __init__(self):
        self.client = None
        self.is_connected = False

    def _connect(self) -> bool:
        """Attempts to connect to osquery extension socket."""
        if not OSQUERY_AVAILABLE:
            return False
            
        try:
            # On Windows, osquery often uses a named pipe or a default path
            # This is a bit complex as it usually expects osqueryd to be running.
            # For now, we'll implement a safe check.
            self.client = osquery.ExtensionClient()
            self.client.open()
            self.is_connected = True
            return True
        except Exception as e:
            logger.debug(f"Could not connect to osquery: {e}")
            self.is_connected = False
            return False

    def scan(self) -> Dict[str, Any]:
        """
        Performs a full system scan.
        Returns a dictionary with system info.
        """
        start_time = time.perf_counter()
        
        results = {
            "os_info": self.get_os_info(),
            "packages": [],
            "listening_ports": [],
            "scan_duration_ms": 0
        }

        if self._connect():
            try:
                results["packages"] = self.get_installed_packages()
                results["listening_ports"] = self.get_listening_ports()
            except Exception as e:
                logger.error(f"Error during osquery scan: {e}")
            finally:
                if self.client:
                    self.client.close()
        else:
            logger.info("osquery unavailable or not running, returning basic system info.")

        results["scan_duration_ms"] = (time.perf_counter() - start_time) * 1000
        return results

    def get_os_info(self) -> Dict[str, str]:
        """Returns basic OS information using standard library."""
        return {
            "platform": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine()
        }

    def get_installed_packages(self) -> List[Dict[str, str]]:
        """Queries osquery for installed software packages."""
        if not self.is_connected:
            return []

        # Example query for Windows (programs) or Linux/macOS (packages)
        query = ""
        if platform.system() == "Windows":
            query = "SELECT name, version, 'chocolatey' as manager FROM chocolatey_packages"
            # We could also use 'programs' table on Windows
        elif platform.system() == "Darwin":
            query = "SELECT name, version, 'brew' as manager FROM homebrew_packages"
        else:
            query = "SELECT name, version, 'package' as manager FROM deb_packages UNION SELECT name, version, 'package' as manager FROM rpm_packages"

        try:
            response = self.client.extension_query(query)
            if response.status.code == 0:
                return response.response
            return []
        except Exception:
            return []

    def get_listening_ports(self) -> List[Dict[str, Any]]:
        """Queries osquery for listening network ports."""
        if not self.is_connected:
            return []

        query = "SELECT port, address, protocol, family, pid FROM listening_ports"
        try:
            response = self.client.extension_query(query)
            if response.status.code == 0:
                return response.response
            return []
        except Exception:
            return []
