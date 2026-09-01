# Changelog

Notable project changes are recorded here. Colofon follows Semantic Versioning for
repository releases; the versioned Typst packages declare their own compatible versions.

## Unreleased

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

[Unreleased]: https://github.com/jmurray2011/colofon/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/jmurray2011/colofon/releases/tag/v0.1.1
[0.1.0]: https://github.com/jmurray2011/colofon/releases/tag/v0.1.0
