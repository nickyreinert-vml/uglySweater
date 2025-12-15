"""functions/ui/routes.py
Purpose:
- Provide Flask blueprint wiring for UI endpoints.
Main Functions:
- build_ui_blueprint: attach controller actions to HTTP routes.
Dependent Files:
- Relies on UIController and AuthManager instances.
"""

from flask import Blueprint, request, session

# --- UI OPS ---

def build_ui_blueprint(ui_controller, auth_manager, limiter, rate_limits) -> Blueprint:
    """Create UI blueprint with rate limits and auth protections.
    Purpose: keep app factory lean by encapsulating blueprint setup.
    Input Data: controller, auth manager, limiter, and rate limit dict.
    Output Data: configured Blueprint ready for registration.
    Process: define routes, apply limiter decorators, and auth wrappers.
    Dependent Functions and Classes: Flask Blueprint, UIController methods.
    """
    blueprint = Blueprint("ui", __name__)

    @blueprint.route("/")
    @limiter.limit(rate_limits.get("app", "20 per minute"))
    def index():
        """Render landing page.
        Purpose: delegate to controller with session and request context.
        Input Data: none explicitly, uses Flask globals.
        Output Data: HTML response from controller.
        Process: invoke ui_controller.render_index and return result.
        Dependent Functions and Classes: UIController.render_index.
        """
        return ui_controller.render_index(session, request)

    @blueprint.route("/download")
    def download():
        """Handle download redirect.
        Purpose: log download intent then redirect to configured URL.
        Input Data: none explicitly, uses Flask session.
        Output Data: redirect response from controller.
        Process: call ui_controller.download_report.
        Dependent Functions and Classes: UIController.download_report.
        """
        return ui_controller.download_report(session)

    @blueprint.route("/peekaboo")
    @auth_manager.require_auth
    def peekaboo():
        """Render analytics dashboard.
        Purpose: serve admin reporting view for authenticated users.
        Input Data: none explicitly within route body.
        Output Data: rendered HTML response from controller.
        Process: call ui_controller.render_admin and return result.
        Dependent Functions and Classes: UIController.render_admin.
        """
        return ui_controller.render_admin()

    @blueprint.route("/up")
    @limiter.exempt
    def health():
        """Serve health check.
        Purpose: expose simple uptime endpoint.
        Input Data: none.
        Output Data: HTTP 200 response.
        Process: delegate to ui_controller.health with no args.
        Dependent Functions and Classes: UIController.health.
        """
        return ui_controller.health()

    return blueprint
