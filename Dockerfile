# syntax=docker/dockerfile:1

# Install the pinned veraPDF CLI from its official unattended installer.
FROM eclipse-temurin:17-jre-jammy AS verapdf-installer

ARG VERAPDF_VERSION=1.30.2
ARG VERAPDF_SERIES=1.30
ARG VERAPDF_SHA256=6cc6341cb1af644044054b81f00a6590a7918abb18f762243de115258bcad838

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl unzip \
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


# Colofon and every runtime dependency.
FROM eclipse-temurin:17-jre-jammy

ARG TARGETARCH
ARG TYPST_VERSION=0.15.0
ARG TYPST_SHA256_AMD64=59b207df01be2dab9f13e80f73d04d7ff8273ffd46b3dd1b9eef5c60f3eeabea
ARG TYPST_SHA256_ARM64=cdf50ffc7b8ba759ed02200632eda3d78eb8b99aacb6611f4f75684990647620

LABEL org.opencontainers.image.title="Colofon" \
      org.opencontainers.image.description="Themeable Typst document factory with PDF/UA validation" \
      org.opencontainers.image.source="https://github.com/jmurray2011/colofon" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    COLOFON_HOME=/opt/colofon \
    COLOFON_PACKAGES=/opt/colofon/packages \
    COLOFON_FONTS=/opt/colofon/engine/fonts \
    TYPST=/usr/local/bin/typst \
    VERAPDF=/usr/local/bin/verapdf \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      poppler-utils \
      python3 \
      python3-pip \
      xz-utils \
 && rm -rf /var/lib/apt/lists/*

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
    rm -rf "$archive" "/tmp/typst-${triple}"; \
    typst --version

COPY tools/requirements.txt /tmp/colofon-requirements.txt
RUN python3 -m pip install --no-cache-dir --disable-pip-version-check \
      -r /tmp/colofon-requirements.txt \
 && rm /tmp/colofon-requirements.txt

COPY --from=verapdf-installer /opt/verapdf /opt/verapdf
RUN ln -s /opt/verapdf/verapdf /usr/local/bin/verapdf \
 && verapdf --version

COPY . /opt/colofon
RUN chmod 0755 /opt/colofon/tools/colofon \
 && python3 -c "import pymupdf, yaml" \
 && pdftotext -v 2>&1 | head -1

WORKDIR /work

ENTRYPOINT ["/opt/colofon/tools/colofon"]
CMD ["help"]
