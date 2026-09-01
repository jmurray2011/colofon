# house changelog

## 0.1.0 - 2026-06-21
- First packaged release. Promotes the shared engine (`engine/book.typ`) to a
  versioned `@local/house` Typst package, resolved in-repo via
  `--package-path packages`.
- Exports the `book` template (Part/Chapter/Section/Appendix machinery) used by the
  guides, plus the document-factory templates `report`, `article`, `minutes`,
  `memo`, and `form`, the shared `apply-common` base, components
  (`kicker`/`kbd`/`hr`/`tbl`/`swatch`/`callout`/`shot`/`wide`/...), and the inline
  helpers (`cmd`/`path`/`param`/`procedure`/`note`/`tip`/`important`/`warning`/`caution`).
- Code blocks are copy-paste exact: long lines auto-shrink (`_fitline`) instead of
  having zero-width spaces injected. Every `image()` needs `alt` for PDF/UA-1.
- API note: `shot()` takes already-loaded image **content**, not a path
  (`shot(image("/book/assets/x.png", alt: "..."))`). A package cannot resolve a
  consumer's root-absolute asset path, so the consumer loads the image and passes it.
