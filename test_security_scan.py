import asyncio
import json
from pathlib import Path

# Add the project root to the path so we can import our modules
import sys
from pathlib import Path

project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from scanners.linux.security_scanner import SecurityScanner

async def test_security_scan():
    """Test the security scanner with a basic configuration."""
    # Configuration for the scan
    config = {
        "scanners": ["nmap", "clamav", "chkrootkit", "rkhunter", "yara", "suricata", "lynis"],
        "nmap": {
            "targets": ["127.0.0.1"],
            "ports": "1-1000",
            "arguments": "-T4 -A -v"
        },
        "clamav": {
            "paths": ["/tmp", "/home"]
        },
        "yara": {
            "paths": ["/tmp"]
        },
        "suricata": {
            "log_paths": ["/var/log/suricata/fast.log"]
        }
    }
    
    print("Starting security scan...")
    scanner = SecurityScanner(config)
    
    try:
        # Run the scan
        success = await scanner.scan()
        
        # Save results
        output_file = "test_scan_results.json"
        with open(output_file, 'w') as f:
            json.dump(scanner.to_dict(), f, indent=2)
        
        print(f"\nScan {'completed successfully' if success else 'failed'}")
        print(f"Results saved to: {output_file}")
        
        # Print a summary of findings
        print("\n=== Scan Summary ===")
        for result in scanner.results:
            print(f"\n{result['scanner'].upper()} Results:")
            if 'findings' in result:
                print(f"  - Found {len(result['findings'])} issues")
                for finding in result['findings'][:5]:  # Show first 5 findings
                    print(f"    - {finding.get('title', 'Finding')}: {finding.get('description', 'No description')}")
                    if 'severity' in finding:
                        print(f"      Severity: {finding['severity']}")
            elif 'error' in result:
                print(f"  Error: {result['error']}")
            else:
                print("  No findings")
        
        # Print any errors
        if scanner.errors:
            print("\n=== Errors ===")
            for error in scanner.errors:
                print(f"- {error}")
                
    except Exception as e:
        print(f"Error during scan: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Create test_scan directory if it doesn't exist
    import os
    os.makedirs("test_scan", exist_ok=True)
    
    # Run the test scan
    asyncio.run(test_security_scan())
