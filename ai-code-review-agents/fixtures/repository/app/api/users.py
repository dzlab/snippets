
from fastapi import FastAPI, Depends, HTTPException
from app.auth import get_current_user
from app.models import User, UserProfile
from app import db
import logging

app = FastAPI()
logger = logging.getLogger(__name__)


@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return db.get_user(user_id)


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized")
    db.delete_user(user_id)
    return {"status": "deleted"}


@app.post("/api/users/{user_id}/email")
def update_email(user_id: int, new_email: str, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot modify other users")
    try:
        db.update_user_email(user_id, new_email)
        return {"status": "updated"}
    except DatabaseError as exc:
        logger.error(f"Failed to update email for user {user_id}: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")
