
from fastapi import FastAPI, Depends, HTTPException
from app.auth import get_current_user
from app.models import User
from app import db
import html

app = FastAPI()


@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    return db.get_post(post_id)


@app.post("/api/posts")
def create_post(content: str, current_user: User = Depends(get_current_user)):
    if not content or len(content) > 5000:
        raise HTTPException(status_code=400, detail="Invalid post content")
    safe_content = html.escape(content)
    return db.create_post(user_id=current_user.id, content=safe_content)


@app.post("/api/posts/{post_id}/comments")
def create_comment(post_id: int, content: str, current_user: User = Depends(get_current_user)):
    if not content or len(content) > 1000:
        raise HTTPException(status_code=400, detail="Invalid comment content")
    safe_content = html.escape(content)
    db.add_comment(post_id=post_id, user_id=current_user.id, content=safe_content)
    return {"status": "created", "content": safe_content}
