import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from scanners.malware.malware_scanner import MalwareScanner
from scanners.security.security_audit_scanner import SecurityAuditScanner
from scanners.network.network_scanner import NetworkScanner
from scanners.network_intel.network_intel_scanner import NetworkIntelScanner

async def test_malware_scanner():
    print("\nXXX Testing MalwareScanner XXX")
    config = {
        "clamav": {"paths": ["."]},
        # "yara": {"paths": ["."]} # disable yara if no rules
    }
    scanner = MalwareScanner(config)
    print("Running scan...")
    await scanner.scan()
    print("Results:", json.dumps(scanner.to_dict(), indent=2))

async def test_security_scanner():
    print("\nXXX Testing SecurityAuditScanner XXX")
    config = {
        # Minimal config
        "lynis": {},
        "chkrootkit": {"paths": ["."]}, # Scan current dir as root?
        # "rkhunter": {"paths": ["."]}
    }
    scanner = SecurityAuditScanner(config)
    print("Running scan...")
    await scanner.scan()
    print("Results:", json.dumps(scanner.to_dict(), indent=2))

async def test_network_scanner():
    print("\nXXX Testing NetworkScanner XXX")
    config = {
        "nmap": {"targets": ["127.0.0.1"], "ports": "80"},
        # "suricata": {"log_paths": []}
    }
    scanner = NetworkScanner(config)
    print("Running scan...")
    await scanner.scan()
    print("Results:", json.dumps(scanner.to_dict(), indent=2))

async def test_network_intel_scanner():
    print("\nXXX Testing NetworkIntelScanner XXX")
    config = {
        "ping_sweep": {"network": "127.0.0.1"},
        "nmap": {"targets": ["127.0.0.1"], "ports": "80"},
        "dns_enum": {"domains": ["localhost"]}
    }
    scanner = NetworkIntelScanner(config)
    print("Running scan...")
    await scanner.scan()
    print("Results:", json.dumps(scanner.to_dict(), indent=2))

async def main():
    print("Starting agents test...")
    
    try:
        await test_network_scanner()
    except Exception as e:
        print(f"NetworkScanner failed: {e}")

    try:
        await test_malware_scanner()
    except Exception as e:
        print(f"MalwareScanner failed: {e}")

    try:
        await test_security_scanner()
    except Exception as e:
        print(f"SecurityAuditScanner failed: {e}")

    try:
        await test_network_intel_scanner()
    except Exception as e:
        print(f"NetworkIntelScanner failed: {e}")

    print("\nTest complete.")

if __name__ == "__main__":
    asyncio.run(main())
