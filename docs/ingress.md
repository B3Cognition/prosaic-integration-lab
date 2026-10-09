# TLS ingress and deployment drain

Run the owned reference without paid inference:

```sh
.venv/bin/python -m lab_runner test --candidate --mode ingress --postgres-version 16
.venv/bin/python -m lab_runner test --candidate --mode ingress --postgres-version 18
```

The runner pins NGINX by digest and delivers generated private certificate/config
files into an owned read-only volume. NGINX runs as UID 101 with no capabilities,
an immutable root and bounded temporary storage. Its HTTP upstreams are both
owned replicas on the private fixture network. Public TLS clients verify the
generated CA; the fixture also runs the configured OIDC provider against owned
Keycloak over verified TLS. It never contacts an existing gateway or issuer.

The executable configuration in `lab_runner.ingress.configuration` uses ordinary
round robin. Initial headers have a two-second deadline, bodies are limited to
8 KiB, and active connections/upstream waits are finite. Forwarded identity
headers are stripped; bearer authentication and host subject bindings remain
authoritative. Automatic upstream retries are disabled for all requests. A lost
mutation reply requires inspection or reuse of the exact original idempotency
key and request; never issue a fresh key to compensate for an unknown outcome.
These retry semantics follow the [NGINX proxy contract](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream).

Acceptance exercises verified TLS, both backends, owner review, frozen billing
scope, partial-header expiry, oversized and unauthorized bodies, discarded
responses, in-flight worker SIGTERM drain/restart and gateway QUIT. Gateway drain
allows up to 15 seconds. Replicas keep accepted work alive during graceful
shutdown; abrupt termination still follows durable unknown-usage recovery.
The fixture exposes backend ports only on host loopback for independent tests.

For deployment, restrict backend access to the gateway's private network and
provision managed certificates through the deployment secret system. This
reference does not certify an unencrypted cross-host network: use authenticated
TLS between gateway and service wherever the private-network trust assumption
does not hold. Generated self-signed lab certificates are test assets.

Drain routing before replacing a replica, wait for accepted requests or use the
documented unknown-outcome recovery, then verify readiness on the replacement
before admitting it. Keep pending runs on their compatible pinned workflow assets
and SDK image: changing the asset fingerprint requires completing/draining those
runs or retaining an old compatible execution fleet. The service refuses asset
mismatch instead of silently executing a changed workflow. Back up persistent
stores independently; replacing disposable fixture containers is not an upgrade
procedure. See [persistence.md](persistence.md) and [recovery.md](recovery.md).
