"""Worker Uvicorn custom — désactive le header Server (anti-fingerprinting).

Uvicorn ajoute le header `Server: uvicorn` après le middleware ASGI.
Pour le supprimer, on sous-classe UvicornWorker et on désactive server_header.
"""

import uvicorn.workers


class SecureUvicornWorker(uvicorn.workers.UvicornWorker):
    """UvicornWorker sans header Server (OWASP A05 anti-fingerprinting)."""

    CONFIG_KWARGS = {
        "server_header": False,
        "date_header": False,
    }
