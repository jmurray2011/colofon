# Initial setup {#ch-initial-setup}

After the application is installed and running, complete its initial setup: load a
configuration file, start the service, verify the health check, and secure the public
endpoint. These steps are the same across all supported platforms.

## Load the configuration {#sec-setup}

Copy `config.example.toml` to `config.toml`, set the listen address, and start the
service. Open `https://<server>/status` and confirm that the service reports `Ready`.

![A fictional service status page showing a ready state and three completed setup checks.](shot:/tools/factory-examples/assets/shot-status.svg)

> [!note]
> Keep `config.toml` outside the web root and grant write access only to the service
> account. Restart the service after changing it.

## Test the deployment {#sec-test}

Submit a small test job and wait for it to reach `Complete`. Download its output and
compare it with the input. This confirms that the application, worker, storage, and
reverse proxy all work together.

## Secure the server {#sec-secure}

Before putting the deployment into production, install a signed certificate (see
[reverse proxy and TLS](#ch-tls)) and configure single sign-on (see
[identity and SSO](#ch-sso)). Test both ordinary user access and the documented
recovery procedure before opening the service to users.

> [!warning]
> Until you replace the self-signed certificate, browsers show an
> untrusted-connection warning. Replace it with a certificate signed by a trusted
> authority before you go live.
