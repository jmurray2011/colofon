#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd -- "$HERE/../.." && pwd)
GALLERY="$ROOT/docs/images"

command -v pdftoppm >/dev/null || {
  echo "render-gallery: pdftoppm is required (install poppler-utils)" >&2
  exit 2
}

"$HERE/build.sh"
mkdir -p "$GALLERY"

pdftoppm -png -f 1 -l 1 -singlefile -scale-to-x 900 -scale-to-y -1 \
  "$HERE/build/field-guide.pdf" "$GALLERY/larkspur-field-guide-cover"
pdftoppm -png -f 5 -l 5 -singlefile -scale-to-x 900 -scale-to-y -1 \
  "$HERE/build/field-guide.pdf" "$GALLERY/larkspur-field-guide-chapter"
pdftoppm -png -f 1 -l 1 -singlefile -scale-to-x 1200 -scale-to-y -1 \
  "$HERE/build/onepager.pdf" "$GALLERY/larkspur-onepager"
chmod 0644 "$GALLERY"/larkspur-*.png

printf 'Rendered README gallery in %s\n' "$GALLERY"
