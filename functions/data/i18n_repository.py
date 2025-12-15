"""functions/data/i18n_repository.py
Purpose:
- Deliver vocabulary dictionaries for templating and validation.
Main Classes:
- I18NRepository: caches JSON payload and exposes language lookups.
Dependent Files:
- Depends on i18n.json provided at project root.
"""

import json
from functools import lru_cache
from typing import Any, Dict

from utils.logger import build_logger

LOGGER = build_logger("i18n_repository")

# --- VOCAB OPS ---

class I18NRepository:
    """Vocabulary accessor around i18n json file.
    Purpose: provide helper for retrieving localized copies of vocab data.
    Input Data: path to JSON file.
    Output Data: dictionaries keyed by language codes.
    Process: lazy load JSON and expose helper for retrieving sanitized vocab.
    Dependent Functions and Classes: json module and functools cache.
    """

    def __init__(self, file_path: str) -> None:
        """Constructor.
        Purpose: save JSON path for repeated lookups.
        Input Data: string path relative to project root.
        Output Data: none.
        Process: assign attribute and log file path.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        self.file_path = file_path
        LOGGER.log_debug(f"I18N file configured {file_path}", depth=1)

    def vocab_for(self, language_code: str) -> Dict[str, Any]:
        """Return vocabulary for requested language.
        Purpose: supply templates with localized copy for html labels.
        Input Data: two letter language code string.
        Output Data: dictionary containing html and lexical sections.
        Process: load file, fallback to english, return best match.
        Dependent Functions and Classes: _load_file helper.
        """
        payload = self._load_file()
        target = payload.get(language_code.lower())
        if target:
            return target
        LOGGER.log_debug("Language missing, falling back to en", depth=2)
        return payload.get("en", {})

    def industries(self) -> Dict[str, str]:
        """Expose english industries listing.
        Purpose: support persona validation reference data.
        Input Data: none.
        Output Data: dictionary of industries keyed by slug.
        Process: load english vocab and return industries block.
        Dependent Functions and Classes: _load_file helper.
        """
        return self._load_file().get("en", {}).get("industries", {})

    def business_problems(self) -> Dict[str, str]:
        """Expose english business problems listing.
        Purpose: support persona validation reference data.
        Input Data: none.
        Output Data: dictionary of problems keyed by slug.
        Process: load english vocab and return business_problems block.
        Dependent Functions and Classes: _load_file helper.
        """
        return self._load_file().get("en", {}).get("business_problems", {})

    @lru_cache(maxsize=1)
    def _load_file(self) -> Dict[str, Any]:
        """Load and cache JSON payload.
        Purpose: avoid repeated disk IO for each request.
        Input Data: none.
        Output Data: dictionary parsed from JSON file.
        Process: open resource, json.load content, return dictionary.
        Dependent Functions and Classes: json module for parsing.
        """
        with open(self.file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        LOGGER.log_debug("i18n.json loaded", depth=2)
        return data
