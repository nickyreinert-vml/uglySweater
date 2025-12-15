"""functions/api/prediction_service.py
Purpose:
- Wrap OpenAI Assistants API interactions for persona predictions.
Main Classes:
- PredictionService: ensures threads exist and runs predictions safely.
Dependent Files:
- Requires SessionRepository for error logging and persona context.
"""

from __future__ import annotations

from typing import Any, Dict

from utils.logger import build_logger

LOGGER = build_logger("prediction_service")

# --- AI OPS ---

class PredictionService:
    """Coordinate OpenAI thread lifecycle and message processing.
    Purpose: shield route handlers from API specifics.
    Input Data: OpenAI client instance and session repository.
    Output Data: textual responses from assistant runs.
    Process: create thread, send prompt, poll run, parse result.
    Dependent Functions and Classes: OpenAI beta threads API.
    """

    def __init__(self, client, session_repo) -> None:
        """Constructor.
        Purpose: store OpenAI client and repository dependencies.
        Input Data: openai.OpenAI client and SessionRepository instance.
        Output Data: none.
        Process: assign attributes and log readiness.
        Dependent Functions and Classes: LOGGER for diagnostics.
        """
        self.client = client
        self.session_repo = session_repo
        LOGGER.log_debug("PredictionService initialized", depth=1)

    def ensure_thread(self, session_store) -> bool:
        """Guarantee session contains thread identifier.
        Purpose: reuse assistant threads for consecutive predictions.
        Input Data: Flask session dictionary.
        Output Data: boolean success flag.
        Process: return existing id or create new via _create_thread.
        Dependent Functions and Classes: _create_thread helper.
        """
        if session_store.get("thread_id"):
            return True
        thread_id = self._create_thread()
        if not thread_id:
            return False
        session_store["thread_id"] = thread_id
        return True

    def run_prediction(self, session_store, persona: Dict[str, str], vocab: Dict[str, Any]) -> Dict[str, Any]:
        """Execute assistant run and return formatted response.
        Purpose: send persona prompt, poll run, clean annotations.
        Input Data: Flask session, persona dict, vocabulary dict.
        Output Data: dictionary containing status and response text.
        Process: ensure thread, dispatch prompt, poll run, sanitize response.
        Dependent Functions and Classes: helper methods inside class.
        """
        if not self.ensure_thread(session_store):
            return {"status": "error", "message": "thread_error"}
        prompt = self._build_prompt(persona, vocab)
        try:
            message = self._send_prompt(session_store["thread_id"], prompt)
            run = self._start_run(session_store["thread_id"])
            payload = self._poll_run(session_store["thread_id"], run.id)
            content = self._extract_message(payload)
        except Exception as exc:
            self.session_repo.log_error(session_store, str(exc), persona)
            return {"status": "error", "message": "openai_error"}
        return {"status": "success", "data": {"response": content}}

    def _create_thread(self) -> str | None:
        """Create OpenAI thread and return id.
        Purpose: abstract OpenAI call for easier testing.
        Input Data: none beyond configured client.
        Output Data: thread id string or None on failure.
        Process: call client beta threads create and capture id.
        Dependent Functions and Classes: OpenAI client.
        """
        try:
            thread = self.client.beta.threads.create()
            return thread.id
        except Exception as exc:
            LOGGER.log_error(f"Thread creation failed: {exc}", depth=2)
            return None

    def _send_prompt(self, thread_id: str, prompt: str):
        """Append user message to thread.
        Purpose: keep run_prediction slim and testable.
        Input Data: thread identifier and prompt string.
        Output Data: OpenAI message object.
        Process: call messages.create via client.
        Dependent Functions and Classes: OpenAI client.
        """
        return self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt,
        )

    def _start_run(self, thread_id: str):
        """Start assistant run.
        Purpose: trigger assistant processing for the prepared thread.
        Input Data: thread id string.
        Output Data: run object reference.
        Process: call runs.create with assistant id from env.
        Dependent Functions and Classes: OpenAI client and env var.
        """
        import os

        assistant_id = os.environ.get("ASSISTANT_ID")
        return self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

    def _poll_run(self, thread_id: str, run_id: str):
        """Poll OpenAI run for completion.
        Purpose: block until status completed or raise error.
        Input Data: thread id and run id strings.
        Output Data: messages list once completed.
        Process: loop retrieval calls, stop on completion or unexpected state.
        Dependent Functions and Classes: OpenAI client.
        """
        attempts = 0
        while attempts < 20:
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.status == "completed":
                return self.client.beta.threads.messages.list(thread_id=thread_id)
            if run.status not in {"queued", "in_progress"}:
                raise RuntimeError(f"unexpected run status {run.status}")
            attempts += 1
        raise RuntimeError("run timeout")

    def _extract_message(self, messages) -> str:
        """Parse assistant text output.
        Purpose: drop annotations and return clean string.
        Input Data: OpenAI message list response.
        Output Data: response text string.
        Process: fetch first message, remove annotation text, return value.
        Dependent Functions and Classes: OpenAI response schema.
        """
        content = messages.data[0].content[0].text
        for annotation in content.annotations:
            content.value = content.value.replace(annotation.text, "")
        return content.value

    def _build_prompt(self, persona: Dict[str, str], vocab: Dict[str, Any]) -> str:
        """Prepare prompt string for persona.
        Purpose: instruct assistant using selected language label.
        Input Data: persona dictionary and vocabulary map.
        Output Data: formatted string prompt.
        Process: embed industry, problem, and required language info.
        Dependent Functions and Classes: none.
        """
        language_name = vocab.get("_language", "English")
        return (
            f"I am working in `{persona['industry']}` and I am concerned about "
            f"{persona['businesProblem']}. IMPORTANT: respond in {language_name}."
        )
