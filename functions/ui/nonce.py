"""functions/ui/nonce.py
Purpose:
- Provide helpers for generating CSP compatible nonces.
Main Functions:
- generate_nonce: create base64 nonce for inline script whitelisting.
Dependent Files:
- Consumed by UI controllers when rendering templates.
"""

import base64
import os

# --- UI OPS ---

def generate_nonce() -> str:
    """Create random nonce string.
    Purpose: feed CSP headers with unpredictable values per request.
    Input Data: none.
    Output Data: URL safe base64 encoded string.
    Process: os.urandom for entropy, base64 encode, decode to utf-8.
    Dependent Functions and Classes: os.urandom and base64.b64encode.
    """
    return base64.b64encode(os.urandom(16)).decode("utf-8")
