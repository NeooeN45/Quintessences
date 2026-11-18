# syntax=docker/dockerfile:1.7
# MinIO de développement et de CI — SOLUTION PROVISOIRE (voir README.md).
#
# L'édition communautaire de MinIO n'est plus distribuée sous forme d'image ni
# de binaire par son éditeur, et ses dépôts amont sont archivés. Le serveur et
# le client sont donc construits depuis des archives de sources officielles
# épinglées par commit et vérifiées par empreinte SHA-256 à chaque construction.
# Aucun binaire n'est téléchargé depuis un miroir tiers.
#
# Empreintes : relevées le 2026-11-16 (GSIE-PROMPT-0034, bilan
# 23_QUALITY_MANAGEMENT/AUDITS/LEVEE_BLOCAGES_PR74_2026-11-16.md §7.1).
# Une empreinte différente fait échouer la construction : ne jamais la
# remplacer sans revérifier la source et consigner le changement.
FROM golang:1.26-bookworm@sha256:a688600ca24f8a4d3ca77f95b0dd40704a9fc787c826660eb7ba0b641b8b175d AS builder
ENV CGO_ENABLED=0 GOTOOLCHAIN=local GOFLAGS=-mod=readonly
WORKDIR /src

# Serveur — RELEASE.2025-10-15T17-29-55Z, corrige CVE-2025-62506.
FROM builder AS server-build
ADD --checksum=sha256:45521908307306e925c98d629e1c17d78c8b72b6ee242b1bfb1409f7d8ee5841 \
    https://codeload.github.com/minio/minio/tar.gz/9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a \
    /tmp/minio.tar.gz
RUN tar -xzf /tmp/minio.tar.gz --strip-components=1 -C /src \
    && go mod verify \
    && go build -trimpath -o /out/minio .

# Client — RELEASE.2025-08-13T08-35-41Z.
FROM builder AS client-build
ADD --checksum=sha256:95cd293c7119f16921a6dc515a1fb74a2227f19fd994b9c8b770a154e802ac44 \
    https://codeload.github.com/minio/mc/tar.gz/7394ce0dd2a80935aded936b09fa12cbb3cb8096 \
    /tmp/mc.tar.gz
RUN tar -xzf /tmp/mc.tar.gz --strip-components=1 -C /src \
    && go mod verify \
    && go build -trimpath -o /out/mc .

FROM debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251 AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 minio \
    && useradd --uid 10001 --gid 10001 --no-create-home minio \
    && mkdir -p /data /tmp/minio-home \
    && chown 10001:10001 /data /tmp/minio-home
ENV HOME=/tmp/minio-home MC_CONFIG_DIR=/tmp/minio-home/.mc
USER 10001:10001

FROM runtime AS client
LABEL org.opencontainers.image.source="https://github.com/minio/mc" \
      org.opencontainers.image.revision="7394ce0dd2a80935aded936b09fa12cbb3cb8096" \
      org.opencontainers.image.licenses="AGPL-3.0-only"
COPY --from=client-build /out/mc /usr/local/bin/mc
COPY --from=client-build /src/LICENSE /licenses/mc-LICENSE
ENTRYPOINT ["/usr/local/bin/mc"]

FROM runtime AS server
LABEL org.opencontainers.image.source="https://github.com/minio/minio" \
      org.opencontainers.image.revision="9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a" \
      org.opencontainers.image.licenses="AGPL-3.0-only"
COPY --from=server-build /out/minio /usr/local/bin/minio
COPY --from=server-build /src/LICENSE /licenses/minio-LICENSE
EXPOSE 9000 9001
ENTRYPOINT ["/usr/local/bin/minio"]
CMD ["server", "/data"]
