"""Configuration Gunicorn — durcissement et performance.

Référence : https://docs.gunicorn.org/en/stable/configure.html
"""

import os


def _positive_int(name: str, default: int) -> int:
    """Lit un entier strictement positif ou refuse le démarrage."""
    raw_value = os.environ.get(name, str(default))
    value = int(raw_value)
    if value <= 0:
        raise ValueError(f"{name} doit être strictement positif")
    return value


# Workers : nombre fixe, cohérent avec config.py Settings.gunicorn_workers
# (le pool sizing PostgreSQL/PgBouncer est calculé pour ce nombre exact de
# workers — voir validate_production_security dans core/config.py).
# Surchargeable via GSIE_GUNICORN_WORKERS pour les déploiements à capacité
# différente, mais db_pool_size/db_max_overflow doivent être réajustés en
# conséquence pour respecter max_connections.
workers = _positive_int("GSIE_GUNICORN_WORKERS", 5)

# Worker class : SecureUvicornWorker (supprime header Server — OWASP A05)
worker_class = "gsie_api.worker.SecureUvicornWorker"

# Connexions concurrentes par worker (ASGI)
worker_connections = 1000

# Bind
bind = "0.0.0.0:8000"

# Performance
keepalive = 5  # secondes — réutilise les connexions TCP

# Anti-fuite mémoire : recycle les workers après N requêtes. Le jitter est
# volontairement du même ordre que le seuil afin d'éviter que les cinq workers
# atteignent leur limite dans une même fenêtre sous charge homogène.
max_requests = _positive_int("GSIE_GUNICORN_MAX_REQUESTS", 5000)
max_requests_jitter = _positive_int("GSIE_GUNICORN_MAX_REQUESTS_JITTER", 5000)

# Timeouts
graceful_timeout = 30  # timeout propre avant SIGKILL
timeout = 30  # timeout par requête

# Logging
accesslog = "-"
errorlog = "-"

# Sécurité — désactive le header Server (anti-fingerprinting OWASP A05)
# SecureUvicornWorker configure server_header=False et date_header=False
