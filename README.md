# Prosaic integration lab

Reference application and repeatable acceptance tests for multiuser Prosaic
Harness workflows, shared PostgreSQL persistence and customer usage accounting.

## Current status

The first working consumer and synthetic acceptance lanes are implemented.
Two identical HTTP replicas use shared PostgreSQL, separate restricted roles,
owner-only views, durable idempotency and installed release wheels. Default
tests make no paid or local real-model calls. Verified on Docker Desktop
Linux/arm64 with PostgreSQL 16 and 18. CI, amd64 and non-sticky proxy routing
are not certified.

Start with the [approved design](docs/superpowers/specs/2026-10-09-prosaic-integration-lab-design.md),
[Codex handoff](docs/handoff.md) and [tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1).

## Planned scope

An optional [local Runtime configuration](configs/README.md) is available for
the host-side model endpoint at `http://127.0.0.1:8000/v1`. It requires the exact
model ID and a secret-file key; it is not enabled by default.

- Two identical Python service replicas and one shared PostgreSQL primary.
- Application-owned fixture authentication, run authorization and idempotency.
- Released Harness/Runtime packages and their optional PostgreSQL adapters.
- Synthetic inference and exact accounting assertions by default; no paid calls.
- Repeatable cross-worker, isolation, recovery and bounded-load acceptance tests.
- Explicitly opt-in TokenProxy tests after deterministic acceptance works.

This repository is a consumer of Prosaic, not another workflow engine. Fix
library defects in their owning repositories and retain regressions there.
Accounting means usage evidence and cost estimates, not customer invoicing.
The eventual fixture service is not a production authentication gateway.

## Continue on another machine

```sh
git clone https://github.com/B3Cognition/prosaic-integration-lab.git
cd prosaic-integration-lab
```

Open the checkout in Codex and use this prompt:

> Read AGENTS.md, docs/handoff.md, the approved design and the tracking issue.
> Continue the approved implementation plan from docs/verification/progress.md.
> Preserve the
> public SDK, authorization, accounting and exact-owned fixture boundaries.

Python 3.12, `uv`, and a running Docker daemon are needed for the verified path.
Podman is accepted by the runner but has not been verified here.

## Run the lab

From this checkout:

```sh
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python --require-hashes dependencies/requirements.lock
.venv/bin/python scripts/prepare_dependencies.py
uv pip install --python .venv/bin/python --no-deps .cache/wheels/prosaic-*.whl .cache/wheels/prosaic_runtime-*.whl .cache/wheels/prosaic_harness-*.whl
uv pip install --python .venv/bin/python --no-deps .cache/wheels/prosaic_runtime_postgres-*.whl .cache/wheels/prosaic_harness_postgres-*.whl
.venv/bin/python scripts/audit_install.py dependencies/releases.json .cache/wheels
docker build -f containers/Dockerfile -t prosaic-integration-lab:dev .
.venv/bin/python -m pytest -q
.venv/bin/python -m lab_runner test --mode deterministic --postgres-version 16
.venv/bin/python -m lab_runner test --mode recovery --postgres-version 16
.venv/bin/python -m lab_runner test --mode load --postgres-version 16
```

Repeat acceptance with `--postgres-version 18`. Each invocation allocates fresh
loopback ports and owned resources, exports sanitized JUnit/JSON into its
Git-ignored `.lab/<ownership-id>/` directory, then validates cleanup. Missing
infrastructure, unexpected skips and failed cleanup fail the command.
Generated fixture credentials are lab-only and removed after successful cleanup.

Released distributions contain immutable Git dependency references. We install
their original verified wheels without dependency resolution after installing
the hash-locked third-party graph. The payload audit verifies all five installed
release wheels, avoiding upstream VCS resolution without changing METADATA.
No sibling checkout or private library API is used.

## See the accounting evidence

```sh
.venv/bin/python -m lab_runner demo --postgres-version 16 --open-report
```

This runs a fresh owned synthetic stack and creates actual measured runs for
Alice, Bob and Carol. It also shows two rejected-output attempts and a request
with missing final usage. The command prints owner-scoped usage, saves a readable
`accounting.html` and a filtered `accounting.json` under `.lab/<id>/report/`,
verifies cleanup, then opens the saved report in your default browser.
Omit `--open-report` for terminal-only use. The report persists after teardown.

The demo checks independent endpoint counters against the Runtime ledger.
It shows per-call input/cached/output tokens, exact decimal estimates and
unknown coverage. All prices are fixed synthetic fixtures; every assessment
is billing-ineligible. This is accounting evidence, not a customer invoice.

Earlier failed `.lab/` receipts remain as historic test-first/regression evidence.
A current test command exits nonzero on any failing assertion, skip, required
infrastructure failure or cleanup failure; old failing receipts do not mean
the current suite is red.

## Multiuser terminal workload

Run from this repository with Docker running and the consumer image built:

