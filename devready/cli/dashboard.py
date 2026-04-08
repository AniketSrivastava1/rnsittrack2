from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Label, ProgressBar
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual import work
import os
import asyncio
import json
import websockets
from typing import Optional, Dict, List, Any

from .daemon_client import DaemonClient, DaemonError

class HealthWidget(Static):
    """Widget to display the health score."""
    score = reactive(0)
    
    def render(self) -> str:
        if self.score >= 90:
            color, emoji = "green", "✅"
        elif self.score >= 70:
            color, emoji = "yellow", "⚠️"
        else:
            color, emoji = "red", "❌"
        return f"{emoji} Health Score: [#ffffff on {color}]{self.score}/100[/]"

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
            yield HealthWidget(id="health-score")
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
        self.query_one("#status-line", Label).update("Refreshing data...")
        try:
            snapshot = await self.daemon_client.get_latest_snapshot(self.project_path)
            if snapshot:
                self.update_ui(snapshot)
            self.query_one("#status-line", Label).update("Ready")
        except DaemonError as e:
            self.query_one("#status-line", Label).update(f"Error: {e}")

    def update_ui(self, snapshot: Dict[str, Any]):
        """Update dashboard widgets with snapshot data."""
        self.health_score = snapshot.get("health_score", 0)
        self.query_one("#health-score", HealthWidget).score = self.health_score
        
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
        # Using a hypothetical WebSocket URL based on base_url
        ws_url = self.daemon_client.base_url.replace("http", "ws") + f"/ws/scan?project_path={self.project_path}"
        while True:
            try:
                async with websockets.connect(ws_url) as websocket:
                    self.query_one("#status-line", Label).update("Connected to daemon")
                    async for message in websocket:
                        data = json.loads(message)
                        if data["type"] == "scan_progress":
                            self.query_one("#scan-progress", ProgressBar).update(progress=data["progress"])
                        elif data["type"] == "scan_complete":
                            self.refresh_data()
            except Exception:
                self.query_one("#status-line", Label).update("Reconnecting to daemon...")
                await asyncio.sleep(5)

    def action_refresh(self):
        self.refresh_data()
    
    async def action_scan(self):
        self.scanning = True
        self.query_one("#status-line", Label).update("Scanning...")
        try:
            await self.daemon_client.scan(project_path=self.project_path)
            # Scan result will come via WebSocket or we'll refresh later
        except DaemonError as e:
            self.query_one("#status-line", Label).update(f"Scan failed: {e}")
        finally:
            self.scanning = False

    def action_fix(self):
        # Implementation for fix action...
        pass
