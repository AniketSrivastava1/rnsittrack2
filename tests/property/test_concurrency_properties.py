"""
Property tests for concurrent request handling.
Feature: architect-core-api-data-state
"""
import asyncio

import pytest

_PAYLOAD = {
    "project_path": "/concurrent/test",
    "project_name": "concurrent-test",
    "tools": [],
    "dependencies": {},
    "env_vars": {},
    "scan_duration_seconds": 0.1,
}


@pytest.mark.asyncio
async def test_concurrent_snapshot_creates_all_succeed(test_client):
    """
    Feature: architect-core-api-data-state, Property 47: Scan Requests Queued Sequentially
    Validates: Requirements 14.3
    All concurrent snapshot creation requests should succeed without data corruption.
    """
    tasks = [test_client.post("/api/v1/snapshots", json=_PAYLOAD) for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    assert all(r.status_code == 201 for r in responses)
    ids = [r.json()["snapshot_id"] for r in responses]
    assert len(set(ids)) == 10  # all unique IDs - no corruption


@pytest.mark.asyncio
async def test_metrics_responds_during_concurrent_requests(test_client):
    """
    Feature: architect-core-api-data-state, Property 48: Non-Blocking Health Checks During Scans
    Validates: Requirements 14.5
    Metrics endpoint should respond quickly even while other requests are in flight.
    """
    import time

    # Fire off several snapshot creates concurrently
    create_tasks = [test_client.post("/api/v1/snapshots", json=_PAYLOAD) for _ in range(5)]

    # Simultaneously hit metrics
    start = time.monotonic()
    metrics_resp = await test_client.get("/api/v1/metrics")
    elapsed = time.monotonic() - start

    assert metrics_resp.status_code == 200
    assert elapsed < 1.0  # should respond well under 1 second

    # Let creates finish
    await asyncio.gather(*create_tasks)


@pytest.mark.asyncio
async def test_concurrent_reads_all_succeed(test_client):
    """
    Validates: Requirements 14.4 - concurrent reads don't block each other.
    """
    # Create a snapshot first
    r = await test_client.post("/api/v1/snapshots", json=_PAYLOAD)
    snap_id = r.json()["snapshot_id"]

    # Concurrent reads
    tasks = [test_client.get(f"/api/v1/snapshots/{snap_id}") for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    assert all(r.status_code == 200 for r in responses)
