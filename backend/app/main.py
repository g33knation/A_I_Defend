import os
import sys
import re
from pathlib import Path
import json

# Add the backend directory to the Python path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import httpx
import uuid
import ipaddress
from datetime import datetime


def classify_ip_origin(ip_str: str, agent_identifiers: list[str] = []) -> tuple[str, str]:
    """
    Classify an IP address as internal, external, or a known agent.
    Returns (emoji_indicator, label) tuple.
    """
    if ip_str in agent_identifiers:
        return ("🤖", "KNOWN AGENT")
    
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return ("🏠", "INTERNAL")
        else:
            return ("🌐", "EXTERNAL")
    except ValueError:
        # Not a valid IP (might be a hostname)
        if ip_str in ['localhost', '127.0.0.1', 'local']:
            return ("🏠", "INTERNAL")
        # Check for common internal hostnames
        if any(x in ip_str.lower() for x in ['local', 'internal', 'intranet', 'lan']):
            return ("🏠", "INTERNAL")
        return ("❓", "UNKNOWN")

# Configuration
MODEL_SERVER_URL = os.getenv("MODEL_SERVER_URL") or "http://model-server:11434"
# Nervous System Security: Formalize trust between Brain and Legs
BRAIN_API_KEY = os.getenv("BRAIN_API_KEY") or "octopus-nervous-system-secret"

# Import routers
from app.routers import scans, agents, defense_actions
from app.routers.defense_actions import DefenseActionRequest

# Create FastAPI app
app = FastAPI(title="Defense AI Backend - Brain")

from fastapi import Header

async def verify_nervous_system_key(x_api_key: str = Header(None)):
    """Security dependency to verify requests from agents (legs)."""
    if not x_api_key or x_api_key != BRAIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Brain Error: Unauthorized access. The nervous system link is unverified."
        )
    return x_api_key

# CORS configuration - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global exception caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}  # Explicitly add for error cases
    )

class FeedbackIn(BaseModel):
    detection_id: int
    feedback: str

class AskIn(BaseModel):
    query: str
    model: str = "hermes3:latest"  # Default to hermes3 for offline capability

class EventIn(BaseModel):
    source: str
    type: str
    payload: dict = {}

class LogIn(BaseModel):
    agent_id: str
    log_level: str
    message: str
    context: dict = {}
    timestamp: datetime = None


