# Changelog

Notable project changes are recorded here. Colofon follows Semantic Versioning for
repository releases; the versioned Typst packages declare their own compatible versions.

## Unreleased

### Added

- A self-describing MCP authoring surface with server workflow instructions and a
  `colofon_describe` tool backed by the versioned automation API.
- A safe, deterministic `colofon init` command for creating container-first document,
  book, and optional consumer-brand starter projects without overwriting existing files.
- A README gallery rendered reproducibly from the fictional, AI-generated Larkspur
  field guide and one-page document.
- Discoverable Draft 2020-12 JSON Schemas for description, diagnostics, lint, project
  initialization, and document/book build results, with representative contract tests.
- Automated, hash-verified corresponding-source attachments and changelog-derived notes
  for tagged GitHub releases.

### Changed

- Clarified the recommended container-first consumer layout, including host ownership,
  Docker Desktop, consumer-brand, and advanced native-vendoring guidance.

## 0.2.1 - 2026-09-01

### Fixed

- Confine book chapters, variables files, consumer brand packages, and screenshot assets
  to the configured project root, including after symlink resolution.
- Resolve root-absolute screenshot references against the consumer project instead of the
  Colofon installation.
- Exercise lint plus verified document and book builds in the container MCP smoke test.

## 0.2.0 - 2026-09-01

### Added

- A versioned JSON automation contract for factory descriptions, toolchain diagnostics,
  lint results, and verified document and book build results.
- A workspace-confined Go MCP server with lint, standalone-document build, and book build
  tools over local stdio transport.
- The MCP server and its dependency license texts in both core and form container images.
- Go tests for path confinement and MCP tool discovery, plus CI and Dependabot coverage for
  the Go module.

## 0.1.1 - 2026-09-01

### Added

- Static analysis, unit tests, AMD64 runtime tests, ARM64 build verification, the
  PDF/UA example gate, and a critical-vulnerability container scan in CI.
- Weekly Dependabot updates for GitHub Actions, Docker, and Python dependencies.
- Hash-locked container wheels, an immutable Java base-image digest, and a non-root
  runtime user.
- Contributor, security, release, issue-reporting, and third-party license guidance.
- A separate `colofon-form` image, explicitly licensed AGPL-3.0-only, with a complete
  corresponding-source offer and vendored license text for its PyMuPDF/MuPDF form
  support.

### Changed

- Reduced the runtime image by keeping download tools, pip, and Git in build stages.
- `colofon test` now runs the unit suite before building every factory example.
- Removed PyMuPDF and fillable-form support from the default MIT-oriented image; forms
  are now an explicit host extra or separate AGPL image.
- Retry veraPDF once for its virtual-clock audit exception while still requiring a
  normal compliant verdict from the retry.

## 0.1.0 - 2026-09-01

- Released the themeable Typst house style and document factory.
- Added Markdown/YAML books, nine standalone document types, and fillable form tooling.
- Added PDF/UA-1 and copy-safety validation.
- Added the fictional, AI-generated Larkspur example suite.
- Published AMD64 and ARM64 container images through GitHub Container Registry.

[Unreleased]: https://github.com/jmurray2011/colofon/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/jmurray2011/colofon/releases/tag/v0.2.1
[0.2.0]: https://github.com/jmurray2011/colofon/releases/tag/v0.2.0
[0.1.1]: https://github.com/jmurray2011/colofon/releases/tag/v0.1.1
[0.1.0]: https://github.com/jmurray2011/colofon/releases/tag/v0.1.0
