"""Tests unitaires — worker Gunicorn (worker.py).

Note : gunicorn nécessite fcntl (Unix-only). Sur Windows, on teste
que SecureUvicornWorker est None (fallback). Sur Unix, on teste
l'héritage et les CONFIG_KWARGS.
"""

import sys


def should_be_none_when_windows():
    """Sur Windows, SecureUvicornWorker doit être None (gunicorn indisponible)."""
    if sys.platform == "win32":
        from gsie_api.worker import SecureUvicornWorker
        assert SecureUvicornWorker is None
    else:
        from gsie_api.worker import SecureUvicornWorker
        import uvicorn.workers
        assert issubclass(SecureUvicornWorker, uvicorn.workers.UvicornWorker)
        assert SecureUvicornWorker.CONFIG_KWARGS["server_header"] is False
        assert SecureUvicornWorker.CONFIG_KWARGS["date_header"] is False
