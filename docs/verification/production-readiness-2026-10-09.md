# Prosaic production blueprint readiness

**Decision: do not deploy this lab service unchanged or present it as a production blueprint.**
The installed libraries pass substantial correctness testing, including durable
recovery, ownership isolation and measured accounting. The consumer and released
accounting adapter still have reproducible production gaps. The new audit lane
has **49 passing and 9 failing test cases on each of PostgreSQL 16 and 18**,
with zero skips and verified cleanup. The nine failures remain visible gates;
they have not been weakened, marked expected or fixed by this audit.

Date: 2026-10-09. Scope: released Prosaic 0.3.1, Runtime/Harness 0.6.0,
PostgreSQL adapters 0.1.0, two identical consumer replicas on Docker Desktop
Linux/arm64, host Python 3.12.14. All inference was synthetic. No local model,
cloud provider, production database or model credit was used.

## What the tests establish

| Check | Result | Meaning |
| --- | --- | --- |
| Lab unit suite | 38 passed | Ownership/resource cleanup, projections, provenance, CLI and stream regressions |
| Prosaic Python and frozen differential suite | 432 passed, zero skips | Python behavior against immutable v0.2.0 TypeScript oracle |
| Original shipped CLI oracle suites | 55 passed across 13 suites | CLI compatibility through the installed Python command |
| Prosaic installed wheel smoke | Passed | Parsing/discovery/apply/import/revert work with Node hidden from PATH |
| Runtime released snapshot | 361 passed | Tests of the exact Runtime release installed in the lab |
| Runtime released PostgreSQL adapter | 24 passed, zero skips | Real PostgreSQL replay/races/pagination/rollback/quarantine and synthetic transport capture |
| Runtime newer checkout | 456 passed | Additional checkout behavior; not evidence that the lab has those capabilities |
| Harness checkout matching release | 172 passed | Workflow, boundary, recovery, transport and budget tests |
| Existing recovery lane, PostgreSQL 16 and 18 | 27 passed on each | Receipt adoption, explicit interrupted retry, unknown accounting, scope safety |
| Existing load lane, PostgreSQL 16 | 23 passed | Bounded execution admission and concurrent state decisions |
| Expanded production audit, PostgreSQL 16 and 18 | 49 passed, 9 failed on each | Production gaps reproduced alongside existing correctness checks |
| Multiuser baseline | 500 of 500 workflows completed | 50 users, 10 runs/user, concurrency 2; no rejection/error; 500 ledger calls reconcile |
| Overload | 1,000 attempts; 29 dispatches reconcile | 100 users, concurrency 32; 6 complete, 971 start-rejected, 23 approval-deferred; no correctness error |
| PostgreSQL 18 accounting demo | 6 calls; 5 complete, 1 unresolved | Known fixture estimate USD 0.001850; missing usage stays unknown |

The expanded checks verify malformed/oversized inputs cannot dispatch; identical
keys are isolated by owner; completed requests do not redispatch; lost HTTP
responses do not authorize another call; accounting conflicts cannot amend
accepted attribution/amounts; quarantined evidence is visible without another
estimate; private input and mounted-credential sentinels are absent from tested
public responses and both stdout/stderr server logs; runtime roles cannot become
administrators or amend application identity. Harness readiness correctly rejects
a missing receipt column and a missing receipt-write grant.

The released adapter suite additionally checks concurrent intent/observation
replay, conflicting first observations, partial evidence, atomic assessment,
bounded pages with complete report aggregation, transaction rollback/restart,
non-streaming and streaming transport capture, and prevention of dispatch with
an uninitialized ledger. This is component evidence; the service still disables
streaming and tools. Installed payload verification for all five wheels and the
lab wheel/sdist build also passed after testing.
Prosaic, Harness and the newer Runtime checkout also built wheel/sdist artifacts
successfully; build outputs remain ignored and were not installed over releases.

Two public-SDK tests add real HTTP inference with PostgreSQL persistence and
reconstruction: missing final usage blocks a finite token budget, and rejected
validation consumes the known token budget before a second call. Explicit retry
does not bypass either block; changed recorder defaults do not move the original
call to a different tenant/account. These are SDK/adapter proofs, not deployment
of a budgeted workflow through the current service endpoint. Worker loss before
receipt under a finite budget still needs a combined HTTP acceptance case.

## Fix before production adoption

### P1 Accounting and application readiness can give a false healthy result

**Confirmed on both database majors.** Rename the accounting intent `payload`
column or observation `payload_hash` column: `/readyz` still returns 200. Revoke
accounting intent INSERT or application reservation INSERT: readiness still
returns 200. Remove the application's owner/idempotency unique constraint:
readiness still returns 200. These schemas/roles cannot perform the advertised
operations, so deployment traffic can be admitted into a broken service.

