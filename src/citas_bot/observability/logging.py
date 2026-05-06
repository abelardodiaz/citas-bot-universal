"""Structured logging configuration.

Two render modes:
- console: human-friendly colored output for development
- json: machine-parseable for production log aggregators (Loki, ELK, etc.)
"""

from __future__ import annotations

import logging
import sys
from typing import Literal

import structlog
from structlog.types import Processor


def configure_logging(level: str = "INFO", format: Literal["console", "json"] = "console") -> None:
    """Configure structlog and stdlib logging.

    Idempotent: safe to call multiple times (e.g., once at startup, once per
    test setup). Existing handlers on the root logger are replaced.
    """

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level.upper(),
        force=True,
    )

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    renderer: Processor
    if format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound logger for the given module."""

    return structlog.get_logger(name)
