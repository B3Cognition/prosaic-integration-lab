# Lago Billing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Native execution is recommended; do not spawn agents without authorization.

**Goal:** Verify durable Prosaic usage delivery and fixture-charge reconciliation against disposable local Lago through failures and retries.

**Architecture:** A separate Python exporter scans frozen application reservations using the installed public Runtime recorder. An application-owned PostgreSQL outbox persists exclusive token dimensions and delivers immutable events to Lago. The existing owned runner provisions and removes the optional fixture and retains sanitized evidence.

**Tech Stack:** Python 3.12, psycopg, httpx, pytest, Docker/Podman, lab PostgreSQL 16/18, release-pinned Lago with PostgreSQL event storage and Redis.

**Spec:** `docs/superpowers/specs/2026-10-09-lago-billing-design.md`

## Global Constraints

- No sibling library changes, private imports or model-client instrumentation are required.
- Existing accounting evidence remains billing-ineligible.
- Replicas need no Lago key and no billing-table write privileges.
- Use Lago's PostgreSQL event store in this slice; do not extrapolate deduplication results to ClickHouse.
- Missing, quarantined, unsupported or unresolved evidence is explicitly excluded with a reason; it never becomes zero usage.
- Preserve existing user changes and historic receipts; no push or release.
- Keep frozen scope, loopback ports, release checksums, exact resource IDs and verified cleanup.

## Review Focus

- A completed call with unknown cached usage must be excluded, never charged as uncached input.
- A late observation must be discovered after earlier scans, including beyond the first 1000 calls.
- A duplicate validation response must recover only after remote payload comparison.
- A stale worker must not acknowledge another worker's lease.
- Pricing/account-mapping changes must produce a conflict instead of a second event.

## Files and interfaces

- `src/prosaic_integration_lab/billing_projection.py`: `project(call, reservation, mapping) -> dict`; returns three immutable event payloads or an exclusion with a bounded reason.
- `src/prosaic_integration_lab/billing_store.py`: `BillingStore(dsn)` with `enqueue(projection)`, `claim(limit, lease_seconds)`, `ack(key, token)`, `fail(key, token, category, retry_at)` and `summary(scope)`; explicit migration/readiness functions.
- `src/prosaic_integration_lab/billing_scan.py`: `scan(metadata, recorder_factory, store, mappings)`; public recorder pagination and reservation validation.
- `src/prosaic_integration_lab/billing_delivery.py`: `deliver(store, client, limit)`; finite HTTP and exact duplicate reconciliation.
- `src/prosaic_integration_lab/metadata.py`: add `billing_reservations()` returning frozen identifiers only.
- `lab_runner/lago.py`: `start(stack)`, `seed(config, accounts)`, `current_usage(config, subscription)`, `reconcile(config, expected)`; fixture lifecycle via OwnedStack.
- `dependencies/lago.json`: immutable source/image/API provenance.
- `lab_runner/__main__.py`: optional `test --mode lago`, finite lane timeout, sanitized results.
- `tests/unit/test_billing_projection.py`, `tests/unit/test_billing_delivery.py`, `tests/unit/test_billing_scan.py`: projection and external-boundary regressions.
- `tests/acceptance/test_lago.py`, `tests/acceptance/test_billing_outbox.py`: actual stack evidence, durable recovery and privileges.

### Task 1: Projection and source traversal

- [ ] Verify installed release wheel payloads using `scripts/audit_install.py` and record the selected released/candidate mode. Read installed public recorder contracts and fixture token responses.
- [ ] Write projection tests using actual recorder-shaped call fixtures. Pin unknown cache, known zero/nonzero cache, reasoning overlap, total inconsistencies, model/tier mismatch, failed/cancelled calls with measured usage and untrusted observations.

```python
result = project(complete_call_with_unknown_cache, reservation, mapping)
assert result['exclusion'] == 'unknown_cached_input'
assert result['events'] == []
```

- [ ] Run `.venv/bin/python -m pytest tests/unit/test_billing_projection.py -q`; observe failure before implementation.
- [ ] Implement projection with strict integers, supported fixture-model semantics, Decimal-independent token quantities, finished_at timestamps and opaque transaction IDs. Store source identity separately from mapping/payload fingerprints. Reject changed payload/mapping under the same source identity.
- [ ] Add the narrow reservation API; enumerate namespace/environment/application/tenant/actor/account/request/run filters exactly. Page calls with limit 1000 and offsets; restart each scan from the beginning and validate every returned context.

```python
scan(metadata, recorder_factory, store, mappings)
scan(metadata, recorder_factory, store, mappings)
assert store.projected_call_ids() == expected_call_ids
```

- [ ] Use a fake public recorder boundary to reproduce 1001 calls under one reservation and an unresolved call that gains an observation between scans. Watch failures, implement traversal, rerun targeted tests. Cross-actor shared accounts must map together; equal account names in different tenants must remain separate.

### Task 2: Durable outbox and restricted roles

- [ ] Write required real-PostgreSQL tests for atomic three-event enqueue, immutable conflict detection, competing claims, stale token acknowledgements, lease expiry and persisted exclusions.

```python
first = store.claim(limit=3, lease_seconds=1)
# Fixture barrier expires this lease and a second process reclaims it.
second = reclaimed_rows
assert store.ack(first[0]['key'], first[0]['token']) is False
assert store.ack(second[0]['key'], second[0]['token']) is True
```

