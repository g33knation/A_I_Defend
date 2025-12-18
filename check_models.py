import requests
import json

try:
    response = requests.get("http://localhost:8000/models", timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Models: {response.text}")
except Exception as e:
    print(f"Error: {e}")
