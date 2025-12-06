FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app /app/app
COPY app/init.sql /app/init.sql

# Create entrypoint script
RUN echo '#!/bin/bash\n\
    echo "Initializing database..."\n\
    # Wait for DB to be ready is handled by docker-compose depends_on\n\
    \n\
    echo "Starting backend..."\n\
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload\n\
    ' > /entrypoint.sh && chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
