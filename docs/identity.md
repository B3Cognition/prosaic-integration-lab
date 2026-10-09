# Configurable authentication

The service supports explicit lab fixture authentication and a configurable OIDC
provider. Keycloak is the tested reference. Other issuers configure the same
issuer/audience/JWKS/introspection interface; no Keycloak SDK or endpoint lookup
from token headers is involved. Current signature policy is RS256, RSA2048+.

`deployment_mode: production` requires OIDC and HTTPS issuer/JWKS/introspection,
and rejects fixture identities. This secures identity configuration; service TLS
ingress qualification is separately tracked in issue 11. Execution `environment`
remains `sandbox` for this synthetic test blueprint, including the identity lane,
so its estimates remain billing-ineligible. This profile is not a production
model provider configuration or a production deployment certification.

Copy [oidc.example.json](../configs/oidc.example.json) into secret-managed runtime
configuration, replacing endpoints, audience, subject bindings and credentials.
Never commit populated config. Use operating-system trust roots, or supply a
read-only `ca_file` for a private CA. HTTPS verification cannot be disabled in the
production profile. Lab-only `allow_insecure_http` is explicit opt-in.

Tokens require exp/iat/sub/iss/aud and the configured audience/issuer. The maximum
token lifetime is configurable up to 3600 seconds (default 300). Optional
`required_scope` requires an exact space-delimited scope. Subject bindings are
trusted server configuration: tenant, actor and billing account never come from
token claims or forwarded headers. `disabled` and `not_before` provide local
binding policy after config delivery/restart. Existing reservations retain their
frozen attribution when current bindings change.

Every accepted token is also checked through configured RFC7662 introspection,
with no active-token cache. Inactive tokens return 401. Provider/network/protocol
failure returns curated 503 and cannot dispatch a workflow. Offline JWT validation
alone does not promise immediate provider revocation. Introspection needs a
confidential API client; its credential belongs in private runtime config, not
headers supplied by the caller. Keycloak exposes the endpoints described in its
[OIDC documentation](https://www.keycloak.org/securing-apps/oidc-layers).

Configure a Keycloak audience mapper to include the service API audience in
access tokens; checking a signature alone is insufficient. Bind the verified
stable user `sub`, rather than mutable username/email, to service-owned identity.
For interactive applications, use authorization-code/PKCE at the login client.
The owned fixture uses direct grants with generated users solely for automated
tests, not as the recommended login flow.

Per replica: complete authentication deadline 2 seconds, eight outbound connections,
64 KiB response limit, at most 32 JWK entries, cached keys 60 seconds and unknown-key
refresh at most once per 5 seconds. These bounds are configurable within validated
limits. Publish replacement keys before activating them and retain old keys
through outstanding token expiry. Removed keys stop verifying after cache expiry;
online introspection can reject revoked tokens earlier. Token `jku`/`x5u` never
selects a network URL. Claim and signature verification use the pinned
[PyJWT API](https://pyjwt.readthedocs.io/en/stable/api.html).

Run the owned reference lane from the terminal:

```sh
.venv/bin/python -m lab_runner test --candidate --mode identity --postgres-version 16
.venv/bin/python -m lab_runner test --candidate --mode identity --postgres-version 18
```

It creates a digest-pinned Keycloak 26.8 realm with a generated one-day TLS
certificate, private generated users/client credentials, PostgreSQL and two
replicas. All ports bind loopback. It exercises real token issuance, cross-replica
owner access/accounting, spoofed billing claims, signing-key rotation, logout and
issuer outage. It never contacts an existing Keycloak instance. Exact owned
resource cleanup and sanitized receipts are required; no model credits are used.
