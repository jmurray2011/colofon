#!/usr/bin/env bash
# Populate tools/.toolcache/ with the binaries the Dockerfile bakes into the build image.
# veraPDF's headless installer is fiddly, so we vendor a known-good copy. Typst is fetched
# by the Dockerfile itself (pinned), so it is not cached here.
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${VERAPDF_SRC:-$HOME/.local/verapdf}"
DEST="$WS/tools/.toolcache/verapdf"

[ -x "$SRC/verapdf" ] || { echo "veraPDF not found at $SRC (set VERAPDF_SRC=...)" >&2; exit 1; }
mkdir -p "$WS/tools/.toolcache"
rm -rf "$DEST"
cp -r "$SRC" "$DEST"
echo "vendored veraPDF -> tools/.toolcache/verapdf ($(du -sh "$DEST" | cut -f1))"
