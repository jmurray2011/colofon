#!/usr/bin/env bash
# colofon - the house-style + document-factory engine.
#
# Consumer repos vendor this style; this repo is the source of truth for the
# @local/house and @local/bookmd Typst packages (packages/), the fonts
# (engine/fonts), and the factory tools (tools/). This script
# builds the factory examples as a self-test, applying the same gate the factory
# applies to real documents: PDF/UA-1, no compile warnings, copy-paste safe. Needs
# the pinned host toolchain (Typst 0.15.0, veraPDF) plus python3 + PyYAML.
# Fillable-form validation is opt-in because it uses AGPL-licensed PyMuPDF; run
# `./build.sh --with-forms` after installing tools/requirements-form.txt. Do not
# weaken the document and book gate.
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B="$WS/build"
mkdir -p "$B"

mode=core
case "${1:-}" in
  "") ;;
  --with-forms) mode=all ;;
  --forms-only) mode=forms ;;
  *)
    echo "usage: ./build.sh [--with-forms|--forms-only]" >&2
    exit 2
    ;;
esac

if [[ "$mode" != forms ]]; then
  echo ">> make_book: example book (book.yaml + Markdown chapters -> book)"
  python3 "$WS/tools/make_book.py" "$WS/tools/factory-examples/book/book.yaml" -o "$B/example-book.pdf"

  echo ">> make_doc: every doctype from Markdown"
  for d in report article minutes memo release-notes runbook kb-article bug-report onepager; do
    python3 "$WS/tools/make_doc.py" "$WS/tools/factory-examples/sample-$d.md" -o "$B/example-$d.pdf"
  done
fi

if [[ "$mode" != core ]]; then
  echo ">> make_form: fillable AcroForm (AGPL optional extra)"
  python3 "$WS/tools/make_form.py" "$WS/tools/factory-examples/sample-form.typ" -o "$B/example-form.pdf"
else
  echo ">> make_form: skipped (use --with-forms for the AGPL optional extra)"
fi

echo ">> factory examples built into $B/"
