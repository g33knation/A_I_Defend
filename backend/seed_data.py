import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
import random

DB_USER = "postgres"
DB_PASSWORD = "changeit"
DB_HOST = "db"
DB_PORT = "5432"
DB_NAME = "defense"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def seed_data():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print("Connected. Seeding data...")

    # Sample events
    events = [
        {
            "source": "network-intel",
            "type": "port_scan",
            "payload": {"details": {"ports": [22, 80, 443, 3389], "address": "192.168.1.105"}},
            "offset": 10
        },
        {
            "source": "malware-scanner",
            "type": "malware_detected",
            "payload": {"details": {"infected_files": ["/tmp/suspicious.sh", "/home/user/download.exe"]}},
            "offset": 45
        },
        {
            "source": "security-scanner",
            "type": "lynis_scan",
            "payload": {"details": {"warnings": [{"message": "SSH root login allowed"}, {"message": "Firewall disabled"}]}},
            "offset": 120
        },
        {
            "source": "network-intel",
            "type": "ids_alert",
            "payload": {"details": {"alerts": [{"signature": "ET SCAN Potential SSH Brute Force"}]}},
            "offset": 5
        },
        {
            "source": "system-monitor",
            "type": "auth_failure",
            "payload": {"user": "admin", "ip": "10.0.0.50"},
            "offset": 2
        }
    ]

    for evt in events:
        # Insert Event
        created_at = datetime.utcnow() - timedelta(minutes=evt["offset"])
        event_id = await conn.fetchval(
            """
            INSERT INTO events (source, type, payload, created_at)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            evt["source"], evt["type"], json.dumps(evt["payload"]), created_at
        )
        print(f"Inserted event {event_id}")

        # Insert Detection (simulating the backend logic)
        summary = f"{evt['source']}: {evt['type']}"
        score = 0.5
        category = "unknown"
        
        if evt['type'] == 'malware_detected':
            summary = "Malware detected: /tmp/suspicious.sh, /home/user/download.exe"
            score = 0.9
            category = "malware"
        elif evt['type'] == 'port_scan':
            summary = "Port scan on 192.168.1.105: 22, 80, 443, 3389"
            score = 0.3
            category = "reconnaissance"
        elif evt['type'] == 'lynis_scan':
            summary = "Security warnings: SSH root login allowed; Firewall disabled"
            score = 0.6
            category = "vulnerability"
        elif evt['type'] == 'ids_alert':
            summary = "IDS alerts: ET SCAN Potential SSH Brute Force"
            score = 0.85
            category = "intrusion"

        await conn.execute(
            """
            INSERT INTO detections (event_id, summary, score, adjusted_score, category, ai_output, created_at)
            VALUES ($1, $2, $3, $3, $4, $5, $6)
            """,
            event_id, summary, score, category, json.dumps(evt["payload"]), created_at
        )
        print(f"Inserted detection for event {event_id}")

    await conn.close()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
