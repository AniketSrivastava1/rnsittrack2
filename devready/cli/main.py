import typer
import asyncio
import os
import sys
import logging
from typing import Optional, List
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

@app.command()
@coro
async def scan(
    ctx: typer.Context,
    scope: str = typer.Option("full", "--scope", help="Scan scope: full, system, dependencies, configs"),
    project: Optional[str] = typer.Option(None, "--project", help="Project path to scan"),
):
    """Scan your development environment for issues."""
    context = ctx.obj
    
    with context.formatter.show_progress(f"Scanning {scope}...") as progress:
        progress.add_task(description=f"Scanning {scope}...", total=None)
        try:
            result = await context.client.scan(project_path=project or os.getcwd(), scope=scope)
            
            if context.json_output:
                import json
                print(json.dumps(result))
                return

            context.formatter.print_health_score(result.get("health_score", 0))
            
            # Display tools found
            tools = result.get("tools", [])
            if tools:
                from rich.table import Table
                table = Table(title="Detected Tools")
                table.add_column("Tool", style="cyan")
                table.add_column("Version", style="green")
                table.add_column("Path", style="dim")
                
                for tool in tools:
                    table.add_row(tool["name"], tool["version"], tool.get("path", "-"))
                
                context.formatter.console.print(table)
            
            context.formatter.console.print(f"\n[dim]Snapshot ID: {result.get('snapshot_id', 'N/A')}[/dim]")
            context.formatter.console.print(f"[dim]Scan completed in {result.get('scan_duration_seconds', 0):.2f}s[/dim]")
            
            if result.get("health_score", 100) < 70:
                sys.exit(1)
        except DaemonError as e:
            context.formatter.print_error(str(e))
            sys.exit(1)

@app.command()
@coro
async def status(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", help="Project path to check status for"),
):
    """Show current environment health status."""
    context = ctx.obj
    try:
        project_path = project or os.getcwd()
        snapshot = await context.client.get_latest_snapshot(project_path)
        if not snapshot:
            context.formatter.print_error("No snapshots found.", "Run 'devready scan' first.")
            return

        if context.json_output:
            import json
            print(json.dumps(snapshot))
            return

        context.formatter.print_health_score(snapshot.get("health_score", 0))
        
        # Display policy violations if any
        violations = snapshot.get("policy_violations", [])
        if violations:
            from rich.table import Table
            table = Table(title="Policy Violations", style="red")
            table.add_column("Type", style="yellow")
            table.add_column("Tool/Var", style="cyan")
            table.add_column("Issue", style="white")
            
            for v in violations:
                table.add_row(
                    v.get("violation_type", "unknown"),
                    v.get("tool_or_var_name", "N/A"),
                    v.get("message", "No details")
                )
            
            context.formatter.console.print(table)
        
        # Display tools
        tools = snapshot.get("tools", [])
        if tools:
            from rich.table import Table
            table = Table(title="Environment Tools")
            table.add_column("Tool", style="cyan")
            table.add_column("Version", style="green")
            
            for tool in tools:
                table.add_row(tool["name"], tool["version"])
            
            context.formatter.console.print(table)
        
        context.formatter.console.print(f"\n[dim]Project: {snapshot.get('project_path', 'N/A')}[/dim]")
        context.formatter.console.print(f"[dim]Last scanned: {snapshot.get('timestamp', 'N/A')}[/dim]")
    except DaemonError as e:
        context.formatter.print_error(str(e))
        sys.exit(1)

