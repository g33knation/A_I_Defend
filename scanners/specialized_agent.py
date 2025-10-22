"""
Specialized Agent Client - Supports network, malware, and security audit agents
"""

import asyncio
import httpx
import socket
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional


class SpecializedAgent:
    """Agent client for specialized scanners."""
    
    def __init__(self, agent_type: str, control_plane_url: str = "http://backend:8000"):
        self.agent_type = agent_type  # 'network', 'malware', or 'security_audit'
        self.control_plane_url = control_plane_url
        self.agent_id: Optional[str] = None
        self.hostname = socket.gethostname()
        self.ip_address = self._get_ip_address()
        self.capabilities = self._get_capabilities()
        self.status = "idle"
        self.current_task = None
        self.heartbeat_interval = 30
        self.scanner = None
        
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
    
    def _get_capabilities(self) -> List[str]:
        """Get capabilities based on agent type."""
        capabilities_map = {
            'network': ['nmap', 'suricata'],
            'network_intel': ['nmap', 'tshark', 'masscan', 'arp-scan', 'dns-enum', 'ping-sweep'],
            'malware': ['clamav', 'yara'],
            'security_audit': ['lynis', 'chkrootkit', 'rkhunter']
        }
        return capabilities_map.get(self.agent_type, [])
    
    async def register(self) -> bool:
        """Register this agent with the control plane."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.control_plane_url}/api/agents/register",
                    json={
                        "hostname": f"{self.hostname}-{self.agent_type}",
                        "ip_address": self.ip_address,
                        "capabilities": self.capabilities,
                        "metadata": {
                            "agent_type": self.agent_type,
                            "os": os.name
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.agent_id = data["agent_id"]
                    print(f"✅ {self.agent_type.upper()} Agent registered: {self.agent_id}")
                    print(f"   Hostname: {self.hostname}-{self.agent_type}")
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
                            "timestamp": datetime.utcnow().isoformat(),
                            "agent_type": self.agent_type
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
                    
        except Exception as e:
            print(f"⚠️  Heartbeat error: {e}")
            return None

    async def send_status_update(self):
        """Send a status-only heartbeat update."""
        if not self.agent_id:
            return
        
        try:
            # Get scanner progress if available
            scan_progress = None
            if self.scanner and hasattr(self.scanner, 'progress'):
                scan_progress = {
                    'progress': self.scanner.progress,
                    'current_scanner': self.scanner.current_scanner,
                    'scan_details': self.scanner.scan_details,
                    'results_count': len(self.scanner.results),
                    'errors_count': len(self.scanner.errors)
                }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{self.control_plane_url}/api/agents/heartbeat",
                    json={
                        "agent_id": self.agent_id,
                        "status": self.status,
                        "current_task": self.current_task,
                        "metrics": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "agent_type": self.agent_type,
                            "scan_progress": scan_progress
                        },
                        "status_update_only": True
                    }
                )
        except Exception as e:
            print(f"⚠️  Status update error: {e}")

    async def process_assignment(self, assignment: Dict[str, Any]):
        """Process a scan assignment."""
        print(f"\n🎯 Processing assignment: {assignment['assignment_id']}")
        print(f"   Scanners: {assignment['scanners']}")
        
        self.status = "scanning"
        self.current_task = assignment['assignment_id']
        await self.send_status_update()
        
        scanner = None
        
        try:
            # Import the appropriate scanner
            if self.agent_type == 'network':
                from network.network_scanner import NetworkScanner
                scanner = NetworkScanner(assignment.get('config', {}))
            elif self.agent_type == 'network_intel':
                from network_intel.network_intel_scanner import NetworkIntelScanner
                scanner = NetworkIntelScanner(assignment.get('config', {}))
            elif self.agent_type == 'malware':
                from malware.malware_scanner import MalwareScanner
                scanner = MalwareScanner(assignment.get('config', {}))
            elif self.agent_type == 'security_audit':
                from security.security_audit_scanner import SecurityAuditScanner
                scanner = SecurityAuditScanner(assignment.get('config', {}))
            else:
                print(f"❌ Unknown agent type: {self.agent_type}")
                return
            
            # Store scanner reference for progress tracking
            self.scanner = scanner
            
            # Run the scan with periodic progress updates
            scan_task = asyncio.create_task(scanner.scan())
            
            # Send progress updates while scanning
            while not scan_task.done():
                await asyncio.sleep(5)  # Update every 5 seconds
                await self.send_status_update()
            
            # Wait for scan to complete
            await scan_task
            
            # Post results to control plane
            for result in scanner.results:
                event_type = f"{result['scanner']}_scan"
                await self.post_event(result['scanner'], event_type, result)
            
            print(f"✅ Assignment completed: {assignment['assignment_id']}")
            print(f"   Results: {len(scanner.results)} findings")
            print(f"   Errors: {len(scanner.errors)} errors")
            
        except Exception as e:
            print(f"❌ Assignment failed: {e}")
        
        finally:
            self.status = "idle"
            self.current_task = None
            self.scanner = None
            await self.send_status_update()
    
    async def post_event(self, source: str, event_type: str, data: Dict[str, Any]):
        """Post scan results as events to the control plane."""
        try:
            event_url = f"{self.control_plane_url}/events"
            print(f"📤 Posting event to {event_url}: {source}/{event_type}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    event_url,
                    json={
                        "source": source,
                        "type": event_type,
                        "payload": data
                    }
                )
                
                if response.status_code == 200:
                    print(f"✅ Event posted successfully: {source}/{event_type}")
                else:
                    print(f"⚠️  Failed to post event: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"⚠️  Error posting event: {e}")
    
    async def run_heartbeat_loop(self):
        """Run continuous heartbeat loop."""
        print(f"💓 Starting heartbeat loop (every {self.heartbeat_interval}s)")
        
        while True:
            assignment = await self.send_heartbeat()
            
            if assignment:
                await self.process_assignment(assignment)
            
            await asyncio.sleep(self.heartbeat_interval)
    
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
    # Get agent type from environment or command line
    agent_type = os.getenv("AGENT_TYPE", sys.argv[1] if len(sys.argv) > 1 else "network")
    control_plane_url = os.getenv("API_URL", "http://backend:8000").replace("/events", "")
    
    print(f"🐙 AI Defend {agent_type.upper()} Scanner Agent Starting...")
    print("=" * 50)
    
    # Create specialized agent
    agent = SpecializedAgent(agent_type, control_plane_url)
    
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
    asyncio.run(main())
