"""
Security Audit Scanner Agent - Specialized for system security auditing
Includes: Lynis, chkrootkit, and rkhunter
"""

import asyncio
import subprocess
import json
import os
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, List


class SecurityAuditScanner:
    """System security audit scanner."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.results = []
        self.errors = []
        self.temp_dir = tempfile.mkdtemp(prefix="security_audit_")
        self.remote_host = config.get('remote_host')  # SSH target: user@host
        self.remote_key = config.get('remote_key')    # SSH key path
    
    async def run_command(self, cmd: List[str], timeout: int = 600) -> Dict[str, Any]:
        """Execute a command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore')
            }
        except asyncio.TimeoutError:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def scan_lynis(self):
        """Run Lynis security audit (local or remote)."""
        if self.remote_host:
            # Remote scan via SSH
            ssh_cmd = ["ssh"]
            if self.remote_key:
                ssh_cmd.extend(["-i", self.remote_key])
            ssh_cmd.extend([self.remote_host, "lynis audit system --quick --quiet"])
            cmd = ssh_cmd
        else:
            cmd = ["lynis", "audit", "system", "--quick", "--quiet"]
        
        try:
            result = await self.run_command(cmd, timeout=900)
            
            warnings = []
            suggestions = []
            hardening_index = None
            
            for line in result["stdout"].split('\n'):
                if 'Warning:' in line:
                    warnings.append(line.replace('Warning:', '').strip())
                elif 'Suggestion:' in line:
                    suggestions.append(line.replace('Suggestion:', '').strip())
                elif 'Hardening index' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        hardening_index = parts[1].strip()
            
            self.results.append({
                'scanner': 'lynis',
                'details': {
                    'warnings': warnings[:10],  # First 10 warnings
                    'suggestions': suggestions[:10],  # First 10 suggestions
                    'hardening_index': hardening_index,
                    'total_warnings': len(warnings),
                    'total_suggestions': len(suggestions)
                }
            })
            
        except Exception as e:
            self.errors.append(f"Lynis scan error: {str(e)}")
    
    async def scan_chkrootkit(self):
        """Run chkrootkit rootkit detection."""
        cmd = ["chkrootkit", "-q"]  # Quiet mode, only show problems
        
        try:
            result = await self.run_command(cmd, timeout=600)
            
            findings = []
            for line in result["stdout"].split('\n'):
                line = line.strip()
                if line and 'INFECTED' in line.upper():
                    findings.append({
                        'type': 'infected',
                        'details': line
                    })
                elif line and 'WARNING' in line.upper():
                    findings.append({
                        'type': 'warning',
                        'details': line
                    })
            
            self.results.append({
                'scanner': 'chkrootkit',
                'details': {
                    'findings': findings,
                    'total_findings': len(findings),
                    'scan_complete': result["returncode"] == 0
                }
            })
            
        except Exception as e:
            self.errors.append(f"chkrootkit scan error: {str(e)}")
    
    async def scan_rkhunter(self):
        """Run rkhunter rootkit detection."""
        # Update rkhunter database first
        update_cmd = ["rkhunter", "--update", "--quiet"]
        await self.run_command(update_cmd, timeout=300)
        
        # Run the scan
        cmd = ["rkhunter", "--check", "--skip-keypress", "--report-warnings-only"]
        
        try:
            result = await self.run_command(cmd, timeout=900)
            
            warnings = []
            for line in result["stdout"].split('\n'):
                line = line.strip()
                if line and ('Warning:' in line or 'warning' in line.lower()):
                    warnings.append(line)
            
            self.results.append({
                'scanner': 'rkhunter',
                'details': {
                    'warnings': warnings,
                    'total_warnings': len(warnings),
                    'scan_complete': True
                }
            })
            
        except Exception as e:
            self.errors.append(f"rkhunter scan error: {str(e)}")
    
    async def scan(self):
        """Run all security audit scans."""
        # Run Lynis if configured
        if 'lynis' in self.config or not self.config:
            await self.scan_lynis()
        
        # Run chkrootkit if configured
        if 'chkrootkit' in self.config or not self.config:
            await self.scan_chkrootkit()
        
        # Run rkhunter if configured
        if 'rkhunter' in self.config or not self.config:
            await self.scan_rkhunter()
        
        # Cleanup
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan results to dictionary."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_type": "security_audit",
            "results": self.results,
            "errors": self.errors
        }


async def main():
    """Test the security audit scanner."""
    config = {}
    
    scanner = SecurityAuditScanner(config)
    await scanner.scan()
    print(json.dumps(scanner.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
