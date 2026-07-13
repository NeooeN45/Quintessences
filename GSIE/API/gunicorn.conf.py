"""Configuration Gunicorn — durcissement et performance.

Référence : https://docs.gunicorn.org/en/stable/configure.html
"""

import multiprocessing

# Workers : 2×CPU + 1 (formule Gunicorn)
workers = multiprocessing.cpu_count() * 2 + 1

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
