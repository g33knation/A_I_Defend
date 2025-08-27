# Agentic RAG System

## Installation

1. Create a virtual environment (recommended) and install dependencies:
   ```bash
   python -m venv .venv
   .venv/Scripts/Activate.ps1   # PowerShell on Windows
   pip install -r requirements.txt
   ```

## Usage

This project uses Ollama for embeddings and chat, and includes local FastAPI memory services.

### 1) Pull models in Ollama
- We will use LLMs: `hermes3`, `qwen3`
- We will use embeddings: `nomic-embed-text`

```powershell
ollama pull hermes3
ollama pull qwen3
ollama pull nomic-embed-text
```

If `ollama` is not on PATH, set `OLLAMA_CMD` to the full path (e.g., `C:\Program Files\Ollama\ollama.exe`).

### 2) Set environment variables (PowerShell)
```powershell
$env:USE_OLLAMA_CLI = "true"               # Prefer CLI on Windows
$env:LLM_MODELS = "hermes3,qwen3"          # Multi-model fallback order
$env:EMBED_MODEL = "nomic-embed-text"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434" # If using HTTP
$env:ADMIN_TOKEN = "super-secret"           # Writer auth token
```

### 3) Run memory services
Open two terminals and run:

```powershell
uvicorn memory_writer:app --host 127.0.0.1 --port 8049 --reload
```

```powershell
uvicorn memory_reader:app --host 127.0.0.1 --port 8050 --reload
```

Health checks:
```powershell
Invoke-RestMethod http://127.0.0.1:8049/health
Invoke-RestMethod http://127.0.0.1:8050/health
```

Optionally seed a memory via writer:
```powershell
$headers = @{ Authorization = "Bearer $env:ADMIN_TOKEN" }
$body = @{ text = "Paris is the capital of France."; role = "assistant"; meta = @{ source="seed" } } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8049/propose -Headers $headers -ContentType 'application/json' -Body $body
```

### 4) Run the agent
```powershell
.venv\Scripts\python.exe agent.py
```

### 5) Run the Web Fetch UI (optional)
A small FastAPI server is provided to interactively test `tool_fetch_url` from your browser.

```powershell
uvicorn ui_server:app --host 127.0.0.1 --port 8048 --reload
```

Alternatively, run directly with environment-configurable host/port:

```powershell
$env:UI_HOST = "127.0.0.1"; $env:UI_PORT = "8048"
.venv\Scripts\python.exe ui_server.py
```

Then open http://127.0.0.1:8048 and paste any URL to fetch. Options let you toggle the Jina Reader fallback and debug logs.

## Configuration

- The system uses ports 8048 (UI), 8050 (reader), and 8049 (writer)
- Make sure Ollama is running on port 11434 for embeddings and LLM services
- If services are not available, the system will use fallback implementations

Environment variables (with defaults):
- `LLM_MODELS` = `hermes3,qwen3`
- `LLM_MODEL` = `llama3.1` (appended to candidates if not in `LLM_MODELS`)
- `EMBED_MODEL` = `nomic-embed-text`
- `USE_OLLAMA_CLI` = `false` (set `true` on Windows to prefer CLI)
- `OLLAMA_CMD` = `ollama`
- `OLLAMA_BASE_URL` = `http://127.0.0.1:11434`
- `ADMIN_TOKEN` = `super-secret`

Notes:
- `agent.py` tries Ollama CLI first (if enabled), then `/api/chat`, then `/api/generate`.
- Planner expects JSON-only outputs; we request `format: "json"` with Ollama HTTP.
