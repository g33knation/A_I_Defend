import asyncio
import hashlib
import logging
import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)

class FileIntegrityMonitor(BaseScanner):
    """File Integrity Monitor for detecting changes in critical system files."""
    
    # Default files and directories to monitor
    DEFAULT_PATHS = [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/group",
        "/etc/sudoers",
        "/etc/ssh/sshd_config",
        "/etc/hosts",
        "/etc/hosts.allow",
        "/etc/hosts.deny",
        "/var/log",
        "/etc/crontab",
        "/etc/cron.d",
        "/etc/cron.daily",
        "/etc/cron.hourly",
        "/etc/cron.weekly",
        "/etc/cron.monthly",
        "/etc/init.d",
        "/etc/rc.local"
    ]
    
    def __init__(self, baseline_file: str = None, config: Dict[str, Any] = None):
        """Initialize the File Integrity Monitor.
        
        Args:
            baseline_file: Path to save/load baseline hashes (default: ~/.fim_baseline.json)
            config: Configuration dictionary with optional keys:
                   - paths: List of files/directories to monitor
                   - exclude: List of patterns to exclude
                   - hashing_algorithm: Hash algorithm to use (default: sha256)
                   - check_permissions: Whether to check file permissions (default: True)
                   - check_ownership: Whether to check file ownership (default: True)
        """
        super().__init__(config)
        self.baseline_file = baseline_file or os.path.expanduser("~/.fim_baseline.json")
        self.paths = self.config.get("paths", self.DEFAULT_PATHS)
        self.exclude = self.config.get("exclude", [])
        self.hashing_algorithm = self.config.get("hashing_algorithm", "sha256").lower()
        self.check_permissions = self.config.get("check_permissions", True)
        self.check_ownership = self.config.get("check_ownership", True)
        self.baseline: Dict[str, Dict[str, Any]] = {}
        self.current_state: Dict[str, Dict[str, Any]] = {}
        
    async def scan(self) -> bool:
        """Perform a file integrity check against the baseline."""
        try:
            # Load baseline if it exists
            if os.path.exists(self.baseline_file):
                self._load_baseline()
            
            # Scan all specified paths
            await self._scan_paths()
            
            # Compare current state with baseline
            self._compare_states()
            
            # Save new baseline if this is the first run
            if not self.baseline:
                self._save_baseline()
                self.results.append({
                    "type": "fim_baseline_created",
                    "severity": "info",
                    "message": "Initial file integrity baseline created",
                    "baseline_file": self.baseline_file,
                    "timestamp": self.scan_id,
                    "files_scanned": len(self.current_state)
                })
            
            return True
            
        except Exception as e:
            error_msg = f"Error during file integrity check: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            return False
    
    async def create_baseline(self) -> bool:
        """Create a new baseline of file hashes."""
        try:
            await self._scan_paths()
            self._save_baseline()
            return True
            
        except Exception as e:
            error_msg = f"Error creating baseline: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            return False
    
    def _load_baseline(self) -> None:
        """Load the baseline from file."""
        try:
            with open(self.baseline_file, 'r') as f:
                import json
                self.baseline = json.load(f)
                
        except Exception as e:
            logger.warning(f"Could not load baseline: {str(e)}")
            self.baseline = {}
    
    def _save_baseline(self) -> None:
        """Save the current state as the new baseline."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.baseline_file)), exist_ok=True)
            
            with open(self.baseline_file, 'w') as f:
                import json
                json.dump(self.current_state, f, indent=2)
                
        except Exception as e:
            error_msg = f"Could not save baseline: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
    
    async def _scan_paths(self) -> None:
        """Scan all specified paths and update current state."""
        self.current_state = {}
        
        for path in self.paths:
            path = os.path.abspath(os.path.expanduser(path))
            
            # Skip if path should be excluded
            if any(re.search(pattern, path) for pattern in self.exclude):
                continue
                
            if os.path.isfile(path):
                await self._process_file(path)
            elif os.path.isdir(path):
                await self._process_directory(path)
    
    async def _process_directory(self, directory: str) -> None:
        """Process all files in a directory recursively."""
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                await self._process_file(file_path)
    
    async def _process_file(self, file_path: str) -> None:
        """Process a single file and add it to the current state."""
        try:
            # Skip if file should be excluded
            if any(re.search(pattern, file_path) for pattern in self.exclude):
                return
                
            # Skip special files
            if not os.path.isfile(file_path) or stat.S_ISFIFO(os.stat(file_path).st_mode):
                return
                
            # Get file stats
            stat_info = os.stat(file_path)
            
            # Calculate file hash
            file_hash = self._calculate_hash(file_path)
            
            # Store file info
            self.current_state[file_path] = {
                "hash": file_hash,
                "size": stat_info.st_size,
                "modified": stat_info.st_mtime,
                "permissions": oct(stat_info.st_mode & 0o777),
                "uid": stat_info.st_uid,
                "gid": stat_info.st_gid,
                "inode": stat_info.st_ino,
                "device": stat_info.st_dev
            }
            
        except (PermissionError, FileNotFoundError) as e:
            logger.warning(f"Could not process file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
    
    def _calculate_hash(self, file_path: str) -> str:
        """Calculate the hash of a file."""
        hash_func = getattr(hashlib, self.hashing_algorithm, hashlib.sha256)
        
        with open(file_path, 'rb') as f:
            file_hash = hash_func()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
                
        return file_hash.hexdigest()
    
    def _compare_states(self) -> None:
        """Compare current state with baseline and generate results."""
        if not self.baseline:
            return
            
        # Check for modified files
        for file_path, current_info in self.current_state.items():
            if file_path not in self.baseline:
                self.results.append(self._create_result("file_added", file_path, current_info))
                continue
                
            baseline_info = self.baseline[file_path]
            
            # Check file hash
            if current_info["hash"] != baseline_info["hash"]:
                self.results.append(self._create_result(
                    "file_modified",
                    file_path,
                    current_info,
                    baseline_info
                ))
            
            # Check file permissions if enabled
            if self.check_permissions and current_info["permissions"] != baseline_info["permissions"]:
                self.results.append(self._create_result(
                    "permissions_changed",
                    file_path,
                    current_info,
                    baseline_info,
                    {
                        "current_permissions": current_info["permissions"],
                        "baseline_permissions": baseline_info["permissions"]
                    }
                ))
            
            # Check file ownership if enabled
            if self.check_ownership and \
               (current_info["uid"] != baseline_info["uid"] or 
                current_info["gid"] != baseline_info["gid"]):
                self.results.append(self._create_result(
                    "ownership_changed",
                    file_path,
                    current_info,
                    baseline_info,
                    {
                        "current_uid": current_info["uid"],
                        "baseline_uid": baseline_info["uid"],
                        "current_gid": current_info["gid"],
                        "baseline_gid": baseline_info["gid"]
                    }
                ))
        
        # Check for deleted files
        for file_path in set(self.baseline.keys()) - set(self.current_state.keys()):
            self.results.append(self._create_result(
                "file_deleted",
                file_path,
                None,
                self.baseline[file_path]
            ))
    
    def _create_result(
        self,
        event_type: str,
        file_path: str,
        current_info: Optional[Dict[str, Any]],
        baseline_info: Optional[Dict[str, Any]] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a standardized result dictionary."""
        severity_map = {
            "file_added": "medium",
            "file_modified": "high",
            "file_deleted": "high",
            "permissions_changed": "medium",
            "ownership_changed": "high"
        }
        
        details = {
            "file_path": file_path,
            "current_info": current_info,
            "baseline_info": baseline_info,
            "event_type": event_type,
            "timestamp": self.scan_id
        }
        
        if additional_details:
            details.update(additional_details)
        
        return {
            "type": "file_integrity",
            "severity": severity_map.get(event_type, "medium"),
            "message": f"File integrity event: {event_type.replace('_', ' ').title()} - {file_path}",
            "timestamp": self.scan_id,
            "details": details
        }
