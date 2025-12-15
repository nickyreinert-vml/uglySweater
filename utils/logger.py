"""utils/logger.py
Purpose:
- Provide a shared logging helper with indentation based depth markers.
Main Functions:
- build_logger: configure and cache application wide logger instances.
Dependent Files:
- Relied on by service modules to emit structured log output.
"""

import logging
import os
from typing import Dict

# --- LOGGER BUILDERS ---

def build_logger(name: str) -> "StructuredLogger":
    """Create logger adapter.
    Purpose: instantiate a structured logger with depth based indentation.
    Input Data: name for the python logger namespace.
    Output Data: StructuredLogger instance ready for use elsewhere.
    Process: configures handlers once, applies env level and wraps adapter.
    Dependent Functions and Classes: StructuredLogger class below.
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = _level_mapping().get(level, logging.INFO)
    base_logger = logging.getLogger(name)
    if not base_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        base_logger.addHandler(handler)
    base_logger.setLevel(numeric_level)
    return StructuredLogger(base_logger)


# --- LOGGER UTILITIES ---

def _level_mapping() -> Dict[str, int]:
    """Map textual levels.
    Purpose: Provide a reusable lookup for python logging levels.
    Input Data: none.
    Output Data: dict mapping level names to numeric codes.
    Process: returns constant dictionary for repeated use.
    Dependent Functions and Classes: none.
    """
    return {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "ERROR": logging.ERROR}


class StructuredLogger:
    """Adapter adding depth aware helpers around logging.Logger.
    Purpose: simplify depth aware debug, info, and error logging.
    Input Data: python logger passed at construction.
    Output Data: formatted log lines written through logging handlers.
    Process: expose helper methods that prepend indentation and fan out.
    Dependent Functions and Classes: python logging.Logger infrastructure.
    """

    def __init__(self, logger: logging.Logger):
        """StructuredLogger constructor.
        Purpose: store the wrapped logging.Logger reference.
        Input Data: logger instance produced by logging.getLogger.
        Output Data: none, sets up object state.
        Process: assigns logger to private attribute for later use.
        Dependent Functions and Classes: relies on logging.Logger.
        """
        self._logger = logger

    def log_debug(self, message: str, depth: int = 0) -> None:
        """Emit depth aware debug entry.
        Purpose: write debug information conditioned on log level.
        Input Data: message string and optional depth integer.
        Output Data: none, side effect is logger output.
        Process: format message with indentation then delegate to logging.
        Dependent Functions and Classes: uses _format helper and logging.Logger.
        """
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(self._format(message, depth))

    def log_info(self, message: str, depth: int = 0) -> None:
        """Emit depth aware info entry.
        Purpose: write info lines with indentation markers.
        Input Data: message string and optional depth integer.
        Output Data: none, side effect is logger output.
        Process: format message then call logger.info.
        Dependent Functions and Classes: uses _format helper and logging.Logger.
        """
        self._logger.info(self._format(message, depth))

    def log_error(self, message: str, depth: int = 0) -> None:
        """Emit depth aware error entry.
        Purpose: centralize error logging with indentation.
        Input Data: message string and optional depth integer.
        Output Data: none, side effect is logger output.
        Process: format message then call logger.error.
        Dependent Functions and Classes: uses _format helper and logging.Logger.
        """
        self._logger.error(self._format(message, depth))

    def _format(self, message: str, depth: int) -> str:
        """Prefix message with indentation.
        Purpose: create visual depth cues in log output.
        Input Data: raw message and desired depth integer.
        Output Data: formatted string with leading spaces.
        Process: multiply space by depth and concate with message.
        Dependent Functions and Classes: none beyond builtin string ops.
        """
        indent = " " * max(depth, 0) * 2
        return f"{indent}{message}"
