"""Structured JSON-lines logging for the Lince Investor Suite.

Every program in the Suite can opt into a single rotating log file at
``~/.local/state/lynx/<program>.log`` (or the XDG ``state`` dir on
platforms that set it). One JSON object per line — easy to grep with
``jq`` or ingest into any observability pipeline.

Usage
-----

```python
from lynx_investor_core.logging import get_logger

log = get_logger("lynx-mining")
log.info("starting analysis", extra={"ticker": "NEM"})
log.warning("cache miss", extra={"ticker": "NEM", "reason": "network"})
```

The module is intentionally small — it configures a single
:class:`logging.Logger` per program name with a rotating file handler
and a JSON formatter. No dependencies beyond the stdlib.

Environment overrides
---------------------

* ``LYNX_LOG_DIR`` — override the log directory.
* ``LYNX_LOG_LEVEL`` — ``DEBUG`` / ``INFO`` / ``WARNING`` / ``ERROR``
  (default ``INFO``).
* ``LYNX_LOG_STDERR`` — ``1`` to mirror to stderr (useful during
  development; the terminal UI usually wants quiet logs).
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


__all__ = ["get_logger", "get_log_dir", "JSONFormatter"]


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------

_STANDARD_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "asctime", "taskName",
}


class JSONFormatter(logging.Formatter):
    """Format every log record as a single-line JSON object.

    Any ``extra={...}`` keys passed to the logger appear as top-level
    keys in the output — no need to use the ``%(foo)s`` format syntax.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                try:
                    json.dumps(value)
                    payload[key] = value
                except TypeError:
                    payload[key] = repr(value)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def get_log_dir() -> Path:
    """Return the directory where log files are written."""
    override = os.environ.get("LYNX_LOG_DIR")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "state"
    return base / "lynx"


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

_LOGGERS: Dict[str, logging.Logger] = {}


def _level_from_env(default: int = logging.INFO) -> int:
    raw = os.environ.get("LYNX_LOG_LEVEL", "").upper().strip()
    if not raw:
        return default
    mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return mapping.get(raw, default)


def get_logger(
    name: str,
    *,
    log_dir: Optional[Path] = None,
    level: Optional[int] = None,
    max_bytes: int = 5_000_000,
    backup_count: int = 3,
    stderr: Optional[bool] = None,
) -> logging.Logger:
    """Return a JSON-line logger named *name*.

    Repeated calls with the same name return the same logger (idempotent).
    Use one call per program startup — typically ``get_logger("lynx-mining")``
    right after ``argparse`` finishes.
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    lg = logging.getLogger(f"lynx.{name}")
    lg.setLevel(level if level is not None else _level_from_env())
    lg.propagate = False

    # Avoid double-handlers if somehow get_logger is called with the same
    # logger name via stdlib.
    for h in list(lg.handlers):
        lg.removeHandler(h)

    directory = log_dir or get_log_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{name}.log"
        fh = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=max_bytes, backupCount=backup_count,
            encoding="utf-8",
        )
        fh.setFormatter(JSONFormatter())
        lg.addHandler(fh)
    except OSError:
        # Read-only filesystem or no permission — the log is best-effort,
        # swallow and continue to stderr-only (or nothing).
        pass

    if stderr is None:
        stderr = os.environ.get("LYNX_LOG_STDERR") == "1"
    if stderr:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(JSONFormatter())
        lg.addHandler(sh)

    _LOGGERS[name] = lg
    return lg
