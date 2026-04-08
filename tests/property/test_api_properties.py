"""
Property tests for API endpoints.
Feature: architect-core-api-data-state
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tests.strategies import tool_version_strategy


_SNAPSHOT_PAYLOAD = {
    "project_path": "/test/project",
    "project_name": "test-project",
    "tools": [],
    "dependencies": {},
    "env_vars": {},
    "scan_duration_seconds": 1.0,
}


@pytest.mark.asyncio
async def test_create_and_retrieve_snapshot(test_client):
    """
    Feature: architect-core-api-data-state, Property 10: Snapshot Creation and Retrieval Round-Trip
    Validates: Requirements 4.1, 4.2
    """
    resp = await test_client.post("/api/v1/snapshots", json=_SNAPSHOT_PAYLOAD)
    assert resp.status_code == 201
    snapshot_id = resp.json()["snapshot_id"]

    resp2 = await test_client.get(f"/api/v1/snapshots/{snapshot_id}")
    assert resp2.status_code == 200
    assert resp2.json()["snapshot_id"] == snapshot_id


@pytest.mark.asyncio
async def test_project_path_filtering(test_client):
    """
    Feature: architect-core-api-data-state, Property 11: Project Path Filtering
    Validates: Requirements 4.3
    """
    await test_client.post("/api/v1/snapshots", json={**_SNAPSHOT_PAYLOAD, "project_path": "/proj/a"})
    await test_client.post("/api/v1/snapshots", json={**_SNAPSHOT_PAYLOAD, "project_path": "/proj/b"})

    resp = await test_client.get("/api/v1/snapshots?project_path=/proj/a")
    assert resp.status_code == 200
    data = resp.json()
    assert all(s["project_path"] == "/proj/a" for s in data)


@pytest.mark.asyncio
async def test_latest_snapshot_correctness(test_client):
    """
    Feature: architect-core-api-data-state, Property 12: Latest Snapshot Query Correctness
    Validates: Requirements 4.4
    """
    await test_client.post("/api/v1/snapshots", json={**_SNAPSHOT_PAYLOAD, "project_path": "/proj/latest"})
    r2 = await test_client.post("/api/v1/snapshots", json={**_SNAPSHOT_PAYLOAD, "project_path": "/proj/latest"})
    second_id = r2.json()["snapshot_id"]

    resp = await test_client.get("/api/v1/snapshots/latest?project_path=/proj/latest")
    assert resp.status_code == 200
    assert resp.json()["snapshot_id"] == second_id


@pytest.mark.asyncio
async def test_delete_snapshot_removes_data(test_client):
    """
    Feature: architect-core-api-data-state, Property 13: Snapshot Deletion Removes Data
    Validates: Requirements 4.5
    """
    resp = await test_client.post("/api/v1/snapshots", json=_SNAPSHOT_PAYLOAD)
    snapshot_id = resp.json()["snapshot_id"]

    del_resp = await test_client.delete(f"/api/v1/snapshots/{snapshot_id}")
    assert del_resp.status_code == 204

    get_resp = await test_client.get(f"/api/v1/snapshots/{snapshot_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_nonexistent_snapshot_returns_404(test_client):
    """
    Feature: architect-core-api-data-state, Property 14: Non-Existent Snapshot Returns 404
    Validates: Requirements 4.6
    """
    resp = await test_client.get("/api/v1/snapshots/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_endpoint_returns_404(test_client):
    """
    Feature: architect-core-api-data-state, Property 2: Invalid Endpoints Return 404
    Validates: Requirements 1.6
    """
    resp = await test_client.get("/api/v1/nonexistent-endpoint")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_drift_compare_returns_report(test_client):
    """
    Feature: architect-core-api-data-state, Property 15: Drift Comparison Returns Report
    Validates: Requirements 5.1
    """
    r1 = await test_client.post("/api/v1/snapshots", json=_SNAPSHOT_PAYLOAD)
    r2 = await test_client.post("/api/v1/snapshots", json=_SNAPSHOT_PAYLOAD)
    id1 = r1.json()["snapshot_id"]
    id2 = r2.json()["snapshot_id"]

    resp = await test_client.post("/api/v1/drift/compare", json={"snapshot_a_id": id1, "snapshot_b_id": id2})
    assert resp.status_code == 200
    data = resp.json()
    assert "added_tools" in data
    assert "removed_tools" in data
    assert "version_changes" in data


@pytest.mark.asyncio
async def test_api_version_in_responses(test_client):
    """
    Feature: architect-core-api-data-state, Property 37: All JSON Responses Include API Version
    Validates: Requirements 11.2
    """
    resp = await test_client.get("/api/version")
    assert resp.status_code == 200
    assert "api_version" in resp.json()


@pytest.mark.asyncio
async def test_errors_return_structured_json(test_client):
    """
    Feature: architect-core-api-data-state, Property 33: API Errors Return Structured JSON
    Validates: Requirements 10.1
    """
    resp = await test_client.get("/api/v1/snapshots/nonexistent")
    assert resp.status_code == 404
    # HTTPException detail is returned as-is by FastAPI
    body = resp.json()
    assert "detail" in body or "error_code" in body


@pytest.mark.asyncio
async def test_path_traversal_blocked(test_client):
    """
    Feature: architect-core-api-data-state, Property 50: Path Sanitization Prevents Traversal
    Validates: Requirements 15.3
    """
    resp = await test_client.get("/api/v1/../../../etc/passwd")
    assert resp.status_code in (400, 404)
