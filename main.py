from fastapi import FastAPI, Depends
from pydantic import BaseModel
import asyncpg
import httpx
import os
import json

app = FastAPI(title="Defense AI Backend")

# Database and Model Server URLs
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://defender:changeit@a_i_defend-postgres-1:5432/defense"
)
MODEL_SERVER_URL = os.getenv("MODEL_SERVER_URL", "http://model-server:11434")

# DB pool
@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)

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
    feedback: str  # "false_positive" | "confirmed_threat"

class AskIn(BaseModel):
    query: str

# Endpoints
@app.post("/events")
async def ingest_event(event: EventIn):
    try:
        payload_json = json.dumps(event.payload)
    except TypeError:
        return {"error": "Payload must be JSON-serializable"}

    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO events (source, type, payload) VALUES ($1, $2, $3) RETURNING *",
            event.source,
            event.type,
            payload_json
        )
    return {"event_id": row["id"]}

@app.get("/detections")
async def list_detections():
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM detections ORDER BY created_at DESC LIMIT 50")
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
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{MODEL_SERVER_URL}/ask", json={"query": req.query})
    return r.json()
