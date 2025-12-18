import requests
import json

url = "http://localhost:8000/ask"
payload = {
    "query": "Hello, are you online?",
    "model": "hermes3:latest"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response:", response.json())
    else:
        print("Error:", response.text)
except Exception as e:
    print(f"Exception: {e}")
