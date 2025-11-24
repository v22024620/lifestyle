"""Logging utilities with structured context support."""
import logging
from typing import Optional


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with consistent format including context placeholders."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger instance, defaulting to root."""
    return logging.getLogger(name)


def bind_context(logger: logging.Logger, **kwargs) -> logging.LoggerAdapter:
    """Attach contextual metadata (e.g., trace_id, studio_id) to logs."""
    return logging.LoggerAdapter(logger, kwargs)
