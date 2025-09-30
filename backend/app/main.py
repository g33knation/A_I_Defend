import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import httpx

# Import routers
from app.routers import scans

# Create FastAPI app
app = FastAPI(title="Defense AI Backend")

# CORS configuration
origins = [
    "http://localhost:8001",
    "http://localhost:5173",
    "http://127.0.0.1:8001",
    "http://127.0.0.1:5173",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add CORS headers middleware
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    # Handle preflight requests
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        if origin in origins:
            response = Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "600",
                },
            )
            return response

    # Process the request
    response = await call_next(request)
    
    # Add CORS headers to all responses
    origin = request.headers.get("Origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "Content-Type, Authorization"
    
    return response

# Database configuration
DB_USER = "postgres"
DB_PASSWORD = "changeit"
DB_HOST = "localhost"
DB_PORT = "5432"  # Using default PostgreSQL port
DB_NAME = "defense"

# Format: postgresql://user:password@host:port/dbname
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"Connecting to database at: postgresql://{DB_USER}:******@{DB_HOST}:{DB_PORT}/{DB_NAME}")
MODEL_SERVER_URL = os.getenv("MODEL_SERVER_URL", "http://localhost:11434")

# DB pool
@app.on_event("startup")
async def startup():
    try:
        print("Attempting to connect to database...")
        app.state.pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=1,
            max_size=10,
            timeout=30.0,
            command_timeout=5.0
        )
        # Test the connection
        async with app.state.pool.acquire() as conn:
            await conn.fetch("SELECT 1")
        print("Successfully connected to the database")
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

# Schemas
class EventIn(BaseModel):
    source: str
    type: str
    payload: dict

class FeedbackIn(BaseModel):
    detection_id: int

class AskIn(BaseModel):
    query: str
    model: str = "llama2"  # Default to llama2, but can be overridden

# Endpoints
@app.get("/events", response_model=list[dict])
async def list_events():
    """List all security events."""
    try:
        async with app.state.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, source, type, payload, 
                       created_at AT TIME ZONE 'UTC' as created_at
                FROM events 
                ORDER BY created_at DESC 
                LIMIT 50
                """
            )
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events")
async def ingest_event(event: EventIn):
    """Ingest a new security event."""
    try:
        async with app.state.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO events (source, type, payload, created_at)
                VALUES ($1, $2, $3, NOW())
                """,
                event.source, event.type, event.payload
            )
        return {"status": "received", "event": event.dict()}
    except Exception as e:
        print(f"Error ingesting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include API routers
app.include_router(scans.router)

@app.get("/detections")
async def list_detections():
    """List all detections."""
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT d.*, COALESCE(json_agg(f) FILTER (WHERE f.id IS NOT NULL), '[]') as feedbacks
            FROM detections d
            LEFT JOIN detection_feedback f ON d.id = f.detection_id
            GROUP BY d.id
            ORDER BY d.created_at DESC
            LIMIT 50
        """)
    return [dict(r) for r in rows]

@app.post("/feedback")
async def submit_feedback(fb: FeedbackIn):
    async with app.state.pool.acquire() as conn:
        await conn.execute(
            "UPDATE detections SET feedback=$1 WHERE id=$2",
            fb.feedback, fb.detection_id
        )
    return {"status": "ok"}

@app.post("/ask")
async def ask_model(req: AskIn):
    """Send a query to Ollama and return the response."""
    try:
        async with httpx.AsyncClient() as client:
            # Call Ollama's API with the specified model
            ollama_url = "http://localhost:11434/api/generate"
            payload = {
                "model": req.model,  # Use the model from the request
                "prompt": req.query,
                "stream": False
            }
            
            response = await client.post(
                ollama_url,
                json=payload,
                timeout=60.0  # Increased timeout for model inference
            )
            response.raise_for_status()
            result = response.json()
            
            return {"response": result.get("response", "")}
            
    except Exception as e:
        print(f"Error querying Ollama: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error querying Ollama: {str(e)}"
        )