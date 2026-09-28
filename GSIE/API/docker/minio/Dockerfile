# syntax=docker/dockerfile:1.7
# MinIO de développement/CI : les anciennes images amont sont indisponibles.
# Sources figées ; aucun téléchargement de binaire depuis un miroir tiers.
FROM golang:1.26-bookworm@sha256:a688600ca24f8a4d3ca77f95b0dd40704a9fc787c826660eb7ba0b641b8b175d AS builder
ENV CGO_ENABLED=0 GOTOOLCHAIN=local
WORKDIR /src

FROM builder AS server-build
ADD https://github.com/minio/minio.git#9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a /src
RUN go build -mod=readonly -trimpath -o /out/minio .

FROM builder AS client-build
ADD https://github.com/minio/mc.git#7394ce0dd2a80935aded936b09fa12cbb3cb8096 /src
RUN go build -mod=readonly -trimpath -o /out/mc .

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
