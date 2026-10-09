# Prosaic integration lab implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if the maintainer explicitly selects delegation. Track steps with the checkboxes below.

**Goal:** Build repeatable acceptance tests of installed Prosaic, Runtime and Harness releases across two HTTP replicas, with durable state, owner isolation and measured synthetic usage, without paid model calls.

**Architecture:** One Python 3.12 consumer image runs twice against a disposable PostgreSQL primary. Application metadata controls authorization and HTTP idempotency; public Harness and Runtime adapters own workflow and accounting persistence. A local OpenAI-compatible fixture supplies deterministic responses and independently counted dispatches.

**Tech stack:** Python 3.12, FastAPI, Uvicorn, psycopg binary/libpq 17+, pytest, HTTPX, Docker or Podman, PostgreSQL 16/18.

**Spec:** [Approved design](../specs/2026-10-09-prosaic-integration-lab-design.md).

**Status:** Written for maintainer review; implementation has not started. Recommend native execution to avoid fresh agent contexts for this closely coupled first slice. No agents are authorized by this recommendation.

## Global constraints

- Use released packages with checksums and locked dependencies; no sibling editable installs or mutable branches.
- Harness 0.6.0, Runtime 0.6.0, Harness PostgreSQL 0.1.0, Runtime PostgreSQL 0.1.0 are the initial baseline.
- Python 3.12 application image; two instances of that exact image, one application process each.
- Shared PostgreSQL primary; exercise majors 16 and 18, Linux/arm64 and Linux/amd64 separately.
- Public installed APIs only. No copied engines, private imports or monkey-patching.
- Derive tenant, actor, billing account and namespace from trusted host context; owner-only public views.
- Separate migration and runtime credentials; replicas never run DDL.
- Initially admit at most two execution operations per replica, with no unbounded queue.
- All published ports bind to loopback; fixture authentication is lab-only.
- Synthetic inference is the default. No paid calls, real endpoint credentials or live-user prompts in the first six stages.
- Required acceptance lanes fail on missing infrastructure, skips, timeouts and failed cleanup.
- Preserve unrelated changes and historic evidence. Do not push, release or modify sibling repositories under this plan.

## Review focus

1. Crash between ownership reservation and Harness creation: duplicates must never redispatch uncertain work. Task 3 tests every boundary.
2. Owner strings, JSON bodies and headers containing identity overrides: reject rather than merge into trusted attribution. Task 3 tests nested and top-level attempts.
3. Lost database commit acknowledgement: preserve uncertainty and reconcile durable evidence without another provider dispatch. Task 5 checks independent endpoint counters.
4. Changed assets/defaults on another replica: reject asset/scope mismatch before dispatch while preserving frozen attribution. Tasks 4 and 5 exercise both cases.
5. Cleanup failures or replaced container identities: fail the suite and leave foreign resources untouched. Task 2 tests identity mismatch and partial startup.

## Delivery sequence and review boundaries

Implement Task 1 then Task 2 as the first milestone. Record their actual evidence before continuing into HTTP execution. Each later task is a separate reviewable milestone; do not call the entire lab complete until all required synthetic lanes are verified. Task 7 remains disabled unless the maintainer separately authorizes live provider use.

No cheap cloud model is needed for deterministic integration. Synthetic HTTP responses exercise real Runtime request handling, Harness progression, PostgreSQL storage and accounting. They do not prove model quality or a real provider's usage semantics. A local real model could later be an additional semantic smoke test, but is not an acceptance dependency.

## File responsibilities

