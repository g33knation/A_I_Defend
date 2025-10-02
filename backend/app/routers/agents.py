from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/agents", tags=["agents"])

# In-memory storage for agents (in production, use database)
agents = {}
agent_assignments = {}

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
    current_assignment: Optional[Dict[str, Any]] = None

@router.post("/register", response_model=Dict[str, str])
async def register_agent(registration: AgentRegistration):
    """Register a new scanner agent with the control plane."""
    # Generate agent ID if not provided
    agent_id = registration.agent_id or str(uuid.uuid4())
    
    # Store agent information
    agents[agent_id] = {
        "agent_id": agent_id,
        "hostname": registration.hostname,
        "ip_address": registration.ip_address,
        "capabilities": registration.capabilities,
        "metadata": registration.metadata,
        "status": "idle",
        "last_heartbeat": datetime.utcnow(),
        "registered_at": datetime.utcnow(),
        "current_assignment": None
    }
    
    print(f"Agent registered: {agent_id} ({registration.hostname})")
    
    return {
        "agent_id": agent_id,
        "status": "registered",
        "message": f"Agent {agent_id} registered successfully"
    }

@router.post("/heartbeat")
async def agent_heartbeat(heartbeat: AgentHeartbeat):
    """Receive heartbeat from an agent to maintain connection."""
    if heartbeat.agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not registered")
    
    # Update agent status
    agents[heartbeat.agent_id].update({
        "status": heartbeat.status,
        "last_heartbeat": datetime.utcnow(),
        "current_task": heartbeat.current_task,
        "metrics": heartbeat.metrics
    })
    
    # Check if there's a pending assignment
    assignment = agent_assignments.get(heartbeat.agent_id)
    
    return {
        "status": "ok",
        "assignment": assignment,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """List all registered agents."""
    return [AgentInfo(**agent) for agent in agents.values()]

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