@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool and global HTTP client on startup."""
    # Initialize global HTTP client
    app.state.client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))
    
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # Fallback for local development ONLY IF NO ENV IS PROVIDED
            # WARNING: In production, system will fail fast if URL is missing
            database_url = "postgres://postgres:changeit@db:5432/defense"
            print(f"WARNING: DATABASE_URL not set, using default development credentials")
        
        app.state.pool = await asyncpg.create_pool(
            dsn=database_url,
            min_size=1,
            max_size=10
        )
        print("Database connection pool created")
    except Exception as e:
        print(f"Error creating database pool: {e}")
        # We don't raise here to allow the app to start, but requests needing DB will fail

# Endpoints
@app.get("/events", response_model=list[dict])
async def list_events():

    """List all security events."""
    try:
        async with app.state.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, source, type, payload, 
                       created_at AT TIME ZONE 'UTC' as created_at
                FROM events 
                ORDER BY created_at DESC 
                LIMIT 50
                """
            )
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/logs", dependencies=[Depends(verify_nervous_system_key)])
async def ingest_log(log: LogIn):
    """Ingest a centralized log from an agent."""
    try:
        async with app.state.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_logs (agent_id, log_level, message, context, created_at)
                VALUES ($1, $2, $3, $4, COALESCE($5::timestamp, NOW()))
                """,
                log.agent_id, log.log_level, log.message, json.dumps(log.context), log.timestamp
            )
            print(f"📝 Log received from {log.agent_id}: [{log.log_level}] {log.message}")
        return {"status": "received"}
    except Exception as e:
        print(f"Error ingesting log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events", dependencies=[Depends(verify_nervous_system_key)])
async def ingest_event(event: EventIn):
    """Ingest a new security event."""
    # print(f"Received event: source={event.source}, type={event.type}")
    try:
        async with app.state.pool.acquire() as conn:
            # Insert the event and get its ID
            event_id = await conn.fetchval(
                """
                INSERT INTO events (source, type, payload, created_at)
                VALUES ($1, $2, $3, NOW())
                RETURNING id
                """,
                event.source, event.type, json.dumps(event.payload)
            )
            print(f"Event inserted with ID: {event_id}")
            
            # Create a detection for certain event types
            severity_map = {
                'malware_detected': 0.9,
                'clamav_scan': 0.9,
                'yara_scan': 0.85,
                'rootkit_scan': 0.8,
                'chkrootkit_scan': 0.8,
                'rkhunter_scan': 0.8,
                'ids_alert': 0.85,
                'suricata_scan': 0.85,
                'security_audit': 0.6,
                'lynis_scan': 0.6,
                'port_scan': 0.3,
                'nmap_scan': 0.3,
                'masscan_scan': 0.3,
                'ping-sweep_scan': 0.2,
                'arp-scan_scan': 0.2,
                'tshark_scan': 0.4,
                'dns-enum_scan': 0.2
            }
            
            category_map = {
                'malware_detected': 'malware',
                'clamav_scan': 'malware',
                'yara_scan': 'malware',
                'rootkit_scan': 'rootkit',
                'chkrootkit_scan': 'rootkit',
                'rkhunter_scan': 'rootkit',
                'ids_alert': 'intrusion',
                'suricata_scan': 'intrusion',
                'security_audit': 'vulnerability',
                'lynis_scan': 'vulnerability',
                'port_scan': 'reconnaissance',
                'nmap_scan': 'reconnaissance',
                'masscan_scan': 'reconnaissance',
                'ping-sweep_scan': 'reconnaissance',
                'arp-scan_scan': 'reconnaissance',
                'tshark_scan': 'reconnaissance',
                'dns-enum_scan': 'reconnaissance'
            }
            
            if event.type in severity_map:
                score = severity_map[event.type]
                category = category_map.get(event.type, 'unknown')
                summary = f"{event.source}: {event.type}"
                
                # Extract current agent IPs and hostnames for classification
                agent_identifiers = []
                for a in agents.agents.values():
                    if a.get('ip_address'): agent_identifiers.append(a.get('ip_address'))
                    if a.get('hostname'): agent_identifiers.append(a.get('hostname'))
                
                # Check if payload is a string or dict
                payload_data = event.payload
                if isinstance(payload_data, str):
                    try:
                        payload_data = json.loads(payload_data)
                    except:
                        pass
                
                # Extract more details from payload if available
                if isinstance(payload_data, dict) and 'details' in payload_data:
                    details = payload_data['details']
                    if isinstance(details, dict):
                        if 'infected_files' in details:
                            files = details['infected_files'][:3]  # First 3 files
                            file_list = ', '.join(files)
                            more = f" (+{len(details['infected_files'])-3} more)" if len(details['infected_files']) > 3 else ""
                            summary = f"Malware detected: {file_list}{more}"
                        elif 'warnings' in details and details['warnings']:
                            warnings = details['warnings'][:2]  # First 2 warnings
                            warning_text = '; '.join([w.get('message', str(w)) for w in warnings if isinstance(w, dict)])
                            more = f" (+{len(details['warnings'])-2} more)" if len(details['warnings']) > 2 else ""
                            summary = f"Security warnings: {warning_text}{more}"
                        elif 'alerts' in details:
                            alerts = details['alerts'][:2]
                            alert_text = '; '.join([a.get('signature', str(a)) for a in alerts if isinstance(a, dict)])
                            more = f" (+{len(details['alerts'])-2} more)" if len(details['alerts']) > 2 else ""
                            # Get source IP for origin classification
                            src_ip = None
                            if alerts and isinstance(alerts[0], dict):
                                src_ip = alerts[0].get('src_ip') or alerts[0].get('source_ip')
                            if src_ip:
                                origin_emoji, origin_label = classify_ip_origin(src_ip, agent_identifiers)
                                summary = f"{origin_emoji} [{origin_label}] IDS alerts from {src_ip}: {alert_text}{more}"
                            else:
                                summary = f"IDS alerts: {alert_text}{more}"
                        elif 'ports' in details:
                            ports = details['ports']
                            address = details.get('address', 'target')
                            # Get scanner source IP for origin classification
                            scanner_ip = details.get('scanner_ip') or details.get('source_ip') or event.payload.get('scanner_ip') or event.source
                            origin_indicator = ""
                            if scanner_ip:
                                origin_emoji, origin_label = classify_ip_origin(scanner_ip, agent_identifiers)
                                origin_indicator = f"{origin_emoji} [{origin_label}] "
                            elif address:
                                # Classify the target if no scanner IP available
                                origin_emoji, origin_label = classify_ip_origin(address, agent_identifiers)
                                origin_indicator = f"Target: {origin_emoji} "
                            # Format port list
                            if len(ports) <= 5:
                                port_list = ', '.join([f"{p.get('port', p)}/{p.get('protocol', 'tcp')}" if isinstance(p, dict) else str(p) for p in ports])
                                summary = f"{origin_indicator}Port scan on {address}: {port_list} (Source: {event.source})"
                            else:
                                port_list = ', '.join([f"{p.get('port', p)}/{p.get('protocol', 'tcp')}" if isinstance(p, dict) else str(p) for p in ports[:5]])
                                summary = f"{origin_indicator}Port scan on {address}: {port_list} (+{len(ports)-5} more) (Source: {event.source})"
                        elif 'live_hosts' in details:
                            # Ping sweep results
                            hosts = details['live_hosts']
                            network = event.payload.get('network', 'network')
                            if len(hosts) <= 5:
                                host_list = ', '.join(hosts)
                                summary = f"Ping sweep on {network}: {len(hosts)} live hosts ({host_list})"
                            else:
                                host_list = ', '.join(hosts[:5])
                                summary = f"Ping sweep on {network}: {len(hosts)} live hosts ({host_list} +{len(hosts)-5} more)"
                        elif 'hosts' in details:
                            # ARP scan results
                            hosts = details['hosts']
                            interface = details.get('interface', 'network')
                            if len(hosts) <= 5:
                                host_list = ', '.join([f"{h.get('ip', 'unknown')}" for h in hosts if isinstance(h, dict)])
                                summary = f"ARP scan on {interface}: {len(hosts)} devices ({host_list})"
                            else:
                                host_list = ', '.join([f"{h.get('ip', 'unknown')}" for h in hosts[:5] if isinstance(h, dict)])
                                summary = f"ARP scan on {interface}: {len(hosts)} devices ({host_list} +{len(hosts)-5} more)"
                        elif 'unique_ips' in details:
                            # Tshark results
                            ips = details['unique_ips']
                            protocols = details.get('protocols', {})
                            proto_summary = ', '.join([f"{k}: {v}" for k, v in list(protocols.items())[:3]])
                            summary = f"Traffic analysis: {len(ips)} unique IPs, protocols: {proto_summary}"
                        elif 'records' in details:
                            # DNS enumeration results
                            records = details['records']
                            domain = event.payload.get('domain', 'domain')
                            record_types = ', '.join(records.keys())
                            summary = f"DNS enumeration on {domain}: {record_types}"
                
                detection_id = await conn.fetchval(
                    """
                    INSERT INTO detections (event_id, summary, score, adjusted_score, category, ai_output, created_at)
                    VALUES ($1, $2, $3, $3, $4, $5, NOW())
                    RETURNING id
                    """,
                    event_id, summary, score, category, json.dumps(event.payload)
                )
                print(f"Detection created with ID: {detection_id}")
                
                # Trigger autonomous defense for high-severity detections
                try:
                    from app.routers.defense_actions import trigger_autonomous_defense
                    defense_result = await trigger_autonomous_defense(
                        event_id=event_id,
                        detection_id=detection_id,
                        score=score,
                        event_type=event.type,
                        payload=event.payload,
                        pool=app.state.pool
                    )
                    if defense_result:
                        print(f"🛡️ Autonomous defense triggered: {defense_result}")
                except Exception as defense_error:
                    print(f"Error in autonomous defense: {defense_error}")
        
        return {"status": "received", "event": event.dict()}
    except Exception as e:
        print(f"Error ingesting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include API routers
# Include routers with Nervous System Security (verify requests from legs)
app.include_router(scans.router, dependencies=[Depends(verify_nervous_system_key)])
app.include_router(agents.router, dependencies=[Depends(verify_nervous_system_key)])
app.include_router(defense_actions.router, dependencies=[Depends(verify_nervous_system_key)])

@app.get("/detections")
async def list_detections():
    """List all detections with their feedback."""
    async with app.state.pool.acquire() as conn:
        # Join with detection_feedback to get the latest feedback for each detection
        rows = await conn.fetch("""
            SELECT d.*, f.feedback
            FROM detections d
            LEFT JOIN detection_feedback f ON d.id = f.detection_id
            ORDER BY d.created_at DESC
            LIMIT 50
        """)
    return [dict(r) for r in rows]

@app.post("/feedback")
async def submit_feedback(fb: FeedbackIn):
    print(f"DEBUG: submit_feedback called for ID {fb.detection_id}")
    async with app.state.pool.acquire() as conn:
        # Use detection_feedback table instead of updating detections table
        # We use an UPSERT pattern to ensure we only have one feedback record per detection
        await conn.execute(
            """
            INSERT INTO detection_feedback (detection_id, feedback, created_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (detection_id) DO UPDATE SET feedback = EXCLUDED.feedback, created_at = NOW()
            """,
            fb.detection_id, fb.feedback
        )
    return {"status": "ok"}

@app.delete("/detections")
async def purge_detections():
    """Delete all detections."""
    async with app.state.pool.acquire() as conn:
        await conn.execute("DELETE FROM detection_feedback")
        await conn.execute("DELETE FROM detections")
    return {"status": "ok", "message": "All detections purged"}

@app.delete("/events")
async def purge_events():
    """Delete all events and associated detections."""
    async with app.state.pool.acquire() as conn:
        # Delete dependent data first to avoid FK constraint violations
        await conn.execute("DELETE FROM detection_feedback")
        await conn.execute("DELETE FROM detections")
        await conn.execute("DELETE FROM events")
    return {"status": "ok", "message": "All events and detections purged"}

def summarize_security_data(data: str, max_chars: int = 5000) -> str:
    """
    Intelligently summarizes large security payloads to prevent LLM context overflow.
    """
    if not data or len(data) <= max_chars:
        return data

    summary = f"[PAYLOAD TRUNCATED - ORIGINAL SIZE: {len(data)} chars]\n"
    
    # Check if it's an Nmap scan
    if "Nmap scan report" in data:
        lines = data.splitlines()
        summary += "\n".join(lines[:20]) # First 20 lines usually contain target and open ports
        summary += f"\n... [{len(lines)-40} lines truncated] ...\n"
        summary += "\n".join(lines[-20:]) # Last 20 lines often contain OS detection and summary
        return summary
        
    # Check if it's Tshark output
    if "Capturing on" in data or "Packets" in data:
        lines = data.splitlines()
        summary += "\n".join(lines[:30]) # Capture stats
        summary += f"\n... [{len(lines)-60} lines truncated] ...\n"
        summary += "\n".join(lines[-30:]) # End summary
        return summary

    # Generic truncation: take start and end
    half_max = max_chars // 2
    return data[:half_max] + f"\n... [{len(data)-max_chars} chars truncated] ...\n" + data[-half_max:]

@app.post("/ask")
async def ask_model(req: AskIn):
    """Send a query to Ollama and return the response."""
    try:
        # Fetch recent context (detections)
        context_text = ""
        # Consolidate all DB operations into one connection block
        try:
            async with app.state.pool.acquire(timeout=5.0) as conn:
                # 1. Fetch Recent Context
                try:
                    rows = await conn.fetch("""
                        SELECT summary, category, score, created_at
                        FROM detections
                        ORDER BY created_at DESC
                        LIMIT 10
                    """)
                    if rows:
                        detections_list = "\n".join([f"- [{r['created_at']}] {r['category'].upper()}: {r['summary']} (Score: {r['score']})" for r in rows])
                        context_text += f"\nRecent Security Detections:\n{detections_list}\n"
                    else:
                        context_text += "\nRecent Security Detections: None recorded.\n"
                except Exception as e:
                    print(f"Error fetching detections: {e}")
                    context_text += "\nRecent Security Detections: Error retrieving data.\n"

                # 2. Fetch Ambiguous Detections
                try:
                    rows = await conn.fetch("""
                        SELECT d.summary, d.category, d.score, d.created_at
                        FROM detections d
                        LEFT JOIN detection_feedback f ON d.id = f.detection_id
                        WHERE d.score >= 0.2 AND d.score <= 0.8
                        AND f.id IS NULL
                        AND d.created_at > NOW() - INTERVAL '24 hours'
                        ORDER BY d.created_at DESC
                        LIMIT 5
                    """)
                    if rows:
                        ambiguous_list = "\n".join([f"- [{r['created_at']}] {r['category'].upper()}: {r['summary']} (Score: {r['score']})" for r in rows])
                        context_text += f"\nAmbiguous Detections (NEED USER GUIDANCE):\n{ambiguous_list}\n"
                    else:
                        context_text += "\nAmbiguous Detections: None.\n"
                except Exception as e:
                    print(f"Error fetching ambiguous detections: {e}")

                # 3. Fetch Autonomous Actions
                try:
                    rows = await conn.fetch("""
                        SELECT action_type, target, reason, status, created_at
                        FROM defense_actions
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                        ORDER BY created_at DESC
                        LIMIT 5
                    """)
                    if rows:
                        actions_list = "\n".join([f"- [{r['created_at']}] {r['action_type'].upper()} on {r['target']}: {r['reason']} (Status: {r['status']})" for r in rows])
                        context_text += f"\nRecent Autonomous Defense Actions:\n{actions_list}\n"
                    else:
                        context_text += "\nRecent Autonomous Defense Actions: None.\n"
                except Exception as e:
                    print(f"Error fetching defense actions: {e}")

        except Exception as pool_err:
            print(f"Error acquiring DB connection: {pool_err}")
            context_text += "\n[System Error: Database Unavailable]\n"

        # Fetch Active Agents (from in-memory store)
        try:
            if agents.agents:
                active_agents = [
                    f"- {a['hostname']} ({a['ip_address']}): {a['status']} ({a['health']}, Latency: {a.get('latency', 0)}s)"
                    for a in agents.agents.values()
                ]
                context_text += f"\nActive Agents:\n" + "\n".join(active_agents) + "\n"
            else:
                context_text += "\nActive Agents: None registered.\n"
        except Exception as e:
            print(f"Error fetching agents context: {e}")
            context_text += "\nActive Agents: Error retrieving data.\n"

        # Fetch Recent Scans (from in-memory store)
        try:
            if scans.scan_results:
                # Sort by start_time descending
                recent_scans = sorted(
                    scans.scan_results.values(), 
                    key=lambda x: x.get('start_time') or "", 
                    reverse=True
                )[:5]
                
                scan_list = []
                for s in recent_scans:
                    status = s.get('status', 'unknown')
                    start = s.get('start_time')
                    
                    # SUMMARIZE LARGE RESULTS
                    results = s.get('results', {})
                    results_str = str(results)
                    summarized_results = summarize_security_data(results_str)
                    
                    scan_list.append(f"- Scan {status} (Started: {start})\n  Results Context: {summarized_results[:1000]}") # Still limit per item
                
                context_text += f"\nRecent Scans (Summarized):\n" + "\n".join(scan_list) + "\n"
            else:
                context_text += "\nRecent Scans: None recorded.\n"
        except Exception as e:
            print(f"Error fetching scans context: {e}")
            context_text += "\nRecent Scans: Error retrieving data.\n"

        system_prompt = """You are an advanced AI Security Assistant for the A_I_Defend system.
        Your capabilities include:
        1. Analyzing security events and detections from the database.
        2. Deploying active scanner agents to investigate targets.
        3. Explaining security concepts and providing remediation advice.
        4. Managing autonomous defense actions (blocking IPs, quarantining files).

        CONFIDENCE & GUIDANCE PROTOCOL:
        - **Ambiguous Detections**: If the context lists "Ambiguous Detections" (scores 0.2-0.8), you MUST explicitly ask the user for confirmation. Explain what was detected and ask if it is authorized activity (e.g., "I detected a port scan from 192.168.1.50. Is this a known device or authorized testing?").
        - **High Confidence**: If you see "Recent Autonomous Defense Actions", report them to the user so they know you have already protected the system.
        - **Low Confidence**: If a user asks about a potential threat and you are unsure, recommend a specific scan to gather more evidence before suggesting drastic actions like blocking.

        COMMANDS:
        You can deploy agents by outputting a specific command pattern. Available scanners: 
        - nmap (Port Scan - Network Monitor)
        - suricata (IDS - Network Monitor)
        - clamav (Malware Scan - Malware Scanner)
        - yara (Malware Scan - Malware Scanner)
        - lynis (Security Audit - Security Scanner)
        - chkrootkit (Rootkit Scan - Security Scanner)
        - rkhunter (Rootkit Scan - Security Scanner)
        - tshark (Traffic Analysis - Network Intel)
        - masscan (Fast Port Scan - Network Intel)
        - arp-scan (Local Discovery - Network Intel)
        - dns-enum (DNS Enumeration - Network Intel)
        - ping-sweep (Live Host Discovery - Network Intel)

        Format: ACTION: SCAN target=<ip_or_host> scanner=<scanner_name>
        Example: ACTION: SCAN target=192.168.1.50 scanner=nmap

        DEFENSE COMMANDS (for active threat response):
        When you detect a threat that requires immediate action, or when the user requests a defensive action, use these commands:
        
        - ACTION: BLOCK_IP ip=<ip_address> reason=<reason>
          Use when: Port scans detected, brute force attempts, IDS alerts from specific IP
          Example: ACTION: BLOCK_IP ip=192.168.1.100 reason="Detected aggressive port scan"
        
        - ACTION: UNBLOCK_IP ip=<ip_address>
          Use when: User requests to unblock a previously blocked IP
          Example: ACTION: UNBLOCK_IP ip=192.168.1.100
        
        - ACTION: QUARANTINE_FILE path=<file_path> reason=<reason>
          Use when: Malware detected in a file (clamav, yara detection)
          Example: ACTION: QUARANTINE_FILE path=/tmp/malware.exe reason="ClamAV: Trojan.Generic"
        
        - ACTION: KILL_PROCESS pid=<process_id> reason=<reason>
          Use when: Suspicious process needs to be terminated
          Example: ACTION: KILL_PROCESS pid=1234 reason="Cryptominer process detected"

        RULES:
        - If the user explicitly asks to run a scan, YOU MUST EXECUTE IT immediately. Do not ask for permissions or reasons.
        - Only deploy a scan *autonomously* if it is CRITICAL to gather missing information for a specific question.
        - Do NOT suggest commands unless you are actually triggering the ACTION.
        - Do NOT run a scan just to "analyze" results. If you are provided with scan results in the context, analyze values directly.
        - If a scan just finished, the results will be in your context. Read them and summarize. Do NOT run another scan (like lynis) unless the user specifically requested a follow-up compliance check.
        - For 'tshark' and 'arp-scan', the 'target' parameter is required by the format but essentially ignored or used as a label, as these tools run on the local network interface. You can set target="local" or the network range.
        
        REPORT FORMATTING (CRITICAL):
        When presenting scan results or analysis, ALWAYS use professional, detailed markdown formatting:
        
        1. **Use Headers**: Start with a main header (## 📊 Report Title) and organize with subheadings.
        
        2. **Use Tables**: Present statistics and data in markdown tables for clarity:
           | Metric | Value |
           |--------|-------|
           | Total Packets | 88 |
        
        3. **Use Emoji Icons**: Add visual context with emojis (📊 📈 🔌 🔗 🌐 🔍 ✅ ❌ ⚠️).
        
        4. **Provide Analysis**: Always include a "Findings" or "Analysis" section explaining what the data means.
        
        5. **Give a Conclusion**: End with a clear status summary (e.g., "Network Status: CLEAN" or "⚠️ Issues Detected").
        
        6. **For tshark reports specifically**, include:
           - Capture duration and time period
           - Summary statistics (packets, bytes, data rate)
           - Protocol breakdown table
           - TCP/UDP conversations
           - IP endpoints
           - Security analysis (suspicious activity, port scans, etc.)
           - Final conclusion on network status
         
        7. **For nmap reports**, include:
           - Target summary
           - Open ports table with service info
           - OS detection results if available
           - Security recommendations
         
        Be thorough, professional, and make reports visually impressive and easy to understand.
        """

        # Construct the user message with context embedded
        user_content = f"""I am the A_I_Defend security system. Here is my current state:

{context_text}

USER QUESTION: {req.query}

Please answer based ONLY on the information above. If I listed specific malware files, port scans, or IDS alerts, mention those EXACT details. If sections say "None recorded", state that those areas are clean."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        print(f"=" * 80)
        print(f"CONTEXT TEXT BEING SENT:")
        print(context_text)
        print(f"=" * 80)

        # Call Ollama's Chat API
        ollama_url = f"{MODEL_SERVER_URL}/api/chat"
        payload = {
            "model": req.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": 16384, # Increase context window for complex logs
                "temperature": 0.2 # Lower temperature for factual analysis
            }
        }
        
        response = await app.state.client.post(
            ollama_url,
            json=payload,
            timeout=600.0
        )
        response.raise_for_status()
        result = response.json()
            
        ai_content = result.get("message", {}).get("content", "")
        
        # PARSE AND EXECUTE ACTIONS
        action_match = re.search(r"ACTION: SCAN target=(\S+) scanner=(\S+)", ai_content)
        if action_match:
            target = action_match.group(1)
            scanner_name = action_match.group(2)
            print(f"AI REQUESTED SCAN: Target={target}, Scanner={scanner_name}")
            
            # Find a suitable agent
            selected_agent_id = None
            if agents.agents:
                for agent_id, agent in agents.agents.items():
                    if agent["status"] == "idle" and (scanner_name in agent["capabilities"] or "all" in agent["capabilities"]):
                        selected_agent_id = agent_id
                        break
            
            execution_msg = ""
            if selected_agent_id:
                # Trigger the scan
                try:
                    assignment_id = str(uuid.uuid4())
                    agents.agent_assignments[selected_agent_id] = {
                        "assignment_id": assignment_id,
                        "targets": [target],
                        "scanners": [scanner_name],
                        "config": {},
                        "priority": 5,
                        "assigned_at": datetime.utcnow().isoformat()
                    }
                    agents.agents[selected_agent_id]["current_assignment"] = assignment_id
                    
                    # Return special marker for frontend to render interactive bubble
                    execution_msg = f"\n<<<SCAN_STARTED|id={assignment_id}|target={target}|scanner={scanner_name}>>>"
                except Exception as exc:
                    execution_msg = f"\n\n[SYSTEM] Command Failed: Error assigning task: {exc}"
            else:
                execution_msg = f"\n\n[SYSTEM] Command Failed: No idle agents found with capability '{scanner_name}'."
            
            # Strip the raw ACTION command from the output so user doesn't see it twice
            parts = ai_content.split("ACTION: SCAN")
            pre_text = parts[0].strip()
            ai_content = f"{pre_text}{execution_msg}" if pre_text else execution_msg.strip()
        
        # PARSE DEFENSE ACTIONS
        # Check for BLOCK_IP command
        block_ip_match = re.search(r'ACTION: BLOCK_IP ip=(\S+)\s+reason="([^"]+)"', ai_content)
        if block_ip_match:
            ip = block_ip_match.group(1)
            reason = block_ip_match.group(2)
            print(f"🛡️ AI REQUESTED BLOCK_IP: IP={ip}, Reason={reason}")
            
            try:
                action_result = await defense_actions.create_defense_action(
                    DefenseActionRequest(
                        action_type="block_ip",
                        target=ip,
                        reason=reason,
                        executed_by="ai"
                    )
                )
                execution_msg = f"\n\n🛡️ **Defense Action Executed**\n- Action: Block IP\n- Target: `{ip}`\n- Reason: {reason}\n- Status: {action_result.get('status', 'pending')}"
                parts = ai_content.split("ACTION: BLOCK_IP")
                pre_text = parts[0].strip()
                ai_content = f"{pre_text}{execution_msg}"
            except Exception as exc:
                print(f"Error executing BLOCK_IP: {exc}")
                parts = ai_content.split("ACTION: BLOCK_IP")
                ai_content = f"{parts[0].strip()}\n\n[SYSTEM] Defense action failed: {exc}"
        
        # Check for UNBLOCK_IP command
        unblock_ip_match = re.search(r'ACTION: UNBLOCK_IP ip=(\S+)', ai_content)
        if unblock_ip_match:
            ip = unblock_ip_match.group(1)
            print(f"🛡️ AI REQUESTED UNBLOCK_IP: IP={ip}")
            
            try:
                action_result = await defense_actions.create_defense_action(
                    DefenseActionRequest(
                        action_type="unblock_ip",
                        target=ip,
                        reason="User/AI requested unblock",
                        executed_by="ai"
                    )
                )
                execution_msg = f"\n\n🛡️ **Defense Action Executed**\n- Action: Unblock IP\n- Target: `{ip}`\n- Status: {action_result.get('status', 'pending')}"
                parts = ai_content.split("ACTION: UNBLOCK_IP")
                pre_text = parts[0].strip()
                ai_content = f"{pre_text}{execution_msg}"
            except Exception as exc:
                print(f"Error executing UNBLOCK_IP: {exc}")
                parts = ai_content.split("ACTION: UNBLOCK_IP")
                ai_content = f"{parts[0].strip()}\n\n[SYSTEM] Defense action failed: {exc}"
        
        # Check for QUARANTINE_FILE command
        quarantine_match = re.search(r'ACTION: QUARANTINE_FILE path=(\S+)\s+reason="([^"]+)"', ai_content)
        if quarantine_match:
            path = quarantine_match.group(1)
            reason = quarantine_match.group(2)
            print(f"🛡️ AI REQUESTED QUARANTINE_FILE: Path={path}, Reason={reason}")
            
            try:
                action_result = await defense_actions.create_defense_action(
                    DefenseActionRequest(
                        action_type="quarantine_file",
                        target=path,
                        reason=reason,
                        executed_by="ai"
                    )
                )
                execution_msg = f"\n\n🛡️ **Defense Action Executed**\n- Action: Quarantine File\n- Target: `{path}`\n- Reason: {reason}\n- Status: {action_result.get('status', 'pending')}"
                parts = ai_content.split("ACTION: QUARANTINE_FILE")
                pre_text = parts[0].strip()
                ai_content = f"{pre_text}{execution_msg}"
            except Exception as exc:
                print(f"Error executing QUARANTINE_FILE: {exc}")
                parts = ai_content.split("ACTION: QUARANTINE_FILE")
                ai_content = f"{parts[0].strip()}\n\n[SYSTEM] Defense action failed: {exc}"
        
        # Check for KILL_PROCESS command
        kill_match = re.search(r'ACTION: KILL_PROCESS pid=(\d+)\s+reason="([^"]+)"', ai_content)
        if kill_match:
            pid = kill_match.group(1)
            reason = kill_match.group(2)
            print(f"🛡️ AI REQUESTED KILL_PROCESS: PID={pid}, Reason={reason}")
            
            try:
                action_result = await defense_actions.create_defense_action(
                    DefenseActionRequest(
                        action_type="kill_process",
                        target=pid,
                        reason=reason,
                        executed_by="ai"
                    )
                )
                execution_msg = f"\n\n🛡️ **Defense Action Executed**\n- Action: Kill Process\n- Target PID: `{pid}`\n- Reason: {reason}\n- Status: {action_result.get('status', 'pending')}"
                parts = ai_content.split("ACTION: KILL_PROCESS")
                pre_text = parts[0].strip()
                ai_content = f"{pre_text}{execution_msg}"
            except Exception as exc:
                print(f"Error executing KILL_PROCESS: {exc}")
                parts = ai_content.split("ACTION: KILL_PROCESS")
                ai_content = f"{parts[0].strip()}\n\n[SYSTEM] Defense action failed: {exc}"
        
        return {"response": ai_content}
            
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        try:
            error_detail = e.response.json().get("error", str(e))
        except:
            error_detail = str(e)
        
        print(f"Ollama API Error ({status_code}): {error_detail}")
        raise HTTPException(
            status_code=status_code if status_code != 404 else 400,
            detail=f"Ollama Error: {error_detail}"
        )
    except httpx.RequestError as e:
        print(f"Ollama Connection Error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Ollama Connection Error: Unable to reach model server. {str(e)}"
        )
    except Exception as e:
        print(f"Error querying Ollama: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error querying Ollama: {str(e)}"
        )

@app.get("/models")
async def list_models():
    """List available Ollama models."""
    try:
        ollama_url = f"{MODEL_SERVER_URL}/api/tags"
        response = await app.state.client.get(ollama_url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            # Extract model names
            models = [model['name'] for model in data.get('models', [])]
            return {"models": models}
        return {"models": []}
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        # Remove hardcoded fallbacks to strictly reflect Ollama state
        return {"models": []}


@app.on_event("shutdown")
async def shutdown_event():
    """Close global resources on shutdown."""
    if hasattr(app.state, "client"):
        await app.state.client.aclose()
    if hasattr(app.state, "pool"):
        await app.state.pool.close()


@app.get("/debug/prompt")
async def debug_prompt():
    """Debug endpoint to show what prompt would be sent to the AI."""
    # Fetch context same way as ask_model
    context_text = ""
    try:
        async with app.state.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT summary, category, score, created_at
                FROM detections
                ORDER BY created_at DESC
                LIMIT 10
            """)
            if rows:
                detections_list = "\n".join([f"- [{r['created_at']}] {r['category'].upper()}: {r['summary']} (Score: {r['score']})" for r in rows])
                context_text += f"\nRecent Security Detections:\n{detections_list}\n"
            else:
                context_text += "\nRecent Security Detections: None recorded.\n"
    except Exception as db_err:
        context_text += f"\nRecent Security Detections: Error: {db_err}\n"
    
    # Fetch agents
    try:
        if agents.agents:
            active_agents = [
                f"- {a['hostname']} ({a['ip_address']}): {a['status']} (Capabilities: {', '.join(a['capabilities'])})"
                for a in agents.agents.values()
            ]
            context_text += f"\nActive Agents:\n" + "\n".join(active_agents) + "\n"
        else:
            context_text += "\nActive Agents: None registered.\n"
    except Exception as e:
        context_text += f"\nActive Agents: Error: {e}\n"
    
    # Fetch scans
    try:
        if scans.scan_results:
            recent_scans = sorted(
                scans.scan_results.values(), 
                key=lambda x: x.get('start_time') or "", 
                reverse=True
            )[:5]
            
            scan_list = []
            for s in recent_scans:
                status = s.get('status', 'unknown')
                start = s.get('start_time')
                scan_list.append(f"- Scan {status} (Started: {start})")
            
            context_text += f"\nRecent Scans:\n" + "\n".join(scan_list) + "\n"
        else:
            context_text += "\nRecent Scans: None recorded.\n"
    except Exception as e:
        context_text += f"\nRecent Scans: Error: {e}\n"
    
    system_prompt = """You are a Security Analyst for A_I_Defend. Answer questions about the security status based on the information provided to you."""
    
    user_content = f"""I am the A_I_Defend security system. Here is my current state:

{context_text}

USER QUESTION: [User's question would go here]

Please answer based ONLY on the information above. If I listed specific malware files, port scans, or IDS alerts, mention those EXACT details. If sections say "None recorded", state that those areas are clean."""
    
    return {
        "context_text": context_text,
        "system_prompt": system_prompt,
        "user_content": user_content,
        "full_prompt_preview": f"SYSTEM: {system_prompt}\n\nUSER: {user_content}"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}