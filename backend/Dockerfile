FROM python:3.11-slim

# Install PostgreSQL client and Docker CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz -o docker.tgz \
    && tar -xzf docker.tgz --strip-components=1 -C /usr/local/bin docker/docker \
    && rm docker.tgz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app /app/app

# Copy initialization script
COPY app/init.sql /app/init.sql

# Create a startup script
RUN echo '#!/bin/bash\n\
# Wait for PostgreSQL to be ready\nuntil PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; do\n  echo "Waiting for PostgreSQL to be ready..."\n  sleep 1\ndone\n\n# Initialize the database\n\
echo "Initializing database..."\n\
PG_PASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f /app/init.sql\n\n# Start the application\nexec uvicorn app.main:app --host 0.0.0.0 --port 8000\n' > /app/startup.sh \
    && chmod +x /app/startup.sh

# Set environment variables
ENV DB_HOST=db
ENV DB_USER=postgres
ENV DB_PASSWORD=changeit
ENV DB_NAME=defense

# Run the startup script
CMD ["/bin/bash", "/app/startup.sh"]