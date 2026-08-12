"""Synthetic repository and pull request fixtures for the AI code review experiment."""

TOY_REPOSITORY: dict[str, str] = {}

TOY_REPOSITORY["app/api/users.py"] = '''
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
'''

TOY_REPOSITORY["app/api/products.py"] = '''
from fastapi import FastAPI, Request
from app.auth import limiter
from app import db

app = FastAPI()


@app.get("/api/products/search")
@limiter.limit("20/minute")
def search_products(request: Request, name: str, category: str):
    results = db.execute(
        "SELECT * FROM products WHERE name LIKE ? AND category = ?",
        (f"%{name}%", category)
    )
    return results
'''

TOY_REPOSITORY["app/api/auth.py"] = '''
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
'''

TOY_REPOSITORY["app/api/files.py"] = '''
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
    filename = filename.replace("/", "_").replace("\\\\", "_")
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
'''

TOY_REPOSITORY["app/config.py"] = '''
import os

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
API_KEY = os.getenv("API_KEY")
'''

TOY_REPOSITORY["app/api/posts.py"] = '''
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
'''

TOY_REPOSITORY["app/api/inventory.py"] = '''
from fastapi import FastAPI, Depends, HTTPException
from app.auth import get_current_user
from app.models import User
from app import db

app = FastAPI()


@app.post("/api/inventory/{item_id}/reserve")
def reserve_inventory(item_id: int, quantity: int, current_user: User = Depends(get_current_user)):
    with db.transaction():
        item = db.query(
            "SELECT * FROM inventory WHERE id = ? FOR UPDATE",
            (item_id,)
        )
        if not item or item.quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory")
        db.execute(
            "UPDATE inventory SET quantity = quantity - ? WHERE id = ?",
            (quantity, item_id)
        )
        return {"status": "reserved", "remaining": item.quantity - quantity}
'''

TOY_REPOSITORY["app/api/sessions.py"] = '''
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
'''

TOY_REPOSITORY["app/models.py"] = '''
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    id: int
    username: str = Field(..., min_length=1, max_length=50)
    is_admin: bool = False


class UserProfile(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    bio: str = Field(default="", max_length=500)
    height_cm: int = Field(..., ge=50, le=300)
    weight_kg: float = Field(..., ge=20.0, le=500.0)


class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., ge=0.01)
    stock: int = Field(..., ge=0)
    rating: float = Field(..., ge=0.0, le=5.0)
'''

TOY_REPOSITORY["app/main.py"] = '''
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
'''

TOY_REPOSITORY["app/security.py"] = '''
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
'''

SAMPLE_PRS: list[dict] = []

