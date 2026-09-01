# engine

Shared, offline build assets for colofon.

- `fonts/` contains IBM Plex Serif, Sans, and Mono, passed to Typst with
  `--font-path`.

The document templates live in `packages/local/house/`; Markdown rendering lives in
`packages/local/bookmd/`. Brand packages belong to the repository that owns the brand
and can be loaded by building with that repository as `tools/make_doc.py --root`.
