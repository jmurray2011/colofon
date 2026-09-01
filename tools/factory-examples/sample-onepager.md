---
doctype: onepager
title: Acme Publishing Quick Reference
subtitle: Markdown-to-PDF cheat sheet
version: v1.0 - June 2026
logo: /tools/factory-examples/assets/example-logo.png
logo-alt: Acme logo
cols: 3
footer-note: Illustrative figures, not product defaults
watermark: Sample
---

> Fictional, AI-generated document created for example purposes. Names, organizations,
> systems, events, and data are not real.

# Source checks

| Check | Pass | Flag |
| --- | --- | --- |
| Front matter | Valid YAML | Missing key |
| Images | Alt text present | Empty alt text |
| Links | Target resolves | Missing target |
| Headings | Ordered levels | Skipped level |
| Code samples | Copy intact | Altered token |

# Scan types

| Type | Checks |
| --- | --- |
| Report | Cover, contents, long-form sections |
| Article | Compact title and flowing prose |
| Memo | To/from/date header and short body |
| Runbook | Procedure, verification, rollback |

# Issue severity

- **Critical** - fix before publishing
- **Warning** - review, likely an issue
- **Suggestion** - optional improvement
- **Info** - context only, no action

# Keyboard shortcuts

| Key | Action |
| --- | --- |
| `Ctrl + S` | Save and re-scan |
| `Ctrl + F` | Find in document |
| `Ctrl + /` | Toggle issue panel |
| `Alt + N` | Next flag |

# CLI quickstart

- `docforge check .` - check the current folder
- `docforge build report.md` - render one document
- `docforge build docs/` - render a folder
- `docforge --help` - list all commands

# Plain-language swaps

| Avoid | Use |
| --- | --- |
| utilize | use |
| in order to | to |
| commence | start |
| prior to | before |
| a number of | some |

# Review workflow

1. Draft the Markdown source
2. Check front matter and links
3. Render the PDF
4. Review the output and text layer
5. Rebuild after corrections

# Good to remember

Keep the source and generated output separate. Rebuild after every edit, and review
the rendered artifact rather than assuming a successful compile guarantees good layout.

> [!tip]
> Callouts work inside a one-pager too - use them sparingly so the columns stay
> dense.
