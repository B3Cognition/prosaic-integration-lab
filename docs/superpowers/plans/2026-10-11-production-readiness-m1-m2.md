# Production readiness milestones 1 and 2 implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development or
> superpowers:executing-plans to implement these tasks with independent review.

**Goal:** Add meaningful native fault, restore, tier routing and normal public-index
consumer coverage for the published SDK train.

**Architecture:** Extend existing owned Lab fixtures and qualification modes.
Keep SDK execution behind public APIs, policy and trusted host bindings. Distinct
fixtures provide independent dispatch/effect counts; sanitized receipts prove
actual execution and exact-owned cleanup.

**Tech stack:** Python 3.12, installed released Prosaic SDKs, pytest, HTTPX,
FastAPI/Uvicorn, asyncio TCP relay, owned Docker PostgreSQL 16/18.

**Spec:** ../specs/2026-10-11-production-readiness-m1-m2-design.md

## Global constraints

- No SDK features, automatic recovery, paid cloud calls or private engine patches.
- Retain five-package release manifest and hash-locked third-party dependencies.
- Local Qwen uses explicit opt-in, loopback only, at most three shared requests.
- Fault/restoration resources require exact ownership, bounded waits and cleanup.
- Unknown usage remains unknown; a saved receipt never authorizes redispatch.
- Preserve historical evidence and unrelated changes.

## Review focus

- A returning old lease owner cannot advance after B's generation takes over.
- Slow/truncated provider responses terminate without duplicating incurred effects.
- Restored native references and uncertain journal rows cannot fall back or retry.
- Tier grants and routes both apply; omission follows the private default.
- Public installation must resolve dependencies and cannot import sibling sources.

## Task 1: Native transport and database faults

Files: `lab_runner/model.py`, new `lab_runner/fault_proxy.py`, new
`lab_runner/native_faults.py`, new `tests/acceptance/test_native_faults.py`,
new unit/functional tests for the model/proxy fixtures.

Interfaces: Existing model `/control`, `/stats`, `/events/accepted`; owned
`OwnedStack._create` and durable manifest; public SQL lease generation and receipt
contracts; existing native proposal helpers. Produce fixture helpers/tests only;
the controller owns CLI lane inclusion and count contracts.

- [ ] Write tests for the new controlled fixture behavior and observe failures.
- [ ] Implement bounded accepted-response faults and a finite owned TCP relay.
- [ ] Assert first/post-tool failures preserve usage uncertainty and effect counts.
- [ ] Assert live A SQL partition, observed expiry/B takeover and late A fencing.
- [ ] Run scoped and full source suites; report acceptance tests for real image runs.
- [ ] Independently review actual diff, correcting substantive findings.

Example invariant:

```python
assert provider_calls_after == provider_calls_before + expected_acceptances
assert journal_state in {'completed', 'uncertain'}
assert len(domain_rows) == expected_effects
assert late_worker_revision == recovered_revision
```

## Task 2: Populated native logical restore

Files: new `lab_runner/native_restore.py`, `lab_runner/recovery_qualification.py`,
`tests/unit/test_recovery_qualification.py`,
`tests/acceptance/test_operational_qualification.py`.

Interfaces: `seed(stack, config, client)` returns private bounded fixture evidence;
`verify(config, fixture, client)` returns fixed verification booleans/counts.
Use `stack.native_fixture` to select eight-call/six-record native seeding, and a
fresh `stack.start_replica` for restored reads. Controller integrates final counts.

- [ ] Add failing strict-evidence and allowance preflight tests.
- [ ] Seed actual paused, receipt, completed and uncertain states through HTTP.
- [ ] Capture original contracts and compare them after consistent dump/restore.
- [ ] Require all native booleans and unchanged provider/handler counters.
- [ ] Parameterize real restore acceptance over legacy/native modes; run full suite.
- [ ] Independently review evidence completeness and restoration/cleanup finally.

Example required evidence:

```python
assert receipt['native_verified'] is True
assert receipt['logical_restore_only'] is True
assert receipt['redispatch_detected'] is False
assert receipt['native_runs'] == 4
```

## Task 3: Tier routing and ordinary PyPI adoption

Files: new `tests/functional/test_model_tier_routing.py`, new
`scripts/local_routing_smoke.py`, `configs/runtime-local.example.yml`,
`configs/README.md`, new `scripts/verify_public_adoption.py`, new tests for both
scripts. Do not modify model/native execution fixtures owned by other tasks.

Interfaces: Existing public factory/bindings/policy and model-tier request fields;
existing manifest/dependency and installed-payload audit helpers. Local script
requires `--live-local --max-calls 3`; adoption accepts `--manifest` and `--export`.

- [ ] Add watched failing script preflight and routing tests.
- [ ] Prove distinct strong/balanced/default dispatch and rejected privileges.
- [ ] Implement three-call bounded local public factory/Harness routing smoke.
- [ ] Implement neutral temporary-venv ordinary PyPI resolver and byte/payload audit.
- [ ] Run scoped/full suites; report commands for authorized live/index verification.
- [ ] Independently review isolation, secret filtering and finite allowances.

Ordinary resolver must contain no `--no-deps` during installation:

```text
python -I -m pip --isolated install --no-cache-dir --index-url https://pypi.org/simple
  --only-binary=:all: --report PRIVATE_REPORT FIVE_EXACT_PINS
```

## Task 4: Integrate, qualify and document

Files: `lab_runner/__main__.py`, `lab_runner/gates.py`, required acceptance workflow,
count-contract tests, `docs/release-gates.md`, `docs/qualification.md`, README and
a new verification ledger.

- [ ] Include new native fault file and collect exact native/qualification counts.
- [ ] Update fixed failure identifiers/count contract tests and safe exports.
- [ ] Add released-only normal public adoption CI step and its safe receipt.
- [ ] Run full suite, immutable image build, affected native/qualification PG16/18.
- [ ] Run actual PyPI adoption and opted-in local Qwen routing within limits.
- [ ] Record actual evidence, review whole branch, fix findings and commit changes.

Release claims require matching source/package/image/profile evidence, no skips,
actual model/effect reconciliation and verified cleanup. Four-cell platform CI
remains the required release boundary; local ARM64 does not prove AMD64.
