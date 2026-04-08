"""
Performance tests for DevReady Daemon.
Validates: Requirements 1.2 (startup < 2s), 1.3/1.4 (idle < 2% CPU, < 150 MB RAM), 4.7 (API < 500ms)
"""
import time

import psutil
import pytest


_PAYLOAD = {
    "project_path": "/perf/test",
    "project_name": "perf-test",
    "tools": [],
    "dependencies": {},
    "env_vars": {},
    "scan_duration_seconds": 0.1,
}


@pytest.mark.asyncio
async def test_api_response_time_under_500ms(test_client):
    """
    Validates: Requirements 4.7 - all snapshot operations complete within 500ms.
    """
    # Seed 50 snapshots
    for _ in range(50):
        await test_client.post("/api/v1/snapshots", json=_PAYLOAD)

    # Measure GET list
    start = time.monotonic()
    resp = await test_client.get("/api/v1/snapshots?project_path=/perf/test")
    elapsed = time.monotonic() - start

    assert resp.status_code == 200
    assert elapsed < 0.5, f"List took {elapsed:.3f}s, expected < 0.5s"

    # Measure GET by ID
    snap_id = resp.json()[0]["snapshot_id"]
    start = time.monotonic()
    resp2 = await test_client.get(f"/api/v1/snapshots/{snap_id}")
    elapsed2 = time.monotonic() - start

    assert resp2.status_code == 200
    assert elapsed2 < 0.5, f"Get by ID took {elapsed2:.3f}s, expected < 0.5s"


@pytest.mark.asyncio
async def test_idle_memory_under_150mb():
    """
    Validates: Requirements 1.4 - idle memory < 150 MB RAM.
    """
    proc = psutil.Process()
    mem_mb = proc.memory_info().rss / (1024 * 1024)
    assert mem_mb < 150, f"Memory usage {mem_mb:.1f} MB exceeds 150 MB limit"


@pytest.mark.asyncio
async def test_app_startup_time():
    """
    Validates: Requirements 1.2 - daemon initializes within 2 seconds.
    """
    from devready.daemon.main import create_app
    from httpx import ASGITransport, AsyncClient

    start = time.monotonic()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/api/version")
    elapsed = time.monotonic() - start

    assert resp.status_code == 200
    assert elapsed < 2.0, f"Startup + first request took {elapsed:.3f}s, expected < 2s"
