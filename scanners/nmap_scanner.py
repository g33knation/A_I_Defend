import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)

class NmapScanner(BaseScanner):
    """Nmap network scanner for port scanning and service discovery."""
    
    DEFAULT_PORTS = "1-1024"  # Default ports to scan
    DEFAULT_ARGS = ["-sV", "-sS", "-T4"]  # Default Nmap arguments
    
    def __init__(self, targets: List[str], config: Dict[str, Any] = None):
        """Initialize the Nmap scanner.
        
        Args:
            targets: List of target IPs or hostnames to scan
            config: Configuration dictionary with optional keys:
                   - ports: Ports to scan (default: 1-1024)
                   - args: Additional Nmap arguments
                   - sudo: Whether to run with sudo (default: True)
        """
        super().__init__(config)
        self.targets = targets
        self.ports = self.config.get("ports", self.DEFAULT_PORTS)
        self.additional_args = self.config.get("args", [])
        self.use_sudo = self.config.get("sudo", True)
        self.xml_output = None
        
    async def scan(self) -> bool:
        """Run the Nmap scan."""
        try:
            # Create a temporary file for XML output
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
                xml_file = tmp.name
            
            # Build the Nmap command
            cmd = ["nmap", "-oX", xml_file]
            
            # Add ports if specified
            if self.ports:
                cmd.extend(["-p", str(self.ports)])
                
            # Add additional arguments
            cmd.extend(self.DEFAULT_ARGS)
            cmd.extend(self.additional_args)
            
            # Add targets
            cmd.extend(self.targets)
            
            # Run the command
            result = await self.run_command(cmd)
            
            if result["returncode"] != 0:
                error_msg = f"Nmap scan failed: {result['stderr']}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                return False
                
            # Parse the XML output
            self.xml_output = self._parse_nmap_xml(xml_file)
            self.results = self._process_results(self.xml_output)
            
            # Clean up
            Path(xml_file).unlink(missing_ok=True)
            
            return True
            
        except Exception as e:
            error_msg = f"Error during Nmap scan: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            return False
    
    def _parse_nmap_xml(self, xml_file: str) -> Dict[str, Any]:
        """Parse Nmap XML output into a Python dictionary."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Convert XML to dictionary
            result = {
                "scanner": "nmap",
                "args": root.get("args"),
                "start": root.get("start"),
                "hosts": []
            }
            
            for host in root.findall("host"):
                host_data = {
                    "status": host.find("status").get("state") if host.find("status") is not None else "unknown",
                    "addresses": [],
                    "hostnames": [],
                    "ports": []
                }
                
                # Get addresses
                for addr in host.findall("address"):
                    host_data["addresses"].append({
                        "type": addr.get("addrtype"),
                        "address": addr.get("addr")
                    })
                
                # Get hostnames
                for hostname in host.findall("hostnames/hostname"):
                    host_data["hostnames"].append({
                        "name": hostname.get("name"),
                        "type": hostname.get("type")
                    })
                
                # Get ports
                for port in host.findall("ports/port"):
                    port_data = {
                        "port": int(port.get("portid")),
                        "protocol": port.get("protocol"),
                        "state": port.find("state").get("state") if port.find("state") is not None else "unknown",
                        "service": {}
                    }
                    
                    service = port.find("service")
                    if service is not None:
                        port_data["service"] = {
                            "name": service.get("name"),
                            "product": service.get("product", ""),
                            "version": service.get("version", ""),
                            "extrainfo": service.get("extrainfo", "")
                        }
                    
                    host_data["ports"].append(port_data)
                
                result["hosts"].append(host_data)
            
            return result
            
        except Exception as e:
            error_msg = f"Error parsing Nmap XML: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            return {}
    
    def _process_results(self, nmap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Nmap results into a standardized format."""
        results = []
        
        for host in nmap_data.get("hosts", []):
            for port in host.get("ports", []):
                if port["state"] != "open":
                    continue
                    
                result = {
                    "type": "port_scan",
                    "severity": self._determine_severity(port),
                    "target": host["addresses"][0]["address"] if host["addresses"] else "unknown",
                    "port": port["port"],
                    "protocol": port["protocol"],
                    "service": port["service"].get("name", "unknown"),
                    "product": port["service"].get("product", ""),
                    "version": port["service"].get("version", ""),
                    "timestamp": self.scan_id,
                    "details": {
                        "nmap_data": port
                    }
                }
                
                results.append(result)
        
        return results
    
    def _determine_severity(self, port_data: Dict[str, Any]) -> str:
        """Determine the severity of a found port/service."""
        port = port_data.get("port", 0)
        service = port_data.get("service", {}).get("name", "").lower()
        
        # Common vulnerable services
        critical_services = {"http", "https", "ssh", "rdp", "vnc", "smtp", "imap", "pop3", "ftp"}
        
        # Common vulnerable ports
        critical_ports = {
            21,  # FTP
            22,  # SSH
            23,  # Telnet
            25,  # SMTP
            53,  # DNS
            80,  # HTTP
            110, # POP3
            135, # MS RPC
            139, # NetBIOS
            143, # IMAP
            389, # LDAP
            443, # HTTPS
            445, # SMB
            1433, # MS SQL
            1521, # Oracle
            2049, # NFS
            3306, # MySQL
            3389, # RDP
            5432, # PostgreSQL
            5900, # VNC
            8080  # HTTP Proxy
        }
        
        if port in {80, 443} and "http" in service:
            return "medium"  # Common web services are typically expected
            
        if port in critical_ports or any(svc in service for svc in critical_services):
            return "high"
            
        if 1 <= port <= 1024:  # Well-known ports
            return "medium"
            
        return "low"
