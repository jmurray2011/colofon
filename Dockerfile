# Reproducible build toolchain for colofon Typst documents.
# The image carries ONLY the tools (Typst + veraPDF + a JRE); the repo is mounted at
# run time, so source and fonts are always live. Build the image with:
#   tools/prepare-toolcache.sh && docker build -t colofon/build .
# Then run `./build.sh` with the repository mounted at `/work`.
FROM eclipse-temurin:17-jre-jammy

ARG TYPST_VERSION=0.15.0
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl xz-utils ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Typst (pinned, static musl build - runs on any base)
RUN curl -fsSL "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz" -o /tmp/typst.tar.xz \
 && tar -xJf /tmp/typst.tar.xz -C /tmp \
 && mv /tmp/typst-x86_64-unknown-linux-musl/typst /usr/local/bin/typst \
 && chmod +x /usr/local/bin/typst \
 && rm -rf /tmp/typst.tar.xz /tmp/typst-x86_64-unknown-linux-musl \
 && typst --version

# veraPDF 1.30.x (validated copy, vendored via tools/prepare-toolcache.sh). It is a thin
# launcher that calls `java`, which the JRE base provides.
COPY tools/.toolcache/verapdf /opt/verapdf
RUN ln -s /opt/verapdf/verapdf /usr/local/bin/verapdf \
 && verapdf --version

WORKDIR /work