```sh
.venv/bin/python -m lab_runner run --users 10 --runs-per-user 20 --concurrency 2
```

The first line prints an exact command to paste into another terminal:

```sh
.venv/bin/python -m lab_runner watch --directory .lab/<printed-owner-id> --stream accounting
```

The workload terminal streams fixture actor, operation, replica, HTTP status,
run IDs and request latency. Each user has a distinct trusted identity, starts
on alternating replicas, approves on the other replica, checks measured usage,
and verifies another user cannot read its run or accounting. `--concurrency`
limits active user sessions; each session sends its runs sequentially. Sessions
beyond that limit wait in the driver. This is a closed-loop workload, not a
fixed requests-per-second benchmark.

The accounting terminal follows per-run complete/unknown call counts and exact
synthetic USD estimates, then the global usage summary. It replays existing
events when attached late and exits after cleanup. `--stream requests` replays
the request stream instead. JSONL evidence and `result.json` survive teardown;
neither stream contains bearer tokens, DSNs or workflow contents.

For an initial overload experiment:

```sh
.venv/bin/python -m lab_runner run --users 20 --runs-per-user 20 --concurrency 20 --allow-overload
```

Each replica admits at most two executions. Capacity-exhausted 503 responses
are counted separately and never blindly retried. Without `--allow-overload`,
any capacity rejection fails the run. With it, correctness/accounting/cleanup
failures still exit nonzero; inspect completed versus capacity-rejected counts.
`start_capacity_rejected` means no dispatch occurred; `approval_deferred` means
the model call was measured but cross-replica approval was rejected for capacity.
Deferred workflows stay waiting, with no automatic retry. Independent fixture
dispatches must reconcile with complete ledger calls for completed and deferred
workflows together.
Limits are 1–1000 users, 1–1000 runs/user, at most 10,000 total runs and 1–64
concurrent sessions. This provides a load/stress foundation; arrival-rate
control, soak duration and performance thresholds remain future work.

These commands use the credential-free synthetic endpoint, without local or
cloud model calls. Estimates are test rate-card values, not billable invoices.

## Production blueprint audit

Read the [production readiness report](docs/verification/production-readiness-2026-10-09.md)
before copying this lab into a production service. The report separates confirmed
defects, adoption requirements and features that can remain disabled.

```sh
.venv/bin/python -m lab_runner test --mode audit --postgres-version 16
.venv/bin/python -m lab_runner test --mode audit --postgres-version 18
```

This lane includes existing recovery/load cases plus adversarial HTTP inputs,
schema/privilege corruption, accounting conflicts/quarantine, token budgets,
private-response/log sentinels and production deployment checks. It currently
exits **1**: 49 test cases pass and 9 fail on each database major, with zero skips
and verified cleanup. Those are visible production gates; they are not expected
failures or changes to the existing green deterministic/recovery/load contracts.

## Optional local model smoke

The sequential production fix ledger is
[production-fixes.md](docs/verification/production-fixes.md). Accounting adapter
and Harness adapters 0.1.1 are unpublished, checksummed candidates; the original release
manifest remains unchanged. To test that explicit candidate after building its
wheel into `.cache/candidates/`:

```sh
docker build -f containers/Candidate.Dockerfile \
  --build-arg CANDIDATE_MANIFEST_SHA256=6dd1eb2e1196a6741ad805255dbbdb7768185206a07e8dd33f2ebceb6b5745b0 \
  -t prosaic-integration-lab:candidate .
.venv/bin/python -m lab_runner test --candidate --mode audit --postgres-version 16
```

Candidate receipts explicitly record dependency mode, wheel-manifest checksum
and immutable image ID. A mismatched image fails before fixture allocation.

Configurable OIDC authentication, including the owned Keycloak TLS test lane, is
documented in [identity.md](docs/identity.md). Run `--mode identity` with either
PostgreSQL major to verify real issuer signatures, revocation and key rotation.

Persistent deployment, explicit versioned migrations and the owned backup/restore
lane (`--mode persistence`) are documented in [persistence.md](docs/persistence.md).
Publishing the upstream wheel and updating released-package provenance are
separate steps after review.

```sh
.venv/bin/python scripts/local_smoke.py
```

This explicitly invokes the local 7B Qwen Coder model at `127.0.0.1:8000/v1`
with one neutral smoke request, reading `~/.omlx_token` directly. It has no cloud
fallback. The first verified local invocation succeeded and reported 85 tokens;
this is a smoke result, not a model-quality or provider-cost certification.

## Remaining acceptance work

The full approved design remains the target. Tool-loop measurement, quarantined
evidence, token-budget recovery, changed-default/scope recovery, the non-sticky
proxy, CI and the architecture matrix still need their own executable evidence.
Paid TokenProxy mode remains unimplemented and disabled. See the
[implementation ledger](docs/verification/progress.md) for precise coverage.

## License

Apache-2.0. See [LICENSE](LICENSE).