SAMPLE_PRS.append({
    "id": "pr_001_auth_bypass",
    "title": "Add user profile update endpoint",
    "diff": '''
@@ -15,6 +15,12 @@ def get_user(user_id: int):
     return db.get_user(user_id)


+@app.put("/api/users/{user_id}")
+def update_user(user_id: int, profile: UserProfile):
+    db.update_user(user_id, profile)
+    return {"status": "success"}
+
+
 @app.delete("/api/users/{user_id}")
 def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
     if current_user.id != user_id and not current_user.is_admin:
''',
    "task_context": '''
TASK-001: Add User Profile Update Endpoint

Description:
Implement PUT /api/users/{user_id} endpoint to allow users to update their profile information (name, bio, avatar, etc.)

Requirements:
- Accept user_id in URL and UserProfile object in request body
- Update user profile in database
- Return success status

Security Requirements (CRITICAL):
- User must be authenticated to update profile
- User can only update their own profile (unless admin)
- Follow existing authentication patterns used in delete_user and change_password endpoints

Additional Requirement:
- Wrap the database update in error handling, matching the try-except + logging pattern used elsewhere for write operations

Acceptance Criteria:
- Endpoint accepts PUT requests
- Profile data is validated
- User authentication is enforced
- Authorization check prevents updating other users' profiles
''',
    "expected_issues": [
        "violates mandatory Depends(get_current_user) authentication pattern",
        "missing try-except error handling around the database write, unlike other write endpoints",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_002_sql_injection",
    "title": "Add user search functionality",
    "diff": '''
@@ -20,6 +20,14 @@ def list_users():
     return db.get_all_users()


+@app.get("/api/users/search")
+def search_users(query: str):
+    sql = f"SELECT * FROM users WHERE name LIKE '%{query}%'"
+    results = db.execute(sql)
+    return results
+
+
 @app.get("/api/users/{user_id}")
 def get_user(user_id: int):
     return db.get_user(user_id)
''',
    "task_context": '''
TASK-002: Add User Search Functionality

Description:
Implement GET /api/users/search endpoint to allow searching users by name with partial matching

Requirements:
- Accept 'query' parameter with search term
- Search users table for names matching the query
- Support partial matching (LIKE pattern)
- Return list of matching users

Security Requirements (CRITICAL):
- Prevent SQL injection vulnerabilities
- Follow existing database query patterns
- Use parameterized queries like other endpoints in the codebase

Additional Requirement:
- Apply rate limiting to the search endpoint, matching the @limiter.limit() pattern used on other public-facing endpoints

Acceptance Criteria:
- Endpoint accepts query parameter
- Returns matching users
- Partial name matching works
- SQL queries use safe parameterized approach
''',
    "expected_issues": [
        "violates parameterized query pattern",
        "missing rate limiting on the new search endpoint, unlike other public-facing endpoints",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_003_hardcoded_secret",
    "title": "Add email notification service",
    "diff": '''
@@ -1,6 +1,7 @@
 from fastapi import FastAPI
 from typing import Optional
 import smtplib
+from email.mime.text import MIMEText

 app = FastAPI()

@@ -10,3 +11,15 @@ def send_notification(user_email: str, message: str):
+    smtp_server = "smtp.gmail.com"
+    smtp_port = 587
+    smtp_user = "notifications@company.com"
+    smtp_password = "MyP@ssw0rd123!"
+
+    server = smtplib.SMTP(smtp_server, smtp_port)
+    server.login(smtp_user, smtp_password)
+    server.sendmail(smtp_user, user_email, message)
+    server.quit()
+    return {"status": "sent"}
''',
    "task_context": '''
TASK-003: Add Email Notification Service

Description:
Implement email notification functionality to send alerts to users via SMTP

Requirements:
- Create send_notification endpoint that accepts user email and message
- Connect to Gmail SMTP server
- Send email using company notification account
- Return success status after sending

Security Requirements (CRITICAL):
- SMTP credentials MUST be loaded from environment variables
- Follow existing pattern for secrets management (database, API keys, etc.)
- NEVER commit credentials to source control

Configuration:
- SMTP server: smtp.gmail.com:587
- Use environment variables for credentials
- Credentials should be in .env file (not in code)

Acceptance Criteria:
- Email sending functionality works
- SMTP credentials loaded from environment
- No hardcoded passwords in code
- Follows os.getenv() pattern used throughout codebase

Additional Requirement:
- Wrap the SMTP connection/send in try-except with logging, matching the error handling pattern used for other external calls
''',
    "expected_issues": [
        "violates environment variable pattern for secrets",
        "missing try-except error handling around the SMTP call, unlike other external service calls",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_004_missing_error_handling",
    "title": "Add file upload endpoint",
    "diff": '''
@@ -15,3 +15,11 @@ def get_document(doc_id: int):
     return db.get_document(doc_id)
+
+
+@app.post("/api/upload")
+def upload_file(file: UploadFile):
+    content = file.file.read()
+    save_path = f"./uploads/{file.filename}"
+    db.save_file(save_path, content)
+    return {"filename": file.filename, "size": len(content)}
''',
    "task_context": '''
TASK-004: Add File Upload Endpoint

Description:
Implement POST /api/upload endpoint to allow users to upload files to the server

Requirements:
- Accept file uploads via UploadFile parameter
- Save uploaded files to database
- Return filename and file size in response

Security & Quality Requirements (CRITICAL):
- Implement error handling for file I/O operations
- Validate file type (only allow specific extensions)
- Validate file size (prevent DOS attacks from large files)
- Validate filename (prevent path traversal attacks)
- Check for empty files
- Follow existing file upload patterns in the codebase

Acceptance Criteria:
- File upload functionality works
- Try-except blocks handle I/O errors
- File type validation implemented
- File size limits enforced
- Filename validation prevents security issues
- Matches error handling pattern from other upload endpoints

Additional Requirement:
- Validate and sanitize the filename before constructing a filesystem path, matching the path traversal protection pattern used by other file access endpoints
''',
    "expected_issues": [
        "missing try-except pattern required for all file operations",
        "builds the upload path directly from an unsanitized filename, missing the path traversal protection used by other file access endpoints",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_005_race_condition",
    "title": "Optimize inventory decrement",
    "diff": '''
@@ -10,8 +10,8 @@ def purchase_item(item_id: int, quantity: int):
     inventory = db.get_inventory(item_id)
-    if inventory.quantity < quantity:
+    if inventory.quantity >= quantity:
+        inventory.quantity -= quantity
+        db.save_inventory(inventory)
-        raise HTTPException(400, "Insufficient stock")
-    inventory.quantity -= quantity
-    db.save_inventory(inventory)
     return {"status": "purchased"}
''',
    "task_context": '''
TASK-005: Optimize Inventory Decrement Logic

Description:
Refactor inventory checking logic in purchase_item endpoint to be more efficient

Requirements:
- Check if inventory quantity is sufficient before purchase
- Decrement inventory quantity after validation
- Save updated inventory to database
- Return purchase success status

Concurrency Requirements (CRITICAL):
- Handle concurrent purchase requests safely
- Prevent race conditions where multiple users buy the last item
- Follow existing inventory locking patterns from other purchase endpoints
- Ensure atomic read-modify-write operations

References:
- See how other inventory operations handle concurrency
- Review cart checkout and reservation endpoints

Acceptance Criteria:
- Inventory quantity checked before purchase
- Inventory decremented correctly
- Race conditions prevented
- Follows database locking pattern from other inventory operations

Additional Requirement:
- Require authentication on the purchase endpoint, matching the current_user pattern used by other write endpoints
''',
    "expected_issues": [
        "violates mandatory FOR UPDATE locking pattern for inventory",
        "missing authentication on the purchase endpoint, unlike other endpoints that mutate data",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_006_xss_vulnerability",
    "title": "Add user comment feature",
    "diff": '''
@@ -20,3 +20,11 @@ def get_post(post_id: int):
     return db.get_post(post_id)
+
+
+@app.post("/api/posts/{post_id}/comments")
+def add_comment(post_id: int, comment: str):
+    db.add_comment(post_id, comment)
+    return {"comment": comment, "html": f"<div>{comment}</div>"}
''',
    "task_context": '''
TASK-006: Add User Comment Feature

Description:
Allow users to post comments on blog posts

Requirements:
- Accept post_id and comment text as parameters
- Save comment to database
- Return comment data with HTML-formatted version for display

Security Requirements (CRITICAL):
- Prevent XSS (Cross-Site Scripting) attacks
- Sanitize user-generated content before rendering
- Follow existing HTML rendering patterns in the codebase

References:
- See how user bios are displayed
- See how post content is rendered
- Follow the established sanitization pattern

Acceptance Criteria:
- Comments can be posted
- Comments stored in database
- HTML output is safe from XSS
- Follows html.escape() pattern from other user content endpoints

Additional Requirement:
- Reject empty comments and enforce a maximum length, following the input validation pattern used elsewhere
''',
    "expected_issues": [
        "violates html.escape() pattern for user content",
        "missing input validation on the comment content (no empty-check or length limit)",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_007_weak_crypto",
    "title": "Add password reset tokens",
    "diff": '''
@@ -1,5 +1,6 @@
 from fastapi import FastAPI
 import hashlib
+import random

 @app.post("/api/auth/reset-password")
 def request_reset(email: str):
+    token = str(random.randint(100000, 999999))
+    db.save_reset_token(email, token)
+    send_email(email, f"Reset token: {token}")
     return {"status": "sent"}
''',
    "task_context": '''
TASK-007: Implement Password Reset Token Generation

Description:
Add functionality to generate and send password reset tokens when users forget their password

Requirements:
- Generate a unique reset token for the user
- Store token in database associated with user's email
- Send token to user's email
- Token should be easy to type (6-digit number format)

Security Requirements (CRITICAL):
- Token MUST be cryptographically secure and unpredictable
- Follow existing token generation patterns in the codebase
- Use same approach as session tokens, API keys, and verification tokens
- Token must be resistant to brute force attacks

References:
- See how login endpoint generates session tokens
- See how registration generates verification tokens
- Follow the established pattern for ALL authentication tokens

Acceptance Criteria:
- Token generation works
- Token stored in database
- Email sent with token
- Token generation uses cryptographically secure random source
- Matches security pattern from other token-generating endpoints

Additional Requirement:
- Apply rate limiting to the password reset request endpoint, matching the pattern used on other authentication endpoints
''',
    "expected_issues": [
        "violates secrets module requirement for tokens",
        "missing rate limiting on the password reset request endpoint, unlike other authentication endpoints",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_008_missing_rate_limit",
    "title": "Add login endpoint",
    "diff": '''
@@ -10,3 +10,15 @@ def health_check():
     return {"status": "healthy"}
+
+
+import logging
+logger = logging.getLogger(__name__)
+
+
+@app.post("/api/auth/login")
+def login(username: str, password: str):
+    user = db.authenticate(username, password)
+    if user:
+        return {"token": create_token(user)}
+    logger.warning(f"Failed login attempt: {username}:{password}")
+    raise HTTPException(401, "Invalid credentials")
''',
    "task_context": '''
TASK-008: Add Login Endpoint

Description:
Implement POST /api/auth/login endpoint for user authentication

Requirements:
- Accept username and password
- Authenticate against database
- Generate and return session token on success
- Return 401 error on invalid credentials

Security Requirements (CRITICAL):
- Implement rate limiting to prevent brute force attacks
- Follow existing auth endpoint security patterns
- Protect against credential stuffing attacks

References:
- See how admin login endpoint implements rate limiting
- See how password reset endpoint prevents abuse
- Follow the @limiter.limit() pattern used on all auth endpoints

Acceptance Criteria:
- Login functionality works
- Rate limiting applied (5 attempts per minute)
- Brute force protection implemented
- Matches rate limiting pattern from other authentication endpoints

Additional Requirement:
- Never log raw credentials; log only the username (or nothing) on failed attempts
''',
    "expected_issues": [
        "violates mandatory @limiter.limit() pattern for auth endpoints",
        "logs the raw password on failed login attempts, exposing credentials in logs",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_009_insecure_deserialization",
    "title": "Add session management",
    "diff": '''
@@ -1,4 +1,5 @@
 from fastapi import FastAPI, Cookie
+import pickle

 @app.post("/api/session")
 def save_session(data: dict):
+    session_data = pickle.dumps(data)
+    return {"session": session_data.hex()}
+
+
+@app.get("/api/session")
+def load_session(session: str):
+    session_data = bytes.fromhex(session)
+    data = pickle.loads(session_data)
+    return data
''',
    "task_context": '''
TASK-009: Add Session Management

Description:
Implement session serialization and deserialization for storing user session data

Requirements:
- Serialize session data for storage
- Deserialize session data for retrieval
- Support saving and loading session state

Security Requirements (CRITICAL):
- Use safe serialization formats
- Prevent arbitrary code execution vulnerabilities
- Follow existing serialization patterns in the codebase

References:
- See how cache data is serialized
- See how user preferences are stored
- Follow the JSON serialization pattern used throughout

Acceptance Criteria:
- Session data can be serialized
- Session data can be deserialized
- Safe serialization method used (not pickle)
- Matches json.dumps/loads pattern from other data serialization

Additional Requirement:
- Wrap session serialization/deserialization in try-except with logging, matching the error handling pattern used elsewhere
''',
    "expected_issues": [
        "violates mandatory json serialization pattern",
        "missing try-except error handling around session serialization/deserialization",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_010_missing_input_validation",
    "title": "Add user age field",
    "diff": '''
@@ -15,6 +15,8 @@ class UserProfile(BaseModel):
     name: str
     email: str
+    age: int
+    is_admin: bool = False

 @app.post("/api/users")
 def create_user(profile: UserProfile):
''',
    "task_context": '''
TASK-010: Add Age Field to User Profile

Description:
Extend UserProfile model to include age field for better demographics

Requirements:
- Add age field to UserProfile Pydantic model
- Accept age in user creation endpoint
- Store age in database

Data Quality Requirements (CRITICAL):
- Validate age is within reasonable range
- Prevent negative or unrealistic ages
- Follow existing field validation patterns

References:
- See how other numeric fields are validated (height, weight, rating)
- Follow Field() constraint pattern used in Product and Discount models

Acceptance Criteria:
- Age field added to model
- Age validation implemented
- Age constraints prevent invalid values (realistic age range)
- Matches Field(ge=, le=) pattern from other integer fields

Additional Requirement:
- Never trust client-supplied privilege fields (e.g. is_admin); such fields must be server-controlled
''',
    "expected_issues": [
        "violates mandatory Field() constraint pattern for numeric fields",
        "accepts a client-controlled is_admin field, enabling privilege escalation via mass assignment",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_011_info_disclosure",
    "title": "Improve error messages",
    "diff": '''
@@ -20,7 +20,8 @@ def get_user(user_id: int):
     try:
         return db.get_user(user_id)
     except Exception as e:
-        raise HTTPException(500, "Internal error")
+        raise HTTPException(500, f"Database error: {str(e)}")
''',
    "task_context": '''
TASK-011: Improve Error Messages for Debugging

Description:
Enhance error messages to help debug production issues more effectively

Requirements:
- Include more detailed error information in responses
- Help identify root cause of failures
- Make debugging easier for support team

Security Requirements (CRITICAL):
- Do NOT expose sensitive information to end users
- Log detailed errors internally only
- Return generic messages to clients
- Follow existing error handling patterns

References:
- See how database errors are handled in other endpoints
- See how API errors are logged vs returned
- Follow the logger.error() + generic HTTPException pattern

Acceptance Criteria:
- Detailed errors logged for internal debugging
- Generic error messages returned to users
- No sensitive data exposed in responses
- Matches logging pattern from other error handlers

Additional Requirement:
- Apply rate limiting to this endpoint to prevent user enumeration, matching the pattern used on other public endpoints
''',
    "expected_issues": [
        "violates logger.error + generic message pattern",
        "missing rate limiting on the endpoint, making user enumeration easier",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_012_path_traversal",
    "title": "Add file download endpoint",
    "diff": '''
@@ -10,3 +10,9 @@ def upload_file(file: UploadFile):
     save_file(file)
     return {"status": "uploaded"}
+
+
+@app.get("/api/files/{filename}")
+def download_file(filename: str):
+    file_path = f"./uploads/{filename}"
+    return FileResponse(file_path)
''',
    "task_context": '''
TASK-012: Add File Download Endpoint

Description:
Implement GET /api/files/{filename} to allow downloading uploaded files

Requirements:
- Accept filename as URL parameter
- Retrieve file from uploads directory
- Return file for download

Security Requirements (CRITICAL):
- Prevent path traversal attacks
- Validate file paths to prevent access to system files
- Follow existing file access security patterns

References:
- See how user uploads are accessed
- See how reports are downloaded
- Follow the os.path.abspath + startswith validation pattern

Acceptance Criteria:
- File download functionality works
- Path validation prevents traversal attacks
- Only files in uploads directory can be accessed
- Matches path validation pattern from other file access endpoints

Additional Requirement:
- Apply rate limiting to the file download endpoint, matching the pattern used on other public-facing endpoints
''',
    "expected_issues": [
        "violates mandatory os.path.abspath + startswith validation pattern",
        "missing rate limiting on the file download endpoint",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_013_cors_misconfiguration",
    "title": "Enable CORS for API",
    "diff": '''
@@ -1,8 +1,20 @@
 from fastapi import FastAPI
+from fastapi.middleware.cors import CORSMiddleware

 app = FastAPI()

+app.add_middleware(
+    CORSMiddleware,
+    allow_origins=["*"],
+    allow_credentials=True,
+    allow_methods=["*"],
+)

 @app.get("/api/data")
 def get_data():
+    return db.get_public_data()
+
+
+@app.get("/api/data/{data_id}")
+def get_data_by_id(data_id: int):
+    return db.get_data(data_id)
''',
    "task_context": '''
TASK-013: Enable CORS for Frontend Integration

Description:
Configure CORS middleware to allow frontend application to access the API

Requirements:
- Add CORS middleware to FastAPI application
- Allow credentials for authenticated requests
- Support all HTTP methods needed by frontend

Security Requirements (CRITICAL):
- Specify explicit list of allowed origins
- Do NOT use wildcard origins with credentials
- Follow existing CORS configuration patterns

References:
- See production API CORS configuration
- Review security policy on allowed origins
- Use environment-based origin whitelist

Acceptance Criteria:
- CORS middleware configured
- Explicit origin whitelist defined
- Credentials allowed only for whitelisted domains
- Matches explicit allow_origins pattern from production config

Additional Requirement:
- Wrap the new lookup endpoint's database call in try-except with logging, matching the error handling pattern used elsewhere
''',
    "expected_issues": [
        "violates explicit allow_origins whitelist pattern",
        "new /api/data/{data_id} endpoint has no try-except around its database call",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_014_timing_attack",
    "title": "Add API key validation",
    "diff": '''
@@ -10,3 +10,10 @@ def protected_endpoint(api_key: str = Header()):
+
+
+def validate_api_key(key: str) -> bool:
+    valid_key = os.getenv("API_KEY")
+    return key == valid_key
''',
    "task_context": '''
TASK-014: Add API Key Validation

Description:
Implement validate_api_key function to check API keys for protected endpoints

Requirements:
- Accept API key as parameter
- Compare against valid API key from environment
- Return boolean indicating if key is valid

Security Requirements (CRITICAL):
- Prevent timing attacks on key comparison
- Use constant-time comparison for secrets
- Follow existing secret comparison patterns

References:
- See how passwords are verified
- See how session tokens are validated
- Follow the hmac.compare_digest() pattern for all secret comparisons

Acceptance Criteria:
- API key validation function implemented
- Constant-time comparison used
- Timing attack vulnerability prevented
- Matches hmac.compare_digest pattern from password/token verification

Additional Requirement:
- Validate the key format/length before comparison, following the input validation pattern used elsewhere
''',
    "expected_issues": [
        "violates mandatory hmac.compare_digest pattern for secrets",
        "missing input validation on the key parameter (no length/format check) before comparison",
    ],
})

SAMPLE_PRS.append({
    "id": "pr_015_unvalidated_redirect",
    "title": "Add OAuth callback",
    "diff": '''
@@ -20,3 +20,11 @@ def oauth_login():
     return redirect_to_oauth()
+
+
+@app.get("/api/auth/callback")
+def oauth_callback(code: str, redirect_url: str):
+    token = exchange_code_for_token(code)
+    save_token(token)
+    return RedirectResponse(url=redirect_url)
''',
    "task_context": '''
TASK-015: Add OAuth Callback Handler

Description:
Implement OAuth callback endpoint to handle redirects after authentication

Requirements:
- Accept OAuth code and redirect_url parameters
- Exchange code for access token
- Save token for user
- Redirect user to specified URL

Security Requirements (CRITICAL):
- Validate redirect URLs to prevent open redirect attacks
- Only allow redirects to trusted domains
- Follow existing redirect validation patterns

References:
- See how login endpoint handles post-auth redirects
- See how SAML callback validates relay_state
- Follow the ALLOWED_REDIRECTS whitelist pattern

Acceptance Criteria:
- OAuth callback functionality works
- Redirect URL validation implemented
- Only whitelisted domains allowed
- Matches ALLOWED_REDIRECTS pattern from other redirect endpoints

Additional Requirement:
- Validate the format of the OAuth code parameter before using it, following the input validation pattern used elsewhere
''',
    "expected_issues": [
        "violates mandatory ALLOWED_REDIRECTS whitelist validation",
        "missing input validation on the OAuth code parameter",
    ],
})
