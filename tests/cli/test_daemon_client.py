import pytest
from devready.cli.daemon_client import DaemonClient, DaemonNotRunningError, DaemonTimeoutError, DaemonResponseError
import httpx

@pytest.mark.asyncio
async def test_scan_success(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8443/api/v1/scan",
        json={"status": "success", "scan_id": "123"},
        status_code=200
    )
    
    client = DaemonClient()
    result = await client.scan()
    assert result["status"] == "success"
    assert result["scan_id"] == "123"
    await client.close()

@pytest.mark.asyncio
async def test_daemon_not_running(httpx_mock):
    # Need to mock 3 attempts because of the retry logic (initial + 2 retries)
    httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
    httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
    httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
    
    client = DaemonClient()
    with pytest.raises(DaemonNotRunningError):
        await client.scan()
    await client.close()

@pytest.mark.asyncio
async def test_daemon_timeout(httpx_mock):
    # Need to mock 3 attempts because of the retry logic
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
    
    client = DaemonClient()
    with pytest.raises(DaemonTimeoutError):
        await client.scan()
    await client.close()

@pytest.mark.asyncio
async def test_daemon_response_error(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8443/api/v1/snapshots/latest?project_path=test",
        status_code=500,
        text="Internal Server Error"
    )
    
    client = DaemonClient()
    with pytest.raises(DaemonResponseError) as excinfo:
        await client.get_latest_snapshot("test")
    assert excinfo.value.status_code == 500
    await client.close()

@pytest.mark.asyncio
async def test_get_latest_snapshot_404(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8443/api/v1/snapshots/latest?project_path=test",
        status_code=404
    )
    
    client = DaemonClient()
    result = await client.get_latest_snapshot("test")
    assert result is None
    await client.close()
