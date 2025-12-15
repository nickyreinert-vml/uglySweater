"""functions/data/config_loader.py
Purpose:
- Centralize configuration loading and environment overrides.
Main Classes:
- ConfigLoader: reads JSON config, applies env overrides for runtime use.
Dependent Files:
- Relies on config.json at the project root.
"""

import json
import os
from typing import Any, Dict

from utils.logger import build_logger

LOGGER = build_logger("config_loader")

# --- CONFIG CORE OPS ---

class ConfigLoader:
    """Read configuration from JSON and merge with env.
    Purpose: supply strongly typed config dictionary for the Flask app.
    Input Data: path to config.json and environment variables.
    Output Data: merged dictionary with runtime safe values.
    Process: load JSON, overlay env overrides, sanitize defaults.
    Dependent Functions and Classes: build_logger for diagnostics.
    """

    def __init__(self, config_path: str = "config.json") -> None:
        """Constructor.
        Purpose: store file path for repeated loads.
        Input Data: optional config path string.
        Output Data: none, maintains path on self.
        Process: assign attribute and log the configuration path.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        self.config_path = config_path
        LOGGER.log_debug(f"Config path set to {config_path}", depth=1)

    def load(self) -> Dict[str, Any]:
        """Produce final configuration dictionary.
        Purpose: expose merged JSON plus env overrides.
        Input Data: none, uses stored path and os.environ.
        Output Data: dict containing runtime config slices.
        Process: load raw JSON, overlay overrides, return sanitized dict.
        Dependent Functions and Classes: _load_file and _apply_env_overrides.
        """
        base_config = self._load_file()
        return self._apply_env_overrides(base_config)

    def _load_file(self) -> Dict[str, Any]:
        """Read config json content.
        Purpose: fetch baseline configuration state from disk.
        Input Data: filesystem path stored on the instance.
        Output Data: dictionary parsed from JSON.
        Process: open file, json.load contents, log success.
        Dependent Functions and Classes: json module for parsing.
        """
        with open(self.config_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        LOGGER.log_debug("Config file loaded", depth=2)
        return data

    def _apply_env_overrides(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Overlay environment overrides.
        Purpose: respect runtime env values for mutable entries.
        Input Data: dictionary from JSON file.
        Output Data: updated dictionary ready for consumers.
        Process: update map entries by reading os.environ values.
        Dependent Functions and Classes: helper builders inside class.
        """
        app_cfg = data.get("app", {})
        db_cfg = data.get("database", {})
        security_cfg = data.get("security", {})
        merged = {
            "download_url": os.getenv("DOWNLOAD_URL", app_cfg.get("download_url", "")),
            "language_routes": self._parse_lang_routes(app_cfg.get("language_routes", {})),
            "hero_backgrounds": self._build_backgrounds(app_cfg.get("hero_backgrounds", {})),
            "i18n_file": app_cfg.get("i18n_file", "i18n.json"),
            "log_db": os.getenv("LOG_DB", db_cfg.get("log_path", "logs.db")),
        }
        merged["rate_limits"] = self._build_rate_limits(data.get("rate_limits", {}))
        merged["basic_auth_folders"] = self._split_folders(
            os.getenv(
                "BASIC_AUTH_FOLDERS",
                ",".join(security_cfg.get("basic_auth_folders", [])),
            )
        )
        return merged

    def _parse_lang_routes(self, defaults: Dict[str, str]) -> Dict[str, str]:
        """Decode optional LANG_ROUTES env string.
        Purpose: allow runtime override using JSON payload in env.
        Input Data: default dictionary from config.json.
        Output Data: dictionary representing merged language routes.
        Process: attempt json.loads on env var, fall back to defaults.
        Dependent Functions and Classes: json library for parsing.
        """
        raw_routes = os.getenv("LANG_ROUTES")
        if not raw_routes:
            return defaults
        try:
            override = json.loads(raw_routes)
            return {**defaults, **override}
        except json.JSONDecodeError:
            LOGGER.log_error("Invalid LANG_ROUTES override", depth=2)
            return defaults

    def _build_rate_limits(self, defaults: Dict[str, str]) -> Dict[str, str]:
        """Assemble app rate limits.
        Purpose: ensure both app and predict rate limit strings exist.
        Input Data: default rate dictionary from config.json.
        Output Data: dictionary with merged rate limits.
        Process: read env overrides and fallback to defaults per key.
        Dependent Functions and Classes: none beyond os module.
        """
        return {
            "app": os.getenv("LIMIT_APP", defaults.get("app", "20 per minute")),
            "predict": os.getenv("LIMIT_PREDICT", defaults.get("predict", "10 per minute")),
        }

    def _build_backgrounds(self, defaults: Dict[str, str]) -> Dict[str, str]:
        """Purpose: merge hero background config with env overrides; Input Data: defaults from config.json; Output Data: dict mapping keys to static asset paths; Process: parse HERO_BACKGROUNDS JSON or fall back to defaults; Dependent Functions and Classes: json lib and LOGGER."""
        raw_value = os.getenv("HERO_BACKGROUNDS")
        if not raw_value:
            return defaults
        try:
            override = json.loads(raw_value)
            return {**defaults, **override}
        except json.JSONDecodeError:
            LOGGER.log_error("Invalid HERO_BACKGROUNDS override", depth=2)
            return defaults

    def _split_folders(self, raw_value: str) -> list[str]:
        """Split folder list safely.
        Purpose: normalize comma separated folder definitions.
        Input Data: combined string from env or config fallback.
        Output Data: list of folder strings without empties.
        Process: split on comma, strip segments, drop blanks.
        Dependent Functions and Classes: none.
        """
        return [segment.strip() for segment in raw_value.split(",") if segment.strip()]
