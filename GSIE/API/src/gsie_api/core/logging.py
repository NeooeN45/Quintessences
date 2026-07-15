"""Logging structuré — structlog + correlation ID (CON-005 traçabilité).

Format JSON en production, console en développement.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import cast

import structlog
from structlog.typing import EventDict, WrappedLogger

# Contexte de requête — trace_id propagé via contextvars
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")


def _add_trace_id(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Injecte le trace_id dans chaque log (CON-005)."""
    tid = trace_id_ctx.get()
    if tid:
        event_dict["trace_id"] = tid
    return event_dict


def setup_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """Configure structlog avec format JSON en production, console en dev."""
    is_production = environment == "production"

    renderer = (
        structlog.processors.JSONRenderer()
        if is_production
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_trace_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def set_trace_id(tid: str | None = None) -> str:
    """Définit le trace_id pour la requête courante. Retourne la valeur définie."""
    value = tid or str(uuid.uuid4())
    trace_id_ctx.set(value)
    return value


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Retourne un logger structlog nommé."""
    return cast("structlog.stdlib.BoundLogger", structlog.get_logger(name))
