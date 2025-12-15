"""functions/auth/csrf.py
Purpose:
- Implement lightweight CSRF token issuance and validation.
Main Classes:
- CSRFProtector: manages tokens tied to Flask session storage.
Dependent Files:
- Utilized by API routes before processing POST payloads.
"""

import secrets
from typing import Dict

from utils.logger import build_logger

LOGGER = build_logger("csrf_protector")

# --- CSRF OPS ---

class CSRFProtector:
    """Issue and validate CSRF tokens per session.
    Purpose: mitigate cross site request forgery for JSON endpoints.
    Input Data: Flask session dictionary per request.
    Output Data: unique tokens stored server side and shared with client.
    Process: generate secure token, store within session, verify on request.
    Dependent Functions and Classes: secrets library for randomness.
    """

    def issue_token(self, session_store: Dict[str, str]) -> str:
        """Create and persist CSRF token.
        Purpose: expose token to frontend for subsequent POST requests.
        Input Data: session dictionary capable of storing strings.
        Output Data: random token string.
        Process: use token_urlsafe then persist under csrf_token key.
        Dependent Functions and Classes: secrets.token_urlsafe.
        """
        token = secrets.token_urlsafe(32)
        session_store["csrf_token"] = token
        LOGGER.log_debug("CSRF token issued", depth=2)
        return token

    def validate(self, session_store: Dict[str, str], provided: str) -> bool:
        """Confirm provided token matches stored value.
        Purpose: block POST handling when tokens do not align.
        Input Data: session dict and token string from headers.
        Output Data: boolean success flag.
        Process: compare stored token with provided, log failures.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        stored = session_store.get("csrf_token")
        if not stored or not provided:
            LOGGER.log_debug("CSRF token missing", depth=2)
            return False
        if stored != provided:
            LOGGER.log_debug("CSRF mismatch detected", depth=2)
            return False
        return True
