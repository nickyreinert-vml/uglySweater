"""functions/api/routes.py
Purpose:
- Define API blueprint for persona prediction endpoint.
Main Classes:
- PredictionAPI: controller that validates input and triggers predictions.
Dependent Files:
- Consumes PredictionService, PersonaValidator, SessionRepository, CSRFProtector.
"""

from typing import Any, Dict

from flask import Blueprint, jsonify, request, session

from utils.logger import build_logger

LOGGER = build_logger("api_routes")

# --- API OPS ---

class PredictionAPI:
    """Controller for /predict endpoint.
    Purpose: handle validation, csrf checks, and service delegation.
    Input Data: Flask request context.
    Output Data: JSON API response.
    Process: validate csrf, persona, call prediction service, log outcome.
    Dependent Functions and Classes: PredictionService and SessionRepository.
    """

    def __init__(
        self,
        prediction_service,
        session_repo,
        persona_validator,
        csrf_protector,
        i18n_repo,
    ) -> None:
        """Constructor.
        Purpose: store dependency references for later requests.
        Input Data: service instances passed from app factory.
        Output Data: none.
        Process: assign attributes and emit debug log.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        self.prediction_service = prediction_service
        self.session_repo = session_repo
        self.persona_validator = persona_validator
        self.csrf_protector = csrf_protector
        self.i18n_repo = i18n_repo
        LOGGER.log_debug("PredictionAPI wired", depth=1)

    def handle_predict(self):
        """Process prediction POST request.
        Purpose: combine CSRF validation, persona sanitization, and AI call.
        Input Data: Flask global request/session objects.
        Output Data: tuple of response object and status code.
        Process: validate csrf, sanitize persona, run prediction, log events.
        Dependent Functions and Classes: helper methods inside class.
        """
        if not self._is_csrf_valid():
            return self._build_error("invalid_csrf", 403)
        persona = request.get_json(silent=True) or {}
        is_valid, sanitized = self.persona_validator.is_valid(persona)
        if not is_valid:
            self.session_repo.log_tampering(session, sanitized)
            return self._build_error("invalid_persona", 405)
        self._cache_persona(sanitized)
        vocab = session.get("vocab") or self.i18n_repo.vocab_for("en")
        result = self.prediction_service.run_prediction(session, sanitized, vocab)
        if result.get("status") == "success":
            self.session_repo.log_request(session, sanitized)
            return jsonify(result)
        return self._build_error(result.get("message", "prediction_error"), 500)

    def _is_csrf_valid(self) -> bool:
        """Validate CSRF token from headers.
        Purpose: centralize header lookup and validation logic.
        Input Data: Flask request header collection.
        Output Data: boolean result.
        Process: read X-CSRF-Token header then call CSRFProtector.
        Dependent Functions and Classes: CSRFProtector.validate.
        """
        token = request.headers.get("X-CSRF-Token", "")
        return self.csrf_protector.validate(session, token)

    def _cache_persona(self, persona: Dict[str, str]) -> None:
        """Store persona on session for downstream logging.
        Purpose: ensure download route has persona context available.
        Input Data: sanitized persona dictionary.
        Output Data: none, mutates session state.
        Process: assign industry and business problem keys to session.
        Dependent Functions and Classes: Flask session proxy.
        """
        session["industry"] = persona.get("industry")
        session["businesProblem"] = persona.get("businesProblem")

    def _build_error(self, message: str, status: int):
        """Return standardized API error payload.
        Purpose: keep API responses consistent across failure branches.
        Input Data: error message string and HTTP status code.
        Output Data: tuple containing Flask response and status code.
        Process: build dictionary per contract then jsonify it.
        Dependent Functions and Classes: flask.jsonify helper.
        """
        payload = {"status": "error", "data": {}, "message": message}
        return jsonify(payload), status


def build_api_blueprint(
    prediction_service,
    session_repo,
    persona_validator,
    csrf_protector,
    i18n_repo,
    limiter,
    rate_limits: Dict[str, str],
) -> Blueprint:
    """Create API blueprint configured with dependencies.
    Purpose: encapsulate blueprint wiring to keep app factory tidy.
    Input Data: service instances, limiter, and rate limit rules.
    Output Data: configured Blueprint ready for registration.
    Process: instantiate controller, define route, apply limiter decorator.
    Dependent Functions and Classes: PredictionAPI class above.
    """
    api = PredictionAPI(
        prediction_service,
        session_repo,
        persona_validator,
        csrf_protector,
        i18n_repo,
    )
    blueprint = Blueprint("api", __name__)

    @blueprint.route("/predict", methods=["POST"])
    @limiter.limit(rate_limits.get("predict", "10 per minute"))
    def predict_route():
        """Prediction endpoint handler.
        Purpose: delegate to controller method required by Flask.
        Input Data: none, uses global request context.
        Output Data: Flask response from controller.
        Process: call api.handle_predict and return its response.
        Dependent Functions and Classes: PredictionAPI.handle_predict.
        """
        return api.handle_predict()

    return blueprint