| Files | Responsibility |
| --- | --- |
| `pyproject.toml`, `dependencies/releases.json`, `dependencies/requirements.lock`, `scripts/verify_dependencies.py` | Installable consumer, immutable provenance, full transitive hashes |
| `containers/Dockerfile`, `containers/provision.py`, `containers/grants.sql` | Identical image, explicit owned-database setup, restricted grants |
| `lab_runner/__main__.py`, `lab_runner/stack.py`, `lab_runner/manifest.py`, `lab_runner/results.py` | CLI, exact-owned lifecycle, sanitized results |
| `src/prosaic_integration_lab/config.py`, `identity.py`, `metadata.py`, `views.py`, `app.py`, `execution.py` | Configuration, trusted principals, reservations, public projection, HTTP, bounded SDK calls |
| `assets/approval.yml`, `assets/synthetic.yml`, `assets/runtime.yml`, `assets/subagents/author.md`, `assets/schemas/result.json` | Immutable neutral test assets |
| `tests/fixtures/model.py`, `tests/fixtures/gates.py` | Synthetic protocol endpoint, dispatch counts and observable barriers |
| `tests/unit/`, `tests/acceptance/` | Local policy tests and real installed-package/stack assertions |
| `.github/workflows/acceptance.yml`, `containers/proxy.conf` | Required synthetic matrix and non-sticky routing |
| `README.md`, `docs/handoff.md`, `docs/verification/` | Verified commands, continuation checkpoint, sanitized receipts |

## Task 1: Released-package consumer and provenance

**Create:** dependency files, verifier, `pyproject.toml`, package initializer, Dockerfile, `tests/unit/test_dependencies.py`, `tests/acceptance/test_image.py`.

**Interfaces:** `verify_dependencies(manifest_path: Path, artifact_dir: Path) -> None` rejects any missing/mismatched artifact. `python -m prosaic_integration_lab --version` emits only distribution versions. Image build takes verified artifacts and the complete locked dependency graph.

- [ ] Write dependency tests for modified bytes, missing wheels, editable/direct mutable dependencies and expected installed version identities. Observe failures before implementing the verifier.
- [ ] Download core/adapter release wheels and both `SHA256SUMS-0.6.0.txt` files into a Git-ignored artifact cache. Compute SHA256 locally and compare to the release checksum files; GitHub metadata alone is not download verification.
- [ ] Record release URLs, source commits, filenames, byte hashes and transitive Prosaic identity in `dependencies/releases.json`.
- [ ] Resolve a complete hash-locked Python 3.12 dependency graph. Inspect wheel METADATA: Harness requires Runtime commit `b13a62eac955b19b13fe2c9dc646a188069f72f2`; Runtime requires Prosaic commit `ee145ef29a62dbcf7f5e8abdf1d979749398718d`. Preserve these requirements. For VCS edges, prepare wheels from those immutable commits and record their provenance/build dependencies and hashes; never silently substitute a similarly numbered package. Record any resolver incompatibility as a blocker before changing dependencies.
- [ ] Install each core before its adapter, using verified wheel artifacts with dependency resolution controlled by the full lock. Audit the resulting installed graph, including VCS requirements, rather than claiming an ordinary `pip check` alone proves source identity.
- [ ] Build from a pinned Python 3.12 image digest without sibling mounts. Run an import probe inside the image:

```python
from importlib.metadata import version
from prosaic_harness import Harness, Workflow
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime import ExecutionContext, RateCard
from prosaic_runtime_postgres import PostgresRecorder
assert version('prosaic-harness') == '0.6.0'
assert version('prosaic-runtime') == '0.6.0'
assert version('prosaic-harness-postgres') == '0.1.0'
assert version('prosaic-runtime-postgres') == '0.1.0'
```

- [ ] Run `.venv/bin/python -m pytest tests/unit/test_dependencies.py -q` and the image acceptance test. Record Python, libpq, package versions, architecture, image digest and commands. Commit this milestone; do not report database or workflow acceptance yet.

## Task 2: Exact-owned stack and explicit provisioning

**Create:** runner CLI/lifecycle/manifest/results files, provisioner/grants, `tests/unit/test_stack.py`, `tests/acceptance/test_provisioning.py`.

