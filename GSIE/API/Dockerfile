# syntax=docker/dockerfile:1.7
# GSIE API — Dockerfile multi-stage (DEC-000019 §18)
# Build : docker build -t gsie-api .
# Run : docker compose up
#
# Build reproductible : Rust Evidence Engine compilé via Maturin en stage
# dédié, puis installé dans l'image Python. Le fallback Python est
# conservé uniquement pour les builds de développement sans Rust.

FROM rust:1.85.0-slim-bookworm@sha256:1829c432be4a592f3021501334d3fcca24f238432b13306a4e62669dec538e52 AS rust-toolchain

FROM python:3.12-slim-bookworm@sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b AS builder

LABEL org.opencontainers.image.title="GSIE API"
LABEL org.opencontainers.image.description="General System Intelligence Engine REST/WebSocket API"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/NeooeN45/Quintessences"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"

WORKDIR /build

# Dépendances système — minimales pour semaine 1 (asyncpg, shapely, pyproj)
RUN apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=60 -o Acquire::https::Timeout=60 update \
    && apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=60 -o Acquire::https::Timeout=60 install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Environnement avec inspection HTTPS (par exemple Kaspersky) : l'autorité
# locale est fournie uniquement comme secret BuildKit et n'est jamais copiée
# dans le contexte ni conservée dans l'image finale. Sans secret, le build
# utilise le magasin de certificats standard de Debian.
RUN --mount=type=secret,id=gsie_host_ca,target=/run/secrets/gsie_host_ca,required=false \
    if [ -s /run/secrets/gsie_host_ca ]; then \
        install -m 0644 /run/secrets/gsie_host_ca /usr/local/share/ca-certificates/gsie-host-ca.crt; \
        update-ca-certificates; \
    fi

# Rust 1.85.0 provient d'une image officielle verrouillée par digest.
# Aucun script d'installation distant n'est exécuté pendant le build.
ENV CARGO_HOME="/usr/local/cargo" \
    RUSTUP_HOME="/usr/local/rustup" \
    PATH="/usr/local/cargo/bin:$PATH"
ENV MATURIN_VERSION=1.9.6
# uv utilise par défaut ses racines Mozilla embarquées. En présence d'une
# autorité d'inspection HTTPS injectée dans Debian par le secret BuildKit,
# il doit utiliser le magasin système (validation TLS conservée).
ENV UV_SYSTEM_CERTS=true
COPY --from=rust-toolchain /usr/local/cargo /usr/local/cargo
COPY --from=rust-toolchain /usr/local/rustup /usr/local/rustup
RUN rustup component add clippy && \
    cargo install --locked maturin --version $MATURIN_VERSION

# Build du moteur Rust (Evidence Engine)
WORKDIR /build/gsie_evidence
COPY GSIE/ENGINES/EVIDENCE_ENGINE/rust/pyproject.toml GSIE/ENGINES/EVIDENCE_ENGINE/rust/Cargo.toml ./
COPY GSIE/ENGINES/EVIDENCE_ENGINE/rust/Cargo.lock ./
COPY GSIE/ENGINES/EVIDENCE_ENGINE/rust/src ./src
RUN maturin build --release && \
    ls -la target/wheels

WORKDIR /build/api

# Dépendances Python
RUN pip install --no-cache-dir "uv==0.11.16"

# Copie du projet API et installation des dépendances + wheel Rust
COPY GSIE/API/pyproject.toml GSIE/API/uv.lock GSIE/API/README.md ./
COPY GSIE/API/gunicorn.conf.py ./
COPY GSIE/API/src/ src/
COPY GSIE/API/alembic/ alembic/
COPY GSIE/API/alembic.ini ./
COPY GSIE/API/docker/ docker/
RUN uv export --locked --no-dev --no-emit-project --output-file /tmp/requirements.txt \
    && uv pip install --system --require-hashes -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt
RUN uv pip install --system --no-deps .
RUN uv pip install --system /build/gsie_evidence/target/wheels/gsie_evidence-*.whl

# --- Stage final ---
FROM python:3.12-slim-bookworm@sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b AS runtime

WORKDIR /app

# Dépendances runtime (sans build-essential)
RUN apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=60 -o Acquire::https::Timeout=60 update \
    && apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=60 -o Acquire::https::Timeout=60 install -y --no-install-recommends \
    libgeos-c1v5 \
    libproj25 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 gsie

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=gsie:gsie --from=builder /build/api/src/ ./src/
COPY --chown=gsie:gsie --from=builder /build/api/pyproject.toml /build/api/gunicorn.conf.py ./
# Alembic — migrations du schéma (opération explicite, jamais automatique)
COPY --chown=gsie:gsie --from=builder /build/api/alembic/ ./alembic/
COPY --chown=gsie:gsie --from=builder /build/api/alembic.ini ./
# Manifeste canonique lu par le scheduler de santé (aucun dataset brut).
COPY --chown=gsie:gsie GSIE/DATASETS/REGISTRY_MANIFEST.json ./data/REGISTRY_MANIFEST.json
COPY --chown=gsie:gsie GSIE/DATASETS/FETCH_QUALIFICATION.json ./data/FETCH_QUALIFICATION.json
# Script d'entrée — garde de migration optionnelle puis démarrage Gunicorn
COPY --chown=gsie:gsie GSIE/API/docker/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

USER gsie

EXPOSE 8000

# Healthcheck embarqué — fonctionne hors docker-compose (K8s, Swarm, registry pull)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Gunicorn + SecureUvicornWorker (sans header Server, OWASP A05)
# Config dans gunicorn.conf.py (workers, keep-alive, max-requests, timeouts)
# entrypoint.sh ne migre que si les drapeaux opératoires sont explicitement fournis
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "gsie_api.app:app", \
     "--config", "gunicorn.conf.py", \
     "-k", "gsie_api.worker.SecureUvicornWorker"]
