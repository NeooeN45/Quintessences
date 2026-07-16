# GSIE API — Dockerfile multi-stage (DEC-000019 §18)
# Build : docker build -t gsie-api .
# Run : docker compose up
#
# Build reproductible : Rust Evidence Engine compilé via Maturin en stage
# dédié, puis installé dans l'image Python. Le fallback Python est
# conservé uniquement pour les builds de développement sans Rust.

FROM python:3.12-slim-bookworm AS builder

LABEL org.opencontainers.image.title="GSIE API"
LABEL org.opencontainers.image.description="General System Intelligence Engine REST/WebSocket API"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/NeooeN45/Quintessences"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"

WORKDIR /build

# Dépendances système — minimales pour semaine 1 (asyncpg, shapely, pyproj)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Rust toolchain (requis pour Maturin / PyO3)
ENV RUST_VERSION=1.80.0
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --default-toolchain $RUST_VERSION && \
    . "$HOME/.cargo/env" && \
    rustup component add clippy && \
    cargo install --locked maturin

# Build du moteur Rust (Evidence Engine)
WORKDIR /build/gsie_evidence
COPY GSIE/ENGINES/EVIDENCE_ENGINE/rust/pyproject.toml GSIE/ENGINES/EVIDENCE_ENGINE/rust/Cargo.toml ./
COPY GSIE/ENGINES/EVIDENCE_ENGINE/rust/Cargo.lock ./
COPY GSIE/ENGINES/EVIDENCE_ENGINE/rust/src ./src
RUN . "$HOME/.cargo/env" && \
    maturin build --release && \
    ls -la target/wheels

WORKDIR /build/api

# Dépendances Python
RUN pip install --no-cache-dir --upgrade pip uv

# Copie du projet API et installation des dépendances + wheel Rust
COPY GSIE/API/pyproject.toml GSIE/API/README.md ./
COPY GSIE/API/gunicorn.conf.py ./
COPY GSIE/API/src/ src/
COPY GSIE/API/alembic/ alembic/
COPY GSIE/API/alembic.ini ./
COPY GSIE/API/docker/ docker/
RUN uv pip install --system .
RUN uv pip install --system /build/gsie_evidence/target/wheels/gsie_evidence-*.whl

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
COPY --chown=gsie:gsie --from=builder /build/api/src/ ./src/
COPY --chown=gsie:gsie --from=builder /build/api/pyproject.toml /build/api/gunicorn.conf.py ./
# Alembic — migrations du schéma (lancées au démarrage par entrypoint.sh)
COPY --chown=gsie:gsie --from=builder /build/api/alembic/ ./alembic/
COPY --chown=gsie:gsie --from=builder /build/api/alembic.ini ./
# Script d'entrée — migrations Alembic puis démarrage Gunicorn
COPY --chown=gsie:gsie GSIE/API/docker/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

USER gsie

EXPOSE 8000

# Gunicorn + SecureUvicornWorker (sans header Server, OWASP A05)
# Config dans gunicorn.conf.py (workers, keep-alive, max-requests, timeouts)
# entrypoint.sh lance les migrations Alembic avant Gunicorn
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "gsie_api.app:app", \
     "--config", "gunicorn.conf.py", \
     "-k", "gsie_api.worker.SecureUvicornWorker"]
