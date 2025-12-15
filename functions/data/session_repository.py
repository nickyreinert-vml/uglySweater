"""functions/data/session_repository.py
Purpose:
- Provide SQLite backed persistence for sessions, requests, and audit logs.
Main Classes:
- SessionRepository: handles schema management and CRUD logging helpers.
Dependent Files:
- Requires config loader for database path configuration.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, Iterable, Tuple

from utils.logger import build_logger

LOGGER = build_logger("session_repository")

# --- SCHEMA OPS ---

class SessionRepository:
    """Purpose: manage SQLite analytics tables; Input Data: SQLite db path; Output Data: persisted telemetry rows; Process: create schema plus CRUD helpers; Dependent Functions and Classes: sqlite3 module."""

    def __init__(self, db_path: str) -> None:
        """Purpose: store database path for reuse; Input Data: SQLite path string; Output Data: none; Process: assign attribute and log configuration; Dependent Functions and Classes: LOGGER."""
        self.db_path = db_path
        LOGGER.log_debug(f"SessionRepository using {db_path}", depth=1)

    def init_schema(self) -> None:
        """Purpose: ensure schema exists; Input Data: none; Output Data: tables on disk; Process: run CREATE statements then optional ALTERs; Dependent Functions and Classes: _schema_statements helper."""
        for statement in self._schema_statements():
            self._execute(statement)
        for alteration in self._alter_statements():
            self._execute(alteration, allow_failure=True)

    def _schema_statements(self) -> Iterable[str]:
        """Purpose: centralize CREATE TABLE SQL; Input Data: none; Output Data: iterable of SQL strings; Process: return tuple covering all tables; Dependent Functions and Classes: none."""
        return (
            """CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, referrer TEXT, utm TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, industry TEXT, businesProblem TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS tampering (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, industry TEXT, businesProblem TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS downloads (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, industry TEXT, businesProblem TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS errors (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, industry TEXT, businesProblem TEXT, error TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""",
        )

    def _alter_statements(self) -> Iterable[str]:
        """Purpose: provide ALTER TABLE SQL for migrations; Input Data: none; Output Data: iterable of ALTER statements; Process: return tuple executed with allow_failure; Dependent Functions and Classes: none."""
        return (
            "ALTER TABLE sessions ADD COLUMN utm TEXT",
            "ALTER TABLE errors ADD COLUMN error TEXT",
        )

    def log_session(self, flask_session: Dict[str, Any], request_obj: Any) -> None:
        """Purpose: capture new session analytics; Input Data: Flask session and request; Output Data: inserted sessions row; Process: collect thread id, referrer, utm params then insert; Dependent Functions and Classes: _execute helper."""
        payload = (
            flask_session.get("thread_id"),
            getattr(request_obj, "referrer", None),
            json.dumps(self._extract_utm(request_obj)),
        )
        self._execute(
            "INSERT INTO sessions (session_id, referrer, utm) VALUES (?, ?, ?)", payload
        )

    def log_error(self, flask_session: Dict[str, Any], error: str, persona: Dict[str, Any]) -> None:
        """Purpose: persist backend error event; Input Data: session dict, error string, persona dict; Output Data: inserted errors row; Process: build tuple and execute insert; Dependent Functions and Classes: _execute helper."""
        payload = (
            flask_session.get("thread_id"),
            persona.get("industry", "unknown"),
            persona.get("businesProblem", "unknown"),
            error,
        )
        self._execute(
            "INSERT INTO errors (session_id, industry, businesProblem, error) VALUES (?, ?, ?, ?)",
            payload,
        )

    def log_request(self, flask_session: Dict[str, Any], persona: Dict[str, Any]) -> None:
        """Purpose: record successful prediction request; Input Data: session dict and persona payload; Output Data: inserted requests row; Process: map persona fields to tuple and execute insert; Dependent Functions and Classes: _execute helper."""
        payload = (
            flask_session.get("thread_id"),
            persona.get("industry"),
            persona.get("businesProblem"),
        )
        self._execute(
            "INSERT INTO requests (session_id, industry, businesProblem) VALUES (?, ?, ?)",
            payload,
        )

    def log_tampering(self, flask_session: Dict[str, Any], persona: Dict[str, Any]) -> None:
        """Purpose: track invalid persona attempts; Input Data: session dict and persona dict; Output Data: inserted tampering row; Process: build tuple with persona metadata and insert; Dependent Functions and Classes: _execute helper."""
        payload = (
            flask_session.get("thread_id"),
            persona.get("industry"),
            persona.get("businesProblem"),
        )
        self._execute(
            "INSERT INTO tampering (session_id, industry, businesProblem) VALUES (?, ?, ?)",
            payload,
        )

    def log_download(self, flask_session: Dict[str, Any]) -> None:
        """Purpose: track download endpoint usage; Input Data: session dict with cached persona fields; Output Data: inserted download row; Process: gather session metadata and execute insert; Dependent Functions and Classes: _execute helper."""
        payload = (
            flask_session.get("thread_id"),
            flask_session.get("industry"),
            flask_session.get("businesProblem"),
        )
        self._execute(
            "INSERT INTO downloads (session_id, industry, businesProblem) VALUES (?, ?, ?)",
            payload,
        )

    def fetch_logs(self) -> Dict[str, Any]:
        """Purpose: supply controller with analytics bundles; Input Data: none; Output Data: dict mapping query names to rows; Process: iterate query map executing via _fetch_all; Dependent Functions and Classes: _log_queries, _fetch_all."""
        return {key: self._fetch_all(sql) for key, sql in self._log_queries().items()}

    def _log_queries(self) -> Dict[str, str]:
        """Purpose: centralize analytics SQL; Input Data: none; Output Data: mapping of report names to SELECT statements; Process: return constant dict; Dependent Functions and Classes: fetch_logs consumer."""
        return {
            "unique_sessions_per_day": "SELECT DATE(timestamp) as day, COUNT(DISTINCT session_id) as count FROM sessions GROUP BY day",
            "unique_referrers": "SELECT referrer, COUNT(DISTINCT session_id) as count FROM sessions GROUP BY referrer",
            "industry_counts": "SELECT industry, COUNT(*) as count FROM requests GROUP BY industry",
            "business_problem_counts": "SELECT businesProblem, COUNT(*) as count FROM requests GROUP BY businesProblem",
            "unique_requests_per_day": "SELECT DATE(timestamp) as day, COUNT(DISTINCT session_id) as count FROM requests GROUP BY day",
            "request_counts": "SELECT industry, businesProblem, COUNT(*) as count FROM requests GROUP BY industry, businesProblem",
            "tampering": "SELECT DATE(timestamp) as day, industry, businesProblem, COUNT(*) as count FROM tampering GROUP BY day, industry, businesProblem",
            "download_counts": "SELECT industry, businesProblem, COUNT(*) as count FROM downloads GROUP BY industry, businesProblem",
            "errors": "SELECT DATE(timestamp) as day, industry, businesProblem, error FROM errors",
        }

    def _extract_utm(self, request_obj: Any) -> Dict[str, Any]:
        """Purpose: capture UTM metadata; Input Data: Flask request with args; Output Data: dict of allowed UTM keys; Process: iterate whitelist and read args; Dependent Functions and Classes: Flask request object."""
        keys = [
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
        ]
        return {key: request_obj.args.get(key) for key in keys}

    def _execute(self, sql: str, params: Tuple[Any, ...] | None = None, allow_failure: bool = False) -> None:
        """Purpose: centralize writes; Input Data: SQL string, params tuple, allow_failure flag; Output Data: none; Process: run statement within connection and commit, handling errors; Dependent Functions and Classes: sqlite3 module, LOGGER."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(sql, params or tuple())
                conn.commit()
        except sqlite3.Error as exc:
            if allow_failure:
                LOGGER.log_debug(f"Non critical migration issue: {exc}", depth=3)
                return
            LOGGER.log_error(f"Database write failed: {exc}", depth=3)

    def _fetch_all(self, sql: str) -> list[Tuple[Any, ...]]:
        """Purpose: wrap read operations; Input Data: SQL select string; Output Data: list of tuples; Process: open connection, execute, fetchall; Dependent Functions and Classes: sqlite3 module."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(sql)
            return cursor.fetchall()
