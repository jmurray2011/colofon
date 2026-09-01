---
doctype: report
title: Acme Document Factory
subtitle: A proof-of-concept report
version: "0.1"
date: June 2026
author: Acme
logo: /tools/factory-examples/assets/example-logo.png
logo-alt: Acme logo
---

> Fictional, AI-generated document created for example purposes. Names, organizations,
> systems, events, and data are not real.

# Overview

This report was generated from **Markdown** by the document factory: a single
`.md` file with YAML front-matter, rendered through the `@local/house` *report*
template to a PDF/UA-1 document.

Key points:

- One toolchain -- cmarker renders the Markdown in-process, no external converter.
- The same validate gate as the books: PDF/UA-1, no warnings, copy-safe.
- Every image needs alt text, enforced by the factory.

# Commands

Code blocks are copy-paste exact -- long lines auto-shrink instead of having
zero-width spaces injected into the clipboard:

```bash
sudo dnf install --setopt=clean_requirements_on_remove=0 some-really-long-package-name-7.1.1-1.x86_64.rpm with trailing args to force a very long line
```

See the [Acme site](https://www.example.com) for more.