- [ ] Run tests against an owned database and observe failures; missing infrastructure fails instead of skipping.
- [ ] Implement `lab_billing` schema/version with separate immutable identity/payload fields and mutable delivery/lease fields. Use transactionally locked bounded claims, database time and fencing tokens. Enqueue all dimensions atomically. Keep observations/exclusions revisitable without mutating Runtime tables.
- [ ] Extend explicit fixture provisioning with an exporter-specific role and source-read/outbox-write grants. Ensure replica roles cannot mutate billing tables and exporter cannot mutate Runtime/Harness evidence. Validate schema/grants before scans or delivery.
- [ ] Reconstruct processes after committed writes; verify pending rows survive crash and bounded failure records contain no payload/credential leaks. Run targeted tests on PostgreSQL 16 and 18.

### Task 3: Lago fixture and HTTP delivery

- [ ] Resolve supported Lago release from immutable upstream source, capture exact API schema, inspect image architecture manifests and pin API/worker, database and Redis digests in `dependencies/lago.json`. Record the verified event-store and monetary contracts.
- [ ] Add fixture tests that fail before integration: intention-before-create, lost-create acknowledgement, loopback endpoints, label/ID validation, timeout and cleanup failure.
- [ ] Implement `lab_runner/lago.py` using `OwnedStack._create` and its durable manifest, without an independent cleanup mechanism. Provision generated secret files, isolated database/Redis/API/worker, finite readiness and a disposable organization. Disable telemetry/external payment integrations. Seed account mappings, UTC subscriptions and three standard sum charges before calls.
- [ ] Write HTTP boundary tests for timeouts, 429, transient 5xx, permanent 4xx, authentication stop, duplicate validation error with exact match and mismatched payload. Verify replay preserves subscription, code, timestamp, properties and transaction ID.

```python
deliver(store, duplicate_client_with_matching_event, limit=3)
assert store.summary(scope)['acknowledged'] == 3
deliver(conflicting_store, duplicate_client_with_changed_quantity, limit=3)
assert conflicting_store.summary(scope)['conflicts'] == 1
```

- [ ] Observe test failures, then implement individual POST delivery, exact duplicate lookup/comparison, fenced updates, bounded persisted backoff and finite HTTP deadlines. Never hold a database transaction over HTTP.
- [ ] Verify one real synthetic event and its exact replay against Lago current usage. Record currency-unit/rounding behavior; do not treat a successful POST as usage convergence.

### Task 4: Required end-to-end robustness lane

- [ ] Add `test --mode lago` to the runner, requiring `test`, preserving default modes and extending the finite subprocess timeout for the explicit lane. Include billing provisioning/readiness checks and retain sanitized JUnit/JSON.
- [ ] Write `test_lago.py` and `test_billing_outbox.py` cases for all twelve spec criteria. Use explicit fixture barriers for crash windows; retain independent model-counter, ledger-call, outbox-event and Lago-quantity expectations.

```python
assert evidence['model_dispatches'] == evidence['ledger_calls']
assert evidence['projected_events'] == 3 * evidence['admissible_calls']
assert evidence['remote_quantities'] == evidence['independent_quantities']
assert evidence['runtime_billing_eligible'] is False
```

- [ ] Prove rejected outputs are included by fixture policy, cross-replica approval adds no events, unknown/quarantined observations are excluded and visible, concurrent scans converge and stale workers cannot overwrite state.
- [ ] Stop Lago while workflows finish; restart using verified exact IDs, refresh ephemeral endpoints, reconstruct exporter and reconcile without new inference. Crash after remote acceptance before local ack and replay the exact event.
- [ ] Generate the pagination fixture with public recorder prepare/observe calls and more than 1000 calls within one run filter. Label direct ledger fixtures separately from actual model-dispatch evidence.
- [ ] Require original event timestamps inside the seeded open period. Deliberate out-of-period evidence fails visibly; no retimestamping or fixture pricing changes hide mismatches. Reconcile quantities first, then per-charge decimal/cent rounding.

### Task 5: Verification and operator documentation

- [ ] Run `.venv/bin/python -m pytest -q`, build the consumer image and run existing deterministic/recovery lanes. Investigate regressions before expanding tests.
- [ ] Run `.venv/bin/python -m lab_runner test --mode lago --postgres-version 16` and repeat with `--postgres-version 18`; missing infrastructure, skips, unknown pending outcomes and cleanup failures fail the command.
- [ ] Run `.venv/bin/python -m build`; audit installed dependency payloads again if dependencies changed. Check `git diff --check` and inspect reports for credential/prompt sentinels.
- [ ] Update README, handoff and verification ledger with actual commands, receipts, host/container architectures, image/source provenance and observed limitations. Preserve old failed receipts; do not describe fixture reconciliation as invoicing or production certification.
- [ ] Review the complete change against the spec: especially unknown cache, delayed observations, exact duplicate comparison, lease fencing and frozen identity. Keep only relevant changes; commit scoped implementation/evidence without pushing or releasing.

## Coverage audit

Task 1 covers public APIs, frozen attribution, token semantics and pagination.
Task 2 covers migration/readiness, privileges, durability, conflicts and fencing.
Task 3 covers immutable Lago provenance, exact ownership, API retry semantics and
duplicate recovery. Task 4 covers spec acceptance criteria 1–12 and real-stack
reconciliation. Task 5 covers regression checks, PostgreSQL matrix, sanitization,
documentation and honest evidence. No wallet/payment/invoice feature is included.
