# Prosaic integration lab

Reference application and repeatable acceptance tests for multiuser Prosaic
Harness workflows, shared PostgreSQL persistence and customer usage accounting.

## Current status

Read [the current delivery status](docs/current-status.md) for the implemented
ecosystem milestones, qualified SDK candidates and remaining publication gates.

Version **0.2.0** combines the hardened multiuser blueprint and Lago metering.
Two identical HTTP replicas use shared PostgreSQL, separate restricted roles,
owner-only views, durable idempotency and installed release wheels. Default
tests make no paid or local real-model calls. Configurable Keycloak/OIDC and
Auth0, verified TLS ingress, bounded load, recovery and protected metrics are
implemented. Read the [release ledger](docs/verification/release-train-2026-10-09.md)
for the actual native matrix and published dependency evidence. Deployment
identity/TLS/HA/capacity qualification and customer invoicing remain separate.

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

Use the Git checkout or complete release source archive for runner scripts,
fixtures and configuration. The wheel contains the Python application/runner
modules; the terminal stack runner also requires those repository assets.

```sh
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python --require-hashes dependencies/requirements.lock
.venv/bin/python scripts/prepare_dependencies.py
.venv/bin/python -m ensurepip
.venv/bin/python scripts/install_dependencies.py --manifest dependencies/releases.json
.venv/bin/python scripts/audit_install.py --manifest dependencies/releases.json
.venv/bin/python scripts/build_consumer.py --manifest dependencies/releases.json --dependency-mode released --tag prosaic-integration-lab:dev
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

Wheel caches are isolated by the SHA256 of the exact selected manifest bytes:
`.cache/wheels/<manifest-sha256>/`. The installer passes only the five verified
manifest filenames to pip and rejects legacy/renamed SDK mixtures. Historical
Lab 0.2.0 pins remain byte-identical in `dependencies/releases-lab-0.2.0.json`.
The active pins are still the historical release family. Future `b3-prosaic*`
distribution names retain the same Python imports; migration requires a fresh
environment. PyPI's unrelated `prosaic` is never a migration shortcut.

Use `--manifest path/to/candidate.json --dependency-mode candidate` with the
build helper for explicit candidates. Supply the complete five-wheel candidate
family through `--wheel-dir` or its manifest digest cache; unpublished artifacts
must be supplied explicitly. Candidate images start from the same pinned Python
base as released images. The build snapshots exact manifest bytes and selected
wheels in a temporary public context, aborts on concurrent manifest changes,
and prints the immutable image ID. The packaged explicit inventory at
`dependencies/public-build-inputs.json` selects public files in both Git
checkouts and complete source archives; adding a runtime file requires updating
that inventory. Extra local files never enter the context. The audit validates
any executable SDK cache against the verified source code, including hash-based
and optimized caches, without deleting existing installed files.
Installed-payload audit supports the historic
positional arguments as well as `--manifest` and `--wheel-dir`.

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
private-response/log sentinels and production deployment checks. The original
49-pass/9-fail report is preserved. Its fourteen blocker groups have local fixes
and regression coverage; see the [follow-up](docs/verification/production-follow-up-2026-10-09.md)
and current released-package verification in the release ledger.

## Optional local model smoke

The sequential production fix ledger is
[production-fixes.md](docs/verification/production-fixes.md). The release train
publishes recorder/store adapters 0.1.1 and deliberately updates
`dependencies/releases.json` to their exact released artifacts. Default commands
use those releases. Earlier candidate manifests and receipts remain historical
evidence; they are not a fallback for a failed release gate. A mismatched image
fails before fixture allocation.

Configurable OIDC authentication, including the owned Keycloak TLS test lane, is
documented in [identity.md](docs/identity.md). Run `--mode identity` with either
PostgreSQL major to verify real issuer signatures, revocation and key rotation.

Persistent deployment, explicit versioned migrations and the owned backup/restore
lane (`--mode persistence`) are documented in [persistence.md](docs/persistence.md).

Owner terminal recovery (`recover`), crash/receipt handling and atomic credential
delivery are documented in [recovery.md](docs/recovery.md); `--mode operations`
executes the owned recovery lane.

HTTP workflows require finite call, recorded-token and duration limits before
startup creates database resources. The synthetic workflow allows three calls,
300 recorded tokens and 120 seconds; approval performs no model execution.
Consumed or unknown usage blocks further dispatch, including explicit retry
consent across replicas. Run `--mode budget` to exercise the owned worker-loss
and exhausted-budget regressions. Recorded-token limits are checked by Harness
against durable receipts; they do not guarantee a provider invoice ceiling.

Verified TLS ingress, Keycloak authentication, non-sticky routing and in-flight
drain/restart tests run with `--mode ingress`; deployment assumptions and commands
are in [ingress.md](docs/ingress.md).
Pinned dependency and native release verification are recorded in the release ledger.

```sh
.venv/bin/python scripts/local_smoke.py
```

This explicitly invokes the local 7B Qwen Coder model at `127.0.0.1:8000/v1`
with one neutral smoke request, reading `~/.omlx_token` directly. It has no cloud
fallback. The first verified local invocation succeeded and reported 85 tokens;
this is a smoke result, not a model-quality or provider-cost certification.

## Remaining acceptance work

Longer deployment-specific soak, real provider/tool/streaming qualification,
HA/PITR, managed identity/TLS/monitoring and customer invoice/payment closure
remain separate. Paid TokenProxy mode is unimplemented and disabled. See the
[production follow-up](docs/verification/production-follow-up-2026-10-09.md) and
[capacity runbook](docs/capacity-retention.md) for the measured pilot limits.

## Local Lago billing robustness

The optional Lago lane checks fixture charges against public Runtime usage
evidence. It provisions a digest-pinned Lago 1.55.0 local stack, freezes trusted
account/subscription mappings and the current billing period before inference,
and delivers exclusive input, cached-input and output quantities through an
application-owned PostgreSQL outbox. Replicas receive no Lago key; the exporter
uses a separate restricted database role. Existing default lanes need no Lago.

```sh
.venv/bin/python scripts/build_consumer.py --manifest dependencies/releases.json --dependency-mode released --tag prosaic-integration-lab:dev
.venv/bin/python -m lab_runner test --mode lago --postgres-version 16
.venv/bin/python -m lab_runner test --mode lago --postgres-version 18
```

The lane exercises actual Harness calls, rejected outputs, cross-replica approval,
Lago outages, duplicate replay, concurrent scans, expired/stale leases and killed
exporter processes before send and after remote acceptance. Direct public-ledger
fixtures separately exercise more than 1000 calls in one run, delayed evidence,
unknown cache details, quarantine, reasoning overlap, equal account names in
different tenants, fractional-cent charge rounding and out-of-period rejection.
These direct fixtures are not extra inference calls.

Immutable transaction IDs and timestamps survive retries. Unknown token detail
stays excluded; a payload/mapping conflict blocks the source. Delivery is at
least once with verified Lago deduplication. HTTP acknowledgement and processed
usage are checked separately. Infrastructure errors, unexpected skips, failures
and unverified cleanup return a nonzero exit code.

The bundled upstream demo image contains its own PostgreSQL/Redis/API/worker;
the selected `--postgres-version` applies to Prosaic's shared database. The
owned fixture uses loopback ports and an explicit private subnet selected against
existing Docker networks. Source/image/API provenance lives in
[`dependencies/lago.json`](dependencies/lago.json). No existing billing deployment,
payment processor or live inference credentials are used.

Sanitized JUnit, `result.json` and the initial multiuser `billing.json` survive
exact-owned teardown under `.lab/<owner>/`. Generated credentials and Lago data
are removed. The finite standalone exporter command is
`PYTHONPATH=src .venv/bin/python -m prosaic_integration_lab.billing_exporter --config <private-config-file>`;
its config contains only `billing_dsn` and local `lago.url`/`lago.key`. Provisioning
and mapping creation remain runner/operator operations. A pass can leave pending
events during retry backoff; current-usage reconciliation is a separate required
acceptance gate.

Fixture retail rates intentionally differ from Runtime's provider-cost estimates.
Runtime evidence remains `billing_eligible=False`. This lane verifies open-period
metering and fixture charge reconciliation, not customer invoices, wallets,
payments, finalized-period corrections or production billing readiness.

## License

Apache-2.0. See [LICENSE](LICENSE).
