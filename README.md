# colofon

A house style and document factory built on [Typst](https://typst.app). Hand it Markdown
(or a YAML book outline) and get a styled, accessible (PDF/UA-1) PDF back. The visual brand
-- accent colors and the callout palette -- is themeable, so the same engine renders any
brand's documents.

[![CI](https://github.com/jmurray2011/colofon/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurray2011/colofon/actions/workflows/ci.yml)

| Path | What it is |
| --- | --- |
| `packages/local/house/` | The house-style Typst package: the `book` template, document-factory templates, and components. Brand colors come from a `theme` argument. |
| `packages/local/bookmd/` | Author book chapters in Markdown -- maps Markdown onto the house `cmd` / callout / cross-reference / figure constructs. |
| `packages/preview/cmarker/` | Vendored Markdown-to-Typst renderer (offline, reproducible). |
| `engine/fonts/` | IBM Plex (Serif / Sans / Mono), passed to Typst via `--font-path`. |
| `tools/` | The factory CLIs and the copy-safe gate. |

## Quick start

Create a complete neutral starter project, then build its verified report and book with
the released container:

```sh
mkdir my-documents && cd my-documents
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" \
  ghcr.io/jmurray2011/colofon:0.2.1 init .
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" \
  ghcr.io/jmurray2011/colofon:0.2.1 doc documents/example-report.md \
  -o build/example-report.pdf
```

`init` never overwrites an existing file. Use `--kind document` or `--kind book` for a
smaller project, `--doctype memo` (or another supported doctype) to change the standalone
starter, and `--brand example-studio` to include a consumer-local starter brand. Add
`--dry-run` to inspect the planned files without writing them.

## What it produces

These previews are rendered from the checked-in Larkspur sources. The house style,
organization, content, and data are fictional and AI-generated for example purposes.

| Field-guide cover | Chapter page |
| --- | --- |
| ![Cover of the fictional Larkspur Observer Field Guide.](docs/images/larkspur-field-guide-cover.png) | ![A fictional Larkspur field-guide chapter showing headings, body text, and a note callout.](docs/images/larkspur-field-guide-chapter.png) |

![A fictional landscape Larkspur station one-page overview.](docs/images/larkspur-onepager.png)

Sources: [`book/book.yaml`](examples/larkspur/book/book.yaml),
[`01-arrival.md`](examples/larkspur/book/chapters/01-arrival.md), and
[`onepager.md`](examples/larkspur/documents/onepager.md). Regenerate these images with
`examples/larkspur/render-gallery.sh`.

## The factory

```sh
tools/make_doc.py  doc.md [-o out.pdf]     # Markdown + YAML front matter -> a standalone document
tools/make_book.py book.yaml [-o out.pdf]  # a YAML outline + Markdown chapters -> a full book()
tools/make_form.py form.typ [-o out.pdf]   # optional AGPL extra -> a fillable AcroForm PDF
tools/bookmd_lint.py chapter.md ...        # plain-English preflight: alt text, dangling refs, stale shots
```

Markdown documents compile to **PDF/UA-1** with no warnings and are checked copy-paste-safe
(no zero-width spaces). `./build.sh` builds the examples in `tools/factory-examples/` as a
self-test. `tools/colofon test` runs the unit suite and then that complete build gate.
Fillable forms have a separate accessibility limitation described below.

## Automation API

The shell entrypoint has a versioned JSON contract for scripts, agents, and integrations.
Human-readable output remains the default; add `--json` when another program consumes the
result:

```sh
tools/colofon describe --json
tools/colofon doctor --json
tools/colofon init new-project --brand example-studio --json
tools/colofon lint --json chapters/intro.md chapters/operate.md
tools/colofon doc report.md -o build/report.pdf --json
tools/colofon book book.yaml -o build/book.pdf --json
```

`describe` returns the automation API and factory versions, every doctype's required and
optional front-matter keys, the book schema, and enabled capabilities. `doctor` checks the
configured Typst, veraPDF, `pdftotext`, and Python executables without building anything.
Build results include the absolute artifact path, byte size, SHA-256 digest, and individual
PDF/UA-1 and copy-safety verdicts. The top-level `api_version` is the compatibility boundary
for machine consumers; it is independent of the Colofon release version.

A successful document result has this shape (values shortened here):

```json
{
  "api_version": "1",
  "kind": "document-build",
  "ok": true,
  "results": [{
    "artifact": {"bytes": 48210, "path": "/work/build/report.pdf", "sha256": "…"},
    "checks": {
      "copy_safe": "pass",
      "pdfua1": "pass",
      "typst_pdfua1": "pass",
      "verified": true
    },
    "ok": true,
    "source": "/work/report.md"
  }],
  "errors": []
}
```

## MCP server

`colofon-mcp` is a small local stdio server built with the official MCP Go SDK. It exposes
four core tools and startup instructions describing the safe authoring workflow:

- `colofon_describe` returns the current authoring schemas, versions, and capabilities.
- `colofon_lint` reads and checks one or more Markdown files.
- `colofon_build_document` builds and verifies one standalone Markdown document.
- `colofon_build_book` builds and verifies one YAML/Markdown book.

The server receives an explicit workspace at startup. Tool arguments must be relative to
that workspace; symlink escapes and absolute paths are rejected, including chapter,
variables-file, brand, and screenshot references discovered inside source files. Generated
files are restricted to `build/`. Calls are serialized, time-limited, and delegated to the same
factory commands and compliance gates used by the CLI. The server has no network transport
and does not expose fillable forms or PyMuPDF.

The released core container is the recommended distribution because it includes the MCP
binary and the complete Colofon toolchain. Configure an MCP client to run it with stdin kept
open and an absolute host project path mounted at `/work`:

```json
{
  "mcpServers": {
    "colofon": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/absolute/path/to/document-project:/work",
        "ghcr.io/jmurray2011/colofon:0.2.1",
        "mcp", "--stdio", "--workspace", "/work"
      ]
    }
  }
}
```

For host development, build the binary and launch it through the normal entrypoint:

```sh
go build -o bin/colofon-mcp ./cmd/colofon-mcp
tools/colofon mcp --stdio --workspace /absolute/path/to/document-project
```

The bare binary is only an adapter: host use still requires the Python, Typst, veraPDF,
fonts, and `pdftotext` dependencies listed below.

## Authoring syntax

### Standalone documents

A standalone document is Markdown with a leading YAML block. `doctype` selects the
template; the other keys become template arguments:

```markdown
---
doctype: report
title: Deployment Review
subtitle: Findings and recommendations
version: "1.0"
date: September 2026
author: Example Engineering
logo: /assets/example-logo.png
logo-alt: Example organization logo
---

# Summary

The deployment is ready with the exceptions listed below.

> [!warning]
> Complete the rollback test before release.
```

Each doctype has one required identifying field:

| `doctype` | Required field | Example |
| --- | --- | --- |
| `report` | `title` | [`sample-report.md`](tools/factory-examples/sample-report.md) |
| `article` | `title` | [`sample-article.md`](tools/factory-examples/sample-article.md) |
| `minutes` | `meeting` | [`sample-minutes.md`](tools/factory-examples/sample-minutes.md) |
| `memo` | `re` | [`sample-memo.md`](tools/factory-examples/sample-memo.md) |
| `release-notes` | `product` | [`sample-release-notes.md`](tools/factory-examples/sample-release-notes.md) |
| `runbook` | `title` | [`sample-runbook.md`](tools/factory-examples/sample-runbook.md) |
| `kb-article` | `title` | [`sample-kb-article.md`](tools/factory-examples/sample-kb-article.md) |
| `bug-report` | `title` | [`sample-bug-report.md`](tools/factory-examples/sample-bug-report.md) |
| `onepager` | `title` | [`sample-onepager.md`](tools/factory-examples/sample-onepager.md) |

Front matter is strict: missing required keys and unknown keys are errors. See
`DOCTYPE_SCHEMA` in [`tools/make_doc.py`](tools/make_doc.py) for every allowed optional
field. When `logo` is set, `logo-alt` is required.

### Body Markdown

The body supports CommonMark plus Colofon's book-oriented extensions:

| Source | Result |
| --- | --- |
| `` `systemctl restart relay` `` | Styled, indexed inline command/literal |
| `## Recovery {#recovery}` | Heading with a stable cross-reference label |
| `[recovery procedure](#recovery)` | Cross-reference that prints the target title |
| `> [!note]` followed by quoted lines | `note`, `tip`, `important`, `warning`, or `caution` callout |
| `![Status page](shot:/assets/status.png)` | Framed screenshot; alt text becomes its caption |
| `![Architecture](/assets/architecture.svg)` | Ordinary image loaded from the project root |
| <code>```bash</code> ... <code>```</code> | Copy-safe fenced code block |
| `<!--raw-typst #idx("term")-->` | Raw Typst escape hatch for constructs with no Markdown form |
| `{{version}}` | Book variable substituted by `make_book.py` |

For example:

````markdown
# Operations {#operations}

Run `systemctl status relay`, then review the [recovery procedure](#recovery).

![A status page showing that all checks passed.](shot:/assets/status.png)

> [!tip]
> Test recovery with a non-production account first.

## Recovery {#recovery}

```bash
relayctl restore --check backup.tar
```

<!--raw-typst #idx("recovery")-->
````

Every image needs meaningful alt text. The linter rejects empty alt text, dangling
cross-references, and missing or stale screenshots before Typst runs.

### Books

For a book, `book.yaml` owns structure and metadata while its chapter files own content:

```yaml
title: Acme Relay
subtitle: Operations Guide
vars-from: release.yaml
version: "{{version}}"
date: September 2026
logo: /assets/example-logo.png
logo-alt: Acme logo
brand: sample-brand
parts:
  - title: Operate
    blurb: Routine operation and recovery.
    chapters:
      - chapters/operations.md
  - title: Reference
    appendix: true
    chapters:
      - chapters/configuration.md
```

Chapter paths and `vars-from` are relative to `book.yaml`. Asset paths are root-absolute
from the Typst project root. A variables file is an ordinary YAML mapping:

```yaml
version: 1.4.0
package: acme-relay-1.4.0.tar.gz
```

Use `{{version}}` or `{{package}}` in book metadata and chapters. Undefined variables are
hard errors. Parts come from `book.yaml`; each chapter begins with a top-level `#` heading.
Set `appendix: true` on a part to switch subsequent chapter numbering to appendices. See
the complete [`book.yaml`](tools/factory-examples/book/book.yaml) and its
[`release.yaml`](tools/factory-examples/book/release.yaml), then build it with:

```sh
tools/make_book.py tools/factory-examples/book/book.yaml -o build/example-book.pdf
```

Fillable forms use Typst source rather than Markdown; start from
[`sample-form.typ`](tools/factory-examples/sample-form.typ). They require the optional
PyMuPDF extra, which is AGPL-3.0 or commercially licensed. The added AcroForm widget layer
is intentionally not gate-verified as PDF/UA-1.

## Complete example suite

[`examples/larkspur/`](examples/larkspur/) applies one fictional house style to a book,
every Markdown doctype, and a fillable form. Its README links every source and explains how
to build all eleven outputs. Every artifact identifies itself as fictional and AI-generated
for example purposes; no external text or artwork was used.

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
`--package-path packages --font-path engine/fonts` (see any consumer's `build.sh`). Source files
`#import "@local/house:0.1.0": *`. Bumping the vendored copy is how a consumer adopts a new
style version.

## Requirements

- Typst 0.15.0 (`~/.local/bin/typst`)
- veraPDF (`~/.local/verapdf/verapdf`) for the PDF/UA-1 check
- python3 + PyYAML for the document and book factory
  (`pip install -r tools/requirements.txt`)
- PyMuPDF only for optional fillable forms
  (`pip install -r tools/requirements-form.txt`; AGPL-3.0 or commercial terms apply)
- `typstyle` (optional) for formatting

Contributors also need Ruff, ShellCheck, and actionlint for `./tools/check.sh`; CI installs
its lint tools from pinned versions. Building the MCP server requires Go 1.25.7 or later.

## Container images

The default image contains Colofon, IBM Plex, Typst, veraPDF, Java, Python, PyYAML, and
`pdftotext`. It intentionally excludes PyMuPDF and does not provide fillable-form support.
The Java base is digest-pinned, Python wheels are version- and hash-locked for both
supported architectures, and Typst and veraPDF downloads are versioned and
checksum-verified.

```sh
docker build -t colofon:local .
docker run --rm colofon:local version
docker run --rm colofon:local test
docker run --rm -i -v "$PWD:/work" colofon:local mcp --workspace /work
```

Release images are published for AMD64 and ARM64 through GitHub Container Registry.
Use `latest` for a quick trial or an immutable version tag for repeatable builds:

```sh
docker pull ghcr.io/jmurray2011/colofon:latest
docker run --rm ghcr.io/jmurray2011/colofon:latest version

docker pull ghcr.io/jmurray2011/colofon:0.2.1
```

Mount a document project at `/work` to build its sources. Outputs and `.factory-build/`
remain in the mounted project:

```sh
docker run --rm -v "$PWD:/work" -w /work colofon:local \
  doc report.md -o build/report.pdf

docker run --rm -v "$PWD:/work" -w /work colofon:local \
  book book.yaml -o build/book.pdf
```

### Fillable-form image (AGPL)

Fillable forms are isolated in `ghcr.io/jmurray2011/colofon-form`. This combined image
contains PyMuPDF and is explicitly distributed under AGPL-3.0-only. Its full license and
corresponding-source offer are in [AGPL-COMPLIANCE.md](AGPL-COMPLIANCE.md).

```sh
docker build --target forms -t colofon-form:local .
docker run --rm colofon-form:local test

docker pull ghcr.io/jmurray2011/colofon-form:0.2.1
docker run --rm -v "$PWD:/work" -w /work \
  ghcr.io/jmurray2011/colofon-form:0.2.1 \
  form request.typ -o build/request.pdf
```

The entrypoint also provides `lint`, `convert`, and `help`. The image runs as UID/GID
1000 by default. On Linux hosts that use different IDs, add
`--user "$(id -u):$(id -g)"` so generated files use the invoking user's ownership.

## Project guidance

- [CONTRIBUTING.md](CONTRIBUTING.md) covers development and pull requests.
- [SECURITY.md](SECURITY.md) explains private vulnerability reporting.
- [CHANGELOG.md](CHANGELOG.md) records user-visible changes.
- [RELEASING.md](RELEASING.md) defines the immutable-tag release process.

## License

Colofon-authored code is MIT -- see [LICENSE](LICENSE). When distributed as part of the
optional form image, it is additionally offered under AGPL-3.0-only as described in
[AGPL-COMPLIANCE.md](AGPL-COMPLIANCE.md). Vendored packages under
`packages/preview/` retain the licenses included in their package directories. IBM
Plex is distributed under the SIL Open Font License in `engine/fonts/LICENSE.txt`.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the complete image dependency
and license summary.
