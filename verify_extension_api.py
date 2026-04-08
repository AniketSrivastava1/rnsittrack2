import urllib.request
import urllib.error
import urllib.parse
import json
import os

BASE_URL = "http://127.0.0.1:8443"
PROJECT_PATH = os.path.abspath(".")

def test_api():
    print(f"Testing Daemon API at {BASE_URL} for project: {PROJECT_PATH}")
    
    print("\n--- Testing GET /api/v1/snapshots/latest ---")
    url = f"{BASE_URL}/api/v1/snapshots/latest?project_path={urllib.parse.quote(PROJECT_PATH)}"
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req) as response:
            status = response.status
            data = json.loads(response.read().decode())
            print(f"Status Code: {status}")
            print(f"Response: {data}")
            print("[OK] GET /latest successful.")
            snapshot_id = data.get("snapshot_id")
    except urllib.error.HTTPError as e:
        status = e.code
        data = json.loads(e.read().decode())
        print(f"Status Code: {status}")
        print(f"Response: {data}")
        if status == 404 and data.get("error_code") == "SNAPSHOT_NOT_FOUND":
            print("[OK] GET /latest successful (No snapshot found, but endpoint is properly configured).")
            snapshot_id = "test-id"
        elif status == 404:
            print("[FAIL] GET /latest returned 404 endpoint not found, check routing.")
            snapshot_id = "test-id"
        else:
            print("[FAIL] GET /latest returned unexpected status.")
            return
    except urllib.error.URLError:
        print("[FAIL] Failed to connect. Is the daemon running on 127.0.0.1:8443?")
        return

    print("\n--- Testing POST /api/v1/fixes/recommendations ---")
    url = f"{BASE_URL}/api/v1/fixes/recommendations"
    req_body = {
        "snapshot_id": snapshot_id if snapshot_id else "test-id",
        "team_policy": {
            "required_tools": [],
            "forbidden_tools": [],
            "version_constraints": {},
            "env_var_requirements": []
        }
    }
    data = json.dumps(req_body).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as response:
            status = response.status
            print(f"Status Code: {status}")
            print(f"Response: {json.loads(response.read().decode())}")
            print("[OK] POST /recommendations successful.")
    except urllib.error.HTTPError as e:
        status = e.code
        print(f"Status Code: {status}")
        try:
            print(f"Response: {json.loads(e.read().decode())}")
        except:
            print("Could not parse response")
        if status == 404:
            print("[OK] POST /recommendations successful (Snapshot not found).")
        else:
            print("[FAIL] POST /recommendations returned unexpected status.")

if __name__ == "__main__":
    test_api()
