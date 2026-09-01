---
doctype: bug-report
brand: sample-brand
title: Session cookie issued without the Secure attribute
severity: High
status: Open
product: Example Platform
version: "4.2.0"
component: Authentication / session management
discovered: June 2026
owner: Security Team
---

> Fictional, AI-generated document created for example purposes. Names, organizations,
> systems, events, and data are not real.

The login flow issues its session cookie without the `Secure` attribute, so the
browser will send it over plain HTTP. On any mixed-content page or downgraded
request the session identifier can be observed in transit.

# Environment

- Example Platform 4.2.0, default deployment behind a TLS-terminating proxy.
- Reproduced in a current Chromium and Firefox with developer tools open.

# Finding

After authentication the server responds with:

```http
Set-Cookie: SESSIONID=abc123; Path=/; HttpOnly
```

The cookie carries `HttpOnly` but not `Secure`. Because the proxy also serves a
plain-HTTP redirect on port 80, a client that first hits `http://` transmits the
cookie before the redirect upgrades the connection.

> [!warning]
> This is exploitable wherever a user can be steered to an `http://` URL for the
> site - a stale bookmark, a typed host, or an attacker-supplied link.

# Impact

- A network observer can capture a valid session identifier and replay it.
- The exposure exists for the lifetime of the session, not just at login.

# Suggested fix

- Add `Secure` to the session cookie and set `SameSite=Lax` while reviewing.
- Serve an HSTS header so browsers refuse the plain-HTTP path entirely.

# References

- CWE-614: Sensitive cookie without the `Secure` attribute.
