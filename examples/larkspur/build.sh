#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd -- "$HERE/../.." && pwd)
OUT="$HERE/build"
mkdir -p "$OUT"

for source in "$HERE"/documents/*.md; do
  name=${source##*/}
  name=${name%.md}
  "$ROOT/tools/make_doc.py" "$source" --root "$ROOT" -o "$OUT/$name.pdf"
done

"$ROOT/tools/make_book.py" "$HERE/book/book.yaml" -o "$OUT/field-guide.pdf"
"$ROOT/tools/make_form.py" "$HERE/field-request.typ" -o "$OUT/field-request.pdf"

printf 'Built Larkspur examples in %s\n' "$OUT"
