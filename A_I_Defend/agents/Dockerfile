FROM python:3.11-slim

# Install tshark and dependencies
RUN apt-get update && apt-get install -y \
    tshark \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY network_monitor_agent.py .

# Make the script executable
RUN chmod +x network_monitor_agent.py

# Run as root to allow network capture (required for tshark)
# In production, consider using capabilities instead
CMD ["python", "-u", "network_monitor_agent.py"]
