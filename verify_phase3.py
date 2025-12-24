import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "octopus-nervous-system-secret"

def verify_events():
    print("🧪 Verifying Phase 3 Events...")
    headers = {"X-API-Key": API_KEY}
    
    try:
        resp = requests.get(f"{BASE_URL}/events", headers=headers)
        if resp.status_code == 200:
            events = resp.json()
            defense_events = [e for e in events if e.get('source') == 'defense-leg' or e.get('type') == 'suspicious_traffic']
            
            print(f"📊 Total Events: {len(events)}")
            print(f"📡 Defense Leg Events: {len(defense_events)}")
            
            if defense_events:
                print("\n✅ Latest Defense Event Details:")
                latest = defense_events[-1]
                print(f"   Time: {latest.get('created_at')}")
                print(f"   Type: {latest.get('type')}")
                print(f"   Target IPs: {latest.get('payload', {}).get('suspicious_ips', {})}")
            else:
                print("\n⚠️  No periodic scans found yet. Wait a few minutes for the first cycle.")
        else:
            print(f"❌ Failed to fetch events: {resp.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_events()
