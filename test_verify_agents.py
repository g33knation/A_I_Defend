import urllib.request
import json
import sys

try:
    with urllib.request.urlopen('http://localhost:8000/api/agents') as response:
        agents = json.loads(response.read().decode())
        
    print(f"Found {len(agents)} agents.")
    
    intel_found = False
    for agent in agents:
        print(f"Agent: {agent.get('hostname')} - Capabilities: {agent.get('capabilities')}")
        if 'tshark' in agent.get('capabilities', []) and 'masscan' in agent.get('capabilities', []):
            intel_found = True
            
    if intel_found:
        print("SUCCESS: Network Intel agent found with expected capabilities.")
    else:
        print("FAILURE: Network Intel agent NOT found.")
        sys.exit(1)
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
