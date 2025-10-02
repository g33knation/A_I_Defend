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
    libblas3 \
    liblinear4 \
    && ldconfig \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scanner code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /var/log/lynis /var/run/clamav /var/log/clamav /var/lib/clamav \
    && chown -R clamav:clamav /var/log/clamav /var/run/clamav /var/lib/clamav \
    && chmod 750 /var/log/clamav /var/run/clamav /var/lib/clamav

# Update ClamAV database as root
RUN chown -R clamav:clamav /var/lib/clamav \
    && freshclam --stdout \
    && chown -R 1000:1000 /var/log/lynis /var/run/clamav /var/log/clamav /var/lib/clamav

# Fix library symlinks manually
RUN ln -sf /usr/lib/x86_64-linux-gnu/blas/libblas.so.3 /usr/lib/x86_64-linux-gnu/libblas.so.3 \
    && ldconfig

# Don't switch to non-root user for now to avoid permission issues
# USER 1000:1000

# Default command - run as agent
CMD ["python", "-u", "/app/agent_client.py"]
