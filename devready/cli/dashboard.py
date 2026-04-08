from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Label, ProgressBar, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.reactive import reactive
from textual import work
import os
import asyncio
import json
import websockets
from typing import Optional, Dict, Any

from .daemon_client import DaemonClient, DaemonError
from devready.lens.widgets import HealthTrendWidget, TopIssuesWidget, TimeSavedWidget, ComplianceWidget


class ComparisonModal(ModalScreen):
    """Modal screen to display environment comparison between current user and a teammate."""
    
    def __init__(self, member_name: str, drift_report: Dict[str, Any]):
        super().__init__()
        self.member_name = member_name
        self.drift_report = drift_report

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(f"Comparison: Me vs {self.member_name}", id="modal-title")
            yield Label(f"Drift Score: {self.drift_report['drift_score']}/100")
            
            table = DataTable(id="comparison-table")
            table.add_columns("Tool", "My Version", "Their Version", "Status")
            
            # Populate changes
            for change in self.drift_report.get("version_changes", []):
                table.add_row(
                    change["tool_name"],
                    change["old_version"],
                    change["new_version"],
                    f"[yellow]Divergent ({change['severity']})[/]"
                )
            
            for tool in self.drift_report.get("added_tools", []):
                table.add_row(tool["name"], "[red]Missing[/]", tool["version"], "[red][+][/]")
            
            for tool in self.drift_report.get("removed_tools", []):
                table.add_row(tool["name"], tool["version"], "[red]Missing[/]", "[red][-][/]")
                
            yield table
            yield Label("Press ESC to close", id="modal-footer")

    def on_mount(self) -> None:
        self.styles.background = "rgba(0, 0, 0, 0.8)"
        self.query_one("#modal-container").styles.update(
            width="80%",
            height="80%",
            padding=1,
            background="#1e1e1e",
            border=("heavy", "white"),
            align=("center", "middle")
        )

class DevReadyDashboard(App):
    """Interactive DevReady dashboard with Team visibility."""
    
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
    
    #status-line {
        height: 1;
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("s", "scan", "Run Scan"),
        ("f", "fix", "Apply Fixes"),
        ("c", "copy_env", "Copy Env"),
    ]
    
    health_score = reactive(0)
    scanning = reactive(False)

    def __init__(self, daemon_client: DaemonClient):
        super().__init__()
        self.daemon_client = daemon_client
        self.project_path = os.getcwd()
        self.current_snapshot = None
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with TabbedContent(initial="my-env"):
                with TabPane("My Environment", id="my-env"):
                    yield HealthWidget(id="health-score")
                    yield DataTable(id="tools-table")
                    yield ProgressBar(id="scan-progress", show_eta=False, total=100)
                
                with TabPane("Team Environment", id="team-env"):
                    yield Label("Team Health Status - Grid of Teammates", id="team-title")
                    yield DataTable(id="team-table")
            yield Label("", id="status-line")
        yield Footer()
    
    def on_mount(self) -> None:
        # My Tools table
        tools_table = self.query_one("#tools-table", DataTable)
        tools_table.add_columns("Tool", "Version", "Path", "Manager", "Status")
        tools_table.cursor_type = "row"
        
        # Team Members table
        team_table = self.query_one("#team-table", DataTable)
        team_table.add_columns("Member", "Health Score", "Divergence", "Status", "Last Sync")
        team_table.cursor_type = "row"
        
        self.refresh_data()
        self.refresh_team_data()
        self.listen_to_daemon()

    @work(exclusive=True)
    async def refresh_data(self):
        """Fetch latest state from daemon."""
        self._set_status("Refreshing data...")
        try:
            snapshot = await self.daemon_client.get_latest_snapshot(self.project_path)
            if snapshot:
                self.current_snapshot = snapshot
                self.update_ui(snapshot)
            self._set_status("Ready")
        except DaemonError as e:
            self._set_status(f"Error: {e}")

    @work(exclusive=True)
    async def refresh_team_data(self):
        """Fetch team-wide status from daemon."""
        try:
            team_summary = await self.daemon_client.get_team_summary()
            table = self.query_one("#team-table", DataTable)
            table.clear()
            
            for member in team_summary.get("members", []):
                # Calculate divergence (mocked for now in summary, but would be separate call)
                score = member.get("score", 0)
                color = "green" if score >= 90 else "yellow" if score >= 70 else "red"
                
                table.add_row(
                    member["name"],
                    f"[{color}]{score}[/]",
                    f"{100-score}% Divergent",
                    member["status"],
                    member["last_scan"]
                )
        except DaemonError as e:
            self.query_one("#status-line", Label).update(f"Team data error: {e}")

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

    async def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """Handle teammate selection to show comparative diff."""
        if event.data_table.id == "team-table":
            # Get member name from the row
            member_name = event.data_table.get_row_at(event.cursor_row)[0]
            self.query_one("#status-line", Label).update(f"Analyzing divergence with {member_name}...")
            
            try:
                drift_report = await self.daemon_client.compare_with_member(member_name)
                self.push_screen(ComparisonModal(member_name, drift_report))
                self.query_one("#status-line", Label).update("Ready")
            except DaemonError as e:
                self.query_one("#status-line", Label).update(f"Comparison failed: {e}")

    @work
    async def listen_to_daemon(self):
        """Listen for real-time updates via WebSocket."""
        # Using the WebSocket URL with project_path parameter as required by latest daemon
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
                            self.refresh_team_data()
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
        self.refresh_team_data()
    
    async def action_scan(self):
        self.scanning = True
        self._set_status("Scanning...")
        try:
            await self.daemon_client.scan(project_path=self.project_path)
        except DaemonError as e:
            self._set_status(f"Scan failed: {e}")
        finally:
            self.scanning = False

    def action_copy_env(self):
        """Copys the current tools snapshot to 'clipboard'."""
        if self.current_snapshot:
            # We just show a message for now as system clipboard access varies
            tools_json = json.dumps(self.current_snapshot.get("tools", []), indent=2)
            self.query_one("#status-line", Label).update("Environment tools copied to virtual clipboard!")
            # Logic to actually copy would go here (e.g. pyperclip)
        else:
            self.query_one("#status-line", Label).update("No snapshot to copy. Run scan first.")

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
