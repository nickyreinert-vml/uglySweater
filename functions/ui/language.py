"""functions/ui/language.py
Purpose:
- Handle language selection logic for templated responses.
Main Classes:
- LanguageResolver: inspects headers, hostnames, and query params.
Dependent Files:
- Utilized by UIController before rendering templates.
"""

from typing import Dict

from utils.logger import build_logger

LOGGER = build_logger("language_resolver")

# --- LANGUAGE OPS ---

class LanguageResolver:
    """Resolve language codes from incoming HTTP context.
    Purpose: centralize logic reused by index route rendering.
    Input Data: preference headers, hostnames, and query args.
    Output Data: two letter lowercase language code.
    Process: evaluate explicit query override, header, then host map.
    Dependent Functions and Classes: relies on Flask request interface.
    """

    def __init__(self, default_code: str = "en") -> None:
        """Constructor.
        Purpose: capture fallback language when no signal present.
        Input Data: optional default language string.
        Output Data: none, sets attribute for reuse.
        Process: assign provided code and log configuration.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        self.default_code = default_code
        LOGGER.log_debug(f"Default language {default_code}", depth=1)

    def resolve(self, session_store, request_obj, routes: Dict[str, str]) -> str:
        """Determine language for request.
        Purpose: compute language preference snapshot stored on session.
        Input Data: session dict, Flask request, routes mapping.
        Output Data: resolved two letter string.
        Process: check query param, header, host mapping sequentially.
        Dependent Functions and Classes: helper _from_host.
        """
        lang = request_obj.args.get("lang", "").lower().strip()[:2]
        if lang:
            return self._persist(session_store, lang)
        header_lang = (request_obj.headers.get("X-Language", "").lower().strip())[:2]
        if header_lang:
            return self._persist(session_store, header_lang)
        host_lang = self._from_host(request_obj.host, routes)
        return self._persist(session_store, host_lang)

    def _persist(self, session_store, code: str) -> str:
        """Persist language on session and return code.
        Purpose: keep session level memory of the selected language.
        Input Data: session store and two letter code.
        Output Data: persisted code string.
        Process: write to session for future reuse.
        Dependent Functions and Classes: none.
        """
        session_store["language"] = code or self.default_code
        return session_store["language"]

    def _from_host(self, host: str, routes: Dict[str, str]) -> str:
        """Resolve language from host lookup.
        Purpose: match request host to configured map.
        Input Data: host string and mapping dictionary.
        Output Data: resolved language or default if missing.
        Process: strip port, lookup mapping, fallback to default.
        Dependent Functions and Classes: none.
        """
        hostname = (host or "").split(":")[0]
        return routes.get(hostname, self.default_code)
