from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.syntax import Syntax
from rich.theme import Theme
from typing import List, Dict, Any, Optional
import sys
import os

class RichFormatter:
    """Formats API data into beautiful terminal output using Rich."""
    
    def __init__(self, no_color: bool = False, force_terminal: Optional[bool] = None):
        self.theme = Theme({
            "health.high": "green",
            "health.medium": "yellow",
            "health.low": "red",
            "drift.added": "green",
            "drift.removed": "red",
            "drift.changed": "yellow",
            "tool.outdated": "yellow",
            "tool.missing": "red",
        })
        # If force_terminal is None, rich will auto-detect TTY
        self.console = Console(
            no_color=no_color, 
            theme=self.theme, 
            force_terminal=force_terminal,
            width=None if sys.stdout.isatty() else 120 # Fixed width for CI logs
        )
    
    @property
    def is_interactive(self) -> bool:
        """Returns True if the output is a TTY and not suppressed."""
        return self.console.is_terminal and not os.environ.get("DEVREADY_NON_INTERACTIVE")
    
    def print_health_score(self, score: int):
        """Display health score panel with dynamic color."""
        if score >= 90:
            color = "health.high"
            emoji = "✅"
        elif score >= 70:
            color = "health.medium"
            emoji = "⚠️"
        else:
            color = "health.low"
            emoji = "❌"
        
        self.console.print(
            Panel(
                Text.assemble((f"{emoji} Health Score: ", color), (f"{score}/100", f"bold {color}")),
                title="Environment Health",
                border_style=color,
                expand=False
            )
        )
    
    def print_tool_table(self, tools: List[Dict[str, Any]], title: str = "Detected Tools"):
        """Display tools in a formatted table with highlighting for issues."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Tool", style="bold")
        table.add_column("Version")
        table.add_column("Path", style="dim")
        table.add_column("Manager", style="green")
        table.add_column("Status")
        
        # Sort tools by name
        sorted_tools = sorted(tools, key=lambda t: t.get("name", ""))
        
        for tool in sorted_tools:
            name = tool.get("name", "Unknown")
            version = tool.get("version", "-")
            path = tool.get("path", "-")
            manager = tool.get("manager", "-")
            
            # Simulated status logic for formatting demo
            # In real use, this would come from the daemon's policy check
            status = tool.get("status", "ok")
            status_text = "OK"
            style = None
            
            if status == "outdated":
                status_text = "OUTDATED"
                style = "tool.outdated"
            elif status == "missing":
                status_text = "MISSING"
                style = "tool.missing"
            
            table.add_row(
                Text(name, style=style),
                Text(version, style=style),
                path,
                manager,
                Text(status_text, style=style)
            )
        
        self.console.print(table)
    
    def print_drift_report(self, drift: Dict[str, Any]):
        """Display drift report with diff-style +/- formatting."""
        self.console.print(Panel("Environment Drift Report", style="bold yellow", expand=False))
        
        has_changes = False
        
        # Added tools
        added = drift.get("added_tools", [])
        if added:
            has_changes = True
            self.console.print("\n[drift.added]Added Tools:[/drift.added]")
            for tool in added:
                self.console.print(f"  [drift.added]+ {tool['name']} ({tool['version']})[/drift.added]")
        
        # Removed tools
        removed = drift.get("removed_tools", [])
        if removed:
            has_changes = True
            self.console.print("\n[drift.removed]Removed Tools:[/drift.removed]")
            for tool in removed:
                self.console.print(f"  [drift.removed]- {tool['name']} ({tool['version']})[/drift.removed]")
        
        # Version changes
        changes = drift.get("version_changes", [])
        if changes:
            has_changes = True
            self.console.print("\n[drift.changed]Version Changes:[/drift.changed]")
            for change in changes:
                self.console.print(
                    f"  [drift.changed]~ {change['tool_name']}: "
                    f"{change['old_version']} → {change['new_version']}[/drift.changed]"
                )
        
        if not has_changes:
            self.console.print("\n[dim]No drift detected. Environment is stable.[/dim]")
        
        # Summary line
        summary = Text.assemble(
            ("\nSummary: ", "bold"),
            (f"{len(added)} added", "drift.added"), ", ",
            (f"{len(removed)} removed", "drift.removed"), ", ",
            (f"{len(changes)} changed", "drift.changed")
        )
        self.console.print(summary)
        
        drift_score = drift.get("drift_score", 0)
        self.console.print(f"Drift Score: [bold]{drift_score}/100[/bold]\n")

    def print_fix_recommendations(self, fixes: List[Dict[str, Any]]):
        """Display fix recommendations with actionable steps."""
        if not fixes:
            self.console.print("[green]No issues found. No fixes needed![/green]")
            return

        self.console.print(Panel("Fix Recommendations", style="bold green", expand=False))
        
        for i, fix in enumerate(fixes, 1):
            title = f"{i}. {fix.get('issue_description', fix.get('title', 'Unknown Fix'))}"
            self.console.print(f"\n[bold]{title}[/bold]")
            self.console.print(f"Description: {fix.get('issue_description', '-')}")

            if fix.get("command"):
                self.console.print(f"Command: [bold cyan]{fix['command']}[/bold cyan]")
            elif fix.get("manual_steps"):
                self.console.print(f"Steps: {fix['manual_steps']}")
            elif fix.get("auto_fix"):
                self.console.print(f"Command: [bold cyan]{fix['auto_fix']}[/bold cyan]")
            else:
                for step in fix.get("steps", []):
                    self.console.print(f"  - {step}")

            self.console.print(f"Confidence: [dim]{fix.get('confidence', 'high')}[/dim]")

    def show_progress(self, description: str) -> Progress:
        """Create a progress indicator."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
            transient=True
        )
    
    def print_error(self, message: str, details: Optional[str] = None):
        """Print a formatted error message."""
        self.console.print(f"\n[bold red]✗ Error:[/bold red] {message}")
        if details:
            self.console.print(f"[dim]{details}[/dim]")
        self.console.print()
