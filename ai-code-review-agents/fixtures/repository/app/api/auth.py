
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.auth import limiter, verify_password
from app import db
import secrets
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

ALLOWED_REDIRECTS = [
    "https://app.company.com",
    "https://app.company.com/dashboard",
    "https://www.company.com",
]


@app.post("/api/auth/login")
@limiter.limit("5/minute")
def login(request: Request, username: str, password: str):
    user = db.get_user_by_username(username)
    if not user or not verify_password(password, user.password_hash):
        logger.warning(f"Failed login attempt for username={username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_urlsafe(32)
    db.save_session(user.id, token)
    return {"token": token}


@app.post("/api/auth/reset-password")
@limiter.limit("3/minute")
def request_password_reset(request: Request, email: str):
    token = secrets.token_urlsafe(32)
    db.save_reset_token(email, token)
    db.enqueue_password_reset_email(email, token)
    return {"status": "sent"}


@app.get("/api/oauth/callback")
@limiter.limit("10/minute")
def oauth_callback(request: Request, code: str, redirect_url: str = "https://app.company.com"):
    if not code or len(code) < 16:
        raise HTTPException(status_code=400, detail="Invalid OAuth code")

    token = db.exchange_oauth_code(code)
    db.save_session(token.user_id, token.value)
    if redirect_url not in ALLOWED_REDIRECTS:
        raise HTTPException(status_code=400, detail="Invalid redirect URL")
    return RedirectResponse(url=redirect_url)
