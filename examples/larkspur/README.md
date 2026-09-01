# Larkspur Field Station examples

This directory demonstrates one coherent house style across every Colofon output type.
Every example is fictional and AI-generated for demonstration purposes. Larkspur Field
Station, its people, systems, observations, events, and data are not real. No external text
or artwork was used, so there is no third-party attribution requirement.

The shared style is [`larkspur-brand`](../../packages/local/larkspur-brand/0.1.0/), which
defines the palette, author, and book colophon. The SVG logo is passed in by each document
that supports one, keeping assets out of the style package.

| Source | Output type |
| --- | --- |
| [`documents/report.md`](documents/report.md) | Report |
| [`documents/article.md`](documents/article.md) | Article |
| [`documents/minutes.md`](documents/minutes.md) | Meeting minutes |
| [`documents/memo.md`](documents/memo.md) | Memorandum |
| [`documents/release-notes.md`](documents/release-notes.md) | Release notes |
| [`documents/runbook.md`](documents/runbook.md) | Operational runbook |
| [`documents/kb-article.md`](documents/kb-article.md) | Knowledge-base article |
| [`documents/bug-report.md`](documents/bug-report.md) | Bug report |
| [`documents/onepager.md`](documents/onepager.md) | Landscape one-pager |
| [`book/book.yaml`](book/book.yaml) | YAML/Markdown book |
| [`field-request.typ`](field-request.typ) | Fillable form |

Build the ten core examples from the repository root:

```sh
examples/larkspur/build.sh
```

The fillable form uses the optional AGPL-licensed PyMuPDF extra. After installing
`tools/requirements-form.txt`, include it explicitly:

```sh
examples/larkspur/build.sh --with-forms
```

PDFs are written to `examples/larkspur/build/`, which is gitignored. The Markdown and book
outputs must pass the PDF/UA-1, no-warning, and copy-safety gates. When requested, the
fillable form reports its accessibility result separately because its AcroForm widget
layer is not gate-verified.
