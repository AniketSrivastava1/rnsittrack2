import json
from typing import Any, Dict, Optional
from rich.console import Console

class OutputHandler:
    """Manages CLI output routing (JSON vs Formatted)."""
    
    def __init__(self, json_mode: bool = False, no_color: bool = False):
        self.json_mode = json_mode
        self.console = Console(no_color=no_color)
    
    def output(self, data: Any, formatter_fn: Optional[Any] = None, *args, **kwargs):
        """Output data based on current mode."""
        if self.json_mode:
            self._print_json(data)
        elif formatter_fn:
            formatter_fn(data, *args, **kwargs)
        else:
            # Fallback if no formatter provided
            self.console.print(data)

    def _print_json(self, data: Any):
        """Print data as formatted JSON."""
        print(json.dumps(data, indent=2, sort_keys=True))
