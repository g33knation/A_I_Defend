FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 python3-pip wget gnupg2 apt-transport-https lsb-release \
    nmap clamav clamav-daemon clamav-freshclam \
    tshark suricata rkhunter chkrootkit lynis yara \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Allow pip packages
RUN pip3 install requests

# Update ClamAV DB at build/run time (but freshclam may need manual)
RUN sed -i 's/^Example/#Example/' /etc/clamav/freshclam.conf || true

WORKDIR /app
COPY linux_scanner.py /app/linux_scanner.py
RUN chmod +x /app/linux_scanner.py

# default scan interval env
ENV SCAN_INTERVAL=600
CMD ["python3","/app/linux_scanner.py"]
