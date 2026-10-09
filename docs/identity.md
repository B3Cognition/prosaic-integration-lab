# Configurable authentication

The service supports explicit lab fixture authentication and a configurable OIDC
provider and an explicit Auth0 JWT profile. Keycloak is the online-introspection
reference. Other introspecting issuers configure the same
issuer/audience/JWKS/introspection interface; no Keycloak SDK or endpoint lookup
from token headers is involved. Current signature policy is RS256, RSA2048+.

`deployment_mode: production` requires `oidc` or `auth0` and HTTPS issuer/JWKS
(plus introspection for `oidc`),
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

For `provider: oidc`, every accepted token is checked through RFC7662 introspection,
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

## Auth0 profile

Copy [auth0.example.json](../configs/auth0.example.json) into private runtime
configuration. Select `provider: auth0`, set the exact HTTPS issuer (including
its trailing slash), the custom API Identifier as `audience`, and the issuer's
`/.well-known/jwks.json` endpoint. Custom domains are supported through these
explicit URLs. Register an RS256 API and grant/request the configured
`run:service` scope. Use authorization-code/PKCE at the interactive login client;
this service consumes access tokens, not login credentials or ID tokens.
Auth0 documents [access-token validation](https://auth0.com/docs/secure/tokens/access-tokens/validate-access-tokens)
and [JWKS locations](https://auth0.com/docs/secure/tokens/json-web-tokens/locate-json-web-key-sets).

The profile shares bounded RSA signature, exact issuer, audience (string or
array), expiration/issued-at and optional scope validation with OIDC. Bind the
stable `sub` (for example `auth0|...`) in trusted `subjects`; organization,
email, tenant and billing claims never select application authorization. No
Auth0 client secret, Management API access, `/userinfo` call or introspection
configuration is required by the API. Supplying introspection to this profile
is rejected rather than silently ignored.

Configure the Auth0 API access-token lifetime to **300 seconds or less**; both
the issued `exp - iat` and the service's `max_token_lifetime` must fit this cap.
Auth0's longer default is deliberately rejected. See
[token lifetime settings](https://auth0.com/docs/secure/tokens/access-tokens/update-access-token-lifetime).
Logout or refresh-token revocation does not make this offline verifier immediately
reject an already-issued access JWT. An otherwise valid JWT can be accepted until
expiry. Local `disabled`/`not_before` bindings take effect after delivering config
and restarting every replica. Cached signing keys are accepted only during their
bounded TTL; a failed expired-key refresh returns 503. It does not fall back to
stale keys. Keycloak `oidc` still checks activity on every request. See Auth0's
[refresh-token revocation limitations](https://auth0.com/docs/secure/tokens/refresh-tokens/revoke-refresh-tokens).

Tests cover Auth0-shaped audience arrays, JWT validation, binding policy, rotation,
outage bounds, factory selection and the HTTP boundary. The owned identity lane
also rolls both real replicas to `auth0`, using real TLS/RS256 tokens from its
owned Keycloak issuer, and verifies cross-replica approval, owner isolation,
frozen billing and binding disablement before body parsing. This tests the JWT
integration contract; it is **not live Auth0 tenant certification**. Actual tenant
issuance, custom domains, scope grants and lifetime settings need deployment
acceptance with that tenant. No existing Auth0 account is contacted by these tests.
