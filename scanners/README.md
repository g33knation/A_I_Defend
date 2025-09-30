# Security Scanner Integration

This directory contains the implementation of various security scanners integrated into the A_I_Defend system.

## Available Scanners

1. **Nmap** - Network scanning and host discovery
2. **ClamAV** - Antivirus scanning
3. **chkrootkit** - Rootkit detection
4. **RKHunter** - Rootkit and backdoor detection
5. **YARA** - Pattern matching for malware identification
6. **Suricata** - Network IDS/IPS
7. **Lynis** - Security auditing tool

## Usage

### 1. Direct Usage (Python)

```python
from scanners.linux.security_scanner import SecurityScanner
import asyncio

async def run_scan():
    config = {
        "scanners": ["nmap", "clamav", "lynis"],
        "nmap": {
            "targets": ["127.0.0.1"],
            "ports": "1-1000"
        },
        "clamav": {
            "paths": ["/tmp", "/home"]
        }
    }
    
    scanner = SecurityScanner(config)
    success = await scanner.scan()
    print(f"Scan completed: {success}")
    print(f"Results: {scanner.results}")

asyncio.run(run_scan())
```

### 2. Using the API

Start a scan:
```bash
curl -X POST http://localhost:8000/api/scans/start \
  -H "Content-Type: application/json" \
  -d '{
    "scanners": ["nmap", "clamav"],
    "config": {
      "nmap": {
        "targets": ["127.0.0.1"],
        "ports": "1-1000"
      }
    }
  }'
```

Check scan status:
```bash
curl http://localhost:8000/api/scans/<scan_id>
```

List all scans:
```bash
curl http://localhost:8000/api/scans
```

## Configuration

Each scanner can be configured using the `config` parameter. Here are the available options:

### Nmap
- `targets`: List of IP addresses or hostnames to scan
- `ports`: Port range to scan (e.g., "1-1024")
- `arguments`: Additional Nmap arguments (default: "-T4 -A -v")

### ClamAV
- `paths`: List of directories to scan
- `max_file_size`: Maximum file size to scan in MB (default: 25)

### YARA
- `paths`: List of directories to scan
- `rules_dir`: Directory containing YARA rules (default: "/etc/yara-rules")

### Suricata
- `log_paths`: List of log file paths to check (default: ["/var/log/suricata/fast.log"])

### Lynis
- `categories`: List of categories to audit (default: all)

## Testing

### Run Tests

1. **Direct Test**:
   ```bash
   python test_security_scan.py
   ```

2. **API Test**:
   ```bash
   # Start the FastAPI server first
   cd backend
   uvicorn app.main:app --reload
   
   # In another terminal
   python test_api_scan.py
   ```

## Dependencies

- Python 3.8+
- Security tools (installed in the Docker container):
  - nmap
  - clamav
  - chkrootkit
  - rkhunter
  - yara
  - suricata
  - lynis

## Notes

- The scanner requires root privileges for some operations (e.g., chkrootkit, rkhunter)
- Make sure the required tools are installed and in the system PATH
- For production use, consider running scans in a containerized environment
