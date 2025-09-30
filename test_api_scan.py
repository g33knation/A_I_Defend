import asyncio
import httpx
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path so we can import our modules
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

async def test_api_scan():
    """Test the scan API endpoint."""
    api_url = "http://localhost:8000/api/scans"
    
    # Start a new scan
    print("Starting a new scan via API...")
    async with httpx.AsyncClient() as client:
        # Start the scan
        response = await client.post(
            f"{api_url}/start",
            json={
                "scanners": ["nmap", "clamav", "lynis"],
                "config": {
                    "nmap": {
                        "targets": ["127.0.0.1"],
                        "ports": "1-1000"
                    }
                }
            }
        )
        
        if response.status_code != 200:
            print(f"Failed to start scan: {response.text}")
            return
        
        scan_data = response.json()
        scan_id = scan_data["scan_id"]
        print(f"Started scan with ID: {scan_id}")
        
        # Poll for scan status
        while True:
            response = await client.get(f"{api_url}/{scan_id}")
            if response.status_code != 200:
                print(f"Error getting scan status: {response.text}")
                break
                
            status_data = response.json()
            status = status_data["status"]
            print(f"Scan status: {status}")
            
            if status in ["completed", "failed"]:
                print("\n=== Scan Results ===")
                print(json.dumps(status_data, indent=2))
                break
                
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_api_scan())
