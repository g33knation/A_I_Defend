#!/usr/bin/env python3
"""
linux_scanner.py
- Runs a small set of scanners
- Parses key outputs
- POSTs normalized events to BACKEND_URL (/events)
"""

import os
import subprocess
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

BACKEND = os.getenv("BACKEND_URL", "http://backend:8000")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "600"))  # default 10m

def post_event(source, etype, payload):
    ev = {"source": source, "type": etype, "payload": payload}
    try:
        r = requests.post(f"{BACKEND}/events", json=ev, timeout=15)
        print(f"[POST] {source}/{etype} -> {r.status_code}")
    except Exception as e:
        print("[POST ERROR]", e)

# ---- helper: run a cmd and return stdout, stderr, exitcode
def run_cmd(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.stdout, p.stderr, p.returncode
    except Exception as e:
        return "", str(e), 1

# ---- nmap quick scan (fast) and parse XML
def scan_nmap(target="127.0.0.1"):
    xml_path = "/tmp/nmap_scan.xml"
    cmd = ["nmap", "-Pn", "-sV", "-oX", xml_path, "-F", target]  # -F fast
    stdout, stderr, rc = run_cmd(cmd, timeout=180)
    if rc != 0:
        post_event("nmap", "error", {"cmd_out": stderr})
        return

    # parse xml
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        hosts = []
        for host in root.findall("host"):
            addr = host.find("address").get("addr") if host.find("address") is not None else None
            for port in host.findall(".//port"):
                portnum = port.get("portid")
                state = port.find("state").get("state")
                svc = port.find("service").get("name") if port.find("service") is not None else None
                hosts.append({"addr": addr, "port": portnum, "state": state, "service": svc})
        post_event("nmap", "port_scan", {"target": target, "results": hosts, "scan_time": datetime.utcnow().isoformat()})
    except Exception as e:
        post_event("nmap", "parse_error", {"error": str(e)})

# ---- clamscan on path (scan mounted Windows user dir or /tmp)
def run_clamscan(paths=None):
    if paths is None:
        paths = ["/mnt/c/Users"] if Path("/mnt/c").exists() else ["/home"]
    for p in paths:
        cmd = ["clamscan", "-r", "--no-summary", p]
        out, err, rc = run_cmd(cmd, timeout=900)
        # clamscan prints lines like: /path/file: OK  OR  /path/file: Eicar-Test-Signature FOUND
        results = []
        for line in out.splitlines():
            if line.strip().endswith("FOUND"):
                parts = line.split(":")
                path = ":".join(parts[:-1]).strip()
                sig = parts[-1].replace("FOUND", "").strip()
                results.append({"file": path, "signature": sig})
        if results:
            post_event("clamav", "malware_found", {"path_scanned": p, "matches": results})
        else:
            post_event("clamav", "scan_clean", {"path_scanned": p})

# ---- YARA scan - assumes a rules dir /rules
def run_yara(rules_dir="/rules", target_dirs=None):
    if not Path(rules_dir).exists():
        return
    if target_dirs is None:
        target_dirs = ["/mnt/c/Users"] if Path("/mnt/c").exists() else ["/home"]
    for tgt in target_dirs:
        # simple recursive scan using yara CLI
        cmd = ["yara", "-r", rules_dir, tgt]
        out, err, rc = run_cmd(cmd, timeout=600)
        matches = []
        for line in out.splitlines():
            # line format: RULE /path/to/file
            try:
                rule, filepath = line.split(" ", 1)
                matches.append({"rule": rule.strip(), "file": filepath.strip()})
            except:
                continue
        if matches:
            post_event("yara", "matches", {"target": tgt, "matches": matches})

# ---- tshark short capture and basic alert rules
def run_tshark_capture(interface="any", duration=15):
    pcap_file = "/tmp/scan_capture.pcap"
    cmd = ["tshark", "-i", interface, "-a", f"duration:{duration}", "-w", pcap_file]
    out, err, rc = run_cmd(cmd, timeout=duration + 30)
    if rc != 0:
        post_event("tshark", "error", {"error": err})
        return
    # Convert pcap to JSON summary (tshark -r -T json)
    cmd2 = ["tshark", "-r", pcap_file, "-T", "json"]
    out2, err2, rc2 = run_cmd(cmd2, timeout=60)
    try:
        packets = json.loads(out2)
        # Basic heuristics: count DNS requests to rare domains, many connections to same IP, odd ports
        post_event("tshark", "pcap_summary", {"packets_count": len(packets)})
    except Exception as e:
        post_event("tshark", "parse_error", {"error": str(e)})

# ---- rkhunter / chkrootkit / lynis quick runs
def run_rkhunter():
    out, err, rc = run_cmd(["rkhunter", "--check", "--sk"], timeout=300)
    # parse relevant lines like 'Warning:' or 'infected'
    warns = [l for l in out.splitlines() if "Warning:" in l or "infected" in l.lower()]
    if warns:
        post_event("rkhunter", "warnings", {"warnings": warns})
    else:
        post_event("rkhunter", "clean", {})

def run_chkrootkit():
    out, err, rc = run_cmd(["chkrootkit"], timeout=300)
    hits = [l for l in out.splitlines() if "INFECTED" in l or "Vulnerable" in l]
    if hits:
        post_event("chkrootkit", "hits", {"hits": hits})

def run_lynis():
    out, err, rc = run_cmd(["lynis", "audit", "system", "--quiet"], timeout=600)
    suggestions = [l for l in out.splitlines() if "[WARNING]" in l or "[SUGGESTION]" in l]
    if suggestions:
        post_event("lynis", "audit_issues", {"items": suggestions})

# ---- suricata (light) - run on pcap or live when installed/configured
def run_suricata_on_pcap(pcap="/tmp/scan_capture.pcap"):
    if not Path(pcap).exists():
        return
    out, err, rc = run_cmd(["suricata", "-r", pcap, "-c", "/etc/suricata/suricata.yaml"], timeout=120)
    # suricata writes eve.json alerts; we can try to read /var/log/suricata/eve.json (if configured)
    alerts_file = "/var/log/suricata/eve.json"
    if Path(alerts_file).exists():
        try:
            with open(alerts_file) as f:
                lines = [json.loads(l) for l in f if l.strip()]
                alerts = [l for l in lines if l.get("event_type") == "alert"]
                if alerts:
                    post_event("suricata", "alerts", {"count": len(alerts), "example": alerts[:3]})
        except Exception as e:
            post_event("suricata", "parse_error", {"error": str(e)})

# ---- main loop
def main_loop():
    while True:
        print("[*] Running Linux scanner cycle", datetime.utcnow().isoformat())
        # network quick scans
        run_tshark_capture(interface="any", duration=10)
        scan_nmap(target="127.0.0.1")  # change to your target/network
        # malware / file checks
        run_clamscan()
        run_yara()
        # host integrity checks
        run_rkhunter()
        run_chkrootkit()
        run_lynis()
        # run suricata if installed and pcap available
        run_suricata_on_pcap()
        print("[*] Cycle complete, sleeping", SCAN_INTERVAL)
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main_loop()
