"""
OctopusLeg - Base Class for AI Defend Agents
provides unified:
- Authentication (Nervous System)
- Registration & Heartbeating
- Centralized Logging
- Event Reporting
"""

import asyncio
import httpx
import socket
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

class OctopusLeg:
    """Base class for all Octopus agents (legs)."""
    
    def __init__(self, agent_type: str, control_plane_url: str = "http://backend:8000"):
        self.agent_type = agent_type
        self.control_plane_url = control_plane_url
        self.hostname = socket.gethostname()
        self.ip_address = self._get_ip_address()
        self.agent_id: Optional[str] = None
        self.status = "idle"
        self.current_task = None
        self.capabilities: List[str] = []
        
        # Nervous System Security
        self.api_key = os.getenv("BRAIN_API_KEY", "octopus-nervous-system-secret")
        self.auth_headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
    def _get_ip_address(self) -> str:
        """Get the agent's IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
            
    async def log(self, level: str, message: str, context: Dict[str, Any] = {}):
        """Send a log to the centralized Brain logger."""
        print(f"[{level}] {message}") # Always print to local stdout
        
        if not self.agent_id:
            return # Can't log remotes if not registered (or could send 'unknown')

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.control_plane_url}/logs",
                    headers=self.auth_headers,
                    json={
                        "agent_id": self.agent_id,
                        "log_level": level,
                        "message": message,
                        "context": context,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                # if response.status_code != 200:
                #    print(f"❌ Remote log failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Failed to send remote log: {e}")

    async def register(self, metadata: Dict[str, Any] = {}) -> bool:
        """Register the leg with the Brain."""
        try:
            print(f"🐙 Connecting to Nervous System at {self.control_plane_url}...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.control_plane_url}/api/agents/register",
                    headers=self.auth_headers,
                    json={
                        "hostname": self.hostname,
                        "ip_address": self.ip_address,
                        "capabilities": self.capabilities,
                        "metadata": {
                            "agent_type": self.agent_type,
                            **metadata
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.agent_id = data["agent_id"]
                    msg = f"Registered as {self.agent_id} ({self.agent_type})"
                    await self.log("INFO", msg)
                    return True
                else:
                    print(f"❌ Registration failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False

    async def send_heartbeat(self, metrics: Dict[str, Any] = {}) -> Optional[Dict[str, Any]]:
        """Send heartbeat to Brain and check for assignments."""
        if not self.agent_id:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.control_plane_url}/api/agents/heartbeat",
                    headers=self.auth_headers,
                    json={
                        "agent_id": self.agent_id,
                        "status": self.status,
                        "current_task": self.current_task,
                        "metrics": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "agent_type": self.agent_type,
                            **metrics
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("assignment")
                elif response.status_code == 404:
                    await self.log("WARN", "Agent not found in backend, re-registering...")
                    await self.register()
                    return None
                else:
                    print(f"⚠️  Heartbeat failed: {response.status_code}")
                    return None
        except Exception as e:
            print(f"⚠️  Heartbeat error: {e}")
            return None

    async def post_event(self, source: str, event_type: str, payload: Dict[str, Any]):
        """Report a security event to the Brain."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{self.control_plane_url}/events",
                    headers=self.auth_headers,
                    json={
                        "source": source,
                        "type": event_type,
                        "payload": payload
                    }
                )
        except Exception as e:
            await self.log("ERROR", f"Failed to post event {event_type}", {"error": str(e)})

    # Abstract methods to be implemented by subclasses if needed
    async def process_assignment(self, assignment: Dict[str, Any]):
        """Process a task assignment from the Brain."""
        raise NotImplementedError("Subclasses must implement process_assignment")

    async def run_heartbeat_loop(self, interval: int = 5):
        """Run the main heartbeat loop."""
        await self.log("INFO", f"Starting heartbeat loop (interval={interval}s)")
        
        # Ensure registered with retry
        while not self.agent_id:
            if await self.register():
                break
            await self.log("WARN", "Registration failed, retrying in 5s...")
            await asyncio.sleep(5)

        while True:
            try:
                assignment = await self.send_heartbeat(self._get_metrics())
                
                if assignment:
                    await self.process_assignment(assignment)
                
                await asyncio.sleep(interval)
            except Exception as e:
                await self.log("ERROR", "Heartbeat loop error", {"error": str(e)})
                await asyncio.sleep(interval)

    def _get_metrics(self) -> Dict[str, Any]:
        """Override to provide custom metrics."""
        return {}
