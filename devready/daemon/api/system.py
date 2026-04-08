"""System endpoints: metrics and version."""
from __future__ import annotations

from fastapi import APIRouter

from devready.daemon.models import MetricsResponse, VersionResponse

router = APIRouter(tags=["system"])

# Injected at startup
_metrics_collector = None

VERSION = "1.0.0"
BUILD = "20260408"


@router.get("/api/v1/metrics")
async def get_metrics() -> MetricsResponse:
    if _metrics_collector is None:
        return MetricsResponse(cpu_percent=0.0, memory_mb=0.0, scan_count=0, avg_scan_duration=0.0)
    return MetricsResponse(
        cpu_percent=_metrics_collector.current_cpu,
        memory_mb=_metrics_collector.current_memory_mb,
        scan_count=_metrics_collector.scan_count,
        avg_scan_duration=_metrics_collector.avg_scan_duration,
    )


@router.get("/api/version")
async def get_version() -> VersionResponse:
    return VersionResponse(api_version="v1", daemon_version=VERSION, build_number=BUILD)
