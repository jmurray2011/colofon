---
doctype: release-notes
product: Acme Platform
version: "2.4.0"
date: June 2026
status: Stable
subtitle: What changed in this release
---

# 2.4.0

## Added

- Batch export now streams results, so large jobs no longer hold the whole set in
  memory before the first row is written.
- A `--dry-run` flag on the ingest CLI previews the plan without writing.

## Changed

- The default gateway timeout moved from 30s to 120s to match real export sizes.

## Fixed

- Fixed a crash when a saved view referenced a deleted column.

## Security

- Upgraded the bundled parser to close a denial-of-service issue (CVE-2026-0001).

> [!important]
> The timeout change alters the default config. Re-check any override you set in
> `config.toml` before upgrading.

# 2.3.1

## Fixed

- Corrected the page count in exported PDFs when a report ended on an even page.
