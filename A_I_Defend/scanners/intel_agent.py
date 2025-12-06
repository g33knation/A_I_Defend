from base_agent import BaseAgent
import time
import logging

logger = logging.getLogger("IntelAgent")

class IntelAgent(BaseAgent):
    def __init__(self):
        super().__init__("network-intel", ["nmap", "masscan", "recon"])

    def handle_assignment(self, assignment: dict):
        logger.info(f"Starting network reconnaissance for assignment: {assignment.get('assignment_id')}")
        self.send_heartbeat(status="scanning", current_task=assignment.get("assignment_id"))
        
        # Simulate scan
        time.sleep(5)
        
        logger.info("Network reconnaissance completed")
        self.send_heartbeat(status="idle", current_task=None)

if __name__ == "__main__":
    agent = IntelAgent()
    agent.run()