**Interfaces:** `OwnedStack.start(engine: str, postgres_major: int) -> StackManifest`, `OwnedStack.stop(manifest: StackManifest) -> None`. Manifest contains an ownership UUID, exact engine resource IDs, image IDs, loopback endpoints and nonsecret fixture paths; never DSNs/tokens. `python -m lab_runner test --mode provisioning --engine docker --postgres-version 16` becomes the first stack acceptance command.

- [ ] Test cleanup identity rejection, partial startup cleanup, required engine absence, wrong PostgreSQL major and failed teardown. Use a fake engine command boundary for unit tests; no global engine mutations.
- [ ] Allocate a new labeled network/container/volume set and fresh database per invocation. Write the ownership manifest atomically. Generate secret files outside Git with restrictive permissions, and use engine-assigned loopback ports. Inspect exact resource IDs and labels before every stop/restart/remove.
- [ ] Provision separate migration and restricted runtime roles in the owned database. Initialize Harness through its explicit migration CLI and Runtime recorder through its public `initialize()` using migration credentials. Initialize application metadata separately. Replicas receive only runtime secrets.
- [ ] Apply Harness's documented table-specific grants; Runtime gets SELECT/INSERT on accounting tables plus UPDATE on intent rows, never DELETE/schema mutation. Determine the released adapter's actual table names from its public operator contract/installed schema before applying exact SQL. Validate effective privileges using runtime credentials and an intentional denied DDL attempt.
- [ ] Execute Harness doctor and both adapters' readiness gates. Test missing schema and incompatible version fail without repairs; verify logged storage, writable primary, durable WAL settings and libpq floor.
- [ ] Run provisioning acceptance on PostgreSQL 16, then 18 where available. Capture sanitized results before teardown; mark cleanup failure as failure even if assertions passed. Verify only exact owned resources disappeared, repeat with a fresh ownership ID, and commit evidence.

## Task 3: Authorized HTTP service and zero-call cross-replica approval

**Create:** service modules, approval asset, `tests/unit/test_identity.py`, `test_views.py`, `tests/acceptance/test_approval.py`, `test_idempotency.py`, `test_authorization.py`.

**Interfaces:** immutable `Principal(tenant_id, actor_id, billing_account_id)` loaded from fixture secret mapping; `reserve(principal, key, canonical_request) -> Reservation`; `public_run(snapshot, reservation) -> dict`; `execute_start(reservation)` and `execute_resume(reservation, expected_revision, decision)` use installed public SDKs. App schemas disallow client identity/model/workflow/config overrides.

Reservation protocol for review:

1. Unique `(tenant_id, actor_id, idempotency_key)` owns a UUID run, canonical request hash, immutable attribution and asset fingerprint. Reserve/commit before SDK execution.
2. Only the request that successfully transitions `reserved -> starting` by conditional update may call `Harness.run`. A duplicate request never calls `run`, even if state is absent. Changed canonical payload returns 409.
3. Commit `starting` before calling Harness. A crash after this commit is conservatively uncertain, including a crash before actual dispatch. Do not use reservation age as retry permission.
4. When a durable Harness snapshot exists, reconcile only the reservation's exact UUID and expected assets/context, expose its filtered state and require its current revision for resume. Never restart it with `run`.
5. If `starting` has no snapshot, expose sanitized `start_uncertain` and block redispatch. This initial service has no automatic orphan-retry endpoint. A safe but unused reservation can remain blocked; operator reconciliation is preferable to a duplicate side effect.
6. For post-execution metadata acknowledgement loss, recover by reading the existing run. Metadata failure cannot authorize execution replay.

