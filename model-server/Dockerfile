FROM ollama/ollama:latest

# Install curl for the entrypoint script
RUN apt-get update && apt-get install -y curl

COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh
RUN chmod +x /entrypoint.sh


ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]