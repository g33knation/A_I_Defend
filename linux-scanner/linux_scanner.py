import os, time, requests, random

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

events = [
    {"source": "linux-scanner", "type": "file", "payload": {"file": "/tmp/test1", "status": "clean"}},
    {"source": "linux-scanner", "type": "file", "payload": {"file": "/tmp/test2", "status": "infected"}},
]

while True:
    ev = random.choice(events)
    try:
        r = requests.post(f"{BACKEND_URL}/events", json=ev)
        print("Sent event:", r.json())
    except Exception as e:
        print("Error sending event:", e)
    time.sleep(10)
