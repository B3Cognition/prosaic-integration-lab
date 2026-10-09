# Production hardening follow-up — 9 October 2026

The fourteen filed blocker groups now have local fixes and regression coverage.
This qualifies a bounded synthetic pilot, not a production release. Original red
audit receipts remain unchanged; the [fix ledger](production-fixes.md) records
each regression, candidate wheel and verification receipt.

Final verification: 182 tracked hardening unit/functional tests and 220 full
shared local tests passed. Required candidate cells passed **88 audit, 19 identity,
5 ingress tests on each PostgreSQL major (16 and 18)**, zero skips, verified
cleanup and payload provenance. Final immutable image:
`sha256:bd5259288814e04cdeadcee99c2b2c48ef5dc1f95fd8d6a7f50019aa660b2dfd`.
These are local ARM Docker results; native remote CI remains pending.

## Fixed locally

Read-only schema/grant readiness; atomic Harness lease registration; bounded
HTTP/database admission; authentication before body parsing; immutable non-root
replicas and separate migrations; owner-only revision-bound approval; configurable
OIDC with real Keycloak TLS, revocation and rotation; transactional upgrades and
backup/restore; explicit uncertain-effect recovery; finite durable execution
budgets; non-sticky TLS ingress and in-flight drain; provenance-checked release
gates; protected metrics and sanitized correlation; atomic reservation ceilings,
private retention copies and independently reconciled open-loop load profiles.

Keycloak is a verified reference provider. Issuer, audience, JWKS, introspection,
CA and trusted subject bindings are configuration. The service does not rely on
Keycloak-specific identity claims for tenant or billing authority.

## Must complete before production promotion

| Requirement | Remaining work |
| --- | --- |
| Released SDK fixes | Publish the reviewed Runtime and Harness adapter candidates, update pinned release provenance, and rerun the released-package gates. The original released accounting adapter still fails readiness regressions. |
| Required native CI | Publish/activate the prepared native AMD64/ARM64 PostgreSQL 16/18 matrix and enforce repository checks. Local Docker evidence does not prove remote CI execution. |
| Actual deployment | Configure the real OIDC provider, managed TLS, private backend networking, migration/credential privileges, monitoring and recovery ownership. The owned Keycloak fixture does not validate the existing deployment. |
| Capacity acceptance | Approve a measured deployment-specific pilot ceiling and rejection/deferral behavior. Longer soak, actual model latency, persistent growth and database HA/PITR/RPO/RTO remain unqualified. |
| Billing release | Synthetic recorder estimates are billing-ineligible. Real provider reconciliation and any separately developed billing/export integration require their own acceptance evidence. |

## Can be postponed within the bounded pilot

Automatic retention deletion/idempotency expiry, automatic retry of uncertain
effects, broad provider/tool/streaming certification, autoscaling and larger load
targets. Keep these disabled. Preserve uncertain evidence and require explicit
owner decisions. The reservation ceiling and generation ceiling force reviewed
operator action instead of silently deleting data.

## Measured limits

Six-user baseline: 20 offered/completed at 1 RPS for 20 seconds, concurrency 2,
tenant admission 1, zero errors/rejections, completed-workflow p95 0.1615 s.
Receipt `aaedc86297c1413f95f71fe9aeabc211` (PostgreSQL 16).

Overload: 300 offered at 30 RPS for 10 seconds, concurrency 8; 163 accepted and
independently reconciled calls, 107 completed, 193 rejection/deferral events,
including 56 deferred approvals. Zero correctness errors; 64.33% rejection and
uneven actor completion mean **SLO failure**, despite accounting correctness.
Completed-workflow p95 0.1291 s excludes rejected requests. Receipt
`19843b8549574aeca8938a423b27cb5d` (PostgreSQL 18). Both used local ARM fixtures,
verified cleanup, synthetic calls and image
`sha256:53f11ede4d2417ffcf64e2aec23b87f564a7009d0e94313d57467fc1cc53fe78`.

No paid model calls or customer credentials were used for this hardening pass.
Terminal traffic/accounting, SLO and retention commands are in
[capacity-retention.md](../capacity-retention.md); operational metrics are in
[observability.md](../observability.md).

Auth0 extension: configurable `provider: auth0` now shares bounded JWT/JWKS
verification with a five-minute lifetime cap and explicit offline revocation
semantics. Keycloak `oidc` retains per-request introspection. See
[Auth0 verification](auth0-2026-10-09.md) and [identity setup](../identity.md).
Local contract tests do not certify an existing Auth0 tenant.
