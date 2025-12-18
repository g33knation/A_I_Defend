"""
Defense Agent - Executes defensive actions like IP blocking and file quarantine
This agent runs with elevated privileges to manage firewall rules and file operations.
"""

import asyncio
import httpx
import socket
import json
import os
import sys
import subprocess
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class DefenseAgent:
    """Agent capable of executing defensive actions."""
    
    def __init__(self, control_plane_url: str = "http://backend:8000"):
        self.control_plane_url = control_plane_url
        self.agent_id = None
        self.hostname = socket.gethostname()
        self.ip_address = self._get_ip_address()
        self.status = "idle"
        self.current_action = None
        self.quarantine_path = os.getenv("QUARANTINE_PATH", "/quarantine")
        self.capabilities = [
            "defense",
            "block-ip",
            "unblock-ip", 
            "quarantine",
            "restore-file",
            "firewall-management"
        ]
        
        # Ensure quarantine directory exists
        os.makedirs(self.quarantine_path, exist_ok=True)
        
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
    
    async def register(self) -> bool:
        """Register this agent with the control plane."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.control_plane_url}/api/agents/register",
                    json={
                        "hostname": self.hostname,
                        "ip_address": self.ip_address,
                        "capabilities": self.capabilities,
                        "metadata": {
                            "agent_type": "defense",
                            "quarantine_path": self.quarantine_path
                        }
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.agent_id = data.get("agent_id")
                    print(f"[+] Registered as defense agent: {self.agent_id}")
                    return True
                else:
                    print(f"[-] Registration failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"[-] Registration error: {e}")
            return False
    
    async def send_heartbeat(self) -> Optional[Dict]:
        """Send heartbeat and check for defense assignments."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.control_plane_url}/api/agents/heartbeat",
                    json={
                        "agent_id": self.agent_id,
                        "status": self.status,
                        "current_task": self.current_action,
                        "metrics": {
                            "active_blocks": await self._count_active_blocks(),
                            "quarantined_files": await self._count_quarantined_files()
                        }
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Check for defense assignment
                    if "assignment" in data and data["assignment"]:
                        return data["assignment"]
                    return None
                else:
                    print(f"[-] Heartbeat failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"[-] Heartbeat error: {e}")
            return None
    
    async def _count_active_blocks(self) -> int:
        """Count currently blocked IPs via iptables."""
        try:
            result = subprocess.run(
                ["iptables", "-L", "INPUT", "-n", "--line-numbers"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Count DROP rules (each block is a DROP rule)
            return result.stdout.count("DROP")
        except Exception:
            return 0
    
    async def _count_quarantined_files(self) -> int:
        """Count files in quarantine."""
        try:
            return len(list(Path(self.quarantine_path).glob("*")))
        except Exception:
            return 0
    
    async def block_ip(self, ip: str, reason: str = "") -> Dict[str, Any]:
        """Block an IP address using iptables."""
        print(f"[*] Blocking IP: {ip} (Reason: {reason})")
        
        try:
            # Check if already blocked
            check_result = subprocess.run(
                ["iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"],
                capture_output=True,
                timeout=5
            )
            
            if check_result.returncode == 0:
                return {
                    "success": True,
                    "message": f"IP {ip} was already blocked",
                    "ip": ip,
                    "action": "block_ip"
                }
            
            # Block the IP
            result = subprocess.run(
                ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"[+] Successfully blocked IP: {ip}")
                return {
                    "success": True,
                    "message": f"Blocked IP {ip}",
                    "ip": ip,
                    "action": "block_ip"
                }
            else:
                print(f"[-] Failed to block IP: {result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to block IP: {result.stderr}",
                    "ip": ip,
                    "action": "block_ip"
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "iptables command timed out", "ip": ip}
        except Exception as e:
            return {"success": False, "message": str(e), "ip": ip}
    
    async def unblock_ip(self, ip: str) -> Dict[str, Any]:
        """Unblock a previously blocked IP address."""
        print(f"[*] Unblocking IP: {ip}")
        
        try:
            result = subprocess.run(
                ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"[+] Successfully unblocked IP: {ip}")
                return {
                    "success": True,
                    "message": f"Unblocked IP {ip}",
                    "ip": ip,
                    "action": "unblock_ip"
                }
            else:
                # Check if it wasn't blocked
                if "No chain/target/match by that name" in result.stderr or "Bad rule" in result.stderr:
                    return {
                        "success": True,
                        "message": f"IP {ip} was not blocked",
                        "ip": ip,
                        "action": "unblock_ip"
                    }
                return {
                    "success": False,
                    "message": f"Failed to unblock IP: {result.stderr}",
                    "ip": ip,
                    "action": "unblock_ip"
                }
                
        except Exception as e:
            return {"success": False, "message": str(e), "ip": ip}
    
    async def quarantine_file(self, file_path: str, reason: str = "") -> Dict[str, Any]:
        """Move a file to quarantine directory."""
        print(f"[*] Quarantining file: {file_path} (Reason: {reason})")
        
        try:
            source = Path(file_path)
            
            if not source.exists():
                return {
                    "success": False,
                    "message": f"File not found: {file_path}",
                    "file_path": file_path,
                    "action": "quarantine_file"
                }
            
            # Create unique quarantine filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_name = f"{timestamp}_{source.name}"
            quarantine_dest = Path(self.quarantine_path) / quarantine_name
            
            # Save metadata about original location
            metadata = {
                "original_path": str(source.absolute()),
                "quarantined_at": datetime.now().isoformat(),
                "reason": reason,
                "original_permissions": oct(source.stat().st_mode)[-3:]
            }
            
            # Move the file
            shutil.move(str(source), str(quarantine_dest))
            
            # Write metadata
            metadata_file = quarantine_dest.with_suffix(quarantine_dest.suffix + ".meta")
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"[+] Successfully quarantined: {file_path} -> {quarantine_dest}")
            return {
                "success": True,
                "message": f"Quarantined {source.name}",
                "file_path": file_path,
                "quarantine_path": str(quarantine_dest),
                "action": "quarantine_file"
            }
            
        except PermissionError:
            return {
                "success": False,
                "message": f"Permission denied: {file_path}",
                "file_path": file_path,
                "action": "quarantine_file"
            }
        except Exception as e:
            return {"success": False, "message": str(e), "file_path": file_path}
    
    async def restore_file(self, quarantine_name: str) -> Dict[str, Any]:
        """Restore a quarantined file to its original location."""
        print(f"[*] Restoring file: {quarantine_name}")
        
        try:
            quarantine_file = Path(self.quarantine_path) / quarantine_name
            metadata_file = quarantine_file.with_suffix(quarantine_file.suffix + ".meta")
            
            if not quarantine_file.exists():
                return {
                    "success": False,
                    "message": f"Quarantined file not found: {quarantine_name}",
                    "action": "restore_file"
                }
            
            # Read metadata
            original_path = None
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    original_path = metadata.get("original_path")
            
            if not original_path:
                return {
                    "success": False,
                    "message": "Cannot restore: original path unknown",
                    "action": "restore_file"
                }
            
            # Restore the file
            shutil.move(str(quarantine_file), original_path)
            
            # Remove metadata file
            if metadata_file.exists():
                metadata_file.unlink()
            
            print(f"[+] Successfully restored: {quarantine_name} -> {original_path}")
            return {
                "success": True,
                "message": f"Restored to {original_path}",
                "original_path": original_path,
                "action": "restore_file"
            }
            
        except Exception as e:
            return {"success": False, "message": str(e), "action": "restore_file"}
    
    async def kill_process(self, pid: int, reason: str = "") -> Dict[str, Any]:
        """Kill a process by PID."""
        print(f"[*] Killing process: {pid} (Reason: {reason})")
        
        try:
            # First check if process exists
            result = subprocess.run(
                ["kill", "-0", str(pid)],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {
                    "success": True,
                    "message": f"Process {pid} does not exist",
                    "pid": pid,
                    "action": "kill_process"
                }
            
            # Kill the process
            result = subprocess.run(
                ["kill", "-9", str(pid)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"[+] Successfully killed process: {pid}")
                return {
                    "success": True,
                    "message": f"Killed process {pid}",
                    "pid": pid,
                    "action": "kill_process"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to kill process: {result.stderr}",
                    "pid": pid,
                    "action": "kill_process"
                }
                
        except Exception as e:
            return {"success": False, "message": str(e), "pid": pid}
    
    async def process_assignment(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Process a defense action assignment."""
        action_type = assignment.get("action_type")
        target = assignment.get("target")
        reason = assignment.get("reason", "")
        defense_action_id = assignment.get("defense_action_id")
        
        print(f"[*] Processing defense action: {action_type} -> {target}")
        self.status = "executing"
        self.current_action = f"{action_type}: {target}"
        
        result = None
        
        if action_type == "block_ip":
            result = await self.block_ip(target, reason)
        elif action_type == "unblock_ip":
            result = await self.unblock_ip(target)
        elif action_type == "quarantine_file":
            result = await self.quarantine_file(target, reason)
        elif action_type == "restore_file":
            result = await self.restore_file(target)
        elif action_type == "kill_process":
            result = await self.kill_process(int(target), reason)
        else:
            result = {"success": False, "message": f"Unknown action type: {action_type}"}
        
        # Report result back to control plane
        await self.report_action_result(defense_action_id, result)
        
        self.status = "idle"
        self.current_action = None
        
        return result
    
    async def report_action_result(self, action_id: int, result: Dict[str, Any]):
        """Report defense action result to control plane."""
        try:
            async with httpx.AsyncClient() as client:
                # Update defense action status
                status = "active" if result.get("success") else "failed"
                await client.post(
                    f"{self.control_plane_url}/events",
                    json={
                        "source": "defense-agent",
                        "type": "defense_action_result",
                        "payload": {
                            "action_id": action_id,
                            "result": result,
                            "status": status
                        }
                    },
                    timeout=10.0
                )
        except Exception as e:
            print(f"[-] Error reporting action result: {e}")
    
    async def run(self):
        """Main agent loop."""
        print("[*] Starting Defense Agent...")
        
        # Register with control plane
        while not await self.register():
            print("[*] Retrying registration in 5 seconds...")
            await asyncio.sleep(5)
        
        print("[+] Defense Agent active and ready")
        
        # Main heartbeat loop
        while True:
            try:
                assignment = await self.send_heartbeat()
                
                if assignment:
                    await self.process_assignment(assignment)
                
                await asyncio.sleep(5)  # 5-second heartbeat interval
                
            except asyncio.CancelledError:
                print("[*] Defense Agent shutting down...")
                break
            except Exception as e:
                print(f"[-] Error in main loop: {e}")
                await asyncio.sleep(5)


async def main():
    """Entry point for defense agent."""
    control_plane_url = os.getenv("API_URL", "http://backend:8000")
    agent = DefenseAgent(control_plane_url=control_plane_url)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
