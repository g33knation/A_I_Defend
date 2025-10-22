"""
Network Intelligence Scanner - Passive network monitoring and scanning
No credentials or permissions needed on target systems
Combines: Nmap, Tshark, Masscan, ARP scanning, DNS enumeration
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


class NetworkIntelScanner:
    """Network intelligence gathering without target permissions."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.results = []
        self.errors = []
        self.temp_dir = tempfile.mkdtemp(prefix="netintel_scan_")
        self.progress = 0
        self.total_scanners = 0
        self.current_scanner = None
        self.scan_details = {}
        
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
        """Active port scanning with Nmap."""
        for target in targets:
            output_file = os.path.join(self.temp_dir, f"nmap_{target.replace('.', '_').replace('/', '_')}.xml")
            cmd = ["nmap", "-p", ports, "-sV", "-T4", "-oX", output_file, target]
            
            try:
                result = await self.run_command(cmd, timeout=600)
                if result["returncode"] != 0:
                    self.errors.append(f"Nmap scan failed for {target}: {result['stderr']}")
                    continue
                
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
                            service_version = service.get('version') if service is not None else ''
                            
                            if state == 'open':
                                ports_found.append({
                                    'port': int(port_id),
                                    'protocol': protocol,
                                    'service': service_name,
                                    'version': service_version,
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
    
    async def scan_arp(self, interface: str = "eth0"):
        """ARP scan to discover live hosts on local network."""
        cmd = ["arp-scan", "--interface", interface, "--localnet"]
        
        try:
            result = await self.run_command(cmd, timeout=60)
            
            hosts = []
            for line in result["stdout"].split('\n'):
                parts = line.split('\t')
                if len(parts) >= 3 and '.' in parts[0]:
                    hosts.append({
                        'ip': parts[0].strip(),
                        'mac': parts[1].strip(),
                        'vendor': parts[2].strip() if len(parts) > 2 else 'Unknown'
                    })
            
            if hosts:
                self.results.append({
                    'scanner': 'arp-scan',
                    'details': {
                        'hosts': hosts,
                        'total_hosts': len(hosts),
                        'interface': interface
                    }
                })
                
        except Exception as e:
            self.errors.append(f"ARP scan error: {str(e)}")
    
    async def scan_tshark(self, interface: str = "eth0", duration: int = 30):
        """Passive network traffic capture and analysis."""
        output_file = os.path.join(self.temp_dir, "capture.pcap")
        
        # Capture packets
        cmd = ["tshark", "-i", interface, "-a", f"duration:{duration}", "-w", output_file]
        
        try:
            await self.run_command(cmd, timeout=duration + 10)
            
            # Analyze captured packets
            analyze_cmd = ["tshark", "-r", output_file, "-T", "json"]
            result = await self.run_command(analyze_cmd, timeout=60)
            
            if result["returncode"] == 0:
                try:
                    packets = json.loads(result["stdout"])
                    
                    # Extract unique IPs and protocols
                    unique_ips = set()
                    protocols = {}
                    
                    for packet in packets[:1000]:  # Limit to first 1000 packets
                        layers = packet.get('_source', {}).get('layers', {})
                        
                        # Extract IPs
                        if 'ip' in layers:
                            src_ip = layers['ip'].get('ip.src')
                            dst_ip = layers['ip'].get('ip.dst')
                            if src_ip:
                                unique_ips.add(src_ip)
                            if dst_ip:
                                unique_ips.add(dst_ip)
                        
                        # Count protocols
                        for proto in ['tcp', 'udp', 'icmp', 'dns', 'http', 'https']:
                            if proto in layers:
                                protocols[proto] = protocols.get(proto, 0) + 1
                    
                    self.results.append({
                        'scanner': 'tshark',
                        'details': {
                            'unique_ips': list(unique_ips),
                            'total_unique_ips': len(unique_ips),
                            'protocols': protocols,
                            'total_packets': len(packets),
                            'capture_duration': duration
                        }
                    })
                    
                except json.JSONDecodeError:
                    self.errors.append("Failed to parse tshark output")
                    
        except Exception as e:
            self.errors.append(f"Tshark capture error: {str(e)}")
    
    async def scan_masscan(self, targets: List[str], ports: str = "1-1000"):
        """Ultra-fast port scanning with Masscan."""
        for target in targets:
            output_file = os.path.join(self.temp_dir, f"masscan_{target.replace('.', '_').replace('/', '_')}.json")
            cmd = ["masscan", target, "-p", ports, "--rate", "1000", "-oJ", output_file]
            
            try:
                result = await self.run_command(cmd, timeout=300)
                
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        content = f.read()
                        # Masscan outputs multiple JSON objects, parse them
                        ports_found = []
                        for line in content.split('\n'):
                            if line.strip() and not line.startswith('#'):
                                try:
                                    data = json.loads(line.rstrip(','))
                                    if 'ports' in data:
                                        for port_info in data['ports']:
                                            ports_found.append({
                                                'ip': data.get('ip'),
                                                'port': port_info.get('port'),
                                                'protocol': port_info.get('proto'),
                                                'status': port_info.get('status')
                                            })
                                except json.JSONDecodeError:
                                    continue
                        
                        if ports_found:
                            self.results.append({
                                'scanner': 'masscan',
                                'target': target,
                                'details': {
                                    'ports': ports_found,
                                    'total_open_ports': len(ports_found)
                                }
                            })
                            
            except Exception as e:
                self.errors.append(f"Masscan error for {target}: {str(e)}")
    
    async def scan_dns_enum(self, domain: str):
        """DNS enumeration to discover subdomains and records."""
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA']
        dns_records = {}
        
        for record_type in record_types:
            cmd = ["dig", "+short", domain, record_type]
            
            try:
                result = await self.run_command(cmd, timeout=10)
                if result["returncode"] == 0 and result["stdout"].strip():
                    dns_records[record_type] = result["stdout"].strip().split('\n')
            except Exception:
                continue
        
        if dns_records:
            self.results.append({
                'scanner': 'dns-enum',
                'domain': domain,
                'details': {
                    'records': dns_records,
                    'total_record_types': len(dns_records)
                }
            })
    
    async def scan_ping_sweep(self, network: str):
        """Fast ping sweep to discover live hosts."""
        cmd = ["nmap", "-sn", "-T4", network]
        
        try:
            result = await self.run_command(cmd, timeout=120)
            
            live_hosts = []
            for line in result["stdout"].split('\n'):
                if 'Nmap scan report for' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        ip = parts[-1].strip('()')
                        live_hosts.append(ip)
            
            if live_hosts:
                self.results.append({
                    'scanner': 'ping-sweep',
                    'network': network,
                    'details': {
                        'live_hosts': live_hosts,
                        'total_live_hosts': len(live_hosts)
                    }
                })
                
        except Exception as e:
            self.errors.append(f"Ping sweep error: {str(e)}")
    
    async def scan(self):
        """Run all network intelligence scans."""
        # Count total scanners to run
        scanners_to_run = []
        if 'ping_sweep' in self.config or not self.config:
            scanners_to_run.append('ping-sweep')
        if 'arp_scan' in self.config or not self.config:
            scanners_to_run.append('arp-scan')
        if 'nmap' in self.config:
            scanners_to_run.append('nmap')
        if 'masscan' in self.config:
            scanners_to_run.append('masscan')
        if 'tshark' in self.config:
            scanners_to_run.append('tshark')
        if 'dns_enum' in self.config:
            scanners_to_run.append('dns-enum')
        
        self.total_scanners = len(scanners_to_run)
        completed = 0
        
        # Ping sweep to discover hosts
        if 'ping_sweep' in self.config or not self.config:
            self.current_scanner = 'ping-sweep'
            network = self.config.get('ping_sweep', {}).get('network', '192.168.1.0/24')
            self.scan_details = {'scanner': 'ping-sweep', 'target': network}
            await self.scan_ping_sweep(network)
            completed += 1
            self.progress = int((completed / self.total_scanners) * 100)
        
        # ARP scan for local network
        if 'arp_scan' in self.config or not self.config:
            self.current_scanner = 'arp-scan'
            interface = self.config.get('arp_scan', {}).get('interface', 'eth0')
            self.scan_details = {'scanner': 'arp-scan', 'interface': interface}
            await self.scan_arp(interface)
            completed += 1
            self.progress = int((completed / self.total_scanners) * 100)
        
        # Nmap port scan
        if 'nmap' in self.config:
            self.current_scanner = 'nmap'
            targets = self.config['nmap'].get('targets', ['127.0.0.1'])
            ports = self.config['nmap'].get('ports', '1-1000')
            self.scan_details = {'scanner': 'nmap', 'targets': targets, 'ports': ports}
            await self.scan_nmap(targets, ports)
            completed += 1
            self.progress = int((completed / self.total_scanners) * 100)
        
        # Masscan for fast scanning
        if 'masscan' in self.config:
            self.current_scanner = 'masscan'
            targets = self.config['masscan'].get('targets', [])
            ports = self.config['masscan'].get('ports', '1-1000')
            if targets:
                self.scan_details = {'scanner': 'masscan', 'targets': targets, 'ports': ports}
                await self.scan_masscan(targets, ports)
            completed += 1
            self.progress = int((completed / self.total_scanners) * 100)
        
        # Tshark passive monitoring
        if 'tshark' in self.config:
            self.current_scanner = 'tshark'
            interface = self.config['tshark'].get('interface', 'eth0')
            duration = self.config['tshark'].get('duration', 30)
            self.scan_details = {'scanner': 'tshark', 'interface': interface, 'duration': duration}
            await self.scan_tshark(interface, duration)
            completed += 1
            self.progress = int((completed / self.total_scanners) * 100)
        
        # DNS enumeration
        if 'dns_enum' in self.config:
            self.current_scanner = 'dns-enum'
            domains = self.config['dns_enum'].get('domains', [])
            for domain in domains:
                self.scan_details = {'scanner': 'dns-enum', 'domain': domain}
                await self.scan_dns_enum(domain)
            completed += 1
            self.progress = int((completed / self.total_scanners) * 100)
        
        self.current_scanner = None
        self.progress = 100
        
        # Cleanup
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan results to dictionary."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_type": "network_intel",
            "results": self.results,
            "errors": self.errors
        }


async def main():
    """Test the network intelligence scanner."""
    config = {
        "ping_sweep": {"network": "192.168.1.0/24"},
        "nmap": {
            "targets": ["192.168.1.1"],
            "ports": "1-100"
        }
    }
    
    scanner = NetworkIntelScanner(config)
    await scanner.scan()
    print(json.dumps(scanner.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
