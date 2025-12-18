import urllib.request
import json
import sys

url = "http://localhost:8000/ask"
payload = {
    "query": "Hello",
    "model": "hermes3:latest"
}
data = json.dumps(payload).encode('utf-8')
headers = {
    "Content-Type": "application/json"
}

req = urllib.request.Request(url, data=data, headers=headers, method='POST')

print(f"Testing {url}...")
try:
    with urllib.request.urlopen(req, timeout=120) as response:
        status_code = response.getcode()
        print(f"Status Code: {status_code}")
        response_body = response.read().decode('utf-8')
        print(f"Response: {response_body}")
        
        if status_code == 200:
            print("SUCCESS: AI responded.")
        else:
            print("FAILURE: Unexpected status code.")
            sys.exit(1)
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(e.read().decode('utf-8'))
    sys.exit(1)
except urllib.error.URLError as e:
    print(f"URL Error: {e.reason}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
