import urllib.request
import json
import time

def main():
    try:
        with urllib.request.urlopen('http://localhost:8000/api/agents') as response:
            agents = json.load(response)
            for agent in agents:
                print(f"Agent: {agent['hostname']}")
                print(f"  Status: {agent['status']}")
                print(f"  Assignment: {agent['current_assignment']}")
                print(f"  Last Heartbeat: {agent['last_heartbeat']}")
                print("-" * 20)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
