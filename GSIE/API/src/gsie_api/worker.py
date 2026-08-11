"""Worker Uvicorn custom — désactive le header Server (anti-fingerprinting).

Uvicorn ajoute le header `Server: uvicorn` après le middleware ASGI.
Pour le supprimer, on sous-classe UvicornWorker et on désactive server_header.

Note : gunicorn nécessite fcntl (Unix-only). Sur Windows, ce module
est importé mais SecureUvicornWorker ne sera utilisé qu'en production
(Linux/Docker). La branche Unix est testée dans Docker.
"""

import sys

if sys.platform != "win32":  # pragma: no cover (Unix-only, testé dans Docker)
    import uvicorn.workers

    class SecureUvicornWorker(uvicorn.workers.UvicornWorker):
        """UvicornWorker sans header Server (OWASP A05 anti-fingerprinting)."""

        CONFIG_KWARGS = {
            "server_header": False,
            "date_header": False,
            # uvloop — boucle d’événements libuv, 2-4x plus rapide qu’asyncio
            # (veille techno 2026-08-02, RFC-0031 action 6, Linux uniquement)
            "loop": "uvloop",
        }
else:  # pragma: no cover (Windows-only, gunicorn non disponible sur Windows)
    # Windows : fallback — SecureUvicornWorker non disponible
    # (gunicorn ne tourne pas sur Windows, uniquement dans Docker/Linux)
    SecureUvicornWorker = None
