from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import json

import asyncio

router = APIRouter(prefix="/api/agents", tags=["agents"])

# In-memory storage for agents (in production, use database)
agents = {}
agent_assignments = {}
registration_lock = asyncio.Lock()

class AgentRegistration(BaseModel):
    agent_id: Optional[str] = None
    hostname: str
    ip_address: str
    capabilities: List[str]  # e.g., ["nmap", "clamav", "lynis"]
    metadata: Dict[str, Any] = {}

class AgentHeartbeat(BaseModel):
    agent_id: str
    status: str  # "idle", "scanning", "error"
    current_task: Optional[str] = None
    metrics: Dict[str, Any] = {}
    status_update_only: bool = False

class ScanAssignment(BaseModel):
    targets: List[str]
    scanners: List[str]
    config: Dict[str, Any] = {}
    priority: int = 5

class AgentInfo(BaseModel):
    agent_id: str
    hostname: str
    ip_address: str
    capabilities: List[str]
    status: str
    last_heartbeat: datetime
    registered_at: datetime
    current_assignment: Optional[str] = None  # Assignment ID, not dict
    metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        # Ensure None values are included in JSON response
        use_enum_values = True

@router.post("/register", response_model=Dict[str, str])
async def register_agent(registration: AgentRegistration):
    """Register a new scanner agent with the control plane."""
    
    async with registration_lock:
        # Check if agent with same hostname already exists
        existing_agent_id = None
        for aid, agent in agents.items():
            if agent["hostname"] == registration.hostname:
                existing_agent_id = aid
                break
        
        # Use existing ID or generate new one
        agent_id = existing_agent_id or registration.agent_id or str(uuid.uuid4())
        
        # Store agent information
        agents[agent_id] = {
            "agent_id": agent_id,
            "hostname": registration.hostname,
            "ip_address": registration.ip_address,
            "capabilities": registration.capabilities,
            "metadata": registration.metadata,
            "status": "idle",
            "last_heartbeat": datetime.utcnow(),
            "last_scan_time": agents[agent_id].get("last_scan_time") if existing_agent_id else None,
            "registered_at": agents[agent_id]["registered_at"] if existing_agent_id else datetime.utcnow(),
            "current_assignment": agents[agent_id].get("current_assignment") if existing_agent_id else None,
            "metrics": None
        }
        
        action = "updated" if existing_agent_id else "registered"
        print(f"Agent {action}: {agent_id} ({registration.hostname})")
    
    return {
        "agent_id": agent_id,
        "status": "registered",
        "message": f"Agent {agent_id} {action} successfully"
    }

@router.post("/heartbeat")
async def agent_heartbeat(heartbeat: AgentHeartbeat):
    """Receive heartbeat from an agent to maintain connection."""
    if heartbeat.agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not registered")
    
    # Check for status change to update last_scan_time
    current_status = agents[heartbeat.agent_id]["status"]
    new_status = heartbeat.status
    
    # Update agent status
    agents[heartbeat.agent_id].update({
        "status": heartbeat.status,
        "last_heartbeat": datetime.utcnow(),
        "current_task": heartbeat.current_task,
        "metrics": heartbeat.metrics,
    })
    
    # If transitioning from scanning to idle, update last_scan_time
    if current_status == "scanning" and new_status == "idle":
        agents[heartbeat.agent_id]["last_scan_time"] = datetime.utcnow()

    # Update current_assignment based on agent report, BUT don't overwrite a pending assignment with None
    # This prevents the UI from "flashing" or losing the assignment state before the agent picks it up
    if heartbeat.current_task:
        agents[heartbeat.agent_id]["current_assignment"] = heartbeat.current_task
    elif heartbeat.agent_id not in agent_assignments:
        # Only clear it if we don't have a pending assignment waiting to be picked up
        agents[heartbeat.agent_id]["current_assignment"] = None

    assignment = None

    if not heartbeat.status_update_only:
        # Check if there's a pending assignment
        assignment = agent_assignments.get(heartbeat.agent_id)
        
        # Clear the assignment after sending it (agent will process it)
        if assignment and heartbeat.agent_id in agent_assignments:
            del agent_assignments[heartbeat.agent_id]
    
    return {
        "status": "ok",
        "assignment": assignment,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/")
async def list_agents():
    """List all registered agents."""
    now = datetime.utcnow()
    stale_threshold = timedelta(seconds=15)
    offline_threshold = timedelta(minutes=2)
    
    agent_list = []
    for agent in agents.values():
        last_heartbeat = agent["last_heartbeat"]
        latency = (now - last_heartbeat).total_seconds()
        
        # Determine health status
        health = "online"
        if latency > offline_threshold.total_seconds():
            health = "offline"
        elif latency > stale_threshold.total_seconds():
            health = "stale"
            
        agent_data = {
            "agent_id": agent["agent_id"],
            "hostname": agent["hostname"],
            "ip_address": agent["ip_address"],
            "capabilities": agent["capabilities"],
            "status": agent["status"], # idle, scanning, etc.
            "health": health, # online, stale, offline
            "latency": round(latency, 2),
            "last_heartbeat": last_heartbeat.isoformat(),
            "last_scan_time": agent.get("last_scan_time").isoformat() if agent.get("last_scan_time") else None,
            "registered_at": agent["registered_at"].isoformat(),
            "current_assignment": agent.get("current_assignment"),
            "metrics": agent.get("metrics"),
            "metadata": agent.get("metadata", {})
        }
        agent_list.append(agent_data)
    
    # Manually serialize to ensure None values are included
    json_str = json.dumps(agent_list, default=str)
    return JSONResponse(content=json.loads(json_str))

@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    """Get information about a specific agent."""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentInfo(**agents[agent_id])

@router.post("/{agent_id}/assign")
async def assign_scan(agent_id: str, assignment: ScanAssignment):
    """Assign a scan task to a specific agent."""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if agent is idle
    if agents[agent_id]["status"] != "idle":
        raise HTTPException(status_code=409, detail="Agent is busy")
    
    # Create assignment
    assignment_id = str(uuid.uuid4())
    agent_assignments[agent_id] = {
        "assignment_id": assignment_id,
        "targets": assignment.targets,
        "scanners": assignment.scanners,
        "config": assignment.config,
        "priority": assignment.priority,
        "assigned_at": datetime.utcnow().isoformat()
    }
    
    agents[agent_id]["current_assignment"] = assignment_id
    
    return {
        "assignment_id": assignment_id,
        "agent_id": agent_id,
        "status": "assigned"
    }

@router.delete("/{agent_id}")
async def deregister_agent(agent_id: str):
    """Deregister an agent."""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    del agents[agent_id]
    if agent_id in agent_assignments:
        del agent_assignments[agent_id]
    
    return {"status": "deregistered", "agent_id": agent_id}

@router.get("/health/check")
async def health_check():
    """Check health of all agents and identify stale ones."""
    now = datetime.utcnow()
    stale_threshold = timedelta(minutes=5)
    
    healthy = []
    stale = []
    
    for agent_id, agent in agents.items():
        time_since_heartbeat = now - agent["last_heartbeat"]
        
        if time_since_heartbeat > stale_threshold:
            stale.append({
                "agent_id": agent_id,
                "hostname": agent["hostname"],
                "last_seen": agent["last_heartbeat"].isoformat(),
                "time_since_heartbeat": str(time_since_heartbeat)
            })
        else:
            healthy.append({
                "agent_id": agent_id,
                "hostname": agent["hostname"],
                "status": agent["status"]
            })
    
    return {
        "total_agents": len(agents),
        "healthy": healthy,
        "stale": stale,
        "timestamp": now.isoformat()
    }
