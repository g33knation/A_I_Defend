import requests
import time

url = "http://localhost:8000/ask"
payload = {"query": "hi"}

for i in range(3):
    print(f"Test {i+1}...")
    try:
        start = time.time()
        response = requests.post(url, json=payload, timeout=600)
        elapsed = time.time() - start
        print(f"Status: {response.status_code} in {elapsed:.2f}s")
        if response.status_code != 200:
            print(f"Error detail: {response.json()}")
    except Exception as e:
        print(f"Exception: {e}")
    print("-" * 20)
