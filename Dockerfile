# syntax=docker/dockerfile:1

# Pin the multi-architecture Temurin manifest. Dependabot updates the digest while
# retaining the human-readable Java/Jammy tag.
FROM eclipse-temurin:17-jre-jammy@sha256:e17d77fb030dd4b642dc078d048a5fb9efcb3676ee20305d905949105a6ccd5a AS tool-installer

ARG TARGETARCH
ARG TYPST_VERSION=0.15.0
ARG TYPST_SHA256_AMD64=59b207df01be2dab9f13e80f73d04d7ff8273ffd46b3dd1b9eef5c60f3eeabea
ARG TYPST_SHA256_ARM64=cdf50ffc7b8ba759ed02200632eda3d78eb8b99aacb6611f4f75684990647620
ARG VERAPDF_VERSION=1.30.2
ARG VERAPDF_SERIES=1.30
ARG VERAPDF_SHA256=6cc6341cb1af644044054b81f00a6590a7918abb18f762243de115258bcad838

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl unzip xz-utils \
 && rm -rf /var/lib/apt/lists/*

COPY tools/verapdf-install.xml /tmp/verapdf-install.xml

RUN set -eux; \
    archive=/tmp/verapdf-installer.zip; \
    folder="verapdf-greenfield-${VERAPDF_VERSION}"; \
    curl -fsSL \
      "https://software.verapdf.org/releases/${VERAPDF_SERIES}/${folder}-installer.zip" \
      -o "$archive"; \
    echo "${VERAPDF_SHA256}  ${archive}" | sha256sum -c -; \
    unzip -q "$archive" -d /tmp; \
    java -jar "/tmp/${folder}/verapdf-izpack-installer-${VERAPDF_VERSION}.jar" \
      /tmp/verapdf-install.xml; \
    /opt/verapdf/verapdf --version

RUN set -eux; \
    case "$TARGETARCH" in \
      amd64) triple=x86_64-unknown-linux-musl; sha="$TYPST_SHA256_AMD64" ;; \
      arm64) triple=aarch64-unknown-linux-musl; sha="$TYPST_SHA256_ARM64" ;; \
      *) echo "unsupported architecture: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    archive=/tmp/typst.tar.xz; \
    curl -fsSL \
      "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-${triple}.tar.xz" \
      -o "$archive"; \
    echo "${sha}  ${archive}" | sha256sum -c -; \
    tar -xJf "$archive" -C /tmp; \
    install -m 0755 "/tmp/typst-${triple}/typst" /usr/local/bin/typst; \
    typst --version

# Resolve only hash-locked wheels here; pip and its build metadata do not enter
# either runtime image.
FROM eclipse-temurin:17-jre-jammy@sha256:e17d77fb030dd4b642dc078d048a5fb9efcb3676ee20305d905949105a6ccd5a AS python-installer

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip \
 && rm -rf /var/lib/apt/lists/*

FROM python-installer AS core-python-deps
COPY tools/requirements-container.txt /tmp/colofon-requirements.txt
RUN python3 -m pip install \
      --disable-pip-version-check \
      --no-cache-dir \
      --no-deps \
      --only-binary=:all: \
      --require-hashes \
      --target /opt/colofon-python \
      -r /tmp/colofon-requirements.txt

FROM python-installer AS form-python-deps
COPY tools/requirements-form-container.txt /tmp/colofon-form-requirements.txt
RUN python3 -m pip install \
      --disable-pip-version-check \
      --no-cache-dir \
      --no-deps \
      --only-binary=:all: \
      --require-hashes \
      --target /opt/colofon-form-python \
      -r /tmp/colofon-form-requirements.txt


# Shared runtime for the permissively licensed core image and the explicitly
# AGPL form image.
FROM eclipse-temurin:17-jre-jammy@sha256:e17d77fb030dd4b642dc078d048a5fb9efcb3676ee20305d905949105a6ccd5a AS runtime-base

LABEL org.opencontainers.image.title="Colofon" \
      org.opencontainers.image.description="Themeable Typst document factory with PDF/UA validation" \
      org.opencontainers.image.source="https://github.com/jmurray2011/colofon" \
      org.opencontainers.image.documentation="https://github.com/jmurray2011/colofon#container-images" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    COLOFON_HOME=/opt/colofon \
    COLOFON_PACKAGES=/opt/colofon/packages \
    COLOFON_FONTS=/opt/colofon/engine/fonts \
    TYPST=/usr/local/bin/typst \
    VERAPDF=/usr/local/bin/verapdf \
    HOME=/home/colofon \
    PYTHONPATH=/opt/colofon-python \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      poppler-utils \
      python3 \
 && apt-get purge -y --auto-remove curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --gid 1000 colofon \
 && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin colofon

COPY --from=tool-installer /usr/local/bin/typst /usr/local/bin/typst
COPY --from=tool-installer /opt/verapdf /opt/verapdf
COPY --from=core-python-deps /opt/colofon-python /opt/colofon-python

RUN ln -s /opt/verapdf/verapdf /usr/local/bin/verapdf \
 && typst --version \
 && verapdf --version \
 && python3 -c "import yaml" \
 && pdftotext -v 2>&1 | head -1

COPY --chown=colofon:colofon . /opt/colofon

USER colofon
WORKDIR /work

ENTRYPOINT ["/opt/colofon/tools/colofon"]
CMD ["help"]


# Optional fillable-form distribution. The combined image is offered under
# AGPL-3.0-only; see AGPL-COMPLIANCE.md for the corresponding-source offer.
FROM runtime-base AS forms

LABEL org.opencontainers.image.title="Colofon Forms" \
      org.opencontainers.image.description="Colofon with AGPL-licensed fillable-form support" \
      org.opencontainers.image.documentation="https://github.com/jmurray2011/colofon/blob/main/AGPL-COMPLIANCE.md" \
      org.opencontainers.image.licenses="AGPL-3.0-only"

ENV COLOFON_FORMS=1 \
    PYTHONPATH=/opt/colofon-form-python:/opt/colofon-python

COPY --from=form-python-deps /opt/colofon-form-python /opt/colofon-form-python
COPY --chmod=0644 licenses/AGPL-3.0.txt /usr/share/licenses/colofon-form/AGPL-3.0.txt

RUN python3 -c "import pymupdf; assert pymupdf.__version__ == '1.28.2'"


# Keep the default target free of PyMuPDF and its AGPL obligations.
FROM runtime-base AS core
