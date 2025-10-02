"""
Agent Client - Handles communication between scanner agents and the control plane.
This implements the "tentacle" side of the octopus architecture.
"""

import asyncio
import httpx
import socket
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


class AgentClient:
    """Client for scanner agents to communicate with the control plane."""
    
    def __init__(self, control_plane_url: str = "http://backend:8000"):
        self.control_plane_url = control_plane_url
        self.agent_id: Optional[str] = None
        self.hostname = socket.gethostname()
        self.ip_address = self._get_ip_address()
        self.capabilities = ["nmap", "lynis", "clamav"]
        self.status = "idle"
        self.current_task = None
        self.heartbeat_interval = 30  # seconds
        
    def _get_ip_address(self) -> str:
        """Get the agent's IP address."""
        try:
            # Get IP by connecting to a public DNS server
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    async def register(self) -> bool:
        """Register this agent with the control plane."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.control_plane_url}/api/agents/register",
                    json={
                        "hostname": self.hostname,
                        "ip_address": self.ip_address,
                        "capabilities": self.capabilities,
                        "metadata": {
                            "os": os.name,
                            "scan_mode": os.getenv("SCAN_MODE", "local")
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.agent_id = data["agent_id"]
                    print(f"✅ Agent registered: {self.agent_id}")
                    print(f"   Hostname: {self.hostname}")
                    print(f"   IP: {self.ip_address}")
                    print(f"   Capabilities: {', '.join(self.capabilities)}")
                    return True
                else:
                    print(f"❌ Registration failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    async def send_heartbeat(self) -> Optional[Dict[str, Any]]:
        """Send heartbeat to control plane and check for assignments."""
        if not self.agent_id:
            print("⚠️  Agent not registered, cannot send heartbeat")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.control_plane_url}/api/agents/heartbeat",
                    json={
                        "agent_id": self.agent_id,
                        "status": self.status,
                        "current_task": self.current_task,
                        "metrics": {
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assignment = data.get("assignment")
                    
                    if assignment:
                        print(f"📋 New assignment received: {assignment['assignment_id']}")
                        return assignment
                    
                    return None
                else:
                    print(f"⚠️  Heartbeat failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"⚠️  Heartbeat error: {e}")
            return None
    
    async def run_heartbeat_loop(self):
        """Run continuous heartbeat loop."""
        print(f"💓 Starting heartbeat loop (every {self.heartbeat_interval}s)")
        
        while True:
            assignment = await self.send_heartbeat()
            
            if assignment:
                # Process the assignment
                await self.process_assignment(assignment)
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def process_assignment(self, assignment: Dict[str, Any]):
        """Process a scan assignment from the control plane."""
        print(f"\n🎯 Processing assignment: {assignment['assignment_id']}")
        print(f"   Targets: {assignment['targets']}")
        print(f"   Scanners: {assignment['scanners']}")
        
        self.status = "scanning"
        self.current_task = assignment['assignment_id']
        
        try:
            # Import scanner here to avoid circular imports
            from linux.security_scanner import SecurityScanner
            
            # Configure scanner with assignment
            config = {
                "scanners": assignment['scanners'],
                "api_url": f"{self.control_plane_url}/events",
                **assignment.get('config', {})
            }
            
            # Add targets to nmap config
            if "nmap" in assignment['scanners']:
                config["nmap"] = {
                    "targets": assignment['targets'],
                    "ports": assignment.get('config', {}).get('ports', '1-1000')
                }
            
            # Run the scan
            scanner = SecurityScanner(config)
            await scanner.scan()
            
            print(f"✅ Assignment completed: {assignment['assignment_id']}")
            print(f"   Results: {len(scanner.results)} findings")
            print(f"   Errors: {len(scanner.errors)} errors")
            
        except Exception as e:
            print(f"❌ Assignment failed: {e}")
        
        finally:
            self.status = "idle"
            self.current_task = None
    
    async def deregister(self):
        """Deregister this agent from the control plane."""
        if not self.agent_id:
            return
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.delete(
                    f"{self.control_plane_url}/api/agents/{self.agent_id}"
                )
                print(f"👋 Agent deregistered: {self.agent_id}")
        except Exception as e:
            print(f"⚠️  Deregistration error: {e}")


async def main():
    """Main agent loop."""
    # Get control plane URL from environment
    control_plane_url = os.getenv("API_URL", "http://backend:8000").replace("/events", "")
    
    # Create agent client
    agent = AgentClient(control_plane_url)
    
    # Register with control plane
    if not await agent.register():
        print("❌ Failed to register agent, exiting...")
        return
    
    try:
        # Start heartbeat loop
        await agent.run_heartbeat_loop()
    except KeyboardInterrupt:
        print("\n⚠️  Shutting down agent...")
    finally:
        await agent.deregister()


if __name__ == "__main__":
    print("🐙 AI Defend Scanner Agent Starting...")
    print("=" * 50)
    asyncio.run(main())
