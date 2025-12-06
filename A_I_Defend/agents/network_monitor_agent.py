#!/usr/bin/env python3
"""
Network Monitoring Agent for A_I_Defend
Continuously monitors network traffic using tshark and reports anomalies to the backend.
"""

import asyncio
import json
import os
import subprocess
import socket
import time
from datetime import datetime
from typing import Dict, List, Optional
import httpx

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
API_KEY = os.getenv("AGENT_API_KEY", "default-agent-key")
AGENT_ID = os.getenv("AGENT_ID", None)
HOSTNAME = socket.gethostname()
INTERFACE = os.getenv("NETWORK_INTERFACE", "any")  # Capture on all interfaces by default
HEARTBEAT_INTERVAL = 30  # seconds
CAPTURE_DURATION = 60  # seconds per capture cycle

# Thresholds for anomaly detection
PACKET_RATE_THRESHOLD = 1000  # packets per second
SUSPICIOUS_PORTS = [23, 135, 139, 445, 3389, 5900]  # Telnet, RPC, NetBIOS, SMB, RDP, VNC
DNS_QUERY_THRESHOLD = 100  # DNS queries per minute

class NetworkMonitorAgent:
    def __init__(self):
        self.agent_id = AGENT_ID
        self.client = httpx.AsyncClient(timeout=30.0)
        self.headers = {"X-API-Key": API_KEY}
        self.running = True
        self.last_heartbeat = 0
        self.packet_count = 0
        self.protocol_stats = {}
        self.ip_connections = {}
        
    async def register(self):
        """Register the agent with the backend."""
        try:
            registration_data = {
                "agent_id": self.agent_id,
                "hostname": HOSTNAME,
                "ip_address": self.get_local_ip(),
                "capabilities": ["network-monitoring", "tshark", "packet-analysis"],
                "metadata": {
                    "interface": INTERFACE,
                    "capture_duration": CAPTURE_DURATION
                }
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/api/agents/register",
                json=registration_data,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            self.agent_id = result["agent_id"]
            print(f"[+] Agent registered successfully: {self.agent_id}")
            return True
        except Exception as e:
            print(f"[-] Failed to register agent: {e}")
            return False
    
    async def send_heartbeat(self):
        """Send heartbeat to the backend."""
        try:
            heartbeat_data = {
                "agent_id": self.agent_id,
                "status": "scanning",
                "current_task": "network-monitoring",
                "metrics": {
                    "packets_captured": self.packet_count,
                    "protocols": self.protocol_stats,
                    "unique_ips": len(self.ip_connections)
                },
                "status_update_only": True
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/api/agents/heartbeat",
                json=heartbeat_data,
                headers=self.headers
            )
            response.raise_for_status()
            self.last_heartbeat = time.time()
            print(f"[*] Heartbeat sent at {datetime.now().isoformat()}")
        except Exception as e:
            print(f"[-] Failed to send heartbeat: {e}")
    
    async def send_event(self, event_type: str, payload: Dict):
        """Send a security event to the backend."""
        try:
            event_data = {
                "source": f"network-monitor-{HOSTNAME}",
                "type": event_type,
                "payload": payload
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/events",
                json=event_data,
                headers=self.headers
            )
            response.raise_for_status()
            print(f"[+] Event sent: {event_type}")
        except Exception as e:
            print(f"[-] Failed to send event: {e}")
    
    def get_local_ip(self) -> str:
        """Get the local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    async def analyze_traffic(self, capture_file: str):
        """Analyze captured traffic for anomalies."""
        try:
            # Parse the capture file with tshark
            cmd = [
                "tshark", "-r", capture_file,
                "-T", "fields",
                "-e", "frame.time_epoch",
                "-e", "ip.src",
                "-e", "ip.dst",
                "-e", "tcp.srcport",
                "-e", "tcp.dstport",
                "-e", "udp.srcport",
                "-e", "udp.dstport",
                "-e", "frame.protocols",
                "-E", "separator=|"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"[-] tshark analysis failed: {result.stderr}")
                return
            
            # Process the output
            protocol_counts = {}
            suspicious_connections = []
            dns_queries = 0
            unique_ips = set()
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                fields = line.split('|')
                if len(fields) < 8:
                    continue
                
                timestamp, src_ip, dst_ip, tcp_src, tcp_dst, udp_src, udp_dst, protocols = fields
                
                # Count unique IPs
                if src_ip:
                    unique_ips.add(src_ip)
                if dst_ip:
                    unique_ips.add(dst_ip)
                
                # Count protocols
                if protocols:
                    for proto in protocols.split(':'):
                        protocol_counts[proto] = protocol_counts.get(proto, 0) + 1
                
                # Check for suspicious ports
                ports = [tcp_src, tcp_dst, udp_src, udp_dst]
                for port in ports:
                    if port and port.isdigit() and int(port) in SUSPICIOUS_PORTS:
                        suspicious_connections.append({
                            "src": src_ip,
                            "dst": dst_ip,
                            "port": int(port),
                            "timestamp": timestamp
                        })
                
                # Count DNS queries
                if 'dns' in protocols.lower():
                    dns_queries += 1
            
            packets_analyzed = len(result.stdout.strip().split('\n'))
            self.packet_count += packets_analyzed
            self.protocol_stats = protocol_counts
            self.ip_connections = {ip: {"count": 1} for ip in unique_ips}
            
            # Always send a summary event to show monitoring activity
            await self.send_event("network-monitor-summary", {
                "details": {
                    "unique_ips": list(unique_ips)[:20],
                    "total_unique_ips": len(unique_ips),
                    "protocols": protocol_counts,
                    "dns_queries": dns_queries,
                    "packets_analyzed": packets_analyzed,
                    "capture_duration": CAPTURE_DURATION,
                    "interface": INTERFACE
                },
                "summary": f"Network monitoring on {HOSTNAME}: {len(unique_ips)} unique IPs, {packets_analyzed} packets analyzed"
            })
            
            # Generate alerts for anomalies
            if suspicious_connections:
                await self.send_event("suspicious-connection", {
                    "details": {
                        "suspicious_connections": suspicious_connections[:10],
                        "total_suspicious": len(suspicious_connections),
                        "unique_ips": list(unique_ips)[:20],
                        "protocols": protocol_counts
                    },
                    "summary": f"Detected {len(suspicious_connections)} suspicious connections on {HOSTNAME}"
                })
            
            if dns_queries > DNS_QUERY_THRESHOLD:
                await self.send_event("high-dns-activity", {
                    "details": {
                        "dns_queries": dns_queries,
                        "threshold": DNS_QUERY_THRESHOLD,
                        "unique_ips": list(unique_ips)[:20]
                    },
                    "summary": f"High DNS query rate detected: {dns_queries} queries"
                })
            
            print(f"[*] Analysis complete: {len(unique_ips)} unique IPs, {len(suspicious_connections)} suspicious connections")
            
        except subprocess.TimeoutExpired:
            print("[-] tshark analysis timed out")
        except Exception as e:
            print(f"[-] Error analyzing traffic: {e}")
    
    async def capture_traffic(self):
        """Capture network traffic using tshark."""
        capture_file = f"/tmp/capture_{int(time.time())}.pcap"
        
        try:
            print(f"[*] Starting capture on interface {INTERFACE} for {CAPTURE_DURATION}s...")
            
            # Capture traffic
            cmd = [
                "tshark",
                "-i", INTERFACE,
                "-a", f"duration:{CAPTURE_DURATION}",
                "-w", capture_file,
                "-q"  # Quiet mode
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0:
                print(f"[+] Capture complete: {capture_file}")
                await self.analyze_traffic(capture_file)
            else:
                print(f"[-] Capture failed with code {process.returncode}")
            
            # Clean up
            try:
                os.remove(capture_file)
            except:
                pass
                
        except Exception as e:
            print(f"[-] Error during capture: {e}")
    
    async def run(self):
        """Main agent loop."""
        # Register with backend
        if not await self.register():
            print("[-] Failed to register, retrying in 10s...")
            await asyncio.sleep(10)
            return await self.run()
        
        # Main monitoring loop
        while self.running:
            try:
                # Send heartbeat if needed
                if time.time() - self.last_heartbeat > HEARTBEAT_INTERVAL:
                    await self.send_heartbeat()
                
                # Capture and analyze traffic
                await self.capture_traffic()
                
                # Brief pause between captures
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                print("\n[*] Shutting down...")
                self.running = False
            except Exception as e:
                print(f"[-] Error in main loop: {e}")
                await asyncio.sleep(10)
        
        await self.client.aclose()

if __name__ == "__main__":
    print(f"[*] Starting Network Monitor Agent on {HOSTNAME}")
    print(f"[*] Backend: {BACKEND_URL}")
    print(f"[*] Interface: {INTERFACE}")
    
    agent = NetworkMonitorAgent()
    asyncio.run(agent.run())
