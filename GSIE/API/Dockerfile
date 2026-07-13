# GSIE API — Dockerfile multi-stage (DEC-000019 §18)
# Build : docker build -t gsie-api .
# Run : docker compose up
#
# Note : les libs géospatiales lourdes (GDAL, rasterio, geopandas) seront
# ajoutées en semaine 5 (GIS Engine). Pour la semaine 1, on n'a besoin que
# de FastAPI + asyncpg + Redis — image légère et build rapide.

LABEL org.opencontainers.image.title="GSIE API"
LABEL org.opencontainers.image.description="General System Intelligence Engine REST/WebSocket API"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/NeooeN45/Quintessences"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"

FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Dépendances système — minimales pour semaine 1 (asyncpg, shapely, pyproj)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip uv

# Copie du projet et installation des dépendances
COPY pyproject.toml README.md ./
COPY src/ src/
RUN uv pip install --system .

# --- Stage final ---
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Dépendances runtime (sans build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-c1v5 \
    libproj25 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 gsie

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=gsie:gsie src/ ./src/
COPY --chown=gsie:gsie pyproject.toml gunicorn.conf.py ./

USER gsie

EXPOSE 8000

# Gunicorn + SecureUvicornWorker (sans header Server, OWASP A05)
# Config dans gunicorn.conf.py (workers, keep-alive, max-requests, timeouts)
CMD ["gunicorn", "gsie_api.app:app", \
     "--config", "gunicorn.conf.py", \
     "-k", "gsie_api.worker.SecureUvicornWorker"]
