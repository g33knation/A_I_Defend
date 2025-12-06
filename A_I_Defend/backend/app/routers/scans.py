from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import subprocess
import json
import asyncio
import uuid
from datetime import datetime
from app.auth import get_current_user

router = APIRouter(prefix="/api/scans", tags=["scans"], dependencies=[Depends(get_current_user)])

# In-memory storage for scan results (in production, use database)
scan_results = {}

class ScanRequest(BaseModel):
    target: str
    scan_type: str  # "quick", "full", "custom"
    options: Dict[str, Any] = {}

class ScanResult(BaseModel):
    scan_id: str
    target: str
    scan_type: str
    status: str  # "pending", "running", "completed", "failed"
    start_time: str
    end_time: Optional[str] = None
    findings: List[Dict[str, Any]] = []
    raw_output: Optional[str] = None

async def run_scan_async(scan_id: str, target: str, scan_type: str, options: Dict[str, Any]):
    """
    Execute the scan asynchronously using the scanner container.
    """
    print(f"Starting scan {scan_id} on {target} ({scan_type})")
    scan_results[scan_id]["status"] = "running"
    
    try:
        # Construct configuration for the scanner
        config = {
            "target": target,
            "scan_type": scan_type,
            "options": options,
            "scan_id": scan_id
        }
        config_json = json.dumps(config)
        
        # Static Python script to run inside the container
        # We pass the configuration via environment variable to avoid code injection
        python_script = """
import asyncio
import json
import sys
import os
import warnings
warnings.filterwarnings('ignore')
try:
    os.chdir('/app')
    sys.path.insert(0, '/app')
    from linux.security_scanner import SecurityScanner

    async def main():
        config_str = os.environ.get('SCAN_CONFIG', '{}')
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid configuration provided"}))
            return

        # Override API URL to use backend container hostname
        if 'api_url' not in config:
            config['api_url'] = 'http://backend:8000/events'
        
        scanner = SecurityScanner(config)
        await scanner.scan()
        # Only print JSON output, suppress all other output
        print(json.dumps(scanner.to_dict()))

    asyncio.run(main())
except Exception as e:
    print(json.dumps({"error": str(e)}))
"""

        # Run the scan in the scanner container
        # We use 'docker exec' to run the script inside the running 'scanner' container
        # Note: This assumes a container named 'scanner' is running.
        # In docker-compose, the service is 'malware-scanner' or 'security-scanner'.
        # Based on previous analysis, there is a 'malware-scanner' container.
        # We might need to adjust the container name if it's different.
        # Assuming 'malware-scanner' is the intended container.
        
        container_name = "malware-scanner" 
        
        cmd = [
            "docker", "exec", 
            "-e", f"SCAN_CONFIG={config_json}", 
            container_name, 
            "python", "-W", "ignore", "-c", python_script
        ]
        
        # Run subprocess in a thread to avoid blocking the event loop
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"Scan failed with return code {process.returncode}")
            print(f"Stderr: {stderr.decode()}")
            scan_results[scan_id]["status"] = "failed"
            scan_results[scan_id]["raw_output"] = stderr.decode()
            scan_results[scan_id]["end_time"] = datetime.utcnow().isoformat()
            return

        output = stdout.decode().strip()
        try:
            # Parse the JSON output from the scanner
            # Find the last line that looks like JSON
            lines = output.split('\n')
            json_line = ""
            for line in reversed(lines):
                if line.strip().startswith('{') and line.strip().endswith('}'):
                    json_line = line
                    break
            
            if not json_line:
                raise ValueError("No JSON output found")
                
            result_data = json.loads(json_line)
            
            scan_results[scan_id]["status"] = "completed"
            scan_results[scan_id]["findings"] = result_data.get("findings", [])
            scan_results[scan_id]["raw_output"] = output
            scan_results[scan_id]["end_time"] = datetime.utcnow().isoformat()
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse scanner output: {e}")
            print(f"Output was: {output}")
            scan_results[scan_id]["status"] = "failed"
            scan_results[scan_id]["raw_output"] = f"Failed to parse output: {output}"
            scan_results[scan_id]["end_time"] = datetime.utcnow().isoformat()

    except Exception as e:
        print(f"Exception during scan execution: {e}")
        scan_results[scan_id]["status"] = "failed"
        scan_results[scan_id]["raw_output"] = str(e)
        scan_results[scan_id]["end_time"] = datetime.utcnow().isoformat()

@router.post("/run", response_model=ScanResult)
async def run_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Initiate a new security scan.
    """
    scan_id = str(uuid.uuid4())
    start_time = datetime.utcnow().isoformat()
    
    scan_results[scan_id] = {
        "scan_id": scan_id,
        "target": request.target,
        "scan_type": request.scan_type,
        "status": "pending",
        "start_time": start_time,
        "findings": [],
        "raw_output": None
    }
    
    # Run the scan in the background
    background_tasks.add_task(
        run_scan_async, 
        scan_id, 
        request.target, 
        request.scan_type, 
        request.options
    )
    
    return ScanResult(**scan_results[scan_id])

@router.get("/{scan_id}", response_model=ScanResult)
async def get_scan_status(scan_id: str):
    """
    Get the status and results of a scan.
    """
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return ScanResult(**scan_results[scan_id])

@router.get("/", response_model=List[ScanResult])
async def list_scans():
    """
    List all scans.
    """
    return [ScanResult(**result) for result in scan_results.values()]
