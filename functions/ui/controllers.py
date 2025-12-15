"""functions/ui/controllers.py
Purpose:
- Group Flask view logic for UI endpoints.
Main Classes:
- UIController: handles index, download, admin, and health routes.
Dependent Files:
- Relies on repositories, services, and helpers injected at creation.
"""

from typing import Any, Dict, Union

from flask import Response, jsonify, redirect, render_template, send_from_directory

from functions.ui.nonce import generate_nonce
from utils.logger import build_logger
import os

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

    def render_index(self, session_store, request_obj) -> Union[str, Response]:
        """Render landing page with localized vocab.
        Purpose: prepare conversation thread and per request security tokens.
        Input Data: Flask session and request instances.
        Output Data: rendered HTML response.
        Process: ensure OpenAI thread, resolve language, issue CSRF, render template.
        Dependent Functions and Classes: render_template, repositories, services.
        """
        if not self.prediction_service.ensure_thread(session_store):
            self.session_repo.log_error(session_store, "thread initialization failed", {})
            resp = jsonify({"status": "error", "message": "thread creation failed"})
            resp.status_code = 500
            return resp
        
        self.session_repo.log_session(session_store, request_obj)
        language = self.language_resolver.resolve(
            session_store, request_obj, self.config.get("language_routes", {})
        )

        vocab = self.i18n_repo.vocab_for(language)
        session_store["vocab"] = vocab
        csrf_token = self.csrf_protector.issue_token(session_store)
        nonce = generate_nonce()
        hero_background = self._resolve_hero_background(request_obj)
        team_key = request_obj.args.get("t", "").strip().lower()
        if not team_key:
            team_key = self.config.get("default_team", "vml")
        download_urls = self._build_download_urls(team_key)
        
        return render_template(
            "index.html",
            vocab=vocab,
            nonce=nonce,
            csrf_token=csrf_token,
            language=language,
            hero_background=hero_background,
            download_urls=download_urls,
        )

    def render_admin(self) -> str:
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

    def serve_background_download(self, request_obj) -> Response:
        """Serve customized background for download.
        Purpose: return background image file based on query params.
        Input Data: request with t, color, icon query params.
        Output Data: file download response or 404.
        Process: extract params, build filename, serve from downloads.
        Dependent Functions and Classes: send_from_directory, config dictionary.
        """
        team_key = request_obj.args.get("t", "").strip().lower()
        color = request_obj.args.get("color", "").strip().lower()
        icon = request_obj.args.get("icon", "").strip().lower()
        
        if not team_key or not color or not icon:
            LOGGER.log_debug("Missing required parameters for background download", depth=2)
            return Response("Missing parameters", status=400)
        
        color_sets = self.config.get("color_sets", [])
        icons = self.config.get("icons", [])
        
        if color not in color_sets or icon not in icons:
            LOGGER.log_debug(f"Invalid color or icon: {color}, {icon}", depth=2)
            return Response("Invalid parameters", status=400)
        
        filename = f"{team_key}_{color}_{icon}.png"
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "images", "downloads")
        LOGGER.log_debug(f"Serving background: {filename}", depth=2)
        
        return send_from_directory(static_dir, filename, as_attachment=True)

    def _build_download_urls(self, team_key: str) -> Dict[str, Dict[str, str]]:
        """Purpose: construct download URLs for all color/icon combinations; Input Data: team key and config; Output Data: nested dict mapping colors and icons to URLs; Process: iterate all combinations and build URLs; Dependent Functions and Classes: config dictionary."""
        color_sets = self.config.get("color_sets", [])
        icons = self.config.get("icons", [])
        
        result = {}
        for color in color_sets:
            result[color] = {}
            for icon in icons:
                result[color][icon] = f"/download_background?t={team_key}&color={color}&icon={icon}"
        
        return result

    def _resolve_hero_background(self, request_obj) -> str:
        """Purpose: derive hero background path from bg query; Input Data: request args mapping; Output Data: static asset path string; Process: read bg param, normalize, match config mapping with default fallback; Dependent Functions and Classes: config dictionary."""
        backgrounds = self.config.get("hero_backgrounds", {})
        default = backgrounds.get("_default")
        raw_key = request_obj.args.get("t", "")
        if not raw_key:
            return default
        normalized = raw_key.strip().lower()
        filepath = backgrounds.get(normalized, default)
        return f"images/hero/{filepath}"
