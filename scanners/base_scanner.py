import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class BaseScanner(ABC):
    """Base class for all security scanners."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the scanner with configuration."""
        self.config = config or {}
        self.scan_id: str = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        
    @abstractmethod
    async def scan(self) -> bool:
        """Perform the scan and return True if successful."""
        pass
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get the scan results."""
        return self.results
    
    def get_errors(self) -> List[str]:
        """Get any errors that occurred during scanning."""
        return self.errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan results to a dictionary."""
        return {
            "scanner": self.__class__.__name__,
            "scan_id": self.scan_id,
            "timestamp": datetime.utcnow().isoformat(),
            "results": self.results,
            "errors": self.errors,
            "status": "completed" if not self.errors else "failed"
        }
    
    def save_results(self, output_dir: str = "results") -> str:
        """Save scan results to a JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"{self.__class__.__name__.lower()}_{self.scan_id}.json")
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        return filename
    
    async def run_command(self, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Run a shell command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise RuntimeError(f"Command timed out after {timeout} seconds")
                
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode().strip() if stdout else "",
                "stderr": stderr.decode().strip() if stderr else ""
            }
            
        except Exception as e:
            error_msg = f"Error running command '{' '.join(command)}': {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            raise
