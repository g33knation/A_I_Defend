from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Model Server Stub")

class AskIn(BaseModel):
    query: str

@app.post("/ask")
def ask(req: AskIn):
    # Dummy scoring logic
    return {
        "response": f"Stub model thinks: '{req.query}'",
        "score": 0.42
    }
