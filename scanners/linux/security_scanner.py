#!/usr/bin/env python3
"""
Comprehensive Security Scanner for Linux Systems
Integrates multiple security tools:
- Nmap (network scanning)
- Lynis (security auditing)
- ClamAV (antivirus)
- TShark (network traffic analysis)
- chkrootkit (rootkit detection)
- YARA (pattern matching)
- RKHunter (rootkit hunter)
- Suricata (IDS/IPS)
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import httpx
try:
    import yaml
except ImportError:
    yaml = None
    print("Warning: pyyaml not installed. Some features may be limited.")

# Make magic import optional
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic-bin not installed. File type detection will be limited.")

import yara

# Import base scanner
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scanners.base_scanner import BaseScanner

class SecurityScanner(BaseScanner):
    """Comprehensive security scanner for Linux systems."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the security scanner with configuration."""
        super().__init__(config)
        self.temp_dir = tempfile.mkdtemp(prefix="security_scan_")
        self.api_url = self.config.get("api_url", "http://localhost:8000/api/events")
        
        # Initialize YARA rules if configured
        self.yara_rules = None
        yara_rules_dir = self.config.get("yara_rules_dir", "/etc/yara-rules")
        if os.path.isdir(yara_rules_dir):
            try:
                self.yara_rules = yara.compile(yara_rules_dir)
            except Exception as e:
                self.errors.append(f"Failed to load YARA rules: {str(e)}")
    
    async def scan(self) -> bool:
        """Run all configured security scans."""
        try:
            # Run all enabled scanners
            scanners = self.config.get("scanners", [
                "nmap", "lynis", "clamav", "chkrootkit", 
                "rkhunter", "yara", "suricata"
            ])
            
            for scanner_name in scanners:
                if scanner_name in self.config:
                    try:
                        scanner_method = getattr(self, f"scan_{scanner_name}")
                        if asyncio.iscoroutinefunction(scanner_method):
                            await scanner_method()
                        else:
                            # For sync methods, run in thread
                            await asyncio.get_event_loop().run_in_executor(
                                None, scanner_method
                            )
                    except Exception as e:
                        self.errors.append(f"Error in {scanner_name} scan: {str(e)}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Scan failed: {str(e)}")
            return False
        finally:
            # Clean up temporary files
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # --- Individual Scanner Implementations ---
    
    async def scan_nmap(self):
        """Run Nmap network scan."""
        targets = self.config.get("nmap", {}).get("targets", ["127.0.0.1"])
        ports = self.config.get("nmap", {}).get("ports", "1-1000")
        args = self.config.get("nmap", {}).get("arguments", "-T4 -A -v")
        
        for target in targets:
            output_file = os.path.join(self.temp_dir, f"nmap_{target.replace('.', '_')}.xml")
            cmd = ["nmap", "-p", str(ports), *args.split(), "-oX", output_file, target]
            
            try:
                result = await self.run_command(cmd, timeout=600)
                if result["returncode"] != 0:
                    self.errors.append(f"Nmap scan failed for {target}: {result['stderr']}")
                    continue
                
                # Parse the Nmap results
                await self._parse_nmap_results(output_file, target)
                
            except Exception as e:
                self.errors.append(f"Error running Nmap scan for {target}: {str(e)}")
                if self.config.get('debug', False):
                    import traceback
                    self.errors.append(traceback.format_exc())
                continue
    
    async def _parse_nmap_results(self, xml_file: str, target: str):
        """Parse Nmap XML output and create events."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for host in root.findall('host'):
                # Parse host information
                host_info = {
                    'target': target,
                    'status': host.find('status').get('state', 'unknown') if host.find('status') is not None else 'unknown',
                    'address': None,
                    'hostnames': [],
                    'ports': []
                }
                
                # Get IP address
                for address in host.findall('address'):
                    if address.get('addrtype') == 'ipv4':
                        host_info['address'] = address.get('addr')
                        break
                
                # Get hostnames
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    for hostname in hostnames.findall('hostname'):
                        host_info['hostnames'].append({
                            'name': hostname.get('name'),
                            'type': hostname.get('type')
                        })
                
                # Get ports and services
                ports = host.find('ports')
                if ports is not None:
                    for port in ports.findall('port'):
                        port_info = {
                            'port': port.get('portid'),
                            'protocol': port.get('protocol'),
                            'state': port.find('state').get('state') if port.find('state') is not None else 'unknown',
                            'service': port.find('service').get('name') if port.find('service') is not None else 'unknown'
                        }
                        host_info['ports'].append(port_info)
                
                # Add to results
                result = {
                    'scanner': 'nmap',
                    'target': target,
                    'type': 'port_scan',
                    'severity': 'info',
                    'details': host_info,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.results.append(result)
                await self._post_event("nmap", "port_scan", result)
                        
        except Exception as e:
            self.errors.append(f"Error parsing Nmap results: {str(e)}")
            if self.config.get('debug', False):
                import traceback
                self.errors.append(traceback.format_exc())
    
    async def scan_clamav(self):
        """Run ClamAV antivirus scan."""
        paths = self.config.get("clamav", {}).get("paths", ["/tmp", "/home", "/var/www"])
        
        for path in paths:
            if not os.path.exists(path):
                self.errors.append(f"ClamAV path does not exist: {path}")
                continue
                
            output_file = os.path.join(self.temp_dir, f"clamav_{os.path.basename(path)}.log")
            cmd = ["clamscan", "-r", "--no-summary", "--log", output_file, path]
            
            try:
                result = await self.run_command(cmd, timeout=3600)  # 1 hour timeout for full scans
                
                # Parse results
                with open(output_file, 'r') as f:
                    scan_results = f.read()
                
                infected_files = []
                for line in scan_results.splitlines():
                    if "FOUND" in line:
                        parts = line.split(": ")
                        if len(parts) >= 2:
                            file_path = parts[0].strip()
                            signature = parts[1].replace("FOUND", "").strip()
                            infected_files.append({
                                "file": file_path,
                                "signature": signature
                            })
                
                if infected_files:
                    result = {
                        "type": "malware_detected",
                        "severity": "critical",
                        "path_scanned": path,
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": {
                            "infected_files": infected_files,
                            "scan_output": scan_results
                        }
                    }
                    self.results.append(result)
                    await self._post_event("clamav", "malware_detected", result)
                
            except Exception as e:
                self.errors.append(f"ClamAV scan error on {path}: {str(e)}")
    
    async def scan_chkrootkit(self):
        """Run chkrootkit to detect rootkits."""
        output_file = os.path.join(self.temp_dir, "chkrootkit.log")
        cmd = ["chkrootkit", "-q"]
        
        try:
            result = await self.run_command(cmd, timeout=900)  # 15 minute timeout
            
            # Check for signs of compromise
            warnings = []
            for line in result["stdout"].splitlines():
                line = line.strip()
                if line and not line.startswith("Searching for") and not line.startswith("Checking"):
                    warnings.append(line)
            
            if warnings or result["returncode"] != 0:
                result = {
                    "type": "rootkit_scan",
                    "severity": "high" if warnings else "info",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "warnings": warnings,
                        "exit_code": result["returncode"],
                        "stderr": result["stderr"]
                    }
                }
                self.results.append(result)
                await self._post_event("chkrootkit", "rootkit_scan", result)
                
        except Exception as e:
            self.errors.append(f"chkrootkit scan error: {str(e)}")
    
    async def scan_rkhunter(self):
        """Run RKHunter to detect rootkits and backdoors."""
        output_file = os.path.join(self.temp_dir, "rkhunter.log")
        cmd = ["rkhunter", "--check", "--sk", "--nocolors", "--report-warnings-only"]
        
        try:
            result = await self.run_command(cmd, timeout=1200)  # 20 minute timeout
            
            # Parse results
            warnings = []
            for line in result["stdout"].splitlines():
                line = line.strip()
                if line and "Warning:" in line:
                    warnings.append(line)
            
            if warnings or result["returncode"] != 0:
                result = {
                    "type": "rkhunter_scan",
                    "severity": "high" if warnings else "info",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "warnings": warnings,
                        "exit_code": result["returncode"],
                        "stderr": result["stderr"]
                    }
                }
                self.results.append(result)
                await self._post_event("rkhunter", "rootkit_scan", result)
                
        except Exception as e:
            self.errors.append(f"RKHunter scan error: {str(e)}")
    
    async def scan_yara(self):
        """Run YARA rules against files."""
        if not self.yara_rules:
            self.errors.append("No YARA rules loaded")
            return
            
        paths = self.config.get("yara", {}).get("paths", ["/tmp", "/bin", "/sbin", "/usr/bin", "/usr/sbin"])
        
        for path in paths:
            if not os.path.exists(path):
                self.errors.append(f"YARA scan path does not exist: {path}")
                continue
                
            matches = []
            
            try:
                if os.path.isfile(path):
                    # Scan single file
                    try:
                        file_matches = self.yara_rules.match(path)
                        if file_matches:
                            matches.append({
                                "file": path,
                                "matches": [{"rule": str(m), "tags": m.tags, "meta": m.meta} for m in file_matches]
                            })
                    except Exception as e:
                        self.errors.append(f"Error scanning {path} with YARA: {str(e)}")
                else:
                    # Recursively scan directory
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                file_matches = self.yara_rules.match(file_path)
                                if file_matches:
                                    matches.append({
                                        "file": file_path,
                                        "matches": [{"rule": str(m), "tags": m.tags, "meta": m.meta} for m in file_matches]
                                    })
                            except Exception as e:
                                # Skip files that can't be read
                                continue
                
                if matches:
                    result = {
                        "type": "yara_scan",
                        "severity": "high",
                        "path_scanned": path,
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": {
                            "matches": matches
                        }
                    }
                    self.results.append(result)
                    await self._post_event("yara", "malware_detected", result)
                    
            except Exception as e:
                self.errors.append(f"YARA scan error on {path}: {str(e)}")
    
    async def scan_suricata(self):
        """Check Suricata logs for alerts."""
        log_paths = self.config.get("suricata", {}).get(
            "log_paths", 
            ["/var/log/suricata/fast.log", "/var/log/suricata/eve.json"]
        )
        
        alerts = []
        
        for log_path in log_paths:
            if not os.path.exists(log_path):
                continue
                
            try:
                if log_path.endswith(".json"):
                    # Parse JSON-based logs (eve.json)
                    with open(log_path, 'r') as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                if entry.get("event_type") == "alert":
                                    alerts.append({
                                        "timestamp": entry.get("timestamp"),
                                        "signature": entry.get("alert", {}).get("signature"),
                                        "severity": entry.get("alert", {}).get("severity", 3),
                                        "source_ip": entry.get("src_ip"),
                                        "dest_ip": entry.get("dest_ip"),
                                        "details": entry
                                    })
                            except json.JSONDecodeError:
                                continue
                else:
                    # Parse plaintext logs (fast.log)
                    with open(log_path, 'r') as f:
                        for line in f:
                            # Example: 01/01-12:00:00.123456  [**] [1:1000001:1] TEST Alert [**] [Classification: Generic Event] [Priority: 3] {TCP} 192.168.1.1:1234 -> 192.168.1.2:80
                            match = re.match(
                                r'^(\d+/\d+-\d+:\d+:\d+\.\d+)\s+\[\*\*\]\s+\[(\d+):(\d+):(\d+)\]\s+(.+?)\s+\[\*\*\]\s+\[Classification:([^\]]+)\]\s+\[Priority:\s*(\d+)\]\s+\{(\w+)\}\s+(\d+\.\d+\.\d+\.\d+):(\d+)\s+->\s+(\d+\.\d+\.\d+\.\d+):(\d+)',
                                line
                            )
                            if match:
                                alerts.append({
                                    "timestamp": match.group(1),
                                    "signature": match.group(5).strip(),
                                    "severity": int(match.group(7)),
                                    "source_ip": match.group(9),
                                    "dest_ip": match.group(11),
                                    "details": line.strip()
                                })
                
            except Exception as e:
                self.errors.append(f"Error reading Suricata log {log_path}: {str(e)}")
        
        if alerts:
            result = {
                "type": "ids_alert",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "alerts": alerts,
                    "total_alerts": len(alerts)
                }
            }
            self.results.append(result)
            await self._post_event("suricata", "ids_alert", result)
    
    async def scan_lynis(self):
        """Run Lynis system audit."""
        output_file = os.path.join(self.temp_dir, "lynis.log")
        cmd = ["lynis", "audit", "system", "--quick"]
        
        try:
            result = await self.run_command(cmd, timeout=1800)  # 30 minute timeout
            
            # Parse results
            warnings = []
            suggestions = []
            
            current_section = None
            for line in result["stdout"].splitlines():
                line = line.strip()
                if not line:
                    continue
                    
                # Check for section headers
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1].lower()
                    continue
                
                # Process warnings and suggestions
                if current_section == "warnings" and line.startswith("[+]"):
                    warnings.append(line[3:].strip())
                elif current_section == "suggestions" and line.startswith("* "):
                    suggestions.append(line[2:].strip())
            
            if warnings or suggestions:
                result = {
                    "type": "security_audit",
                    "severity": "high" if warnings else "medium",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "warnings": warnings,
                        "suggestions": suggestions,
                        "scan_output": result["stdout"]
                    }
                }
                self.results.append(result)
                await self._post_event("lynis", "security_audit", result)
                
        except Exception as e:
            self.errors.append(f"Lynis scan error: {str(e)}")
    
    # --- Helper Methods ---
    
    async def _post_event(self, source: str, event_type: str, data: Dict[str, Any]):
        """Post scan event to the API."""
        event = {
            "source": source,
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=event,
                    timeout=30
                )
                if response.status_code >= 400:
                    self.errors.append(f"Failed to post event: {response.text}")
        except Exception as e:
            self.errors.append(f"Error posting event: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan results to a dictionary."""
        return {
            "scan_id": self.scan_id,
            "timestamp": datetime.utcnow().isoformat(),
            "scanners_run": self.config.get("scanners", []),
            "results": self.results,
            "errors": self.errors
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Example configuration
    config = {
        "scanners": ["nmap", "lynis", "clamav", "chkrootkit", "rkhunter", "yara", "suricata"],
        "api_url": "http://localhost:8000/api/events",
        "nmap": {
            "targets": ["127.0.0.1"],
            "ports": "1-1000"
        },
        "clamav": {
            "paths": ["/tmp", "/home", "/var/www"]
        },
        "yara": {
            "paths": ["/bin", "/sbin", "/usr/bin", "/usr/sbin"],
            "rules_dir": "/etc/yara-rules"
        }
    }
    
    async def main():
        scanner = SecurityScanner(config)
        await scanner.scan()
        
        # Print results
        print(f"Scan completed with {len(scanner.errors)} errors")
        print(json.dumps(scanner.to_dict(), indent=2))
    
    asyncio.run(main())
