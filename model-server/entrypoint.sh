#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
pid=$!

# Wait for Ollama to start.
echo "Waiting for Ollama to start..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done

echo "Ollama started!"

# Pull models
echo "Pulling hermes3..."
ollama pull hermes3

echo "Pulling llama3.2..."
ollama pull llama3.2

echo "Models pulled!"

# Wait for the Ollama process to finish.
wait $pid
