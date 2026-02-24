
import asyncio
import os
import sys
import uuid
import socket
from datetime import datetime

# Add the current directory to path so it can find octopus_leg
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from octopus_leg import OctopusLeg

class IntegrationTestLeg(OctopusLeg):
    """A mock leg for integration testing."""
    def __init__(self, control_plane_url):
        super().__init__("integration-test", control_plane_url)
        self.capabilities = ["test-capability"]

    async def process_assignment(self, assignment):
        pass

async def run_test():
    print("🧪 Starting Automated Octopus Integration Test...")
    
    # Configuration
    # When running from host, we use localhost. Containers would use 'backend'.
    brain_url = os.getenv("BRAIN_URL", "http://localhost:8000")
    print(f"📡 Using Brain URL: {brain_url}")

    # 1. Initialize Leg
    it_leg = IntegrationTestLeg(brain_url)
    
    # 2. Test Registration
    print("\n[STEP 1] Testing Agent Registration...")
    success = await it_leg.register(metadata={"test_run": str(uuid.uuid4())})
    if not success:
        print("❌ FAILED: Registration failed.")
        sys.exit(1)
    print(f"✅ SUCCESS: Registered as {it_leg.agent_id}")

    # 3. Test Centralized Logging
    print("\n[STEP 2] Testing Centralized Logging...")
    test_msg = f"Automated Integration Test Log - {datetime.utcnow().isoformat()}"
    test_context = {"test_id": "auto-verify-123", "status": "verifying"}
    
    # We'll use a unique tag to find it in the DB later
    unique_tag = f"tag_{uuid.uuid4().hex[:8]}"
    test_msg = f"{test_msg} | {unique_tag}"
    
    await it_leg.log("INFO", test_msg, test_context)
    print(f"📤 Log sent: '{test_msg}'")

    # 4. Verify in Database (via docker exec psql)
    print("\n[STEP 3] Verifying Log Storage in Database...")
    await asyncio.sleep(2) # Give it a second to settle
    
    import subprocess
    verify_cmd = [
        "docker", "exec", "-i", "db", "psql", "-U", "postgres", "-d", "defense", "-t", "-c", 
        f"SELECT count(*) FROM agent_logs WHERE message LIKE '%{unique_tag}%';"
    ]
    
    try:
        result = subprocess.run(verify_cmd, capture_output=True, text=True, check=True)
        count = int(result.stdout.strip())
        if count > 0:
            print(f"✅ SUCCESS: Found {count} log entry in database with tag {unique_tag}")
        else:
            print(f"❌ FAILED: No log entry found with tag {unique_tag}")
            sys.exit(1)
    except Exception as e:
        print(f"⚠️  Error verifying database: {e}")
        sys.exit(1)

    print("\n🏆 INTEGRATION TEST PASSED SUCCESSFULLY! 🐙🏁")

if __name__ == "__main__":
    asyncio.run(run_test())
