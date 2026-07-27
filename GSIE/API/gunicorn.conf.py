"""Configuration Gunicorn — durcissement et performance.

Référence : https://docs.gunicorn.org/en/stable/configure.html
"""

import os

# Workers : nombre fixe, cohérent avec config.py Settings.gunicorn_workers
# (le pool sizing PostgreSQL/PgBouncer est calculé pour ce nombre exact de
# workers — voir validate_production_security dans core/config.py).
# Surchargeable via GSIE_GUNICORN_WORKERS pour les déploiements à capacité
# différente, mais db_pool_size/db_max_overflow doivent être réajustés en
# conséquence pour respecter max_connections.
workers = int(os.environ.get("GSIE_GUNICORN_WORKERS", "5"))

# Worker class : SecureUvicornWorker (supprime header Server — OWASP A05)
worker_class = "gsie_api.worker.SecureUvicornWorker"

# Connexions concurrentes par worker (ASGI)
worker_connections = 1000

# Bind
bind = "0.0.0.0:8000"

# Performance
keepalive = 5  # secondes — réutilise les connexions TCP

# Anti-fuite mémoire : recycle les workers après N requêtes
max_requests = 1000
max_requests_jitter = 50  # évite la synchronisation des recycles

# Timeouts
graceful_timeout = 30  # timeout propre avant SIGKILL
timeout = 30  # timeout par requête

# Logging
accesslog = "-"
errorlog = "-"

# Sécurité — désactive le header Server (anti-fingerprinting OWASP A05)
# SecureUvicornWorker configure server_header=False et date_header=False
