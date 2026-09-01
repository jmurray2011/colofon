# Identity and single sign-on {#ch-sso}

Acme Relay supports single sign-on through SAML 2.0. Register the service with
your organization's identity provider and exchange metadata over an approved
channel.

Configure TLS first -- see [reverse proxy and TLS](#ch-tls). When SSO is enabled,
test sign-in with a non-administrator account before enforcing SSO for everyone.

> [!warning]
> Document and test an offline recovery procedure before enforcing SSO. Store any
> recovery credential in the approved secrets system, not in the configuration file.
