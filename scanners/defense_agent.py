"""
Defense Agent - Executes defensive actions like IP blocking and file quarantine
This agent runs with elevated privileges to manage firewall rules and file operations.
"""

import asyncio
import os
import subprocess
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional
from octopus_leg import OctopusLeg

class DefenseAgent(OctopusLeg):
    """Agent capable of executing defensive actions."""
    
    def __init__(self, control_plane_url: str = "http://backend:8000"):
        super().__init__("defense", control_plane_url)
        self.quarantine_path = os.getenv("QUARANTINE_PATH", "/quarantine")
        self.capabilities = [
            "defense", "block-ip", "unblock-ip", 
            "quarantine", "restore-file", "kill-process",
            "firewall-management", "tshark-sniff"
        ]
        
        # Ensure quarantine directory exists
        os.makedirs(self.quarantine_path, exist_ok=True)
    
    async def _get_active_blocks(self) -> int:
        """Count currently blocked IPs via iptables."""
        try:
            result = subprocess.run(
                ["iptables", "-L", "INPUT", "-n", "--line-numbers"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.count("DROP")
        except Exception:
            return 0
            
    async def _count_quarantined_files(self) -> int:
        """Count files in quarantine."""
        try:
            return len(list(Path(self.quarantine_path).glob("*")))
        except Exception:
            return 0

    def _get_metrics(self) -> Dict[str, Any]:
        """Provide defense-specific metrics."""
        # Note: We can't easily await here in a sync method, so we might return cached or 0
        # For simplicity in this refactor, we'll try to keep it synchronous or acceptable
        # Actually OctopusLeg calls this in an async loop but the method is defined as sync.
        # We'll upgrade _get_metrics to async in base or just do a quick check here if possible.
        # Since subprocess is blocking, we should be careful. 
        # Ideally, we should update the base class to support async metrics, but for now let's just use what we can.
        # We'll skip the heavy subprocess call here to avoid blocking the loop too much, 
        # or accepting it since it's an agent.
        return {} # Metrics will be calculated inside send_heartbeat override if needed

    # Override send_heartbeat to include async metrics
    async def send_heartbeat(self, metrics: Dict[str, Any] = {}) -> Optional[Dict[str, Any]]:
        metric_overrides = {
            "active_blocks": await self._get_active_blocks(),
            "quarantined_files": await self._count_quarantined_files()
        }
        return await super().send_heartbeat({**metrics, **metric_overrides})

    async def execute_action(self, action: str, target: str, reason: str = "") -> Dict[str, Any]:
        """Execute a defensive command."""
        await self.log("INFO", f"Executing {action} on {target}", {"reason": reason})
        
        try:
            if action == "block_ip":
                return await self._block_ip(target)
            elif action == "unblock_ip":
                return await self._unblock_ip(target)
            elif action == "quarantine_file":
                return await self._quarantine_file(target, reason)
            elif action == "restore_file":
                return await self._restore_file(target)
            elif action == "kill_process":
                return await self._kill_process(int(target))
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
        except Exception as e:
            await self.log("ERROR", f"Action failed: {e}")
            return {"success": False, "message": str(e)}

    # --- Action Implementations ---
    
    async def _block_ip(self, ip: str) -> Dict[str, Any]:
        # Check if already blocked
        check = subprocess.run(["iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True)
        if check.returncode == 0:
            return {"success": True, "message": f"IP {ip} already blocked"}
            
        res = subprocess.run(["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True, text=True)
        if res.returncode == 0:
            return {"success": True, "message": f"Blocked IP {ip}"}
        else:
            raise Exception(f"iptables error: {res.stderr}")

    async def _unblock_ip(self, ip: str) -> Dict[str, Any]:
        res = subprocess.run(["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True, text=True)
        if res.returncode == 0 or "No chain/target/match" in res.stderr:
            return {"success": True, "message": f"Unblocked IP {ip}"}
        else:
            raise Exception(f"iptables error: {res.stderr}")

    async def _quarantine_file(self, path: str, reason: str) -> Dict[str, Any]:
        src = Path(path)
        if not src.exists():
            return {"success": False, "message": "File not found"}
            
        timestamp = asyncio.get_event_loop().time() # simple timestamp
        dest = Path(self.quarantine_path) / f"{int(timestamp)}_{src.name}"
        
        # Metadata
        meta = {"original_path": str(src.absolute()), "reason": reason}
        shutil.move(str(src), str(dest))
        
        with open(str(dest) + ".meta", "w") as f:
            json.dump(meta, f)
            
        return {"success": True, "message": f"Quarantined to {dest.name}"}

    async def _restore_file(self, name: str) -> Dict[str, Any]:
        src = Path(self.quarantine_path) / name
        meta_file = Path(str(src) + ".meta")
        
        if not src.exists() or not meta_file.exists():
            return {"success": False, "message": "File or metadata missing"}
            
        with open(meta_file, "r") as f:
            meta = json.load(f)
            
        shutil.move(str(src), meta["original_path"])
        meta_file.unlink()
        return {"success": True, "message": f"Restored to {meta['original_path']}"}

    async def _kill_process(self, pid: int) -> Dict[str, Any]:
        try:
            os.kill(pid, 9)
            return {"success": True, "message": f"Killed PID {pid}"}
        except ProcessLookupError:
            return {"success": True, "message": "Process already gone"}
        except PermissionError:
            raise Exception("Permission denied")

    async def process_assignment(self, assignment: Dict[str, Any]):
        """Process defense assignment."""
        action_id = assignment.get("defense_action_id")
        action_type = assignment.get("action_type")
        target = assignment.get("target")
        reason = assignment.get("reason", "")
        
        self.status = "executing"
        self.current_task = f"{action_type}:{target}"
        await self.send_heartbeat() # Update status immediately
        
        result = await self.execute_action(action_type, target, reason)
        
        # Report result
        status = "active" if result.get("success") else "failed"
        await self.post_event("defense-agent", "defense_action_result", {
            "action_id": action_id,
            "result": result,
            "status": status
        })
        
        self.status = "idle"
        self.current_task = None
        
    async def run_periodic_tshark_scan(self):
        """Periodic background sniffing."""
        await self.log("INFO", "Starting periodic tshark scan (every 5m)")
        while True:
            try:
                interface = os.getenv("SNIFF_INTERFACE", "eth0")
                duration = 30
                cmd = ["tshark", "-i", interface, "-a", f"duration:{duration}", "-T", "json", "-l"]
                
                proc = await asyncio.create_subprocess_exec(
                    *cmd, 
                    stdout=asyncio.subprocess.PIPE, 
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    packets = json.loads(stdout.decode('utf-8', errors='ignore'))
                    # Simple volume check
                    if len(packets) > 1000: # Threshold
                        await self.post_event("defense-leg", "suspicious_traffic", {
                            "summary": f"High traffic volume ({len(packets)} packets)",
                            "interface": interface
                        })
                else:
                    await self.log("WARN", "Tshark failed", {"stderr": stderr.decode()})
                    
            except Exception as e:
                await self.log("ERROR", f"Periodic scan error: {e}")
                
            await asyncio.sleep(300)

async def main():
    control_plane_url = os.getenv("API_URL", "http://backend:8000").replace("/events", "")
    print("🐙 AI Defend DEFENSE Leg Starting (Octopus v2)...")
    
    agent = DefenseAgent(control_plane_url)
    
    await asyncio.gather(
        agent.run_heartbeat_loop(interval=5),
        agent.run_periodic_tshark_scan()
    )

if __name__ == "__main__":
    asyncio.run(main())
