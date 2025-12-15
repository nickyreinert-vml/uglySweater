"""app.py
Purpose:
- Flask application entry point wiring blueprints, services, and security.
Main Functions:
- create_app: build configured Flask app with rate limits and auth.
Dependent Files:
- Relies on functions/* modules plus utils/logger for diagnostics.
"""

import os
from typing import Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from openai import OpenAI

from functions.api.prediction_service import PredictionService
from functions.api.routes import build_api_blueprint
from functions.auth.csrf import CSRFProtector
from functions.auth.security import AuthManager
from functions.data.config_loader import ConfigLoader
from functions.data.i18n_repository import I18NRepository
from functions.data.persona_validator import PersonaValidator
from functions.data.session_repository import SessionRepository
from functions.ui.controllers import UIController
from functions.ui.language import LanguageResolver
from functions.ui.routes import build_ui_blueprint
from utils.logger import build_logger

LOGGER = build_logger("app")
load_dotenv(override=True)
limiter = Limiter(get_remote_address)


# --- APP FACTORY ---

def create_app() -> Flask:
    """Purpose: build configured Flask app; Input Data: env vars plus config.json contents; Output Data: fully wired Flask instance; Process: load config, build repositories/services/controllers, register blueprints and handlers; Dependent Functions and Classes: helpers within this module and ConfigLoader."""
    _require_env_keys()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    _apply_basic_auth_config(app)
    limiter.init_app(app)
    config = ConfigLoader().load()
    repos = _build_repositories(config)
    services = _build_services(config, repos)
    controllers = _build_controllers(config, repos, services)
    auth_manager = AuthManager(app, config.get("basic_auth_folders", []))
    _register_blueprints(app, config, controllers, auth_manager, services, repos)
    _register_error_handlers(app, repos["session_repo"])
    return app


def _require_env_keys() -> None:
    """Purpose: ensure sensitive env vars exist; Input Data: os.environ; Output Data: none; Process: iterate required keys and assert presence; Dependent Functions and Classes: LOGGER for diagnostics."""
    keys = [
        "OPENAI_API_KEY",
        "ASSISTANT_ID",
        "SECRET_KEY",
        "BASIC_AUTH_USERNAME",
        "BASIC_AUTH_PASSWORD",
    ]
    for key in keys:
        assert os.environ.get(key), f"Environment variable {key} is required"
    LOGGER.log_debug("Environment keys validated", depth=1)


def _apply_basic_auth_config(app: Flask) -> None:
    """Purpose: load basic auth credentials into Flask config; Input Data: Flask app; Output Data: none; Process: copy BASIC_AUTH_* env values onto app.config; Dependent Functions and Classes: none."""
    app.config["BASIC_AUTH_USERNAME"] = os.environ.get("BASIC_AUTH_USERNAME")
    app.config["BASIC_AUTH_PASSWORD"] = os.environ.get("BASIC_AUTH_PASSWORD")


def _build_repositories(config: Dict[str, str]) -> Dict[str, object]:
    """Purpose: instantiate repositories; Input Data: merged configuration dict; Output Data: dict containing session_repo and i18n_repo; Process: create repositories and ensure schema is initialized; Dependent Functions and Classes: SessionRepository and I18NRepository."""
    session_repo = SessionRepository(config.get("log_db"))
    session_repo.init_schema()
    i18n_repo = I18NRepository(config.get("i18n_file", "i18n.json"))
    return {"session_repo": session_repo, "i18n_repo": i18n_repo}


def _build_services(config: Dict[str, str], repos: Dict[str, object]) -> Dict[str, object]:
    """Purpose: assemble service layer dependencies; Input Data: config map and repo dict; Output Data: dict containing prediction service, validator, language resolver, csrf helper; Process: instantiate OpenAI client then construct dependent services; Dependent Functions and Classes: OpenAI, PredictionService, PersonaValidator, LanguageResolver, CSRFProtector."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    prediction_service = PredictionService(client, repos["session_repo"])
    validator = PersonaValidator(
        repos["i18n_repo"].industries(),
        repos["i18n_repo"].business_problems(),
    )
    language_resolver = LanguageResolver()
    csrf = CSRFProtector()
    return {
        "prediction_service": prediction_service,
        "persona_validator": validator,
        "language_resolver": language_resolver,
        "csrf": csrf,
    }


def _build_controllers(
    config: Dict[str, str],
    repos: Dict[str, object],
    services: Dict[str, object],
) -> Dict[str, object]:
    """Purpose: instantiate controller classes; Input Data: config dict plus repository and service dictionaries; Output Data: dict containing UIController instance; Process: pass dependencies into UIController constructor; Dependent Functions and Classes: UIController."""
    ui_controller = UIController(
        services["prediction_service"],
        repos["session_repo"],
        repos["i18n_repo"],
        services["language_resolver"],
        services["csrf"],
        config,
    )
    return {"ui_controller": ui_controller}


def _register_blueprints(
    app: Flask,
    config: Dict[str, str],
    controllers: Dict[str, object],
    auth_manager: AuthManager,
    services: Dict[str, object],
    repos: Dict[str, object],
) -> None:
    """Purpose: attach UI and API blueprints; Input Data: app, config, controllers, auth manager, services, repos; Output Data: none; Process: build blueprints via helper factories and register; Dependent Functions and Classes: build_ui_blueprint and build_api_blueprint."""
    rate_limits = config.get("rate_limits", {})
    ui_blueprint = build_ui_blueprint(
        controllers["ui_controller"],
        auth_manager,
        limiter,
        rate_limits,
    )
    api_blueprint = build_api_blueprint(
        services["prediction_service"],
        repos["session_repo"],
        services["persona_validator"],
        services["csrf"],
        repos["i18n_repo"],
        limiter,
        rate_limits,
    )
    app.register_blueprint(ui_blueprint)
    app.register_blueprint(api_blueprint)


def _register_error_handlers(app: Flask, session_repo: SessionRepository) -> None:
    """Purpose: add global error handlers; Input Data: app and session repository; Output Data: none; Process: declare 429 handler to log and jsonify rate limit events; Dependent Functions and Classes: Flask errorhandler decorator."""

    @app.errorhandler(429)
    def handle_rate_limit(exc):
        """Purpose: format rate limit response; Input Data: limiter exception; Output Data: (response, status); Process: log error via session_repo then jsonify payload; Dependent Functions and Classes: session_repo.log_error and flask.jsonify."""

        session_repo.log_error(session, "rate_limit", {})
        payload = {"status": "error", "data": {}, "message": "rate_limit"}
        return jsonify(payload), 429


app = create_app()


if __name__ == "__main__":
    debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8080, debug=debug_mode)