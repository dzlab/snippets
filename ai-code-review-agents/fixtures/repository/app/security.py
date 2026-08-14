
from fastapi import HTTPException
import hmac
import logging
import os

logger = logging.getLogger(__name__)


def validate_api_key(key: str) -> bool:
    valid_key = os.getenv("API_KEY")
    if not key or not valid_key or len(key) != len(valid_key):
        return False
    return hmac.compare_digest(key, valid_key)


def raise_generic_server_error(message: str, exc: Exception):
    logger.error(f"{message}: {exc}")
    raise HTTPException(status_code=500, detail="Internal server error")
