FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    nmap \
    lynis \
    clamav \
    clamav-daemon \
    clamav-freshclam \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scanner code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /var/log/lynis /var/run/clamav /var/log/clamav \
    && chown -R 1000:1000 /var/log/lynis /var/run/clamav /var/log/clamav

# Update ClamAV database
RUN freshclam

# Switch to non-root user
USER 1000:1000

# Default command (will be overridden by docker-compose)
CMD ["python", "-m", "http.server", "8000"]