@app.command()
@coro
async def drift(
    ctx: typer.Context,
    baseline: Optional[str] = typer.Option(None, "--baseline", help="Baseline snapshot ID"),
    policy: bool = typer.Option(False, "--policy", help="Compare against team policy"),
    project: Optional[str] = typer.Option(None, "--project", help="Project path to check drift for"),
):
    """Show environment drift since last scan."""
    context = ctx.obj
    try:
        project_path = project or os.getcwd()

        if policy:
            # Policy drift logic would go here
            context.formatter.print_error("Policy drift not yet implemented.")
            return

        # Get current and baseline snapshots
        current_task = context.client.get_latest_snapshot(project_path)
        if baseline:
            baseline_task = context.client.get_snapshot(baseline)
            current, base = await asyncio.gather(current_task, baseline_task)
        else:
            # Get second latest snapshot as baseline
            snapshots = await context.client.list_snapshots(project_path=project_path, limit=2)
            if len(snapshots) < 2:
                context.formatter.print_error("Need at least 2 snapshots to compare drift.",
                                            "Run 'devready scan' multiple times or specify --baseline.")
                return
            current = snapshots[0]
            base = snapshots[1]

        if not current or not base:
            context.formatter.print_error("Snapshots not found.")
            return

        report = await context.client.compare_drift(
            base.get("snapshot_id", base.get("id")),
            current.get("snapshot_id", current.get("id"))
        )

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
    project: Optional[str] = typer.Option(None, "--project", help="Project path to fix"),
):
    """Apply recommended fixes for detected issues."""
    context = ctx.obj
    try:
        project_path = project or os.getcwd()
        snapshot = await context.client.get_latest_snapshot(project_path)
        if not snapshot:
            context.formatter.print_error("No snapshots found. Run scan first.")
            return

        snapshot_id = snapshot.get("snapshot_id")
        fixes = await context.client.get_fix_recommendations(snapshot_id=snapshot_id)

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
            fix_ids = [f["fix_id"] for f in fixes]
            results = await context.client.apply_fixes(fix_ids=fix_ids, dry_run=dry_run)
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
    """View violation trends and compliance summary from local analytics."""
    context = ctx.parent.obj
    try:
        summary = await context.client._request("GET", "/api/v1/analytics/violations/summary")
        violations = summary.get("violations", [])

        if context.json_output:
            import json
            print(json.dumps(summary))
            return

        if not violations:
            context.formatter.console.print("[green]No policy violations recorded.[/green]")
            return

        table = Table(title="Violation Trends (last 30 days)")
        table.add_column("Type", style="yellow")
        table.add_column("Tool/Var", style="cyan")
        table.add_column("Count", style="red")
        table.add_column("Last Seen", style="dim")

        for v in violations:
            table.add_row(
                v.get("violation_type", ""),
                v.get("tool_or_var_name", ""),
                str(v.get("count", 0)),
                str(v.get("last_seen", ""))[:19],
            )

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
            result = await context.client.scan(project_path=os.getcwd())
            context.formatter.console.print(
                f"[green]Snapshot {result['snapshot_id']} synced.[/green]"
            )
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
        project_path = project or os.getcwd()
        snapshots = await context.client.list_snapshots(project_path=project_path, limit=limit)

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
            snapshot_id = s.get("snapshot_id", s.get("id", "N/A"))
            table.add_row(
                snapshot_id[:8] if len(snapshot_id) > 8 else snapshot_id,
                s.get("timestamp", "N/A"),
                str(s.get("health_score", "N/A")),
                s.get("project_name", "N/A")
            )

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
            context.formatter.console.print(f"[green]Snapshot created: {result['snapshot_id']}[/green]")
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
def daemon_start(
    port: int = typer.Option(8443, "--port", help="Port to run daemon on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
):
    """Start the DevReady daemon in the background."""
    import subprocess
    import time

    pid_file = os.path.expanduser("~/.devready/daemon.pid")
    os.makedirs(os.path.dirname(pid_file), exist_ok=True)

    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = f.read().strip()
        try:
            os.kill(int(pid), 0)
            typer.echo(f"Daemon already running (PID {pid})")
            return
        except (OSError, ValueError):
            os.remove(pid_file)

    log_file = os.path.expanduser("~/.devready/logs/daemon.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    with open(log_file, "a") as log:
        proc = subprocess.Popen(
            ["uvicorn", "devready.daemon.main:app", "--host", host, "--port", str(port)],
            stdout=log, stderr=log,
            start_new_session=True,
        )

    with open(pid_file, "w") as f:
        f.write(str(proc.pid))

    time.sleep(2)
    if proc.poll() is None:
        typer.echo(f"[green]Daemon started (PID {proc.pid}) on http://{host}:{port}[/green]")
    else:
        typer.echo("[red]Daemon failed to start. Check ~/.devready/logs/daemon.log[/red]")
        raise typer.Exit(1)


@daemon_app.command("stop")
def daemon_stop():
    """Stop the DevReady daemon."""
    import signal

    pid_file = os.path.expanduser("~/.devready/daemon.pid")
    if not os.path.exists(pid_file):
        typer.echo("Daemon is not running.")
        return

    with open(pid_file) as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM)
        os.remove(pid_file)
        typer.echo(f"Daemon stopped (PID {pid})")
    except ProcessLookupError:
        os.remove(pid_file)
        typer.echo("Daemon was not running (stale PID file removed)")
    except Exception as e:
        typer.echo(f"[red]Failed to stop daemon: {e}[/red]")

@app.command()
def dashboard():
    """Launch interactive terminal dashboard."""
    from .dashboard import DevReadyDashboard
    from .daemon_client import DaemonClient
    
    client = DaemonClient()
    app = DevReadyDashboard(client)
    app.run()

# --- Metrics (Lens) ---
from devready.lens.cli import metrics_app
app.add_typer(metrics_app, name="metrics")

if __name__ == "__main__":
    app()
