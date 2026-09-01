#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd -- "$HERE/../.." && pwd)
OUT="$HERE/build"
mkdir -p "$OUT"

with_forms=0
case "${1:-}" in
  "") ;;
  --with-forms) with_forms=1 ;;
  *)
    echo "usage: examples/larkspur/build.sh [--with-forms]" >&2
    exit 2
    ;;
esac

for source in "$HERE"/documents/*.md; do
  name=${source##*/}
  name=${name%.md}
  "$ROOT/tools/make_doc.py" "$source" --root "$ROOT" -o "$OUT/$name.pdf"
done

"$ROOT/tools/make_book.py" "$HERE/book/book.yaml" -o "$OUT/field-guide.pdf"

if [[ "$with_forms" == 1 ]]; then
  "$ROOT/tools/make_form.py" "$HERE/field-request.typ" -o "$OUT/field-request.pdf"
fi

printf 'Built Larkspur examples in %s\n' "$OUT"
