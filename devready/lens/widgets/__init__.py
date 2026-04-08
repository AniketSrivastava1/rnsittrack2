"""Textual widgets for The Lens — embeddable in The Face dashboard."""
from __future__ import annotations

from typing import Optional

import httpx
from textual.widget import Widget
from textual.widgets import Static


def _sparkline(scores: list) -> str:
    bars = "▁▂▃▄▅▆▇█"
    if not scores:
        return "no data"
    mn, mx = min(scores), max(scores)
    rng = mx - mn or 1
    return "".join(bars[int((s - mn) / rng * 7)] for s in scores)


class _LensWidget(Widget):
    DEFAULT_CSS = "height: auto; border: solid $accent; padding: 0 1;"

    def __init__(self, daemon_url: str = "http://localhost:8443",
                 project_path: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.daemon_url = daemon_url
        self.project_path = project_path

    def _params(self) -> str:
        return f"?project_path={self.project_path}" if self.project_path else ""

    async def _fetch(self, path: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{self.daemon_url}{path}{self._params()}", timeout=10.0)
                r.raise_for_status()
                return r.json()
        except Exception:
            return {}

    def on_mount(self) -> None:
        self.set_interval(60, self._refresh)
        self.call_after_refresh(self._refresh)

    async def _refresh(self) -> None:
        raise NotImplementedError


class HealthTrendWidget(_LensWidget):
    def compose(self):
        yield Static("⏳ Loading...", id="ht-content")

    async def _refresh(self) -> None:
        data = await self._fetch("/api/v1/analytics/trends/health?days=30")
        scores = [e["health_score"] for e in data.get("data", [])]
        s = data.get("summary", {})
        direction = {"improving": "↑", "degrading": "↓", "stable": "→"}.get(s.get("trend_direction", ""), "→")
        self.query_one("#ht-content", Static).update(
            f"Health Trend  {_sparkline(scores)}  {s.get('current_score', '?')} {direction}"
            if scores else "Health Trend  no data")


class TopIssuesWidget(_LensWidget):
    def compose(self):
        yield Static("⏳ Loading...", id="ti-content")

    async def _refresh(self) -> None:
        data = await self._fetch("/api/v1/analytics/issues/top")
        issues = data.get("issues", [])[:5]
        if not issues:
            text = "Top Issues  none ✅"
        else:
            lines = ["Top Issues"] + [
                f"  {i+1}. {v['tool_or_var_name']} ({v['violation_type']}) ×{v['count']}"
                for i, v in enumerate(issues)
            ]
            text = "\n".join(lines)
        self.query_one("#ti-content", Static).update(text)


class TimeSavedWidget(_LensWidget):
    def compose(self):
        yield Static("⏳ Loading...", id="ts-content")

    async def _refresh(self) -> None:
        data = await self._fetch("/api/v1/analytics/time-saved")
        self.query_one("#ts-content", Static).update(
            f"Time Saved  {data.get('total_hours_saved', 0)}h  ({data.get('fix_count', 0)} fixes)")


class ComplianceWidget(_LensWidget):
    def compose(self):
        yield Static("⏳ Loading...", id="cw-content")

    async def _refresh(self) -> None:
        data = await self._fetch("/api/v1/analytics/compliance")
        score = data.get("compliance_score", 0)
        filled = int(score / 10)
        bar = "█" * filled + "░" * (10 - filled)
        self.query_one("#cw-content", Static).update(
            f"Compliance  [{bar}] {score:.1f}%  "
            f"({data.get('compliant_count', 0)}/{data.get('total_count', 0)})")