**Owner:** Runtime PostgreSQL adapter for accounting schema/grant validation;
integration consumer for application metadata validation. Released recorder
`check_ready()` checks only `intents.namespace` and `observations.amount`.
Application `Metadata.check_ready()` checks schema version and column existence,
not types, constraints or required writes. Harness already checks a fuller
contract and its negative cases pass.

**Fix:** validate required table/column types, nullability, scoped keys,
relationships/check constraints and runtime privileges without performing DDL.
Keep migrations separate. Publish and pin the upstream adapter fix before
claiming the installed lab has it.

**Acceptance:** the five corresponding failing test cases become green on
PostgreSQL 16/18; incompatible schema fails readiness/startup, runtime cannot
repair it, ordinary request/replay/recovery behavior stays green.

Sources: `execution.py:29`, `metadata.py:29`, released
`prosaic_runtime_postgres/__init__.py:95`; failures
`test_missing_accounting_contract_fails_readiness_without_repair` (two cases),
`test_missing_write_grant_fails_readiness_without_repair` (accounting/application),
`test_missing_application_uniqueness_fails_readiness_without_repair`.

### P1 Overload limits model execution but leaves database admission unbounded

**Confirmed with real PostgreSQL.** Hold the two execution slots on A, then send
12 new-key starts. Every extra request returns `503 capacity_exhausted`, and
none dispatches a model call, but the durable reservation count still grows.
The service calls `metadata.reserve()` before acquiring execution capacity.
That work uses another executor and opens a database connection per operation.
The existing execution semaphore therefore does not bound database demand,
queued metadata work or storage growth. No per-user quota/retention exists.

**Owner:** integration consumer. This is not a Harness execution-admission bug.

**Fix:** bound request/metadata admission before allocating reservations, with
bounded connections and queueing; define per-tenant/user fairness and reservation
retention. Preserve reservation-before-dispatch, owner-scoped idempotency and
uncertain-start safety. Do not solve growth by deleting unresolved effects.

**Acceptance:** saturation rejects before unnecessary durable allocation;
connection/queue/storage growth remains bounded during a sustained unique-key
flood; existing-run reads and unrelated users remain usable; no duplicate call.

Sources: `app.py:110`, `metadata.py:37`, `execution.py:84`; failure
`test_overloaded_starts_do_not_grow_durable_reservations`.

### P1 Reject unauthenticated slow bodies and bound request duration

**Confirmed over a real TCP socket.** An unauthenticated POST declares a
100-byte body but sends only `{`. It receives no rejection within the one-second
test deadline. Middleware waits for the body before route authentication; the
8 KiB size ceiling does not impose a time limit. Network-scale exhaustion was
not measured, but the missing early rejection/deadline is reproduced.

**Owner:** consumer and production ingress configuration.

**Fix:** authenticate protected requests before reading bodies; enforce body
read deadlines, bounded connection/request concurrency and rate limits at the
ingress and application boundary. Retain size limits and safe errors.

**Acceptance:** incomplete unauthorized requests are rejected promptly or closed
within an explicit deadline; many slow connections cannot exhaust service
capacity; health/readiness and authorized requests remain usable.

Sources: `app.py:47`, `app.py:74`, `stack.py:175`; failure
`test_unauthenticated_partial_post_is_rejected_before_waiting_for_body`.

### P1 Production deployment must contain the service and freeze assets

**Confirmed:** effective service UID is 0 and root filesystem is writable.
The Dockerfile has no service USER and the launcher has no read-only root,
capability restrictions or service resource limits. Workflow assets live on
that writable filesystem. This is a containment/configuration finding, not a
demonstrated remote code-execution exploit.

**Owner:** consumer deployment/image. Keep provisioning privileges separate.

**Fix:** run replicas as a dedicated non-root user; deliver readable secrets
only to that user; make assets/root filesystem immutable; explicitly mount
bounded scratch; drop unnecessary capabilities, forbid privilege escalation,
and set memory/CPU/process limits. Verify Prosaic resolution and subprocesses
still work under these restrictions.

**Acceptance:** non-root and read-only-root assertions pass; both replicas and
recovery work with immutable assets; required scratch remains private/bounded;
service never receives migration/owner credentials.

Sources: `containers/Dockerfile:2`, `stack.py:171`; failures
`test_service_container_runs_as_nonroot`,
`test_service_assets_are_on_readonly_root_filesystem`.