- [ ] Write tests for Alice/Bob/Carol, missing/invalid credentials, body/header spoofing, secret/private-state projection, duplicate keys and changed payload. Assert denial before SDK access and HTTP model dispatch.
- [ ] Create application tables with migration credentials: immutable ownership/context/request fields, unique key, bounded request bytes, reservation phase and expected asset fingerprint. Use canonical finite JSON; reject nonfinite values and excess nesting/body size before reservation. Test canonical key ordering, distinct owners and parallel reservation transactions.
- [ ] Implement the six approved HTTP endpoints. Use uniform 404 for nonowners; 401 unauthenticated, 409 stale revision/busy/conflict, 503 capacity/readiness failure. Map known errors to sanitized codes; never serialize arbitrary exceptions/operator snapshots.
- [ ] Admit at most two executions per replica using nonblocking capacity acquisition before submitting synchronous SDK work to a bounded executor. Release capacity when execution truly finishes, including after client disconnect; drain before stores close. Construct long-lived store/recorder resources after startup, and one Harness per execution.
- [ ] Load the identical approval workflow at `/srv/lab/assets` in both replicas. Use `Workflow.load`, `PostgresRunStore.from_env`, `Harness.run`, `Harness.status` and `Harness.resume(..., expected_revision=...)`; derive namespace from deployment config.
- [ ] Prove A-start/B-inspect/B-resume, approve/reject paths, stale and simultaneous resume, same-key A/B race, restart durability and all reservation crash boundaries. Assert zero model calls. Missing infrastructure fails; no skips.
- [ ] Update deterministic command and status only after acceptance passes, then commit sanitized receipts.

## Task 4: Synthetic Runtime and exact accounting acceptance

**Create:** synthetic workflow/prose/schema/runtime assets, model fixture/gates, `tests/acceptance/test_accounting.py`, `test_isolation.py`, `test_assets.py`.

**Interfaces:** fixture supports the released Runtime's OpenAI-compatible request protocol and exposes a private fixture-control counter API. Scenarios select fixed response IDs/model/token quantities; public requests cannot select endpoint/scenario. `GET /runs/{id}/usage` uses recorder filters fixed from authorized reservation attribution/run ID.

- [ ] Write fixture protocol/count tests and acceptance tests that fail until Runtime execution and recorder wiring exist. Check endpoint counters separately from ledger rows.
- [ ] Implement a local credential-free endpoint with deterministic JSON and, where Runtime uses it, streaming usage responses. Observable gates signal receipt/request boundaries; the test runner waits on explicit events with deadlines, never guessed sleeps.
- [ ] Configure public `PostgresRecorder` and trusted `ExecutionContext`; freeze application, tenant, billing account, actor, request and run attribution at reservation. Supply context separately from model arguments. Keep configuration immutable at the same absolute paths in both replicas.
- [ ] Use `RateCard('synthetic-v1', 'test-model', '2', '8', '0.5')`. For a fixed response with 100 input, 20 cached input and 25 output tokens, assert Decimal USD `0.000370000000000000` after confirming fixture usage semantics. Assert all assessments are billing-ineligible.
- [ ] Exercise Alice/Bob/Carol concurrently, tool-loop and validation-retry calls, rejected output usage, identical replay, missing usage, unknown model and quarantined evidence. Query owner/run-scoped totals and coverage; unknown never becomes final zero cost.
- [ ] Change assets/config on B and verify refusal before dispatch. Scan public responses and captured logs against generated secret/private sentinel values. Run deterministic acceptance and commit evidence.

## Task 5: Recovery and overload at real persistence boundaries

**Create:** `tests/acceptance/test_recovery.py`, `test_accounting_failures.py`, `test_load.py`; extend fixture gates/runner recovery and load modes.

**Interfaces:** `python -m lab_runner test --mode recovery` and `--mode load` own synthetic fixtures with bounded deadlines. Fault injection acts through fixture processes/network/database privileges and public contracts; no patched engines or private imports.

