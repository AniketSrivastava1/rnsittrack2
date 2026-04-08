"""Integration tests for full scan workflow and multi-client scenarios."""
import pytest


_BASE_PAYLOAD = {
    "project_path": "/integration/test",
    "project_name": "integration-test",
    "tools": [],
    "dependencies": {},
    "env_vars": {},
    "scan_duration_seconds": 1.5,
}


@pytest.mark.asyncio
async def test_full_snapshot_workflow(test_client):
    """Full workflow: create → retrieve → list → delete."""
    # Create
    resp = await test_client.post("/api/v1/snapshots", json=_BASE_PAYLOAD)
    assert resp.status_code == 201
    snap_id = resp.json()["snapshot_id"]

    # Retrieve
    resp = await test_client.get(f"/api/v1/snapshots/{snap_id}")
    assert resp.status_code == 200
    assert resp.json()["project_name"] == "integration-test"

    # List
    resp = await test_client.get("/api/v1/snapshots?project_path=/integration/test")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Delete
    resp = await test_client.delete(f"/api/v1/snapshots/{snap_id}")
    assert resp.status_code == 204

    # Verify gone
    resp = await test_client.get(f"/api/v1/snapshots/{snap_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_drift_detection_workflow(test_client):
    """Baseline → current → compare → verify drift report."""
    baseline_payload = {
        **_BASE_PAYLOAD,
        "tools": [{"name": "node", "version": "18.0.0", "path": "/usr/bin/node", "manager": None}],
    }
    current_payload = {
        **_BASE_PAYLOAD,
        "tools": [
            {"name": "node", "version": "20.0.0", "path": "/usr/bin/node", "manager": None},
            {"name": "python", "version": "3.11.0", "path": "/usr/bin/python", "manager": None},
        ],
    }

    r1 = await test_client.post("/api/v1/snapshots", json=baseline_payload)
    r2 = await test_client.post("/api/v1/snapshots", json=current_payload)
    id1, id2 = r1.json()["snapshot_id"], r2.json()["snapshot_id"]

    resp = await test_client.post("/api/v1/drift/compare", json={"snapshot_a_id": id1, "snapshot_b_id": id2})
    assert resp.status_code == 200
    report = resp.json()

    assert len(report["added_tools"]) == 1
    assert report["added_tools"][0]["name"] == "python"
    assert len(report["version_changes"]) == 1
    assert report["version_changes"][0]["tool_name"] == "node"
    assert report["drift_score"] > 0


@pytest.mark.asyncio
async def test_policy_compliance_workflow(test_client):
    """Create snapshot → check policy → verify violations."""
    payload = {
        **_BASE_PAYLOAD,
        "tools": [{"name": "node", "version": "18.0.0", "path": "/usr/bin/node", "manager": None}],
    }
    r = await test_client.post("/api/v1/snapshots", json=payload)
    snap_id = r.json()["snapshot_id"]

    policy = {
        "required_tools": [{"name": "python", "min_version": "3.11.0"}],
        "forbidden_tools": [],
        "version_constraints": {},
        "env_var_requirements": [],
    }
    resp = await test_client.post("/api/v1/drift/policy", json={"snapshot_id": snap_id, "team_policy": policy})
    assert resp.status_code == 200
    violations = resp.json()
    assert len(violations) == 1
    assert violations[0]["violation_type"] == "missing_tool"
    assert violations[0]["tool_or_var_name"] == "python"


@pytest.mark.asyncio
async def test_metrics_endpoint(test_client):
    """Metrics endpoint returns expected fields."""
    resp = await test_client.get("/api/v1/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "cpu_percent" in data
    assert "memory_mb" in data
    assert "scan_count" in data
    assert "avg_scan_duration" in data


@pytest.mark.asyncio
async def test_version_endpoint(test_client):
    """Version endpoint returns api_version."""
    resp = await test_client.get("/api/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["api_version"] == "v1"
    assert "daemon_version" in data
