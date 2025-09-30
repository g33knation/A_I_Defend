import asyncio
import os
import sys
from scanners.scanner_manager import ScannerManager
from pathlib import Path

async def main():
    # Create a test configuration
    config = {
        "scanners": ["nmap", "file_integrity"],
        "nmap": {
            "targets": ["127.0.0.1"],
            "ports": "1-100"  # Just scan common ports for testing
        },
        "file_integrity": {
            "paths": [
                str(Path("test_scan/test_files").absolute())
            ],
            "baseline_file": str(Path("test_scan/baseline.json").absolute())
        }
    }
    
    print("Starting test scan...")
    print(f"Working directory: {os.getcwd()}")
    
    # Create the scanner manager
    manager = ScannerManager(config)
    
    # Run the scan
    success = await manager.run_scan()
    
    # Print results
    print(f"\nScan {'completed successfully' if success else 'failed'}")
    print(f"Results saved to: {manager.save_results('test_scan/results.json')}")
    
    # Print any errors
    if manager.errors:
        print("\nErrors:")
        for error in manager.errors:
            print(f"- {error}")

if __name__ == "__main__":
    # Create test_scan directory if it doesn't exist
    os.makedirs("test_scan", exist_ok=True)
    
    # Run the test
    asyncio.run(main())
