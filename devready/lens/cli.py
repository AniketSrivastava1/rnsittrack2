"""Lens CLI sub-app — `devready metrics` command."""
from __future__ import annotations

import json
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

metrics_app = typer.Typer(name="metrics", help="Show environment health metrics and trends.")
console = Console()


def _fetch(url: str, daemon_url: str) -> dict:
    try:
        r = httpx.get(f"{daemon_url}{url}", timeout=10.0)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        console.print("[red]✗ Daemon unreachable. Start it with: devready daemon start[/red]")
        raise typer.Exit(1)


def _get_daemon_url(override: str) -> str:
    """Resolve daemon URL: CLI flag > env var > ConfigManager."""
    default = "http://localhost:8443"
    if override != default:  # explicit flag was passed
        return override
    try:
        from devready.cli.config_manager import ConfigManager
        return ConfigManager().get("daemon_url", default)
    except Exception:
        return default


def _sparkline(scores: list) -> str:
    bars = "▁▂▃▄▅▆▇█"
    if not scores:
        return "no data"
    mn, mx = min(scores), max(scores)
    rng = mx - mn or 1
    return "".join(bars[int((s - mn) / rng * 7)] for s in scores)


@metrics_app.callback(invoke_without_command=True)
def metrics(
    ctx: typer.Context,
    full: bool = typer.Option(False, "--full"),
    json_output: bool = typer.Option(False, "--json"),
    project: Optional[str] = typer.Option(None, "--project"),
    daemon_url: str = typer.Option("http://localhost:8443", envvar="DEVREADY_DAEMON_URL"),
):
    if ctx.invoked_subcommand:
        return

    daemon_url = _get_daemon_url(daemon_url)

    days = "30" if full else "7"
    p = f"&project_path={project}" if project else ""
    pp = f"?project_path={project}" if project else ""

    trend = _fetch(f"/api/v1/analytics/trends/health?days={days}{p}", daemon_url)
    issues = _fetch(f"/api/v1/analytics/issues/top?days={days}{p}", daemon_url)
    saved = _fetch(f"/api/v1/analytics/time-saved{pp}", daemon_url)
    comp = _fetch(f"/api/v1/analytics/compliance{pp}", daemon_url)

    if json_output:
        print(json.dumps({"trend": trend, "issues": issues, "time_saved": saved, "compliance": comp}, default=str))
        return

    scores = [e["health_score"] for e in trend.get("data", [])]
    summary = trend.get("summary", {})
    direction = {"improving": "↑", "degrading": "↓", "stable": "→"}.get(summary.get("trend_direction", ""), "→")
    console.print(f"\n[bold]Health Trend ({days}d)[/bold]  {_sparkline(scores)}  "
                  f"{summary.get('current_score', '?')} {direction}")

    issue_limit = 10 if full else 3
    issue_list = issues.get("issues", [])[:issue_limit]
    if issue_list:
        console.print(f"\n[bold]Top Issues[/bold]")
        t = Table(show_header=True, header_style="bold")
        t.add_column("Type"); t.add_column("Tool/Var"); t.add_column("Count", justify="right")
        for i in issue_list:
            t.add_row(i["violation_type"], i["tool_or_var_name"], str(i["count"]))
        console.print(t)

    console.print(f"\n[bold]Time Saved[/bold]  {saved['total_hours_saved']}h "
                  f"({saved['total_minutes_saved']} min, {saved['fix_count']} fixes)")

    score = comp.get("compliance_score", 0)
    color = "green" if score >= 85 else "yellow" if score >= 60 else "red"
    console.print(f"\n[bold]Team Compliance[/bold]  [{color}]{score:.1f}%[/{color}]  "
                  f"({comp.get('compliant_count', 0)}/{comp.get('total_count', 0)} machines)\n")
