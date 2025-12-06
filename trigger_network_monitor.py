import urllib.request
import json
import time

API_URL = "http://localhost:8000/api/agents"

def get_agents():
    req = urllib.request.Request(API_URL)
    with urllib.request.urlopen(req) as response:
        return json.load(response)

def assign_task(agent_id, assignment):
    url = f"{API_URL}/{agent_id}/assign"
    data = json.dumps(assignment).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.load(response)
    except Exception as e:
        print(f"Failed to assign to {agent_id}: {e}")
        return None

def main():
    agents = get_agents()
    for agent in agents:
        if 'network-monitor' in agent['hostname']:
            print(f"Targeting {agent['hostname']} ({agent['agent_id']})")
            assignment = {
                "targets": ["backend"], 
                "scanners": ["nmap"],
                "config": {"ports": "80"}
            }
            res = assign_task(agent['agent_id'], assignment)
            print(res)

if __name__ == "__main__":
    main()
