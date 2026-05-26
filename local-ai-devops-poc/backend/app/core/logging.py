"""
Logging configuration for local-ai-devops-poc.

Strategy
--------
- In local/dev: human-readable text via StreamHandler.
- In prod/docker: JSON output so CloudWatch Logs Insights can query fields
  with ``filter @message like /model_chat_complete/`` or
  ``stats avg(elapsed_ms) by model``.

Usage
-----
Call ``configure_logging(level, json_logs)`` once at application startup
(``app/main.py``).  All other modules use the standard ``logging`` module::

    import logging
    logger = logging.getLogger("local_ai_devops")
    logger.info("rag_ingest_ok", extra={"collection": name, "chunks": n})

CloudWatch note
---------------
When running in ECS, stdout/stderr is automatically forwarded to the log
group configured in the task definition.  No SDK calls are needed.
"""
from __future__ import annotations

import json
import logging
import sys
import time


class _JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Extra fields passed via the ``extra=`` kwarg appear as top-level keys so
    CloudWatch Logs Insights can filter/aggregate them without parsing strings.
    """

    # Fields that come from LogRecord and are not useful as JSON extra keys.
    _RESERVED = frozenset(
        logging.LogRecord("", 0, "", 0, None, None, None).__dict__.keys()
    )

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }
        # Attach any extra fields the caller provided.
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    """Configure root logger and the project logger.

    Parameters
    ----------
    level:
        Log level string, e.g. ``"INFO"``, ``"DEBUG"``.
    json_logs:
        When ``True`` emit JSON (suitable for CloudWatch / production).
        When ``False`` emit coloured text (suitable for local development).
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())

    if json_logs:
        handler.setFormatter(_JSONFormatter())
    else:
        # Plain text: easier to read during local development.
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    # Remove default handlers, then add ours (``force=True`` equivalent for 3.8+).
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers to keep output readable.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
