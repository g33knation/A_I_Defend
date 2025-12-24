import requests
import sys

BASE_URL = "http://localhost:8000"
VALID_KEY = "octopus-nervous-system-secret"
INVALID_KEY = "severed-leg-key"

def test_auth():
    print("🧪 Starting Octopus Nervous System Verification...")
    
    # 1. Test unauthorized access
    print("\n[1] Testing unauthorized access to /events...")
    try:
        resp = requests.post(f"{BASE_URL}/events", json={"source": "test", "type": "test", "payload": {}})
        print(f"    Status: {resp.status_code}")
        if resp.status_code == 401:
            print("    ✅ SUCCESS: Unauthorized access rejected.")
        else:
            print("    ❌ FAILURE: Unauthorized access should have been 401.")
    except Exception as e:
        print(f"    ❌ ERROR: {e}")

    # 2. Test authorized access
    print("\n[2] Testing authorized access to /events...")
    headers = {"X-API-Key": VALID_KEY}
    try:
        resp = requests.post(f"{BASE_URL}/events", headers=headers, json={"source": "verifier", "type": "auth_test", "payload": {"status": "ok"}})
        print(f"    Status: {resp.status_code}")
        if resp.status_code == 200:
            print("    ✅ SUCCESS: Authorized access accepted.")
        else:
            print(f"    ❌ FAILURE: Authorized access failed with {resp.status_code}. Detail: {resp.text}")
    except Exception as e:
        print(f"    ❌ ERROR: {e}")

    # 3. Test invalid key
    print("\n[3] Testing invalid key access...")
    headers = {"X-API-Key": INVALID_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/api/agents/", headers=headers)
        print(f"    Status: {resp.status_code}")
        if resp.status_code == 401:
            print("    ✅ SUCCESS: Invalid key rejected.")
        else:
            print("    ❌ FAILURE: Invalid key should have been 401.")
    except Exception as e:
        print(f"    ❌ ERROR: {e}")

if __name__ == "__main__":
    test_auth()
