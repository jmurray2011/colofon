---
doctype: kb-article
title: Why does an export fail with a timeout?
category: Troubleshooting
applies-to:
  - Acme Platform 2.x
updated: June 2026
summary: A large export can exceed the gateway timeout. Raise the limit or split
  the job into smaller ranges.
support-note: If the steps below do not resolve it, contact Support with the
  export ID from the error banner.
---

# Symptoms

An export runs for a while and then stops with a `gateway timeout` banner. The
file is never produced, and the job shows as failed in the history list.

# Cause

The export is held open longer than the gateway allows. This happens when the
selected range is large or the source is under load.

# Resolution

1. Open `config.toml` and raise the gateway timeout:

   ```toml
   [gateway]
   timeout_seconds = 120
   ```

2. Reload the gateway so the new value takes effect.
3. If the export is still too large, split it into date ranges and run each
   separately.

> [!tip]
> Streaming export (2.4.0 and later) avoids most timeouts because rows are written
> as they are produced rather than held until the end.

# Related

- Configuring gateway limits
- Scheduling large exports off-peak
