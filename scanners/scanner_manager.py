import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Type, TypeVar, Union

from .base_scanner import BaseScanner
from .nmap_scanner import NmapScanner
from .lynis_scanner import LynisScanner
from .file_integrity_monitor import FileIntegrityMonitor
from .linux.security_scanner import SecurityScanner

logger = logging.getLogger(__name__)

# Create a type variable for the scanner classes
ScannerType = TypeVar('ScannerType', bound=BaseScanner)

class ScannerManager:
    """Manages multiple security scanners and coordinates their execution."""
    
    # Map of scanner types to their classes
    SCANNER_CLASSES = {
        "nmap": NmapScanner,
        "lynis": LynisScanner,
        "file_integrity": FileIntegrityMonitor,
        "security": SecurityScanner  # Add the comprehensive security scanner
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the scanner manager.
        
        Args:
            config: Configuration dictionary with scanner-specific settings.
                   Example:
                   {
                       "scanners": ["nmap", "lynis", "file_integrity"],
                       "nmap": {
                           "targets": ["localhost", "192.168.1.0/24"],
                           "ports": "1-1024"
                       },
                       "lynis": {
                           "categories": ["authentication", "networking"]
                       },
                       "file_integrity": {
                           "paths": ["/etc", "/usr/local/bin"],
                           "baseline_file": "/var/lib/defend/fim_baseline.json"
                       }
                   }
        """
        self.config = config or {}
        self.scanners: Dict[str, BaseScanner] = {}
        self.scan_id = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        
        # Initialize scanners based on config
        self._initialize_scanners()
    
    def _initialize_scanners(self) -> None:
        """Initialize scanners based on the configuration."""
        scanners_to_enable = self.config.get("scanners", list(self.SCANNER_CLASSES.keys()))
        
        for scanner_name in scanners_to_enable:
            if scanner_name not in self.SCANNER_CLASSES:
                logger.warning(f"Unknown scanner: {scanner_name}")
                continue
                
            scanner_config = self.config.get(scanner_name, {})
            
            try:
                if scanner_name == "nmap":
                    targets = scanner_config.get("targets", ["localhost"])
                    self.scanners[scanner_name] = NmapScanner(
                        targets=targets,
                        config=scanner_config
                    )
                elif scanner_name == "lynis":
                    self.scanners[scanner_name] = LynisScanner(
                        config=scanner_config
                    )
                elif scanner_name == "file_integrity":
                    baseline_file = scanner_config.get("baseline_file")
                    self.scanners[scanner_name] = FileIntegrityMonitor(
                        baseline_file=baseline_file,
                        config=scanner_config
                    )
                
                logger.info(f"Initialized scanner: {scanner_name}")
                
            except Exception as e:
                error_msg = f"Failed to initialize scanner {scanner_name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self.errors.append(error_msg)
    
    async def run_scan(self, scanner_name: Optional[str] = None) -> bool:
        """Run one or all scanners.
        
        Args:
            scanner_name: Name of the scanner to run. If None, run all scanners.
            
        Returns:
            bool: True if all scans completed successfully, False otherwise.
        """
        success = True
        
        try:
            if scanner_name:
                if scanner_name not in self.scanners:
                    error_msg = f"Scanner not found: {scanner_name}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
                    return False
                    
                scanner = self.scanners[scanner_name]
                logger.info(f"Running scanner: {scanner_name}")
                
                if await scanner.scan():
                    self.results.extend(scanner.get_results())
                else:
                    self.errors.extend(scanner.get_errors())
                    success = False
            else:
                # Run all scanners concurrently
                tasks = []
                for name, scanner in self.scanners.items():
                    logger.info(f"Queueing scanner: {name}")
                    tasks.append(self._run_single_scanner(name, scanner))
                
                # Wait for all scanners to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Scanner error: {str(result)}", exc_info=result)
                        self.errors.append(str(result))
                        success = False
                    elif not result.get("success", False):
                        success = False
            
            return success
            
        except Exception as e:
            error_msg = f"Error during scan: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            return False
    
    async def _run_single_scanner(self, name: str, scanner: BaseScanner) -> Dict[str, Any]:
        """Run a single scanner and return its results."""
        try:
            success = await scanner.scan()
            
            if success:
                self.results.extend(scanner.get_results())
            else:
                self.errors.extend(scanner.get_errors())
            
            return {
                "scanner": name,
                "success": success,
                "results": scanner.get_results(),
                "errors": scanner.get_errors()
            }
            
        except Exception as e:
            error_msg = f"Error in scanner {name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            return {
                "scanner": name,
                "success": False,
                "error": str(e)
            }
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get all scan results."""
        return self.results
    
    def get_errors(self) -> List[str]:
        """Get all errors from all scanners."""
        return self.errors
    
    def save_results(self, output_file: str = None) -> str:
        """Save all results to a JSON file.
        
        Args:
            output_file: Path to the output file. If None, a default name is used.
            
        Returns:
            str: Path to the output file.
        """
        if not output_file:
            output_dir = "scan_results"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"scan_{self.scan_id}.json")
        
        result_data = {
            "scan_id": self.scan_id,
            "timestamp": datetime.utcnow().isoformat(),
            "scanners_run": list(self.scanners.keys()),
            "results": self.results,
            "errors": self.errors
        }
        
        with open(output_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        return output_file
    
    def get_scanner(self, scanner_name: str) -> Optional[BaseScanner]:
        """Get a scanner instance by name."""
        return self.scanners.get(scanner_name)
    
    def add_scanner(self, scanner_name: str, scanner: BaseScanner) -> None:
        """Add a custom scanner instance."""
        self.scanners[scanner_name] = scanner
    
    def remove_scanner(self, scanner_name: str) -> bool:
        """Remove a scanner by name."""
        if scanner_name in self.scanners:
            del self.scanners[scanner_name]
            return True
        return False


async def example_usage():
    """Example usage of the ScannerManager."""
    config = {
        "scanners": ["nmap", "lynis", "file_integrity"],
        "nmap": {
            "targets": ["localhost"],
            "ports": "1-1024"
        },
        "lynis": {
            "categories": ["authentication", "networking"]
        },
        "file_integrity": {
            "paths": ["/etc/passwd", "/etc/shadow"],
            "baseline_file": "/tmp/fim_baseline.json"
        }
    }
    
    # Create and run the scanner manager
    manager = ScannerManager(config)
    
    # Run all scanners
    success = await manager.run_scan()
    
    # Save results
    output_file = manager.save_results()
    print(f"Scan complete. Results saved to: {output_file}")
    
    # Print summary
    print(f"\nScan Summary:")
    print(f"- Scanners run: {', '.join(manager.scanners.keys())}")
    print(f"- Total findings: {len(manager.results)}")
    print(f"- Errors: {len(manager.errors)}")
    
    # Print critical findings
    critical_findings = [r for r in manager.results if r.get('severity') == 'critical']
    if critical_findings:
        print("\nCritical Findings:")
        for finding in critical_findings:
            print(f"- {finding.get('message')}")


if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Run the example
    asyncio.run(example_usage())
