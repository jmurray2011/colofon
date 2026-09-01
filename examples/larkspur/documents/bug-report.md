---
doctype: bug-report
brand: larkspur-brand
title: Night-mode preference resets after an offline restart
severity: Medium
status: Open
product: Larkspur Observation Log
version: "2.3.0"
component: Field client settings
discovered: September 19, 2026
owner: Application Team
---

> [!note]
> Fictional AI-generated example. Names, organizations, systems, events, and data are not real.

# Summary

When a field laptop restarts without a network connection, the client opens with the
daylight palette even when night mode was selected before shutdown.

# Steps to reproduce

1. Connect the client and enable night mode.
2. Close the client and disconnect the network.
3. Restart the laptop.
4. Open the client before reconnecting.

# Expected result

The locally saved night-mode preference is applied before the sign-in or synchronization
screen appears.

# Actual result

The daylight palette appears until the client reconnects and downloads the user profile.

# Workaround

Select `Display`, then `Night mode` before entering the observing deck.

> [!important]
> This issue does not alter observation data, but the unexpected bright screen can disrupt
> dark adaptation.
