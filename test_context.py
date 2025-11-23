import requests
import json

# Test endpoint to see what context is being generated
response = requests.post(
    "http://localhost:8000/ask",
    json={"query": "List all detections", "model": "llama3.2:latest"}
)

# Also let's check if detections exist
detections_response = requests.get("http://localhost:8000/detections")

print("=" * 80)
print("DETECTIONS IN DATABASE:")
print("=" * 80)
detections = detections_response.json()
print(f"Total detections: {len(detections)}")
for d in detections[:10]:
    print(f"- {d.get('summary', 'No summary')} (Score: {d.get('score', 'N/A')})")

print("\n" + "=" * 80)
print("AI RESPONSE:")
print("=" * 80)
result = response.json()
print(result.get("response", "No response"))
