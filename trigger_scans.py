import urllib.request
import urllib.parse
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
    print("Fetching agents...")
    try:
        agents = get_agents()
    except Exception as e:
        print(f"Error fetching agents. Is backend running? {e}")
        return

    print(f"Found {len(agents)} agents.")

    for agent in agents:
        agent_id = agent['agent_id']
        hostname = agent['hostname']
        capabilities = agent['capabilities']
        
        print(f"Agent: {hostname} ({agent_id}) - Caps: {capabilities}")
        
        assignment = None
        
        if 'network-monitor' in hostname:
            assignment = {
                "targets": ["backend"], 
                "scanners": ["nmap"],
                "config": {"ports": "80"}
            }
        elif 'malware-scanner' in hostname:
            assignment = {
                "targets": ["/bin"], 
                "scanners": ["clamav"],
                "config": {}
            }
        elif 'security-scanner' in hostname:
            assignment = {
                "targets": [], 
                "scanners": ["lynis"], # Lynis scans system
                "config": {}
            }
        elif 'network-intel' in hostname:
            assignment = {
                "targets": ["backend"], 
                "scanners": ["nmap"],
                "config": {"ports": "80"}
            }
        
        if assignment:
            print(f"Assigning task to {hostname}...")
            res = assign_task(agent_id, assignment)
            if res:
                print(f"Success: {res}")
        else:
            print(f"Skipping {hostname}, unknown type.")

if __name__ == "__main__":
    main()
