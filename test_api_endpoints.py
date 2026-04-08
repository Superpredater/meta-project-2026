"""Quick validation script for OpenEnv API endpoints.

Tests that all required endpoints return JSON (not HTML).
"""
import json
import sys

try:
    from fastapi.testclient import TestClient
    from openenv_email_triage.api import app
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)


def test_endpoints():
    """Test all OpenEnv endpoints return valid JSON."""
    client = TestClient(app)
    
    print("Testing OpenEnv API Endpoints...")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing GET /health")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    assert data["status"] == "healthy"
    print("   ✓ PASS")
    
    # Test 2: Reset endpoint without body (health check)
    print("\n2. Testing POST /reset (without body)")
    response = client.post("/reset")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    assert data["status"] == "ok"
    print("   ✓ PASS")
    
    # Test 3: Reset endpoint with task_id
    print("\n3. Testing POST /reset (with task_id)")
    response = client.post("/reset", json={"task_id": "categorize_easy"})
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    print(f"   Response keys: {list(data.keys())}")
    assert "email" in data
    assert "task_id" in data
    assert data["task_id"] == "categorize_easy"
    print("   ✓ PASS")
    
    # Test 4: Observation endpoint
    print("\n4. Testing GET /observation")
    response = client.get("/observation")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    assert "task_id" in data or "done" in data
    print("   ✓ PASS")
    
    # Test 5: Step endpoint
    print("\n5. Testing POST /step")
    response = client.post("/step", json={
        "operation": "skip"
    })
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    print(f"   Response keys: {list(data.keys())}")
    assert "observation" in data
    assert "reward" in data
    assert "done" in data
    print("   ✓ PASS")
    
    # Test 6: State endpoint
    print("\n6. Testing GET /state")
    response = client.get("/state")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    print(f"   Response keys: {list(data.keys())}")
    assert "task_id" in data
    assert "step" in data
    assert "done" in data
    print("   ✓ PASS")
    
    # Test 7: Render endpoint
    print("\n7. Testing GET /render")
    response = client.get("/render")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    assert "text" in data
    print("   ✓ PASS")
    
    # Test 8: Ensure no HTML responses on validation errors
    print("\n8. Testing POST /reset with invalid task_id")
    response = client.post("/reset", json={"task_id": "invalid_task"})
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    assert response.status_code == 400  # Bad request
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    assert "detail" in data  # FastAPI error format
    print("   ✓ PASS")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("\nSummary:")
    print("- All endpoints return JSON (no HTML error pages)")
    print("- POST /reset works with and without body")
    print("- GET /observation endpoint is available")
    print("- All OpenEnv required endpoints functional")
    print("\nThe API is ready for OpenEnv validation!")


if __name__ == "__main__":
    try:
        test_endpoints()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
