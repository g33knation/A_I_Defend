import os
import hashlib
import json
import time
from datetime import datetime
import httpx
import asyncio
from pathlib import Path

import os

# Configuration
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '30'))  # seconds
TARGET_DIRECTORIES = os.getenv('TARGET_DIRECTORIES', '/etc,/var/log').split(',')
API_URL = os.getenv('API_URL', 'http://localhost:8000/events')

print(f"Starting scanner with configuration:")
print(f"- Scan interval: {SCAN_INTERVAL} seconds")
print(f"- Target directories: {TARGET_DIRECTORIES}")
print(f"- API URL: {API_URL}")

async def get_file_checksum(file_path):
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, PermissionError):
        return None

def get_file_metadata(file_path):
    """Get basic file metadata."""
    try:
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'permissions': oct(stat.st_mode)[-3:],
            'owner': stat.st_uid,
            'group': stat.st_gid
        }
    except (IOError, PermissionError):
        return None

async def scan_directory(directory):
    """Scan a directory for file changes."""
    file_events = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip unreadable files
            if not os.access(file_path, os.R_OK):
                continue
                
            checksum = await get_file_checksum(file_path)
            metadata = get_file_metadata(file_path)
            
            if checksum and metadata:
                file_events.append({
                    'path': file_path,
                    'checksum': checksum,
                    'metadata': metadata,
                    'timestamp': datetime.utcnow().isoformat()
                })
    
    return file_events

async def send_events(events, source):
    """Send events to the backend API."""
    if not events:
        return
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                API_URL,
                json={
                    'source': source,
                    'type': 'filesystem_scan',
                    'payload': {
                        'timestamp': datetime.utcnow().isoformat(),
                        'files_scanned': len(events),
                        'events': events
                    }
                }
            )
            print(f"Sent {len(events)} events: {response.status_code}")
        except Exception as e:
            print(f"Error sending events: {e}")

async def scan_and_report():
    """Scan directories and report changes."""
    print("Starting file system scanner...")
    
    # Initial scan to establish baseline
    print("Performing initial scan...")
    all_events = []
    for directory in TARGET_DIRECTORIES:
        if os.path.exists(directory):
            events = await scan_directory(directory)
            all_events.extend(events)
    
    if all_events:
        await send_events(all_events, "initial_scan")
    
    # Continuous monitoring
    print(f"Monitoring {len(TARGET_DIRECTORIES)} directories every {SCAN_INTERVAL} seconds...")
    
    while True:
        try:
            all_events = []
            for directory in TARGET_DIRECTORIES:
                if os.path.exists(directory):
                    events = await scan_directory(directory)
                    all_events.extend(events)
            
            if all_events:
                await send_events(all_events, "periodic_scan")
                
            await asyncio.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\nStopping scanner...")
            break
        except Exception as e:
            print(f"Error during scan: {e}")
            await asyncio.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    print("Linux File System Scanner")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(scan_and_report())
    except KeyboardInterrupt:
        print("\nScanner stopped by user")
