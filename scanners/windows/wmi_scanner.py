"""
WMI Scanner - Scan Windows systems using WMI/WinRM
No agent installation required on target Windows systems
"""

import asyncio
import subprocess
import json
from typing import Dict, Any, List


class WMIScanner:
    """Scan Windows systems using WMI and PowerShell remoting."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.results = []
        self.errors = []
    
    async def run_remote_command(self, target: str, command: str, username: str, password: str):
        """Execute PowerShell command on remote Windows system."""
        # Using winrm (requires pywinrm package)
        ps_script = f"""
        $password = ConvertTo-SecureString '{password}' -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential('{username}', $password)
        Invoke-Command -ComputerName {target} -Credential $credential -ScriptBlock {{
            {command}
        }}
        """
        
        cmd = ["powershell", "-Command", ps_script]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300
            )
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore')
            }
            
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def scan_windows_defender(self, target: str, username: str, password: str):
        """Get Windows Defender scan results."""
        command = "Get-MpThreatDetection | Select-Object -First 10 | ConvertTo-Json"
        
        result = await self.run_remote_command(target, command, username, password)
        
        if result["returncode"] == 0 and result["stdout"]:
            try:
                threats = json.loads(result["stdout"])
                self.results.append({
                    'scanner': 'windows_defender',
                    'target': target,
                    'details': {
                        'threats': threats if isinstance(threats, list) else [threats],
                        'total_threats': len(threats) if isinstance(threats, list) else 1
                    }
                })
            except json.JSONDecodeError:
                self.errors.append(f"Failed to parse Defender results from {target}")
    
    async def scan_installed_software(self, target: str, username: str, password: str):
        """Get list of installed software for vulnerability assessment."""
        command = """
        Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* |
        Select-Object DisplayName, DisplayVersion, Publisher |
        Where-Object {$_.DisplayName -ne $null} |
        ConvertTo-Json
        """
        
        result = await self.run_remote_command(target, command, username, password)
        
        if result["returncode"] == 0 and result["stdout"]:
            try:
                software = json.loads(result["stdout"])
                self.results.append({
                    'scanner': 'software_inventory',
                    'target': target,
                    'details': {
                        'software': software if isinstance(software, list) else [software],
                        'total_packages': len(software) if isinstance(software, list) else 1
                    }
                })
            except json.JSONDecodeError:
                self.errors.append(f"Failed to parse software list from {target}")
    
    async def scan_security_events(self, target: str, username: str, password: str):
        """Get recent security events from Windows Event Log."""
        command = """
        Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625,4624} -MaxEvents 50 |
        Select-Object TimeCreated, Id, Message |
        ConvertTo-Json
        """
        
        result = await self.run_remote_command(target, command, username, password)
        
        if result["returncode"] == 0 and result["stdout"]:
            try:
                events = json.loads(result["stdout"])
                self.results.append({
                    'scanner': 'security_events',
                    'target': target,
                    'details': {
                        'events': events if isinstance(events, list) else [events],
                        'total_events': len(events) if isinstance(events, list) else 1
                    }
                })
            except json.JSONDecodeError:
                self.errors.append(f"Failed to parse events from {target}")
    
    async def scan(self):
        """Scan Windows targets."""
        targets = self.config.get('wmi', {}).get('targets', [])
        
        for target_config in targets:
            target = target_config.get('host')
            username = target_config.get('username')
            password = target_config.get('password')
            
            # Run scans
            await self.scan_windows_defender(target, username, password)
            await self.scan_installed_software(target, username, password)
            await self.scan_security_events(target, username, password)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan results to dictionary."""
        return {
            "scanner_type": "wmi",
            "results": self.results,
            "errors": self.errors
        }


# Example usage
async def main():
    config = {
        "wmi": {
            "targets": [
                {
                    "host": "192.168.1.100",
                    "username": "Administrator",
                    "password": "password"
                }
            ]
        }
    }
    
    scanner = WMIScanner(config)
    await scanner.scan()
    print(json.dumps(scanner.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
