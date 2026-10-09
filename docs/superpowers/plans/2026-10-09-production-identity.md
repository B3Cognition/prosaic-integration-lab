# Configurable identity implementation brief

The maintainer authorized the production blocker fixes and confirmed an existing
Keycloak deployment, preferring a configurable authentication provider. This
implements issue 7 within that direction; no production server or credentials
are contacted. Execution remains synthetic and billing-ineligible in the lab.

Use a provider boundary with explicit fixture and OIDC implementations. A
production deployment profile requires OIDC, HTTPS issuer/JWKS/introspection,
audience and trusted subject bindings. Fixture bearer maps remain explicit lab
mode. No JWT tenant/account claim or forwarded identity header grants authority.
Require signed RS256 access tokens with exp/iat/sub/iss/aud; use PyJWT and
cryptography for verification. Trusted configuration supplies endpoints; token
jku/x5u URLs never drive network access. Bound token/keyset size, HTTP deadline,
connection pool, cache lifetime and unknown-key refresh. Reject duplicate kids.

Production revocation uses configured RFC7662 online introspection with zero
active-token cache; inactive tokens fail closed. Offline validation alone cannot
prove provider logout/revocation. Server bindings support disable and not-before
policy. Secret delivery includes provider client credentials only in private
runtime config. Failures expose curated responses, never token contents.

Tests proceed red before green: signed claim/algorithm/identity negatives,
spoofed tenant/billing claims, endpoint policy and unavailable provider, bounded
key cache/rotation, real HTTP owner views and revocation. An owned TLS issuer
fixture exercises public provider protocols; an owned Keycloak realm reference
must additionally exercise actual Keycloak configuration, without contacting the
maintainer's existing deployment. Both replicas must agree on frozen attribution
through resume. TLS ingress/drain qualification remains separately issue 11.

Reference contracts: [PyJWT API](https://pyjwt.readthedocs.io/en/stable/api.html)
and [Keycloak OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers).
The service verifies audience explicitly; Keycloak must issue the configured API
audience via its client/audience mapper. Changing bindings never rewrites an
existing reservation's billing attribution.
