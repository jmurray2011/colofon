---
doctype: runbook
title: Restart the Ingest Service
system: Ingest Pipeline
owner: Platform Team
version: "1.2"
date: June 2026
last-reviewed: June 2026
severity: High
---

# Prerequisites

- Shell access to the ingest host with `sudo` rights.
- The on-call rotation acknowledged in the incident channel.

# Procedure

1. Drain the queue so no new work is accepted:

   ```bash
   ingestctl drain --wait
   ```

2. Stop the service and confirm it has exited:

   ```bash
   sudo systemctl stop ingest && systemctl is-active ingest
   ```

3. Start the service and watch the first batch complete.

> [!warning]
> Do not skip the drain. Restarting mid-batch leaves partial rows that the
> reconciler cannot repair automatically.

# Verify

- The health endpoint returns `ok` and the queue depth falls to zero within five
  minutes.

# Rollback

If the service does not return to healthy, restore the previous unit file from
`config.toml.bak` and restart, then escalate.

# Escalation

Page the platform on-call lead. If unresolved in 30 minutes, open a Sev-1.
