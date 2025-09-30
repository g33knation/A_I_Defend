from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import uuid
import os
from datetime import datetime

# Import the security scanner
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from scanners.linux.security_scanner import SecurityScanner
except ImportError as e:
    print(f"Error importing SecurityScanner: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

router = APIRouter(prefix="/api/scans", tags=["scans"])

# In-memory storage for scan results (in production, use a database)
scan_results = {}

class ScanConfig(BaseModel):
    scanners: List[str] = ["nmap", "lynis", "clamav", "chkrootkit", "rkhunter", "yara", "suricata"]
    config: Dict[str, Any] = {}

class ScanResult(BaseModel):
    scan_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

async def run_scan_async(scan_id: str, config: Dict[str, Any]):
    """Run a security scan asynchronously."""
    try:
        scanner = SecurityScanner(config)
        await scanner.scan()
        
        # Store results
        scan_results[scan_id] = {
            "status": "completed",
            "end_time": datetime.utcnow(),
            "results": scanner.to_dict(),
            "error": None
        }
    except Exception as e:
        scan_results[scan_id] = {
            "status": "failed",
            "end_time": datetime.utcnow(),
            "results": None,
            "error": str(e)
        }

@router.post("/start", response_model=Dict[str, str])
async def start_scan(
    scan_config: ScanConfig,
    background_tasks: BackgroundTasks
):
    """Start a new security scan."""
    scan_id = str(uuid.uuid4())
    
    # Initialize scan in progress
    scan_results[scan_id] = {
        "status": "running",
        "start_time": datetime.utcnow(),
        "end_time": None,
        "results": None,
        "error": None
    }
    
    # Start the scan in the background
    background_tasks.add_task(
        run_scan_async,
        scan_id=scan_id,
        config={
            "scanners": scan_config.scanners,
            **scan_config.config
        }
    )
    
    return {"scan_id": scan_id, "status": "started"}

@router.get("/{scan_id}", response_model=ScanResult)
async def get_scan_result(scan_id: str):
    """Get the status and results of a scan."""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = scan_results[scan_id]
    return {
        "scan_id": scan_id,
        "status": result["status"],
        "start_time": result["start_time"],
        "end_time": result["end_time"],
        "results": result.get("results"),
        "error": result.get("error")
    }

@router.get("/", response_model=List[Dict[str, Any]])
async def list_scans():
    """List all scans with their status."""
    return [
        {
            "scan_id": scan_id,
            "status": result["status"],
            "start_time": result["start_time"],
            "end_time": result["end_time"]
        }
        for scan_id, result in scan_results.items()
    ]

# Add this router to your main FastAPI app in main.py
