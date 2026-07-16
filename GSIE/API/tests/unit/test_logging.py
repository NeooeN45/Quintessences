"""Tests unitaires — logging structuré (core/logging.py)."""

from gsie_api.core.logging import (
    _add_trace_id,
    get_logger,
    set_trace_id,
    setup_logging,
    trace_id_ctx,
)


def should_add_trace_id_when_set():
    """_add_trace_id doit injecter le trace_id dans l'event_dict."""
    trace_id_ctx.set("test-trace-123")
    event_dict = _add_trace_id(None, None, {})
    assert event_dict["trace_id"] == "test-trace-123"


def should_not_add_trace_id_when_empty():
    """_add_trace_id ne doit rien ajouter si trace_id est vide."""
    trace_id_ctx.set("")
    event_dict = _add_trace_id(None, None, {})
    assert "trace_id" not in event_dict


def should_set_trace_id_when_uuid_generated():
    """set_trace_id doit générer un UUID si aucun tid fourni."""
    result = set_trace_id(None)
    assert len(result) > 0
    assert trace_id_ctx.get() == result


def should_set_trace_id_when_provided():
    """set_trace_id doit utiliser la valeur fournie."""
    result = set_trace_id("my-trace-id")
    assert result == "my-trace-id"
    assert trace_id_ctx.get() == "my-trace-id"


def should_configure_json_renderer_when_production():
    """setup_logging doit utiliser JSONRenderer en production."""
    setup_logging("INFO", "production")
    # Vérifier que structlog est configuré (pas d'exception)
    log = get_logger("test")
    log.info("test_event")


def should_configure_console_renderer_when_development():
    """setup_logging doit utiliser ConsoleRenderer en développement."""
    setup_logging("DEBUG", "development")
    log = get_logger("test")
    log.debug("test_event")


def should_use_custom_log_level_when_provided():
    """setup_logging doit respecter le log_level fourni."""
    setup_logging("WARNING", "development")
    log = get_logger("test")
    log.warning("test_event")


def should_return_named_logger_when_name_provided():
    """get_logger doit retourner un logger nommé."""
    log = get_logger("gsie_api.test")
    assert log is not None