### P1 Human approval needs a safe result to review

**Confirmed by projection contract/code:** the public view contains revision,
status and choices but discards the output and question. It proves an owner can
advance a pause, not that a human can review the generated result. A production
approval service must not present a meaningful approve button for an invisible
result.

**Owner:** consuming service/product policy. Add a schema-approved result view
bound to the exact revision reviewed. Keep prompts, internal history, private
tool arguments and arbitrary operator state filtered. Test distinct users,
result escaping, stale approvals and changes to reviewed material.

Sources: `views.py:1`, `tests/unit/test_policy.py:21`. This intentionally safe
lab projection needs a production policy; do not expose raw Harness state.

## Production capabilities still missing

These are adoption requirements rather than failures of the documented
disposable lab. Define the intended deployment before copying its configuration.

| Need | Required proof before adoption | Owner |
| --- | --- | --- |
| Real authentication, TLS and secret rotation | Trusted identity-provider mapping; token expiry/revocation; tenant/account mapping; gateway and service cannot accept spoofed identity | Consumer/ingress |
| Durable deployment and upgrades | Separate non-disposable database deployment; versioned application migrations preserving ownership/scope/idempotency/uncertain phases; backup and restore exercise | Consumer/database operations |
| Operational recovery | Runbook for `start_uncertain`, unknown usage and deferred approval; reconciliation never assumes an uncertain call did not happen; no automatic effect retry | Consumer with library contracts |
| Budgeted production model use | Configure policy budgets; combine worker-loss-before-receipt, explicit retry and finite-token-budget tests through A/B HTTP | Consumer/Harness acceptance |
| Gateway/load balancer | Real non-sticky routing, timeout/disconnect handling, graceful drain/redeploy and trusted-header rules through intended ingress | Consumer deployment |
| Repeatable release gates | Required CI, PostgreSQL matrix, target architecture, installed-wheel provenance, upgrade compatibility and audit failures block promotion | All repositories |
| Service observability | Sanitized structured request/run/tenant/call correlation; latency and saturation metrics; alerts for unknown accounting, stuck reservations and readiness failure | Consumer/operations |
| Capacity and retention policy | Intended workload SLOs; fair quotas; bounded DB pools; evidence retention/archival; soak and lock/connection-pressure tests | Consumer/operations |

Static lab bearer identities, loopback ports, fresh schema provisioning and a
runner that removes its database volume are appropriate test fixtures. They
must not become the production identity, storage or lifecycle design. The
synthetic model's unauthenticated control endpoints are fixture-only.

## What can be postponed with explicit feature boundaries

| Work | Can wait while |
| --- | --- |
| Tool loops, cross-user tool isolation and effect idempotency | Tools remain disabled. Enabling them requires two-turn accounting, missing-turn usage and loss around an independently counted effect |
| Streaming and native Anthropic/provider certification | Production advertises only the tested non-streaming OpenAI-compatible path and separately certifies its chosen real endpoint |
| Invoices, paid tools, BYOK/subscription pricing and billing export | Usage is displayed as evidence/estimates; all assessments remain billing-ineligible |
| Monetary spending caps and paid-provider test allowance | No paid mode is enabled. A call allowance is not a monetary cap |
| Durable scheduler/background retries | Synchronous bounded workflows suffice and users explicitly resume. A scheduler needs separate ownership/effect semantics |
| Database HA/failover and multi-region | A single primary meets the declared availability/RPO requirements; a working backup/restore procedure still cannot wait |
| Other architectures and Podman | Production supports only the architecture/engine actually tested. Before x86/Podman adoption, execute their matrix |
| Extended soak, arrival-rate generators and autoscaling | The deployment remains a limited pilot with explicit load ceilings; general production scale still requires SLO evidence |
| Rich billing dashboard and commercial rate-card catalog | Terminal/JSON evidence meets the pilot need; correctness and unknown coverage are retained |

Do not postpone auth boundaries, bounded admission, truthful readiness,
durable upgrade/restore procedures or safe handling of uncertain external effects.

## Load observations

These are local synthetic observations, not a provider throughput claim or a
production benchmark. Percentiles use sorted request samples at
`floor((n-1)*p)`. Total runner time includes startup and cleanup.

| Workload and operation | Samples | p50 ms | p95 ms | p99 ms |
| --- | --- | --- | --- | --- |
| Baseline start | 500 | 68.44 | 78.37 | 87.56 |
| Baseline approval | 500 | 26.36 | 30.76 | 36.39 |
| Baseline usage | 500 | 14.40 | 15.78 | 17.67 |
| Overload start, including rejections | 1,000 | 54.87 | 105.59 | 545.34 |
| Overload approval, including rejections | 29 | 42.51 | 71.40 | 75.32 |
| Overload usage | 29 | 29.96 | 105.42 | 105.98 |

