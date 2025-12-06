FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY base_agent.py .
COPY malware_agent.py .
COPY security_agent.py .
COPY intel_agent.py .

# Default command (overridden in docker-compose)
CMD ["python", "base_agent.py"]