- [ ] Write failing scenarios for worker loss after persisted receipt, missing receipt, lost acknowledgement and accounting prepare/observe failures. Identify publicly observable gates before implementing each crash test; if no public seam permits a deterministic boundary, record a blocked scenario rather than claim sleep-based coverage.
- [ ] Crash only exact owned worker IDs. Preserve its database volume within restart scenarios. On B, adopt durable receipt without redispatch; require explicit interrupted retry consent plus reviewed revision for missing receipt. Token budget must retain abandoned/unknown calls.
- [ ] Deny accounting intent writes before dispatch and assert counter unchanged. Deny observation writes after dispatch and assert no second request. Restore permissions only with owned migration credentials; keep unresolved evidence visible.
- [ ] Resume after trusted defaults change and assert original attribution. Explicit context or recorder-scope conflict must fail safely. Verify independent counters, immutable evidence and no duplicate estimates for every case.
- [ ] Gate two admitted executions on each replica, issue excess work and assert bounded 503 responses without queue growth. Release gates, verify capacity/resource recovery and isolation of unrelated users. Use absolute test deadlines and bounded request counts.
- [ ] Repeat complete synthetic runs with distinct ownership IDs. Verify cleanup and sanitized diagnostics on success/failure. Commit recovery/load evidence and limits.

## Task 6: Non-sticky routing and required CI matrix

**Create:** proxy config, acceptance workflow, `tests/acceptance/test_routing.py`.

- [ ] Assert alternating requests can start/read/resume through a non-sticky proxy while recording replica identity in fixture-only diagnostics.
- [ ] Implement proxy with a loopback published port and no session affinity. Keep service authorization authoritative on each replica.
- [ ] Run deterministic/recovery/load acceptance for PostgreSQL 16 and 18 on Linux/amd64 and Linux/arm64. Use native runners where available; report emulation separately and do not infer an untested matrix cell passed.
- [ ] Make missing engines, unexpected skips, readiness/timeout/cleanup failures fail CI. Publish sanitized JUnit/JSON, dependency manifest, image digest, architecture, PostgreSQL/libpq versions, seed and ownership ID.
- [ ] Map the design's scenarios 1–16 to exact test IDs in the verification receipt. Reconcile README/handoff/issue checklist only with observed evidence; do not inherit upstream counts. Commit this milestone.

## Task 7: Separately authorized live provider lane

**Files:** `lab_runner/live.py`, `tests/acceptance/test_live_policy.py`, `docs/decisions/live-provider.md`.

- [ ] Keep live mode disabled throughout Tasks 1–6. Do not install a real-model service or search for paid credits as part of deterministic acceptance.
- [ ] After explicit maintainer authorization, add `--mode live --allow-paid-calls --max-calls 10`; missing either allowance flag or secret-managed credentials fails before network dispatch. Default CI never selects this mode.
- [ ] Persist a shared allowance across both replicas. Atomically reserve one allowance slot before every actual provider dispatch, including tool-loop/validation retries; crashes never refund uncertain calls. If public Runtime hooks cannot enforce this boundary, require an owned counting proxy or stop to review the approach, rather than enforce only at workflow level.
- [ ] Test allowance enforcement against the synthetic fixture first: parallel exhaustion, retry/tool-loop calls, process restart and rejected credentials cannot bypass it.
- [ ] Verify the selected TokenProxy endpoint's reported model/usage semantics and rates with separately approved bounded calls. Document that a call allowance is not a money cap and no model-quality/provider certification follows from synthetic tests.

## Verification and continuation

Before each code task, write and observe its failing regressions. After implementation, run focused tests and that milestone's real acceptance lane, then commit only scoped files and sanitized receipts. Unit tests alone cannot certify PostgreSQL, cross-replica execution or provider usage.

Target commands become documented only after implementation and fresh verification:

```sh
.venv/bin/python -m pytest tests/unit -q
.venv/bin/python -m lab_runner test --mode provisioning --engine docker --postgres-version 16
.venv/bin/python -m lab_runner test --mode deterministic --engine docker --postgres-version 16
.venv/bin/python -m lab_runner test --mode recovery --engine docker --postgres-version 16
.venv/bin/python -m lab_runner test --mode load --engine docker --postgres-version 16
```

Plan review must confirm the reservation algorithm, immutable dependency strategy, first milestone boundary and execution method. The approved design remains unchanged. Implementation begins after that review, as required by repository instructions.
