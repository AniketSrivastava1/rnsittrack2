import typer
import asyncio
import os
import sys
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from functools import wraps

from rich.table import Table

from .daemon_client import DaemonClient, DaemonError
from .formatter import RichFormatter
from .config_manager import ConfigManager

logger = logging.getLogger("devready")

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)] if verbose else []
    )

app = typer.Typer(
    name="devready",
    help="DevReady - Your Dev Environment Health Co-Pilot",
    add_completion=True,
    rich_markup_mode="rich"
)

class CLIContext:
    def __init__(self, verbose: bool, quiet: bool, json_output: bool, no_color: bool):
        self.verbose = verbose
        self.quiet = quiet
        self.json_output = json_output
        self.no_color = no_color
        self.client = DaemonClient()
        self.formatter = RichFormatter(no_color=no_color)

def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
):
    """DevReady CLI - Environment health monitoring and fixing."""
    setup_logging(verbose)
    ctx.obj = CLIContext(
        verbose=verbose,
        quiet=quiet,
        json_output=json_output,
        no_color=no_color
    )

def _load_team_policy(project_root: str) -> Optional[Dict[str, Any]]:
    """Look for .devready-team.yaml and load it as a dictionary."""
    import yaml
    policy_path = Path(project_root) / ".devready-team.yaml"
    if policy_path.exists():
        try:
            with open(policy_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            pass
    return None

@app.command()
@coro
async def scan(
    ctx: typer.Context,
    scope: str = typer.Option("full", "--scope", help="Scan scope: full, system, dependencies, configs"),
    project: Optional[str] = typer.Option(None, "--project", help="Project path to scan"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git detection"),
    no_docker: bool = typer.Option(False, "--no-docker", help="Skip docker detection"),
    no_node: bool = typer.Option(False, "--no-node", help="Skip node/npm detection"),
    no_java: bool = typer.Option(False, "--no-java", help="Skip java detection"),
    no_python: bool = typer.Option(False, "--no-python", help="Skip python detection"),
    no_syft: bool = typer.Option(False, "--no-syft", help="Skip syft detection"),
    no_vms: bool = typer.Option(False, "--no-vms", help="Skip all version manager detection (nvm, pyenv, etc.)"),
    no_deps: bool = typer.Option(False, "--no-deps", help="Skip dependency scanning"),
    no_system: bool = typer.Option(False, "--no-system", help="Skip system scanning"),
):
    """Scan your development environment for issues."""
    context = ctx.obj
    
    ignore_tools = []
    if no_git: ignore_tools.append("git")
    if no_docker: ignore_tools.append("docker")
    if no_node: ignore_tools.append("node")
    if no_java: ignore_tools.append("java")
    if no_python: ignore_tools.append("python")
    if no_syft: ignore_tools.append("syft")
    if no_vms:
        ignore_tools.extend(["nvm", "pyenv", "asdf", "mise", "rustup", "sdkman"])

    with context.formatter.show_progress(f"Scanning {scope}...") as progress:
        progress.add_task(description=f"Scanning {scope}...", total=None)
        try:
            result = await context.client.scan(
                project_path=project or os.getcwd(), 
                scope=scope,
                ignore_tools=ignore_tools,
                ignore_deps=no_deps,
                ignore_system=no_system,
                team_policy=_load_team_policy(project or os.getcwd())
            )
            
            if context.json_output:
                import json
                print(json.dumps(result))
                return

            context.formatter.print_health_score(result.get("health_score", 0))
            context.formatter.print_violations(result.get("violations", []))
            context.formatter.print_tool_table(result.get("tools", []))
            
            if result.get("health_score", 100) < 70:
                sys.exit(1)
        except DaemonError as e:
            context.formatter.print_error(str(e))
            sys.exit(1)

@app.command()
@coro
async def status(ctx: typer.Context):
    """Show current environment health status."""
    context = ctx.obj
    try:
        snapshot = await context.client.get_latest_snapshot(os.getcwd())
        if not snapshot:
            context.formatter.print_error("No snapshots found.", "Run 'devready scan' first.")
            return

        if context.json_output:
            import json
            print(json.dumps(snapshot))
            return

        context.formatter.print_health_score(snapshot.get("health_score", 0))
        context.formatter.print_violations(snapshot.get("violations", []))
        context.formatter.print_tool_table(snapshot.get("tools", []))
    except DaemonError as e:
        context.formatter.print_error(str(e))
        sys.exit(1)

@app.command()
@coro
async def drift(
    ctx: typer.Context,
    baseline: Optional[str] = typer.Option(None, "--baseline", help="Baseline snapshot ID"),
    policy: bool = typer.Option(False, "--policy", help="Compare against team policy"),
):
    """Show environment drift since last scan."""
    context = ctx.obj
    try:
        if policy:
            # Policy drift logic would go here
            context.formatter.print_error("Policy drift not yet implemented.")
            return

        # Get current and baseline snapshots
        current_task = context.client.get_latest_snapshot(os.getcwd())
        if baseline:
            baseline_task = context.client.get_snapshot(baseline)
        else:
            # If no baseline, compare with second latest? 
            # For now, just handle explicit baseline or latest vs daemon state
            context.formatter.print_error("Please specify a baseline ID or use --policy.")
            return
            
        current, base = await asyncio.gather(current_task, baseline_task)
        
        if not current or not base:
            context.formatter.print_error("Snapshots not found.")
            return

        report = await context.client.compare_drift(base["id"], current["id"])
        
        if context.json_output:
            import json
            print(json.dumps(report))
            return

        context.formatter.print_drift_report(report)
    except DaemonError as e:
        context.formatter.print_error(str(e))
        sys.exit(1)

@app.command()
@coro
async def fix(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview fixes without applying"),
    auto_approve: bool = typer.Option(False, "--yes", "-y", help="Auto-approve all fixes"),
):
    """Apply recommended fixes for detected issues."""
    context = ctx.obj
    try:
        snapshot = await context.client.get_latest_snapshot(os.getcwd())
        if not snapshot:
            context.formatter.print_error("No snapshots found. Run scan first.")
            return

        # Assuming the snapshot contains fix recommendations
        fixes = snapshot.get("fixes", [])
        
        if context.json_output:
            import json
            print(json.dumps(fixes))
            return

        context.formatter.print_fix_recommendations(fixes)
        
        if dry_run or not fixes:
            return

        if not auto_approve:
            if not typer.confirm("Apply these fixes?"):
                return
        
        with context.formatter.show_progress("Applying fixes...") as progress:
            progress.add_task(description="Applying fixes...", total=None)
            results = await context.client.apply_fixes(snapshot["id"])
            # Display results...
            context.formatter.console.print("\n[bold green]Fixes applied successfully![/bold green]")
    except DaemonError as e:
        context.formatter.print_error(str(e))
        sys.exit(1)

# --- Team Commands ---
team_app = typer.Typer(help="Team environment and policy management")
app.add_typer(team_app, name="team")

@team_app.command("status")
@coro
async def team_status(ctx: typer.Context):
    """View team environment health and compliance."""
    context = ctx.parent.obj
    try:
        data = await context.client._request("GET", "/api/v1/team/status") # Hypothetical endpoint
        if context.json_output:
            import json
            print(json.dumps(data))
            return
        
        # Format team status table
        table = Table(title="Team Health Status")
        table.add_column("Member", style="bold")
        table.add_column("Score")
        table.add_column("Compliance")
        
        for member in data.get("members", []):
            table.add_row(member["name"], str(member["score"]), member["compliance"])
        
        context.formatter.console.print(table)
    except DaemonError as e:
        context.formatter.print_error(str(e))

@team_app.command("sync")
@coro
async def team_sync(ctx: typer.Context):
    """Sync current environment snapshot with the team."""
    context = ctx.parent.obj
    try:
        if not typer.confirm("This will upload your environment metadata to the team repository. Proceed?"):
            return
        
        with context.formatter.show_progress("Syncing with team...") as progress:
            progress.add_task(description="Syncing...", total=None)
            await context.client._request("POST", "/api/v1/team/sync")
            context.formatter.console.print("[green]Successfully synced with team.[/green]")
    except DaemonError as e:
        context.formatter.print_error(str(e))

# --- History Commands ---
@app.command()
@coro
async def history(
    ctx: typer.Context,
    limit: int = typer.Option(10, "--limit", help="Number of snapshots to show"),
    project: Optional[str] = typer.Option(None, "--project", help="Filter by project"),
):
    """View environment history and trends."""
    context = ctx.obj
    try:
        snapshots = await context.client.list_snapshots(project_path=project, limit=limit)
        
        if context.json_output:
            import json
            print(json.dumps(snapshots))
            return

        table = Table(title="Snapshot History")
        table.add_column("ID", style="dim")
        table.add_column("Timestamp")
        table.add_column("Score")
        table.add_column("Project")
        
        for s in snapshots:
            table.add_row(s["id"][:8], s["timestamp"], str(s["health_score"]), s["project_name"])
        
        context.formatter.console.print(table)
    except DaemonError as e:
        context.formatter.print_error(str(e))

# --- Doctor Command ---
@app.command()
@coro
async def doctor(ctx: typer.Context):
    """Run diagnostics on DevReady installation."""
    context = ctx.obj
    context.formatter.console.print("[bold]Running DevReady Diagnostics...[/bold]\n")
    
    checks = [
        ("Daemon connectivity", context.client.check_daemon_health),
        # Add more checks here
    ]
    
    all_pass = True
    for name, check_fn in checks:
        passed = await check_fn() if asyncio.iscoroutinefunction(check_fn) else check_fn()
        status_text = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        context.formatter.console.print(f"  {name:.<30} {status_text}")
        if not passed:
            all_pass = False
            
    if all_pass:
        context.formatter.console.print("\n[bold green]Environment looks healthy![/bold green]")
    else:
        context.formatter.console.print("\n[bold red]Issues detected. Please check the logs.[/bold red]")

# --- Snapshot Commands ---
snapshot_app = typer.Typer(help="Manage environment snapshots")
app.add_typer(snapshot_app, name="snapshot")

@snapshot_app.command("create")
@coro
async def snapshot_create(ctx: typer.Context, name: Optional[str] = typer.Argument(None)):
    """Create a new environment snapshot."""
    context = ctx.parent.obj
    try:
        with context.formatter.show_progress("Creating snapshot...") as progress:
            progress.add_task(description="Scanning...", total=None)
            result = await context.client.scan(project_path=os.getcwd())
            context.formatter.console.print(f"[green]Snapshot created: {result['id']}[/green]")
    except DaemonError as e:
        context.formatter.print_error(str(e))

@snapshot_app.command("list")
@coro
async def snapshot_list(ctx: typer.Context):
    """List all available snapshots."""
    # Re-use history logic for now
    await history(ctx, limit=20, project=None)

@snapshot_app.command("delete")
@coro
async def snapshot_delete(ctx: typer.Context, snapshot_id: str):
    """Delete a specific snapshot."""
    context = ctx.parent.obj
    try:
        if not typer.confirm(f"Delete snapshot {snapshot_id}?"):
            return
        await context.client._request("DELETE", f"/api/v1/snapshots/{snapshot_id}")
        context.formatter.console.print("[green]Snapshot deleted.[/green]")
    except DaemonError as e:
        context.formatter.print_error(str(e))

# --- Daemon Commands ---
daemon_app = typer.Typer(help="Control the background daemon process")
app.add_typer(daemon_app, name="daemon")

@daemon_app.command("status")
@coro
async def daemon_status(ctx: typer.Context):
    """Check if the daemon is running."""
    context = ctx.parent.obj
    is_running = await context.client.check_daemon_health()
    if is_running:
        context.formatter.console.print("[green]Daemon is running on http://localhost:8443[/green]")
    else:
        context.formatter.console.print("[red]Daemon is NOT running.[/red]")

@daemon_app.command("start")
def daemon_start():
    """Start the DevReady daemon."""
    # Logic to start the daemon process (e.g. using subprocess)
    print("Starting daemon...")

@daemon_app.command("stop")
def daemon_stop():
    """Stop the DevReady daemon."""
    print("Stopping daemon...")

@app.command()
def dashboard():
    """Launch interactive terminal dashboard."""
    from .dashboard import DevReadyDashboard
    from .daemon_client import DaemonClient
    
    client = DaemonClient()
    app = DevReadyDashboard(client)
    app.run()

if __name__ == "__main__":
    app()
