"""
Specialized Agent Client - Supports network, malware, and security audit agents
"""

import asyncio
import os
import sys
from typing import Dict, Any, List, Optional
from octopus_leg import OctopusLeg

class SpecializedAgent(OctopusLeg):
    """Agent client for specialized scanners."""
    
    def __init__(self, agent_type: str, control_plane_url: str = "http://backend:8000"):
        super().__init__(agent_type, control_plane_url)
        self.capabilities = self._get_capabilities()
        self.scanner = None
        self.heartbeat_interval = 30  # seconds
        
    def _get_capabilities(self) -> List[str]:
        """Get capabilities based on agent type."""
        capabilities_map = {
            'network': ['nmap', 'suricata'],
            'network_intel': ['nmap', 'tshark', 'masscan', 'arp-scan', 'dns-enum', 'ping-sweep'],
            'malware': ['clamav', 'yara'],
            'security_audit': ['lynis', 'chkrootkit', 'rkhunter']
        }
        return capabilities_map.get(self.agent_type, [])
            
    def _get_scan_progress(self) -> Optional[Dict[str, Any]]:
        """Get current scan progress if available."""
        if self.scanner and hasattr(self.scanner, 'progress'):
            return {
                'progress': self.scanner.progress,
                'current_scanner': self.scanner.current_scanner,
                'scan_details': self.scanner.scan_details,
                'results_count': len(self.scanner.results),
                'errors_count': len(self.scanner.errors)
            }
        return None
        
    def _get_metrics(self) -> Dict[str, Any]:
        """Provide custom metrics for heartbeat."""
        return {
            "scan_progress": self._get_scan_progress()
        }

    async def send_status_update(self):
        """Send a quick status update (wrapper around base heartbeat)."""
        await self.send_heartbeat(self._get_metrics())

    async def process_assignment(self, assignment: Dict[str, Any]):
        """Process a scan assignment."""
        await self.log("INFO", f"Processing assignment: {assignment['assignment_id']}")
        
        self.status = "scanning"
        self.current_task = assignment['assignment_id']
        await self.send_status_update()
        
        scanner = None
        
        try:
            # Build configuration from assignment
            targets = assignment.get('targets', [])
            selected_scanners = assignment.get('scanners', [])
            base_config = assignment.get('config', {})
            
            # Create scanner-specific config based on selected scanners
            scan_config = {}
            for scanner_name in selected_scanners:
                if scanner_name in ['nmap', 'masscan']:
                    scan_config[scanner_name] = {
                        'targets': targets,
                        'ports': base_config.get('ports', '1-1000')
                    }
                elif scanner_name == 'ping-sweep':
                    # Use targets as networks for ping sweep
                    scan_config['ping_sweep'] = {
                        'network': targets[0] if targets else '192.168.1.0/24'
                    }
                elif scanner_name == 'arp-scan':
                    scan_config['arp_scan'] = {
                        'interface': base_config.get('interface', 'eth0')
                    }
                elif scanner_name == 'tshark':
                    scan_config['tshark'] = {
                        'interface': base_config.get('interface', 'eth0'),
                        'duration': base_config.get('duration', 30)
                    }
                elif scanner_name == 'dns-enum':
                    scan_config['dns_enum'] = {
                        'domains': targets
                    }
                elif scanner_name == 'clamav':
                    # Use user-provided targets as paths if available, otherwise default to /usr/bin
                    paths = targets if targets else base_config.get('paths', ['/usr/bin'])
                    scan_config['clamav'] = {
                        'paths': paths
                    }
                elif scanner_name == 'yara':
                    # Use user-provided targets as paths if available, otherwise default to /usr/bin
                    paths = targets if targets else base_config.get('paths', ['/usr/bin'])
                    scan_config['yara'] = {
                        'paths': paths,
                        'rules': base_config.get('rules', '/etc/yara/rules')
                    }
                elif scanner_name == 'chkrootkit':
                    paths = targets if targets else base_config.get('paths', ['/'])
                    scan_config['chkrootkit'] = {
                        'paths': paths
                    }
                elif scanner_name == 'rkhunter':
                    paths = targets if targets else base_config.get('paths', ['/'])
                    scan_config['rkhunter'] = {
                        'paths': paths
                    }
                elif scanner_name == 'lynis':
                    scan_config['lynis'] = {}
                else:
                    await self.log("WARN", f"Unknown scanner requested: '{scanner_name}'")
            
            # Import the appropriate scanner class dynamically to avoid circular deps or bloat
            if self.agent_type == 'network':
                from network.network_scanner import NetworkScanner
                scanner = NetworkScanner(scan_config)
            elif self.agent_type == 'network_intel':
                from network_intel.network_intel_scanner import NetworkIntelScanner
                scanner = NetworkIntelScanner(scan_config)
            elif self.agent_type == 'malware':
                from malware.malware_scanner import MalwareScanner
                scanner = MalwareScanner(scan_config)
            elif self.agent_type == 'security_audit':
                from security.security_audit_scanner import SecurityAuditScanner
                scanner = SecurityAuditScanner(scan_config)
            else:
                await self.log("ERROR", f"Unknown agent type for scanning: {self.agent_type}")
                return
            
            # Store scanner reference for progress tracking
            self.scanner = scanner
            
            # Run the scan with periodic progress updates
            scan_task = asyncio.create_task(scanner.scan())
            
            # Send progress updates while scanning
            while not scan_task.done():
                await asyncio.sleep(2)  # Update every 2 seconds
                await self.send_status_update()
            
            # Wait for scan to complete
            await scan_task
            
            # Post results to control plane
            for result in scanner.results:
                event_type = f"{result['scanner']}_scan"
                await self.post_event(result['scanner'], event_type, result)
            
            await self.log("INFO", f"Assignment {assignment['assignment_id']} completed", {
                "results": len(scanner.results),
                "errors": len(scanner.errors)
            })
            
        except Exception as e:
            await self.log("ERROR", f"Assignment failed: {e}", {"assignment_id": assignment['assignment_id']})
        
        finally:
            self.status = "idle"
            self.current_task = None
            self.scanner = None
            await self.send_status_update()


async def main():
    """Main agent loop."""
    # Get agent type from environment or command line
    agent_type = os.getenv("AGENT_TYPE", sys.argv[1] if len(sys.argv) > 1 else "network")
    control_plane_url = os.getenv("API_URL", "http://backend:8000").replace("/events", "")
    
    print(f"🐙 AI Defend {agent_type.upper()} Leg Starting (Octopus v2)...")
    
    # Create specialized agent
    agent = SpecializedAgent(agent_type, control_plane_url)
    
    try:
        # Start heartbeat loop
        await agent.run_heartbeat_loop(interval=30)
    except KeyboardInterrupt:
        print("\n⚠️  Shutting down agent...")

if __name__ == "__main__":
    asyncio.run(main())
