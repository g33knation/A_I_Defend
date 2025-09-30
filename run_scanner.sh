#!/bin/bash

# Create necessary directories
mkdir -p test_scan/results

# Get the host's IP address (works on Linux)
HOST_IP=$(ip route | grep default | awk '{print $3}')

# For Windows/macOS, use host.docker.internal
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "cygwin"* ]]; then
    HOST_IP="host.docker.internal"
fi

echo "Starting scanner container..."
echo "Scanning host IP: $HOST_IP"

# Build and run the scanner container
docker-compose -f docker-compose.scanner.yml build
docker-compose -f docker-compose.scanner.yml up --force-recreate -d

echo "Scanner container started in the background."
echo "To view logs: docker logs -f a_i_defend_scanner"
echo "Results will be saved to: test_scan/scan_results.json"

# Wait a moment for the container to start
sleep 5

# Follow the logs
docker logs -f a_i_defend_scanner
