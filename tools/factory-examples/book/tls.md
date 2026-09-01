# Reverse proxy and TLS {#ch-tls}

These steps apply to Acme Relay {{version}}, installed from `{{rpm}}`. Front the
application with a reverse proxy that terminates TLS and forwards requests to the
application's loopback listener.

## Install a signed certificate {#sec-cert}

Replace the default self-signed certificate with one from a trusted authority.
Generate a certificate signing request, submit it to your certificate authority,
then install the issued certificate and reload the reverse proxy.

> [!note]
> Complete [initial setup](#ch-initial-setup) before changing the public endpoint,
> then repeat the health check through the reverse proxy.
