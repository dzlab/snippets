
from fastapi import FastAPI, HTTPException
import json
import logging

app = FastAPI()
logger = logging.getLogger(__name__)


@app.post("/api/session")
def save_session(data: dict):
    try:
        return {"session": json.dumps(data)}
    except (TypeError, ValueError) as exc:
        logger.error(f"Failed to serialize session: {exc}")
        raise HTTPException(status_code=400, detail="Invalid session data")


@app.get("/api/session")
def load_session(session: str):
    try:
        return json.loads(session)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to deserialize session: {exc}")
        raise HTTPException(status_code=400, detail="Invalid session data")
