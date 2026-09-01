# colofon

A house style and document factory built on [Typst](https://typst.app). Hand it Markdown
(or a YAML book outline) and get a styled, accessible (PDF/UA-1) PDF back. The visual brand
-- accent colors and the callout palette -- is themeable, so the same engine renders any
brand's documents.

| Path | What it is |
| --- | --- |
| `packages/local/house/` | The house-style Typst package: the `book` template plus the document-factory templates (`report` / `article` / `minutes` / `memo` / `form`) and components. Brand colors come from a `theme` argument. |
| `packages/local/bookmd/` | Author book chapters in Markdown -- maps Markdown onto the house `cmd` / callout / cross-reference / figure constructs. |
| `packages/preview/cmarker/` | Vendored Markdown-to-Typst renderer (offline, reproducible). |
| `engine/fonts/` | IBM Plex (Serif / Sans / Mono), passed to Typst via `--font-path`. |
| `tools/` | The factory CLIs and the copy-safe gate. |

## The factory

```sh
tools/make_doc.py  doc.md [-o out.pdf]     # Markdown + YAML front-matter -> report/article/minutes/memo
tools/make_book.py book.yaml [-o out.pdf]  # a YAML outline + Markdown chapters -> a full book()
tools/make_form.py form.typ [-o out.pdf]   # a Typst form -> a fillable AcroForm PDF
tools/bookmd_lint.py chapter.md ...        # plain-English preflight: alt text, dangling refs, stale shots
```

Every document compiles to **PDF/UA-1** with no warnings and is checked copy-paste-safe
(no zero-width spaces). `./build.sh` builds the examples in `tools/factory-examples/` as a
self-test.

## Branding

Templates default to a neutral palette. To brand a document, pass a `theme`:

```typ
#import "@local/house:0.1.0": *
#show: book.with(
  title: "...",
  logo: image("/assets/logo.png", alt: "Acme logo", width: 2.5in),
  theme: (accent: rgb("#7654F5"), tones: (note: rgb("#7654F5"))),
)
```

A theme overrides any of `accent`, `accent2`, and the five callout `tones`; anything you
omit keeps the neutral default. Fonts and the neutral grays are shared engine defaults.
Keep a brand in its own package (a small `.typ` that exports a `theme` dict + the logo) and
import it, so the brand lives in one place across every document.

## Using the style in a document repo

A consumer repo vendors `packages/local/house/` and `engine/fonts/`, then builds with
`--package-path packages --font-path fonts` (see any consumer's `build.sh`). Source files
`#import "@local/house:0.1.0": *`. Bumping the vendored copy is how a consumer adopts a new
style version.

## Requirements

- Typst 0.15.0 (`~/.local/bin/typst`)
- veraPDF (`~/.local/verapdf/verapdf`) for the PDF/UA-1 check
- python3 + PyYAML + PyMuPDF for the factory tools (`pip install -r tools/requirements.txt`)
- `typstyle` (optional) for formatting

## License

Colofon-authored code is MIT -- see [LICENSE](LICENSE). Vendored packages under
`packages/preview/` retain the licenses included in their package directories. IBM
Plex is distributed under the SIL Open Font License in `engine/fonts/LICENSE.txt`.
