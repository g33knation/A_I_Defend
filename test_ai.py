import requests
import json

response = requests.post(
    "http://localhost:8000/ask",
    json={"query": "List all the security detections in the provided context"}
)

result = response.json()

with open("c:/Users/Tommy/.gemini/ai_response.txt", "w", encoding="utf-8") as f:
    f.write("Full response:\n")
    f.write(json.dumps(result, indent=2))
    f.write("\n\n" + "="*80 + "\n\n")
    f.write("Response text:\n")
    f.write(result.get("response", "No response field"))

print("Output written to ai_response.txt")
