"""Synthetic repository and pull request fixtures for the AI code review experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"
REPOSITORY_FIXTURE_ROOT = FIXTURE_ROOT / "repository"
PR_DIFF_ROOT = FIXTURE_ROOT / "prs"


def load_repository(root: Path = REPOSITORY_FIXTURE_ROOT) -> dict[str, str]:
    """Load the synthetic repository from fixture files keyed by repository-relative path."""
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


SAMPLE_PR_METADATA: list[dict[str, Any]] = [
    {'id': 'pr_001_auth_bypass',
     'title': 'Add user profile update endpoint',
     'task_context': '\n'
                     'TASK-001: Add User Profile Update Endpoint\n'
                     '\n'
                     'Description:\n'
                     'Implement PUT /api/users/{user_id} endpoint to allow users to update their '
                     'profile information (name, bio, avatar, etc.)\n'
                     '\n'
                     'Requirements:\n'
                     '- Accept user_id in URL and UserProfile object in request body\n'
                     '- Update user profile in database\n'
                     '- Return success status\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- User must be authenticated to update profile\n'
                     '- User can only update their own profile (unless admin)\n'
                     '- Follow existing authentication patterns used in delete_user and '
                     'change_password endpoints\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Wrap the database update in error handling, matching the try-except + logging '
                     'pattern used elsewhere for write operations\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Endpoint accepts PUT requests\n'
                     '- Profile data is validated\n'
                     '- User authentication is enforced\n'
                     "- Authorization check prevents updating other users' profiles\n",
     'expected_issues': ['violates mandatory Depends(get_current_user) authentication pattern',
                         'missing try-except error handling around the database write, unlike other '
                         'write endpoints'],
     'diff_file': 'pr_001_auth_bypass.diff'},
    {'id': 'pr_002_sql_injection',
     'title': 'Add user search functionality',
     'task_context': '\n'
                     'TASK-002: Add User Search Functionality\n'
                     '\n'
                     'Description:\n'
                     'Implement GET /api/users/search endpoint to allow searching users by name with '
                     'partial matching\n'
                     '\n'
                     'Requirements:\n'
                     "- Accept 'query' parameter with search term\n"
                     '- Search users table for names matching the query\n'
                     '- Support partial matching (LIKE pattern)\n'
                     '- Return list of matching users\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Prevent SQL injection vulnerabilities\n'
                     '- Follow existing database query patterns\n'
                     '- Use parameterized queries like other endpoints in the codebase\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Apply rate limiting to the search endpoint, matching the @limiter.limit() '
                     'pattern used on other public-facing endpoints\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Endpoint accepts query parameter\n'
                     '- Returns matching users\n'
                     '- Partial name matching works\n'
                     '- SQL queries use safe parameterized approach\n',
     'expected_issues': ['violates parameterized query pattern',
                         'missing rate limiting on the new search endpoint, unlike other public-facing '
                         'endpoints'],
     'diff_file': 'pr_002_sql_injection.diff'},
    {'id': 'pr_003_hardcoded_secret',
     'title': 'Add email notification service',
     'task_context': '\n'
                     'TASK-003: Add Email Notification Service\n'
                     '\n'
                     'Description:\n'
                     'Implement email notification functionality to send alerts to users via SMTP\n'
                     '\n'
                     'Requirements:\n'
                     '- Create send_notification endpoint that accepts user email and message\n'
                     '- Connect to Gmail SMTP server\n'
                     '- Send email using company notification account\n'
                     '- Return success status after sending\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- SMTP credentials MUST be loaded from environment variables\n'
                     '- Follow existing pattern for secrets management (database, API keys, etc.)\n'
                     '- NEVER commit credentials to source control\n'
                     '\n'
                     'Configuration:\n'
                     '- SMTP server: smtp.gmail.com:587\n'
                     '- Use environment variables for credentials\n'
                     '- Credentials should be in .env file (not in code)\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Email sending functionality works\n'
                     '- SMTP credentials loaded from environment\n'
                     '- No hardcoded passwords in code\n'
                     '- Follows os.getenv() pattern used throughout codebase\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Wrap the SMTP connection/send in try-except with logging, matching the error '
                     'handling pattern used for other external calls\n',
     'expected_issues': ['violates environment variable pattern for secrets',
                         'missing try-except error handling around the SMTP call, unlike other '
                         'external service calls'],
     'diff_file': 'pr_003_hardcoded_secret.diff'},
    {'id': 'pr_004_missing_error_handling',
     'title': 'Add file upload endpoint',
     'task_context': '\n'
                     'TASK-004: Add File Upload Endpoint\n'
                     '\n'
                     'Description:\n'
                     'Implement POST /api/upload endpoint to allow users to upload files to the '
                     'server\n'
                     '\n'
                     'Requirements:\n'
                     '- Accept file uploads via UploadFile parameter\n'
                     '- Save uploaded files to database\n'
                     '- Return filename and file size in response\n'
                     '\n'
                     'Security & Quality Requirements (CRITICAL):\n'
                     '- Implement error handling for file I/O operations\n'
                     '- Validate file type (only allow specific extensions)\n'
                     '- Validate file size (prevent DOS attacks from large files)\n'
                     '- Validate filename (prevent path traversal attacks)\n'
                     '- Check for empty files\n'
                     '- Follow existing file upload patterns in the codebase\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- File upload functionality works\n'
                     '- Try-except blocks handle I/O errors\n'
                     '- File type validation implemented\n'
                     '- File size limits enforced\n'
                     '- Filename validation prevents security issues\n'
                     '- Matches error handling pattern from other upload endpoints\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Validate and sanitize the filename before constructing a filesystem path, '
                     'matching the path traversal protection pattern used by other file access '
                     'endpoints\n',
     'expected_issues': ['missing try-except pattern required for all file operations',
                         'builds the upload path directly from an unsanitized filename, missing the '
                         'path traversal protection used by other file access endpoints'],
     'diff_file': 'pr_004_missing_error_handling.diff'},
    {'id': 'pr_005_race_condition',
     'title': 'Optimize inventory decrement',
     'task_context': '\n'
                     'TASK-005: Optimize Inventory Decrement Logic\n'
                     '\n'
                     'Description:\n'
                     'Refactor inventory checking logic in purchase_item endpoint to be more '
                     'efficient\n'
                     '\n'
                     'Requirements:\n'
                     '- Check if inventory quantity is sufficient before purchase\n'
                     '- Decrement inventory quantity after validation\n'
                     '- Save updated inventory to database\n'
                     '- Return purchase success status\n'
                     '\n'
                     'Concurrency Requirements (CRITICAL):\n'
                     '- Handle concurrent purchase requests safely\n'
                     '- Prevent race conditions where multiple users buy the last item\n'
                     '- Follow existing inventory locking patterns from other purchase endpoints\n'
                     '- Ensure atomic read-modify-write operations\n'
                     '\n'
                     'References:\n'
                     '- See how other inventory operations handle concurrency\n'
                     '- Review cart checkout and reservation endpoints\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Inventory quantity checked before purchase\n'
                     '- Inventory decremented correctly\n'
                     '- Race conditions prevented\n'
                     '- Follows database locking pattern from other inventory operations\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Require authentication on the purchase endpoint, matching the current_user '
                     'pattern used by other write endpoints\n',
     'expected_issues': ['violates mandatory FOR UPDATE locking pattern for inventory',
                         'missing authentication on the purchase endpoint, unlike other endpoints that '
                         'mutate data'],
     'diff_file': 'pr_005_race_condition.diff'},
    {'id': 'pr_006_xss_vulnerability',
     'title': 'Add user comment feature',
     'task_context': '\n'
                     'TASK-006: Add User Comment Feature\n'
                     '\n'
                     'Description:\n'
                     'Allow users to post comments on blog posts\n'
                     '\n'
                     'Requirements:\n'
                     '- Accept post_id and comment text as parameters\n'
                     '- Save comment to database\n'
                     '- Return comment data with HTML-formatted version for display\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Prevent XSS (Cross-Site Scripting) attacks\n'
                     '- Sanitize user-generated content before rendering\n'
                     '- Follow existing HTML rendering patterns in the codebase\n'
                     '\n'
                     'References:\n'
                     '- See how user bios are displayed\n'
                     '- See how post content is rendered\n'
                     '- Follow the established sanitization pattern\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Comments can be posted\n'
                     '- Comments stored in database\n'
                     '- HTML output is safe from XSS\n'
                     '- Follows html.escape() pattern from other user content endpoints\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Reject empty comments and enforce a maximum length, following the input '
                     'validation pattern used elsewhere\n',
     'expected_issues': ['violates html.escape() pattern for user content',
                         'missing input validation on the comment content (no empty-check or length '
                         'limit)'],
     'diff_file': 'pr_006_xss_vulnerability.diff'},
    {'id': 'pr_007_weak_crypto',
     'title': 'Add password reset tokens',
     'task_context': '\n'
                     'TASK-007: Implement Password Reset Token Generation\n'
                     '\n'
                     'Description:\n'
                     'Add functionality to generate and send password reset tokens when users forget '
                     'their password\n'
                     '\n'
                     'Requirements:\n'
                     '- Generate a unique reset token for the user\n'
                     "- Store token in database associated with user's email\n"
                     "- Send token to user's email\n"
                     '- Token should be easy to type (6-digit number format)\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Token MUST be cryptographically secure and unpredictable\n'
                     '- Follow existing token generation patterns in the codebase\n'
                     '- Use same approach as session tokens, API keys, and verification tokens\n'
                     '- Token must be resistant to brute force attacks\n'
                     '\n'
                     'References:\n'
                     '- See how login endpoint generates session tokens\n'
                     '- See how registration generates verification tokens\n'
                     '- Follow the established pattern for ALL authentication tokens\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Token generation works\n'
                     '- Token stored in database\n'
                     '- Email sent with token\n'
                     '- Token generation uses cryptographically secure random source\n'
                     '- Matches security pattern from other token-generating endpoints\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Apply rate limiting to the password reset request endpoint, matching the '
                     'pattern used on other authentication endpoints\n',
     'expected_issues': ['violates secrets module requirement for tokens',
                         'missing rate limiting on the password reset request endpoint, unlike other '
                         'authentication endpoints'],
     'diff_file': 'pr_007_weak_crypto.diff'},
    {'id': 'pr_008_missing_rate_limit',
     'title': 'Add login endpoint',
     'task_context': '\n'
                     'TASK-008: Add Login Endpoint\n'
                     '\n'
                     'Description:\n'
                     'Implement POST /api/auth/login endpoint for user authentication\n'
                     '\n'
                     'Requirements:\n'
                     '- Accept username and password\n'
                     '- Authenticate against database\n'
                     '- Generate and return session token on success\n'
                     '- Return 401 error on invalid credentials\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Implement rate limiting to prevent brute force attacks\n'
                     '- Follow existing auth endpoint security patterns\n'
                     '- Protect against credential stuffing attacks\n'
                     '\n'
                     'References:\n'
                     '- See how admin login endpoint implements rate limiting\n'
                     '- See how password reset endpoint prevents abuse\n'
                     '- Follow the @limiter.limit() pattern used on all auth endpoints\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Login functionality works\n'
                     '- Rate limiting applied (5 attempts per minute)\n'
                     '- Brute force protection implemented\n'
                     '- Matches rate limiting pattern from other authentication endpoints\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Never log raw credentials; log only the username (or nothing) on failed '
                     'attempts\n',
     'expected_issues': ['violates mandatory @limiter.limit() pattern for auth endpoints',
                         'logs the raw password on failed login attempts, exposing credentials in '
                         'logs'],
     'diff_file': 'pr_008_missing_rate_limit.diff'},
    {'id': 'pr_009_insecure_deserialization',
     'title': 'Add session management',
     'task_context': '\n'
                     'TASK-009: Add Session Management\n'
                     '\n'
                     'Description:\n'
                     'Implement session serialization and deserialization for storing user session '
                     'data\n'
                     '\n'
                     'Requirements:\n'
                     '- Serialize session data for storage\n'
                     '- Deserialize session data for retrieval\n'
                     '- Support saving and loading session state\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Use safe serialization formats\n'
                     '- Prevent arbitrary code execution vulnerabilities\n'
                     '- Follow existing serialization patterns in the codebase\n'
                     '\n'
                     'References:\n'
                     '- See how cache data is serialized\n'
                     '- See how user preferences are stored\n'
                     '- Follow the JSON serialization pattern used throughout\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Session data can be serialized\n'
                     '- Session data can be deserialized\n'
                     '- Safe serialization method used (not pickle)\n'
                     '- Matches json.dumps/loads pattern from other data serialization\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Wrap session serialization/deserialization in try-except with logging, '
                     'matching the error handling pattern used elsewhere\n',
     'expected_issues': ['violates mandatory json serialization pattern',
                         'missing try-except error handling around session '
                         'serialization/deserialization'],
     'diff_file': 'pr_009_insecure_deserialization.diff'},
    {'id': 'pr_010_missing_input_validation',
     'title': 'Add user age field',
     'task_context': '\n'
                     'TASK-010: Add Age Field to User Profile\n'
                     '\n'
                     'Description:\n'
                     'Extend UserProfile model to include age field for better demographics\n'
                     '\n'
                     'Requirements:\n'
                     '- Add age field to UserProfile Pydantic model\n'
                     '- Accept age in user creation endpoint\n'
                     '- Store age in database\n'
                     '\n'
                     'Data Quality Requirements (CRITICAL):\n'
                     '- Validate age is within reasonable range\n'
                     '- Prevent negative or unrealistic ages\n'
                     '- Follow existing field validation patterns\n'
                     '\n'
                     'References:\n'
                     '- See how other numeric fields are validated (height, weight, rating)\n'
                     '- Follow Field() constraint pattern used in Product and Discount models\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Age field added to model\n'
                     '- Age validation implemented\n'
                     '- Age constraints prevent invalid values (realistic age range)\n'
                     '- Matches Field(ge=, le=) pattern from other integer fields\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Never trust client-supplied privilege fields (e.g. is_admin); such fields must '
                     'be server-controlled\n',
     'expected_issues': ['violates mandatory Field() constraint pattern for numeric fields',
                         'accepts a client-controlled is_admin field, enabling privilege escalation '
                         'via mass assignment'],
     'diff_file': 'pr_010_missing_input_validation.diff'},
    {'id': 'pr_011_info_disclosure',
     'title': 'Improve error messages',
     'task_context': '\n'
                     'TASK-011: Improve Error Messages for Debugging\n'
                     '\n'
                     'Description:\n'
                     'Enhance error messages to help debug production issues more effectively\n'
                     '\n'
                     'Requirements:\n'
                     '- Include more detailed error information in responses\n'
                     '- Help identify root cause of failures\n'
                     '- Make debugging easier for support team\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Do NOT expose sensitive information to end users\n'
                     '- Log detailed errors internally only\n'
                     '- Return generic messages to clients\n'
                     '- Follow existing error handling patterns\n'
                     '\n'
                     'References:\n'
                     '- See how database errors are handled in other endpoints\n'
                     '- See how API errors are logged vs returned\n'
                     '- Follow the logger.error() + generic HTTPException pattern\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- Detailed errors logged for internal debugging\n'
                     '- Generic error messages returned to users\n'
                     '- No sensitive data exposed in responses\n'
                     '- Matches logging pattern from other error handlers\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Apply rate limiting to this endpoint to prevent user enumeration, matching the '
                     'pattern used on other public endpoints\n',
     'expected_issues': ['violates logger.error + generic message pattern',
                         'missing rate limiting on the endpoint, making user enumeration easier'],
     'diff_file': 'pr_011_info_disclosure.diff'},
    {'id': 'pr_012_path_traversal',
     'title': 'Add file download endpoint',
     'task_context': '\n'
                     'TASK-012: Add File Download Endpoint\n'
                     '\n'
                     'Description:\n'
                     'Implement GET /api/files/{filename} to allow downloading uploaded files\n'
                     '\n'
                     'Requirements:\n'
                     '- Accept filename as URL parameter\n'
                     '- Retrieve file from uploads directory\n'
                     '- Return file for download\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Prevent path traversal attacks\n'
                     '- Validate file paths to prevent access to system files\n'
                     '- Follow existing file access security patterns\n'
                     '\n'
                     'References:\n'
                     '- See how user uploads are accessed\n'
                     '- See how reports are downloaded\n'
                     '- Follow the os.path.abspath + startswith validation pattern\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- File download functionality works\n'
                     '- Path validation prevents traversal attacks\n'
                     '- Only files in uploads directory can be accessed\n'
                     '- Matches path validation pattern from other file access endpoints\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Apply rate limiting to the file download endpoint, matching the pattern used '
                     'on other public-facing endpoints\n',
     'expected_issues': ['violates mandatory os.path.abspath + startswith validation pattern',
                         'missing rate limiting on the file download endpoint'],
     'diff_file': 'pr_012_path_traversal.diff'},
    {'id': 'pr_013_cors_misconfiguration',
     'title': 'Enable CORS for API',
     'task_context': '\n'
                     'TASK-013: Enable CORS for Frontend Integration\n'
                     '\n'
                     'Description:\n'
                     'Configure CORS middleware to allow frontend application to access the API\n'
                     '\n'
                     'Requirements:\n'
                     '- Add CORS middleware to FastAPI application\n'
                     '- Allow credentials for authenticated requests\n'
                     '- Support all HTTP methods needed by frontend\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Specify explicit list of allowed origins\n'
                     '- Do NOT use wildcard origins with credentials\n'
                     '- Follow existing CORS configuration patterns\n'
                     '\n'
                     'References:\n'
                     '- See production API CORS configuration\n'
                     '- Review security policy on allowed origins\n'
                     '- Use environment-based origin whitelist\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- CORS middleware configured\n'
                     '- Explicit origin whitelist defined\n'
                     '- Credentials allowed only for whitelisted domains\n'
                     '- Matches explicit allow_origins pattern from production config\n'
                     '\n'
                     'Additional Requirement:\n'
                     "- Wrap the new lookup endpoint's database call in try-except with logging, "
                     'matching the error handling pattern used elsewhere\n',
     'expected_issues': ['violates explicit allow_origins whitelist pattern',
                         'new /api/data/{data_id} endpoint has no try-except around its database call'],
     'diff_file': 'pr_013_cors_misconfiguration.diff'},
    {'id': 'pr_014_timing_attack',
     'title': 'Add API key validation',
     'task_context': '\n'
                     'TASK-014: Add API Key Validation\n'
                     '\n'
                     'Description:\n'
                     'Implement validate_api_key function to check API keys for protected endpoints\n'
                     '\n'
                     'Requirements:\n'
                     '- Accept API key as parameter\n'
                     '- Compare against valid API key from environment\n'
                     '- Return boolean indicating if key is valid\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Prevent timing attacks on key comparison\n'
                     '- Use constant-time comparison for secrets\n'
                     '- Follow existing secret comparison patterns\n'
                     '\n'
                     'References:\n'
                     '- See how passwords are verified\n'
                     '- See how session tokens are validated\n'
                     '- Follow the hmac.compare_digest() pattern for all secret comparisons\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- API key validation function implemented\n'
                     '- Constant-time comparison used\n'
                     '- Timing attack vulnerability prevented\n'
                     '- Matches hmac.compare_digest pattern from password/token verification\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Validate the key format/length before comparison, following the input '
                     'validation pattern used elsewhere\n',
     'expected_issues': ['violates mandatory hmac.compare_digest pattern for secrets',
                         'missing input validation on the key parameter (no length/format check) '
                         'before comparison'],
     'diff_file': 'pr_014_timing_attack.diff'},
    {'id': 'pr_015_unvalidated_redirect',
     'title': 'Add OAuth callback',
     'task_context': '\n'
                     'TASK-015: Add OAuth Callback Handler\n'
                     '\n'
                     'Description:\n'
                     'Implement OAuth callback endpoint to handle redirects after authentication\n'
                     '\n'
                     'Requirements:\n'
                     '- Accept OAuth code and redirect_url parameters\n'
                     '- Exchange code for access token\n'
                     '- Save token for user\n'
                     '- Redirect user to specified URL\n'
                     '\n'
                     'Security Requirements (CRITICAL):\n'
                     '- Validate redirect URLs to prevent open redirect attacks\n'
                     '- Only allow redirects to trusted domains\n'
                     '- Follow existing redirect validation patterns\n'
                     '\n'
                     'References:\n'
                     '- See how login endpoint handles post-auth redirects\n'
                     '- See how SAML callback validates relay_state\n'
                     '- Follow the ALLOWED_REDIRECTS whitelist pattern\n'
                     '\n'
                     'Acceptance Criteria:\n'
                     '- OAuth callback functionality works\n'
                     '- Redirect URL validation implemented\n'
                     '- Only whitelisted domains allowed\n'
                     '- Matches ALLOWED_REDIRECTS pattern from other redirect endpoints\n'
                     '\n'
                     'Additional Requirement:\n'
                     '- Validate the format of the OAuth code parameter before using it, following the '
                     'input validation pattern used elsewhere\n',
     'expected_issues': ['violates mandatory ALLOWED_REDIRECTS whitelist validation',
                         'missing input validation on the OAuth code parameter'],
     'diff_file': 'pr_015_unvalidated_redirect.diff'},
]


def load_pr_diff(diff_file: str, diff_root: Path = PR_DIFF_ROOT) -> str:
    """Load one pull request diff fixture."""
    return (diff_root / diff_file).read_text(encoding="utf-8")


def load_sample_prs(
    metadata: list[dict[str, Any]] = SAMPLE_PR_METADATA,
    diff_root: Path = PR_DIFF_ROOT,
) -> list[dict[str, Any]]:
    """Load PR metadata and attach the diff text from fixture files."""
    pull_requests: list[dict[str, Any]] = []
    for item in metadata:
        pull_request = dict(item)
        diff_file = pull_request.pop("diff_file")
        pull_request["diff"] = load_pr_diff(diff_file, diff_root)
        pull_requests.append(pull_request)
    return pull_requests


TOY_REPOSITORY = load_repository()
SAMPLE_PRS = load_sample_prs()
