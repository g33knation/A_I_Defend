from base_agent import BaseAgent
import time
import logging

logger = logging.getLogger("SecurityAgent")

class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__("security-scanner", ["lynis", "rkhunter", "audit"])

    def handle_assignment(self, assignment: dict):
        logger.info(f"Starting security audit for assignment: {assignment.get('assignment_id')}")
        self.send_heartbeat(status="scanning", current_task=assignment.get("assignment_id"))
        
        # Simulate scan
        time.sleep(5)
        
        logger.info("Security audit completed")
        self.send_heartbeat(status="idle", current_task=None)

if __name__ == "__main__":
    agent = SecurityAgent()
    agent.run()
