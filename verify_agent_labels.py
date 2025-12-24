import httpx
import json

API_URL = "http://localhost:8000"

def verify_all():
    # 1. Get agents to find a known IP
    print("--- Testing Agent Labeling ---")
    response = httpx.get(f"{API_URL}/api/agents/")
    agents = response.json()
    if not agents:
        print("No agents found")
    else:
        agent_ip = agents[0]['ip_address']
        agent_hostname = agents[0]['hostname']
        print(f"Using Agent IP: {agent_ip} (Hostname: {agent_hostname})")

        # Send a mock port scan event from this agent
        # We'll use the hostname as the source to test our fallback in ingest_event
        payload = {
            "source": agent_hostname,
            "type": "port_scan",
            "payload": {
                "details": {
                    "address": "127.0.0.1",
                    "ports": [80, 443]
                }
            }
        }
        
        response = httpx.post(f"{API_URL}/events", json=payload)
        print(f"Event sent: {response.status_code}")

        # Wait for background processing
        import time
        time.sleep(2)

        # Check detections
        response = httpx.get(f"{API_URL}/detections")
        detections = response.json()
        
        found = False
        for d in detections:
            if agent_hostname in d['summary'] or agent_ip in d['summary']:
                print(f"FOUND DETECTION: {d['summary']}")
                if "[KNOWN AGENT]" in d['summary'] and "🤖" in d['summary']:
                    print("SUCCESS: Detection labeled correctly!")
                    found = True
                    # 2. Test Feedback on this detection
                    print("\n--- Testing Feedback Submission ---")
                    fb_payload = {
                        "detection_id": d['id'],
                        "feedback": "confirmed_threat"
                    }
                    fb_response = httpx.post(f"{API_URL}/feedback", json=fb_payload)
                    print(f"Feedback sent: {fb_response.status_code}")
                    if fb_response.status_code == 200:
                        print("SUCCESS: Feedback submitted successfully!")
                    else:
                        print(f"FAILURE: Feedback failed with {fb_response.text}")
                    break
        
        if not found:
            print("FAILURE: Detection with agent label not found.")

if __name__ == "__main__":
    verify_all()
