"""functions/data/persona_validator.py
Purpose:
- Sanitize and validate persona payloads submitted by the frontend.
Main Classes:
- PersonaValidator: cleans persona text and enforces whitelist membership.
Dependent Files:
- Pulls dictionaries from I18NRepository for allowed values.
"""

from typing import Dict, Tuple

import bleach

from utils.logger import build_logger

LOGGER = build_logger("persona_validator")

# --- PERSONA OPS ---

class PersonaValidator:
    """Clean and validate persona dictionaries.
    Purpose: ensure payloads contain expected keys before predictions run.
    Input Data: dictionaries of allowed industries and business problems.
    Output Data: sanitized payloads flagged as valid or invalid.
    Process: store allowed sets then expose sanitize plus validate helpers.
    Dependent Functions and Classes: bleach for HTML sanitization.
    """

    def __init__(self, industries: Dict[str, str], problems: Dict[str, str]) -> None:
        """Constructor.
        Purpose: cache set based lookups for validation speed.
        Input Data: industries and business problem dictionaries.
        Output Data: none.
        Process: convert keys to sets for membership checks.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        self.allowed_industries = set(industries.keys())
        self.allowed_problems = set(problems.keys())
        LOGGER.log_debug("PersonaValidator initialized", depth=1)

    def sanitize(self, persona: Dict[str, str]) -> Dict[str, str]:
        """Clean persona fields.
        Purpose: remove unsafe characters to block injection attempts.
        Input Data: raw persona dictionary from request JSON.
        Output Data: sanitized dictionary with trimmed strings.
        Process: iterate supported keys and apply bleach.clean.
        Dependent Functions and Classes: bleach.clean for sanitization.
        """
        clean_data = {}
        for key in ("industry", "businesProblem"):
            raw_value = persona.get(key, "") or ""
            clean_data[key] = bleach.clean(str(raw_value)).strip()
        return clean_data

    def is_valid(self, persona: Dict[str, str]) -> Tuple[bool, Dict[str, str]]:
        """Validate persona dictionary.
        Purpose: confirm sanitized values exist within allow lists.
        Input Data: raw persona dictionary from API request.
        Output Data: tuple(boolean, sanitized dict).
        Process: sanitize payload then test membership for both fields.
        Dependent Functions and Classes: sanitize helper.
        """
        sanitized = self.sanitize(persona)
        is_industry = sanitized.get("industry") in self.allowed_industries
        is_problem = sanitized.get("businesProblem") in self.allowed_problems
        return is_industry and is_problem, sanitized
