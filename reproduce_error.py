import requests
import json

url = "http://localhost:8000/ask"
payload = {
    "query": "Is there any danger?",
    "model": "hermes3:latest"
}

try:
    response = requests.post(url, json=payload, timeout=350)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
