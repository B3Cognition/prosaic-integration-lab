# Changelog

## 0.2.0 — 2026-10-09

- Multiuser terminal traffic and separate accounting viewers; bounded open-loop
  stress profiles with independently reconciled calls and explicit SLO results.
- Trusted owner/tenant/billing binding, atomic idempotency, bounded HTTP/database
  admission and shared persistent reservation ceilings.
- Configurable OIDC/Keycloak introspection and Auth0 short-lived JWT verification,
  protected metrics, immutable non-root replicas and verified TLS ingress/drain.
- Explicit migrations, private backup/restore, uncertain-effect recovery and
  conservative retention copies that never delete unresolved evidence.
- Durable Lago outbox, fenced delivery and reconciliation against synthetic
  fixture charge rates, including duplicate/crash/conflict/unknown-evidence cases.
- Required release provenance and native AMD64/ARM64 PostgreSQL 16/18 gates:
  audit, identity, ingress and pinned Lago acceptance. No paid inference.

This is a bounded integration blueprint. Local/cloud identity deployment,
production certificates, HA/PITR/longer capacity qualification and customer
invoicing/payment collection require separate deployment acceptance.
