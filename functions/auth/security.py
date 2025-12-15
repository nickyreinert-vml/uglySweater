"""functions/auth/security.py
Purpose:
- Provide reusable helpers for HTTP basic authentication and selective route protection.
Main Classes:
- AuthManager: wraps Flask-BasicAuth with folder level protections.
Dependent Files:
- Consumed by UI blueprints to guard administrative routes.
"""

from functools import wraps
from typing import Callable, Iterable

from flask import Request
from flask_basicauth import BasicAuth

from utils.logger import build_logger

LOGGER = build_logger("auth_manager")

# --- AUTH OPS ---

class AuthManager:
    """Encapsulate Flask-BasicAuth configuration.
    Purpose: centralize selective authentication logic for protected folders.
    Input Data: Flask app instance and iterable of folder prefixes.
    Output Data: authenticated responses when credentials validated.
    Process: hold BasicAuth instance and evaluate request paths per folder list.
    Dependent Functions and Classes: flask_basicauth.BasicAuth for challenge flow.
    """

    def __init__(self, app, folders: Iterable[str]) -> None:
        """Constructor.
        Purpose: instantiate BasicAuth and store folder whitelist.
        Input Data: Flask app and folders list or tuple.
        Output Data: none, registers BasicAuth on app context.
        Process: build BasicAuth, normalize folders, and log configuration.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        self.basic_auth = BasicAuth(app)
        self.protected_folders = [folder for folder in folders if folder]
        LOGGER.log_debug(
            f"Protected folders configured: {self.protected_folders}", depth=1
        )

    def require_auth(self, view_func: Callable) -> Callable:
        """Decorator enforcing authentication for protected paths.
        Purpose: wrap view functions and enforce basic auth where required.
        Input Data: view function from Flask blueprint.
        Output Data: wrapped callable for Flask routing.
        Process: inspect request path and challenge when under protected folder.
        Dependent Functions and Classes: _needs_auth helper and BasicAuth.
        """

        @wraps(view_func)
        def wrapper(*args, **kwargs):
            """Purpose: enforce basic auth based on folder list.
            Input Data: Flask view positional and keyword arguments.
            Output Data: Flask response or the original view result.
            Process: resolve request, verify path, challenge if needed.
            Dependent Functions and Classes: _needs_auth helper, BasicAuth.
            """
            request_obj = kwargs.get("request_obj")
            if not request_obj:
                from flask import request as flask_request

                request_obj = flask_request
            if self._needs_auth(request_obj):
                if not self.basic_auth.authenticate():
                    return self.basic_auth.challenge()
            return view_func(*args, **kwargs)

        return wrapper

    def _needs_auth(self, request_obj: Request) -> bool:
        """Determine whether path requires authentication.
        Purpose: compare incoming path with configured folder prefixes.
        Input Data: Flask request instance.
        Output Data: boolean flag.
        Process: iterate folder list and test startswith semantics.
        Dependent Functions and Classes: none.
        """
        path = request_obj.path or ""
        for folder in self.protected_folders:
            if path.startswith(folder):
                return True
        return False
