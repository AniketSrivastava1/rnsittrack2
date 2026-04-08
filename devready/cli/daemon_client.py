import httpx
import asyncio
import logging
from typing import Optional, Dict, List, Any
from .config_manager import ConfigManager
from .errors import DaemonError, DaemonNotRunningError, DaemonTimeoutError, DaemonResponseError

logger = logging.getLogger(__name__)

class DaemonClient:
    def __init__(self, base_url: Optional[str] = None):
        self.config = ConfigManager()
        self.base_url = base_url or self.config.get("daemon_url", "http://localhost:8443")
        self.client = httpx.AsyncClient(timeout=30.0, base_url=self.base_url)
    
    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Generic request handler with retry logic."""
        retries = 2
        backoff = 1.0
        
        for attempt in range(retries + 1):
            try:
                response = await self.client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError:
                if attempt == retries:
                    raise DaemonNotRunningError()
            except httpx.TimeoutException:
                if attempt == retries:
                    raise DaemonTimeoutError(f"Daemon request {method} {path} timed out")
            except httpx.HTTPStatusError as e:
                raise DaemonResponseError(e.response.status_code, e.response.text)
            except Exception as e:
                if attempt == retries:
                    raise DaemonError(f"Unexpected error communicating with daemon: {e}")
            
            await asyncio.sleep(backoff)
            backoff *= 2
        
        raise DaemonError("Failed to communicate with daemon after retries")

    async def scan(self, project_path: Optional[str] = None, scope: str = "full") -> Dict[str, Any]:
        """Request a scan from the daemon."""
        return await self._request("POST", "/api/v1/scan", json={"project_path": project_path, "scope": scope})
    
    async def get_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Retrieve a specific snapshot."""
        return await self._request("GET", f"/api/v1/snapshots/{snapshot_id}")
    
    async def get_latest_snapshot(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Get the most recent snapshot for a project."""
        try:
            return await self._request("GET", "/api/v1/snapshots/latest", params={"project_path": project_path})
        except DaemonResponseError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def list_snapshots(self, project_path: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List snapshots with optional project filter."""
        params = {"limit": limit}
        if project_path:
            params["project_path"] = project_path
        return await self._request("GET", "/api/v1/snapshots", params=params)

    async def compare_drift(self, snapshot_a_id: str, snapshot_b_id: str) -> Dict[str, Any]:
        """Compare two snapshots for drift."""
        return await self._request(
            "POST", 
            "/api/v1/drift/compare", 
            json={"snapshot_a_id": snapshot_a_id, "snapshot_b_id": snapshot_b_id}
        )
    
    async def apply_fixes(self, snapshot_id: str, fix_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Apply recommended fixes."""
        return await self._request(
            "POST",
            "/api/v1/fixes/apply",
            json={"snapshot_id": snapshot_id, "fix_ids": fix_ids}
        )
    
    async def check_daemon_health(self) -> bool:
        """Check if daemon is running and responsive."""
        try:
            response = await self.client.get("/api/version", timeout=5.0)
            return response.status_code == 200
        except:
            return False

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()
