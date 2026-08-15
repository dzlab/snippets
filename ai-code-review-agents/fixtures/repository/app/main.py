
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app import db
import logging
import os

app = FastAPI()
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://app.company.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/api/data/{data_id}")
def get_data_by_id(data_id: int):
    try:
        return db.get_data(data_id)
    except DatabaseError as exc:
        logger.error(f"Failed to load data {data_id}: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")
