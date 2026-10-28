"""Logging for the server and the worker: readable text, or JSON lines for log collectors (Loki, ...).

Log calls pass context as `extra`, e.g. `log.info("Generated", extra={"design_id": ...})`;
the JSON format keeps it as fields, the text format appends it as key=value.
"""

import json
import logging
import sys
from datetime import UTC, datetime

from pic2cookie.settings import LogSettings

# Attributes every LogRecord has; anything else came in through `extra`.
_STANDARD = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "color_message",
}


def _context(record: logging.LogRecord) -> dict:
    return {k: v for k, v in record.__dict__.items() if k not in _STANDARD}


class TextFormatter(logging.Formatter):
    def __init__(self):
        super().__init__("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        line = super().format(record)
        if context := _context(record):
            line += "  " + " ".join(f"{k}={v}" for k, v in context.items())
        return line


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            **_context(record),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def setup(cfg: LogSettings) -> None:
    """Send all logs (ours and uvicorn's) to stderr in the configured format."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter() if cfg.format == "json" else TextFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(cfg.level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "rq.worker"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
    # Access logs hold visitors' IP addresses; a hosted instance may turn them off.
    logging.getLogger("uvicorn.access").disabled = not cfg.access
    for noisy in ("botocore", "boto3", "urllib3", "pymongo", "PIL", "trimesh"):
        logging.getLogger(noisy).setLevel(max(logging.WARNING, logging.getLevelName(cfg.level)))