Baseline wall time was 40.13 seconds; all 500 measured calls were complete.
Overload wall time was 11.10 seconds. Its 971 rejected starts did not dispatch;
23 deferred approvals retained a measured call and waiting workflow, with no
automatic retry. Six workflows completed. The allowed-overload pass means
correctness/accounting held, not acceptable user throughput or fairness.

## Reproduce and inspect

Run from the lab with the documented pinned image and Docker available:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m lab_runner test --mode recovery --postgres-version 16
.venv/bin/python -m lab_runner test --mode recovery --postgres-version 18
.venv/bin/python -m lab_runner test --mode audit --postgres-version 16
.venv/bin/python -m lab_runner test --mode audit --postgres-version 18
.venv/bin/python -m lab_runner run --users 50 --runs-per-user 10 --concurrency 2
.venv/bin/python -m lab_runner run --users 100 --runs-per-user 10 --concurrency 32 --allow-overload
```

The audit commands currently exit **1** because of the nine stated findings.
Normal units/recovery/load remain green. Logs/JUnit exports retain safe failure
names, not raw driver or credential-bearing diagnostics.

Evidence in `.lab/` survives teardown:

- Final audit 16: `fc42c4b1a00f4df18a60dd852b7a1da0/result.json` and `junit.xml`.
- Final audit 18: `f51696c81ec64ed7a99414054efb9c4e/result.json` and `junit.xml`.
- Recovery 16/18: `2f5f6a4c1cfa4464a8201aca35ea908e` / `48137b51ff8e4c75a42dcf720636709c`.
- Load 16: `dd346a714fa64d4caead1dc41d4fa97e`.
- Baseline 500: `1b8c0818713b4885827ead0e3f77f72f`, request/accounting streams.
- Overload 1,000: `c2afc831df1f46968998c325fd58872c`, request/accounting streams.
- Demo 18: `18a0115c39e1449b87325318f959f92d/report/accounting.html` and JSON.
- Released Runtime adapter 16: `705a49c3762944bc8c071d7f236d74a4`, 24 tests.

The Prosaic verification script also produced `prosaic/parity-results/latest.json`.
Local library stdout receipts are under `/tmp/prosaic-audit-*`; preserve relevant
sanitized summaries in committed evidence before moving machines.

## Provenance and failed setup attempts

Prosaic checkout `ee145ef` and Harness `2bd14fd` match installed releases.
Runtime release `b13a62e` was tested from a frozen Git snapshot with 361 passes.
Runtime checkout `c17dca4` passed 456 tests after its subprocess environment was
aligned to that checkout. Native-provider and newer HTTP/accounting behavior
there must not be claimed for the installed Runtime wheel. No editable install
or library source patch changed the consumer baseline.

Initial Prosaic testing had 88 failures/303 skips before its required frozen
oracle was bootstrapped; then 24 CLI failures because the repository-local CLI
path was absent. The missing `.venv` path was temporarily linked to the existing
pinned lab environment, then the exact alias was removed after verification;
the final complete verification passed 432 plus 55 checks. Initial
Runtime testing had one subprocess CLI mismatch and 455 passes; aligned checkout
execution passed all 456. These were setup/provenance errors, not confirmed
library behavior defects. All initial receipts were preserved.

The first upstream adapter run had 22 passes and two setup failures because its
Harness fixture module was not on PYTHONPATH and the uninitialized-database
case requires CREATEDB. The rerun supplied the release-matching Harness test
fixture and granted CREATEDB to the migration role only inside a fresh owned
test database fixture; all 24 passed. Runtime service roles remained restricted.
The initial sanitized failure receipt is `be8c7d23339d4ac0aac6270e283ae4cb`.

One simultaneous demo setup failed while creating its owned network. It retained
an unresolved create intention, `cleanup=failed`, and no recorded resources:
`f1e9d53df5454572a0d6451c58e50c62`. Subsequent successful owner-filtered engine
inventories found no container/network/volume for that owner. A fresh demo
succeeded with verified cleanup. The original receipt remains failed; the
sanitized engine error did not retain enough detail to establish the create
failure's root cause. Improve safe phase/return-code diagnostics and concurrent
fixture-start qualification. Do not claim every attempted fixture cleaned up
successfully or weaken unknown-create safety to make that receipt green.

No end-to-end certification is claimed for a real model, tool effects,
streaming, database failover, x86, Podman, production ingress or a long soak.
