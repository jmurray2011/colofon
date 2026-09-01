#!/usr/bin/env bash
# colofon - the house-style + document-factory engine.
#
# Consumer repos vendor this style; this repo is the source of truth for the
# @local/house and @local/bookmd Typst packages (packages/), the fonts
# (engine/fonts), and the factory tools (tools/). This script
# builds the factory examples as a self-test, applying the same gate the factory
# applies to real documents: PDF/UA-1, no compile warnings, copy-paste safe. Needs
# the pinned host toolchain (Typst 0.15.0, veraPDF) plus python3 + PyYAML/PyMuPDF
# (see tools/requirements.txt). Do not weaken the gate.
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B="$WS/build"
mkdir -p "$B"

echo ">> make_book: example book (book.yaml + Markdown chapters -> book)"
python3 "$WS/tools/make_book.py" "$WS/tools/factory-examples/book/book.yaml" -o "$B/example-book.pdf"

echo ">> make_doc: every doctype from Markdown"
for d in report article minutes memo release-notes runbook kb-article bug-report onepager; do
  python3 "$WS/tools/make_doc.py" "$WS/tools/factory-examples/sample-$d.md" -o "$B/example-$d.pdf"
done

echo ">> make_form: fillable AcroForm"
python3 "$WS/tools/make_form.py" "$WS/tools/factory-examples/sample-form.typ" -o "$B/example-form.pdf"

echo ">> factory examples built into $B/"
