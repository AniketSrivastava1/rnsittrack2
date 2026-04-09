from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Label, ProgressBar
from textual.containers import Container
from textual.reactive import reactive
from textual import work
import os
import asyncio
import json
import websockets
from typing import Optional, Dict, Any

from .daemon_client import DaemonClient, DaemonError
from devready.lens.widgets import HealthTrendWidget, TopIssuesWidget, TimeSavedWidget, ComplianceWidget


class DevReadyDashboard(App):
    """Interactive DevReady dashboard."""
    
    CSS = """
    Screen {
        background: #1e1e1e;
    }
    
    #main-container {
        padding: 1;
    }
    
    HealthWidget {
        height: 3;
        content-align: center middle;
        border: heavy white;
        margin: 1 0;
    }
    
    DataTable {
        height: 1fr;
        border: solid white;
    }
    
    #footer-info {
        height: 1;
        background: #333333;
        color: #cccccc;
        content-align: center middle;
    }
    
    ProgressBar {
        width: 100%;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("s", "scan", "Run Scan"),
        ("f", "fix", "Apply Fixes"),
    ]
    
    health_score = reactive(0)
    scanning = reactive(False)

    def __init__(self, daemon_client: DaemonClient):
        super().__init__()
        self.daemon_client = daemon_client
        self.project_path = os.getcwd()
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield HealthTrendWidget(daemon_url=self.daemon_client.base_url,
                                    project_path=self.project_path, id="health-trend")
            yield TopIssuesWidget(daemon_url=self.daemon_client.base_url,
                                  project_path=self.project_path, id="top-issues")
            yield TimeSavedWidget(daemon_url=self.daemon_client.base_url,
                                  project_path=self.project_path, id="time-saved")
            yield ComplianceWidget(daemon_url=self.daemon_client.base_url,
                                   project_path=self.project_path, id="compliance")
            yield DataTable(id="tools-table")
            yield ProgressBar(id="scan-progress", show_eta=False, total=100)
            yield Label("", id="status-line")
        yield Footer()
    
    def on_mount(self) -> None:
        table = self.query_one("#tools-table", DataTable)
        table.add_columns("Tool", "Version", "Path", "Manager", "Status")
        table.cursor_type = "row"
        
        self.refresh_data()
        self.listen_to_daemon()

    @work(exclusive=True)
    async def refresh_data(self):
        """Fetch latest state from daemon."""
        self._set_status("Refreshing data...")
        try:
            snapshot = await self.daemon_client.get_latest_snapshot(self.project_path)
            if snapshot:
                self.update_ui(snapshot)
            self._set_status("Ready")
        except DaemonError as e:
            self._set_status(f"Error: {e}")

    def update_ui(self, snapshot: Dict[str, Any]):
        """Update dashboard widgets with snapshot data."""
        self.health_score = snapshot.get("health_score", 0)
        table = self.query_one("#tools-table", DataTable)
        table.clear()
        for tool in snapshot.get("tools", []):
            table.add_row(
                tool.get("name", ""),
                tool.get("version", ""),
                tool.get("path", ""),
                tool.get("manager", ""),
                tool.get("status", "ok")
            )

    @work
    async def listen_to_daemon(self):
        """Listen for real-time updates via WebSocket."""
        ws_url = self.daemon_client.base_url.replace("http", "ws") + f"/ws/scan?project_path={self.project_path}"
        while True:
            try:
                async with websockets.connect(ws_url) as websocket:
                    self._set_status("Connected to daemon")
                    async for message in websocket:
                        data = json.loads(message)
                        if data.get("event") == "scan_started":
                            self.query_one("#scan-progress", ProgressBar).update(progress=0)
                            self._set_status("Scanning...")
                        elif data.get("event") == "scan_complete":
                            self.refresh_data()
            except Exception:
                self._set_status("Reconnecting to daemon...")
                await asyncio.sleep(5)

    def _set_status(self, msg: str) -> None:
        try:
            self.query_one("#status-line", Label).update(msg)
        except Exception:
            pass

    def action_refresh(self):
        self.refresh_data()
    
    async def action_scan(self):
        self.scanning = True
        self._set_status("Scanning...")
        try:
            await self.daemon_client.scan(project_path=self.project_path)
        except DaemonError as e:
            self._set_status(f"Scan failed: {e}")
        finally:
            self.scanning = False

    def action_fix(self):
        self.run_worker(self._apply_fixes(), exclusive=True)

    async def _apply_fixes(self):
        self.query_one("#status-line", Label).update("Fetching fixes...")
        try:
            snapshot = await self.daemon_client.get_latest_snapshot(self.project_path)
            if not snapshot:
                self.query_one("#status-line", Label).update("No snapshot found — run a scan first.")
                return
            fixes = await self.daemon_client.get_fix_recommendations(
                snapshot_id=snapshot.get("snapshot_id")
            )
            if not fixes:
                self.query_one("#status-line", Label).update("No fixes needed.")
                return
            fix_ids = [f["fix_id"] for f in fixes]
            await self.daemon_client.apply_fixes(fix_ids=fix_ids, dry_run=True)
            self.query_one("#status-line", Label).update(f"Dry-run complete for {len(fix_ids)} fix(es).")
        except DaemonError as e:
            self.query_one("#status-line", Label).update(f"Fix error: {e}")
