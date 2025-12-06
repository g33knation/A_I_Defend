import os
import time
import json
import socket
import requests
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BaseAgent")

class BaseAgent:
    def __init__(self, agent_type: str, capabilities: List[str]):
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.agent_id = None
        self.hostname = socket.gethostname()
        self.ip_address = self._get_ip_address()
        
        # Configuration
        self.backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
        self.api_key = os.getenv("AGENT_API_KEY", "default-agent-key")
        self.headers = {"X-API-Key": self.api_key}
        
        logger.info(f"Initializing {self.agent_type} agent on {self.hostname} ({self.ip_address})")

    def _get_ip_address(self):
        try:
            # Connect to backend to determine our IP relative to it
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't actually connect, just determines route
            s.connect(("backend", 8000))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def register(self):
        """Register the agent with the backend."""
        url = f"{self.backend_url}/api/agents/register"
        payload = {
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "capabilities": self.capabilities,
            "metadata": {
                "type": self.agent_type,
                "version": "1.0.0"
            }
        }
        
        while True:
            try:
                logger.info(f"Attempting to register with {url}...")
                response = requests.post(url, json=payload, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.agent_id = data.get("agent_id")
                    logger.info(f"Successfully registered with ID: {self.agent_id}")
                    return True
                else:
                    logger.error(f"Registration failed: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Connection error during registration: {e}")
            
            time.sleep(10)

    def send_heartbeat(self, status: str = "idle", current_task: str = None, metrics: Dict[str, Any] = None):
        """Send heartbeat to backend."""
        if not self.agent_id:
            return
            
        url = f"{self.backend_url}/api/agents/heartbeat"
        payload = {
            "agent_id": self.agent_id,
            "status": status,
            "current_task": current_task,
            "metrics": metrics or {}
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Check for assignments
                assignment = data.get("assignment")
                if assignment:
                    self.handle_assignment(assignment)
            else:
                logger.warning(f"Heartbeat failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")

    def handle_assignment(self, assignment: Dict[str, Any]):
        """Handle a scan assignment. Override in subclasses."""
        logger.info(f"Received assignment: {assignment}")
        # Default implementation just logs it

    def run(self):
        """Main agent loop."""
        if not self.register():
            return

        logger.info("Starting main loop...")
        while True:
            try:
                self.send_heartbeat()
                time.sleep(10)
            except KeyboardInterrupt:
                logger.info("Stopping agent...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)
