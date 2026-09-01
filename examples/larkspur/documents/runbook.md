---
doctype: runbook
brand: larkspur-brand
title: Restore the Weather Relay
system: Summit Weather Mast
owner: Station Operations
version: "1.2"
date: September 2026
last-reviewed: September 2026
severity: High
---

> [!note]
> Fictional AI-generated example. Names, organizations, systems, events, and data are not real.

# Trigger

Use this runbook when the observation log reports weather data older than five minutes or
the relay health check returns `stale`.

# Safety checks

1. Confirm that no lightning warning is active.
2. Do not climb the mast or open its enclosure during precipitation.
3. Tell the night lead that automated weather holds may be delayed.

> [!caution]
> If wind exceeds the station access limit, stop here and keep the observing dome closed.

# Recovery procedure {#recovery}

1. Run `relayctl status weather-mast` from the operations terminal.
2. Confirm that the serial gateway responds to `ping weather-gateway`.
3. Restart the relay with `relayctl restart weather-mast`.
4. Wait two minutes, then run `relayctl samples weather-mast --count 3`.

# Verification

Verify that three samples have increasing timestamps and plausible temperature, humidity,
and wind values. Confirm that the observation log changes from `stale` to `current`.

# Rollback

If the [recovery procedure](#recovery) fails, stop the relay, keep the dome closed, and
record weather manually until the daytime technician investigates.
