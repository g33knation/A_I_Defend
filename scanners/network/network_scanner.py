"""
Network Scanner Agent - Specialized for network security scanning
Includes: Nmap (port scanning) and Suricata (IDS/IPS)
"""

import asyncio
import subprocess
import json
import os
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, List
import xml.etree.ElementTree as ET


class NetworkScanner:
    """Network-focused security scanner."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.results = []
        self.errors = []
        self.temp_dir = tempfile.mkdtemp(prefix="network_scan_")
        
    async def run_command(self, cmd: List[str], timeout: int = 300) -> Dict[str, Any]:
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
    
    async def scan_nmap(self, targets: List[str], ports: str = "1-1000"):
        """Run Nmap network scan."""
        for target in targets:
            output_file = os.path.join(self.temp_dir, f"nmap_{target.replace('.', '_').replace('/', '_')}.xml")
            cmd = ["nmap", "-p", ports, "-sV", "-T4", "-oX", output_file, target]
            
            try:
                result = await self.run_command(cmd, timeout=600)
                if result["returncode"] != 0:
                    self.errors.append(f"Nmap scan failed for {target}: {result['stderr']}")
                    continue
                
                # Parse XML output
                if os.path.exists(output_file):
                    tree = ET.parse(output_file)
                    root = tree.getroot()
                    
                    for host in root.findall('host'):
                        address = host.find('address').get('addr')
                        ports_found = []
                        
                        for port in host.findall('.//port'):
                            port_id = port.get('portid')
                            protocol = port.get('protocol')
                            state = port.find('state').get('state')
                            
                            service = port.find('service')
                            service_name = service.get('name') if service is not None else 'unknown'
                            
                            if state == 'open':
                                ports_found.append({
                                    'port': int(port_id),
                                    'protocol': protocol,
                                    'service': service_name,
                                    'state': state
                                })
                        
                        self.results.append({
                            'scanner': 'nmap',
                            'target': target,
                            'details': {
                                'address': address,
                                'ports': ports_found,
                                'total_open_ports': len(ports_found)
                            }
                        })
                        
            except Exception as e:
                self.errors.append(f"Nmap scan error for {target}: {str(e)}")
    
    async def scan_suricata(self, log_paths: List[str] = None):
        """Check Suricata IDS/IPS logs for alerts."""
        log_paths = log_paths or ["/var/log/suricata/fast.log", "/var/log/suricata/eve.json"]
        alerts = []
        
        for log_path in log_paths:
            if not os.path.exists(log_path):
                continue
            
            try:
                if log_path.endswith('.json'):
                    # Parse JSON logs
                    with open(log_path, 'r') as f:
                        for line in f:
                            try:
                                event = json.loads(line)
                                if event.get('event_type') == 'alert':
                                    alerts.append({
                                        'timestamp': event.get('timestamp'),
                                        'signature': event.get('alert', {}).get('signature'),
                                        'severity': event.get('alert', {}).get('severity'),
                                        'category': event.get('alert', {}).get('category'),
                                        'src_ip': event.get('src_ip'),
                                        'dest_ip': event.get('dest_ip')
                                    })
                            except json.JSONDecodeError:
                                continue
                else:
                    # Parse fast.log format
                    with open(log_path, 'r') as f:
                        for line in f:
                            if '[**]' in line:
                                alerts.append({
                                    'raw': line.strip(),
                                    'signature': line.split('[**]')[1].strip() if len(line.split('[**]')) > 1 else 'Unknown'
                                })
                
                if alerts:
                    self.results.append({
                        'scanner': 'suricata',
                        'details': {
                            'log_file': log_path,
                            'alerts': alerts,
                            'total_alerts': len(alerts)
                        }
                    })
                    
            except Exception as e:
                self.errors.append(f"Suricata log parsing error for {log_path}: {str(e)}")
    
    async def scan(self):
        """Run all network scans."""
        # Run Nmap if configured
        if 'nmap' in self.config:
            targets = self.config['nmap'].get('targets', ['127.0.0.1'])
            ports = self.config['nmap'].get('ports', '1-1000')
            await self.scan_nmap(targets, ports)
        
        # Check Suricata logs if configured
        if 'suricata' in self.config:
            log_paths = self.config['suricata'].get('log_paths')
            await self.scan_suricata(log_paths)
        
        # Cleanup
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan results to dictionary."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_type": "network",
            "results": self.results,
            "errors": self.errors
        }


async def main():
    """Test the network scanner."""
    config = {
        "nmap": {
            "targets": ["127.0.0.1"],
            "ports": "1-1000"
        }
    }
    
    scanner = NetworkScanner(config)
    await scanner.scan()
    print(json.dumps(scanner.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
