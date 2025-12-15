"""functions/ui/controllers.py
Purpose:
- Group Flask view logic for UI endpoints.
Main Classes:
- UIController: handles index, download, admin, and health routes.
Dependent Files:
- Relies on repositories, services, and helpers injected at creation.
"""

from typing import Any, Dict

from flask import Response, jsonify, redirect, render_template

from functions.ui.nonce import generate_nonce
from utils.logger import build_logger

LOGGER = build_logger("ui_controller")

# --- UI OPS ---

class UIController:
    """Controller orchestrating templated routes.
    Purpose: keep Flask blueprints thin by encapsulating logic here.
    Input Data: repositories, services, and helper components.
    Output Data: Flask responses for UI endpoints.
    Process: expose small methods invoked by blueprint route functions.
    Dependent Functions and Classes: render_template and injected services.
    """

    def __init__(
        self,
        prediction_service,
        session_repo,
        i18n_repo,
        language_resolver,
        csrf_protector,
        config: Dict[str, Any],
    ) -> None:
        """Constructor.
        Purpose: store dependencies for later reuse.
        Input Data: service objects and configuration dictionary.
        Output Data: none.
        Process: assign to instance attributes and log initialization.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        self.prediction_service = prediction_service
        self.session_repo = session_repo
        self.i18n_repo = i18n_repo
        self.language_resolver = language_resolver
        self.csrf_protector = csrf_protector
        self.config = config
        LOGGER.log_debug("UIController ready", depth=1)

    def render_index(self, session_store, request_obj) -> Response:
        """Render landing page with localized vocab.
        Purpose: prepare conversation thread and per request security tokens.
        Input Data: Flask session and request instances.
        Output Data: rendered HTML response.
        Process: ensure OpenAI thread, resolve language, issue CSRF, render template.
        Dependent Functions and Classes: render_template, repositories, services.
        """
        if not self.prediction_service.ensure_thread(session_store):
            self.session_repo.log_error(session_store, "thread initialization failed", {})
            return jsonify({"status": "error", "message": "thread creation failed"}), 500
        self.session_repo.log_session(session_store, request_obj)
        language = self.language_resolver.resolve(
            session_store, request_obj, self.config.get("language_routes", {})
        )
        vocab = self.i18n_repo.vocab_for(language)
        session_store["vocab"] = vocab
        csrf_token = self.csrf_protector.issue_token(session_store)
        nonce = generate_nonce()
        hero_background = self._resolve_hero_background(request_obj)
        return render_template(
            "index.html",
            vocab=vocab,
            nonce=nonce,
            csrf_token=csrf_token,
            language=language,
            hero_background=hero_background,
        )

    def download_report(self, session_store) -> Response:
        """Redirect user to configured download URL.
        Purpose: trigger analytics logging before redirecting externally.
        Input Data: Flask session dict.
        Output Data: HTTP redirect response.
        Process: log download event then redirect to config download url.
        Dependent Functions and Classes: session repository for logging.
        """
        self.session_repo.log_download(session_store)
        return redirect(self.config.get("download_url", "/"))

    def render_admin(self) -> Response:
        """Render peekaboo admin page.
        Purpose: expose analytics tables for password protected view.
        Input Data: none beyond repository state.
        Output Data: rendered HTML response for admin template.
        Process: fetch aggregated logs and pass to template.
        Dependent Functions and Classes: session repository fetch_logs.
        """
        logs = self.session_repo.fetch_logs()
        return render_template("peekaboo.html", logs=logs)

    def health(self) -> Response:
        """Return health check response.
        Purpose: allow uptime monitors to validate service availability.
        Input Data: none.
        Output Data: empty 200 response.
        Process: respond immediately without additional processing.
        Dependent Functions and Classes: Flask Response helpers.
        """
        return Response("", status=200)

    def _resolve_hero_background(self, request_obj) -> str:
        """Purpose: derive hero background path from bg query; Input Data: request args mapping; Output Data: static asset path string; Process: read bg param, normalize, match config mapping with default fallback; Dependent Functions and Classes: config dictionary."""
        backgrounds = self.config.get("hero_backgrounds", {})
        default = backgrounds.get("default") or next(iter(backgrounds.values()), "images/background_section_1_left.jpg")
        raw_key = request_obj.args.get("bg", "")
        if not raw_key:
            return default
        normalized = raw_key.strip().lower()
        return backgrounds.get(normalized, default)
