
from fastapi import FastAPI, HTTPException, Request, UploadFile
from app.auth import limiter
from app import db
import os
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "/var/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".png", ".pdf", ".txt"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    filename = filename.replace("/", "_").replace("\\", "_")
    return "".join(ch for ch in filename if ch.isalnum() or ch in "._-")


@app.post("/api/upload")
def upload_file(file: UploadFile):
    try:
        safe_name = sanitize_filename(file.filename)
        extension = os.path.splitext(safe_name)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        content = file.file.read()
        if not content or len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail="Invalid file size")

        save_path = os.path.join(UPLOAD_DIR, safe_name)
        safe_path = os.path.abspath(save_path)
        if not safe_path.startswith(os.path.abspath(UPLOAD_DIR)):
            raise HTTPException(status_code=400, detail="Invalid file path")

        db.save_file(safe_path, content)
        return {"filename": safe_name, "size": len(content)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to upload file {file.filename}: {exc}")
        raise HTTPException(status_code=500, detail="Upload failed")


@app.get("/api/downloads/{filename}")
@limiter.limit("30/minute")
def download_file(request: Request, filename: str):
    base_dir = UPLOAD_DIR
    file_path = os.path.join(base_dir, filename)
    safe_path = os.path.abspath(file_path)

    if not safe_path.startswith(os.path.abspath(base_dir)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    try:
        with open(safe_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
