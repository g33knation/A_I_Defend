import urllib.request
import json

url = "http://localhost:8000/api/agents/register"
payload = {
    "hostname": "test-agent-01",
    "ip_address": "192.168.1.100",
    "capabilities": ["nmap", "vuln-scan"]
}
headers = {
    "Content-Type": "application/json"
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status Code: {response.getcode()}")
        print(f"Response: {response.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
