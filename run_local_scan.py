import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from scanners.scanner_manager import ScannerManager

async def main():
    # Configuration for local scanning
    config = {
        "scanners": ["nmap", "file_integrity"],
        "nmap": {
            "targets": ["localhost"],
            "ports": "1-1000",
            "arguments": "-T4 -A -v"
        },
        "file_integrity": {
            "paths": [
                str(Path("test_scan/test_files").absolute())
            ],
            "baseline_file": str(Path("test_scan/baseline.json").absolute())
        }
    }
    
    print("Starting local scan...")
    print(f"Working directory: {os.getcwd()}")
    
    # Create the scanner manager
    manager = ScannerManager(config)
    
    try:
        # Run the scan
        success = await manager.run_scan()
        
        # Save results
        output_file = "test_scan/scan_results.json"
        manager.save_results(output_file)
        
        print(f"\nScan {'completed successfully' if success else 'failed'}")
        print(f"Results saved to: {output_file}")
        
        # Print any errors
        if manager.errors:
            print("\nErrors:")
            for error in manager.errors:
                print(f"- {error}")
                
    except Exception as e:
        print(f"Error during scan: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Create test_scan directory if it doesn't exist
    os.makedirs("test_scan", exist_ok=True)
    
    # Run the scan
    asyncio.run(main())
