---
doctype: kb-article
brand: larkspur-brand
title: Why does an observation remain queued?
subtitle: Diagnose a record that has not transferred to the archive
category: Troubleshooting
applies-to:
  - Observation Log 2.x
  - Field Relay 1.x
updated: September 2026
summary: A queued record is safe on the field laptop but has not yet received a verified
  archive receipt.
support-note: If the queue remains unchanged after these steps, preserve the local data and
  contact the daytime operator with the session ID.
---

> [!note]
> Fictional AI-generated example. Names, organizations, systems, events, and data are not real.

# Symptoms

The session banner shows `queued`, and the record has no archive receipt. Other local
records remain available.

# Cause

The field relay may be offline, busy retrying a large image, or waiting for the archive to
confirm its checksum. A queued state does not mean the local record is lost.

# Resolution

1. Confirm that the laptop shows a network connection.
2. Run `relayctl queue` and note the oldest session ID.
3. If the relay is paused, run `relayctl resume`.
4. Wait two minutes and refresh the observation log.

> [!warning]
> Do not delete local records to clear the queue. Local copies are removed only after a
> verified archive receipt exists.

# Verification

The record is complete when its state is `verified` and the receipt displays a checksum.
