# Prosaic integration lab

Reference service for consuming Prosaic's validated workflow factory, private
host bindings, durable multiuser execution and owner-scoped usage accounting.
The native demo discovers approved specialists, admits a proposed graph, runs
two specialists, pauses for a structured human decision and resumes on another
HTTP replica.

Start with [the consumer guide](docs/consume-native-workflows.md) for the API and
host integration patterns. [Current delivery status](docs/current-status.md)
records the exact qualified SDKs and release evidence.

## Try the native workflow

This branch consumes the five original qualified `b3-prosaic` candidate wheels.
Public package-index publication is blocked by PyPI publisher setup; Lab 0.3.0
has not been released. The explicit candidate path below works independently of
that publication step. Python imports and CLI names remain unchanged.

You need Python 3.12, the GitHub `gh` CLI authorized to read Actions artifacts,
and a running Docker daemon. Use a fresh environment: legacy and `b3-prosaic`
distributions share import paths and must not be installed together. Podman is
accepted by the runner but is not a verified path here.

```sh
git clone --branch codex/ecosystem-production https://github.com/B3Cognition/prosaic-integration-lab.git
cd prosaic-integration-lab
python3.12 -m venv .venv-candidate
.venv-candidate/bin/python -m pip install --require-hashes -r dependencies/requirements.lock
.venv-candidate/bin/python scripts/prepare_sdk_candidates.py \
  --profile dependencies/sdk-candidates.json \
  --manifest .cache/sdk-candidate/manifest.json
.venv-candidate/bin/python scripts/install_dependencies.py --manifest .cache/sdk-candidate/manifest.json
.venv-candidate/bin/python scripts/audit_install.py --manifest .cache/sdk-candidate/manifest.json
.venv-candidate/bin/python -m pip check
export PATH="$PWD/.venv-candidate/bin:$PATH"
.venv-candidate/bin/python scripts/build_consumer.py \
  --manifest .cache/sdk-candidate/manifest.json --dependency-mode candidate \
  --tag prosaic-integration-lab:candidate
.venv-candidate/bin/python -m lab_runner demo --mode native \
  --candidate --candidate-manifest .cache/sdk-candidate/manifest.json \
  --postgres-version 16
```

The profile selects these exact original artifacts:

| Distribution | Version |
| --- | --- |
| `b3-prosaic` | 0.4.0 |
| `b3-prosaic-runtime` | 0.8.0 |
| `b3-prosaic-runtime-postgres` | 0.2.0 |
| `b3-prosaic-harness` | 0.7.0 |
| `b3-prosaic-harness-postgres` | 0.2.0 |

Preparation verifies successful source-specific SDK qualification, original
wheel/source hashes and embedded upstream receipts. Installation uses only those
five wheels after the locked third-party dependencies; the audit verifies their
installed payloads. Manifest-specific caches and an isolated public image build
exclude other wheels, sibling checkouts, credentials and local run data.

The demo allocates fresh loopback ports, an owned PostgreSQL database and two
replicas. It handles generated fixture credentials privately, drives the public
HTTP APIs, records a filtered result and verifies exact-owned cleanup. Invalid
human input and foreign-owner access are also checked. Missing infrastructure,
execution failure or failed cleanup returns a nonzero exit code. No paid or local
real-model calls are made. Repeat with `--postgres-version 18` if needed.

These SDK Actions artifacts are retained for 90 days. The candidate path is a
temporary consumption channel; an unavailable artifact fails explicitly.
[The publication checkpoint](docs/current-status.md#publication-and-deployment-boundaries)
tracks the permanent package-index channel and future Lab 0.3.0 public-pin adoption.

## Follow the integration

The [consumer guide](docs/consume-native-workflows.md) maps the supported public
SDK APIs to the service code. [Native workflow HTTP usage](docs/native-workflows.md)
shows catalogue, proposal, start, pause, revision-checked response and usage
requests for an already configured service.

The service supplies trusted identity, current authorization, tool
implementations, credentials and retained bundles. Clients supply a bounded
graph using logical aliases and JSON inputs. Clients do not provide filesystem
directories, endpoints, executable bindings or invocation identities. Inline
instructions, specialist composition and tool access require separate grants.

The wheel includes application and runner modules. Stack commands also need
this Git checkout or a complete source archive for scripts, fixtures and
configuration. Runner commands use public installed SDK APIs; no editable SDK
checkout or private SDK import is required.

## Other demonstrations

The accounting demo uses the same candidate image and a fresh owned synthetic
stack. It shows accepted and rejected outputs, missing usage, exact fixture
estimates and two-replica approval. The HTML/JSON reports survive verified
teardown; `--open-report` opens the saved accounting report.

```sh
.venv-candidate/bin/python -m lab_runner demo \
  --candidate --candidate-manifest .cache/sdk-candidate/manifest.json \
  --postgres-version 16 --open-report
```

For a bounded multiuser terminal workload:

```sh
.venv-candidate/bin/python -m lab_runner run \
  --candidate --candidate-manifest .cache/sdk-candidate/manifest.json \
  --postgres-version 16 --users 10 --runs-per-user 20 --concurrency 2
```

Its first line prints a command for another terminal. Copy that command, or use
the printed exact ownership directory:

```sh
.venv-candidate/bin/python -m lab_runner watch \
  --directory .lab/PRINTED_OWNER_ID --stream accounting
```

The watcher replays existing owner-scoped events and exits after cleanup.
Use `--stream requests` for HTTP operation/status/latency events. The workload
checks foreign-owner isolation and reconciles independent provider counters with
recorded calls; it is a closed-loop fixture, not an arrival-rate benchmark.
See [capacity and retention](docs/capacity-retention.md) and the
[SDK accounting contract](https://github.com/B3Cognition/prosaic-runtime/blob/da3b43e12027b78d60b846c427021559b4927ba4/docs/accounting.md).
These demonstrations make no real-model calls or customer charges.

## Run the required acceptance gates

After candidate setup and image build above:

```sh
.venv-candidate/bin/python -m pytest -q
.venv-candidate/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases-lab-0.2.0.json
.venv-candidate/bin/python -c 'from lab_runner.legacy_upgrade import build_baseline; build_baseline()'
.venv-candidate/bin/python scripts/required_acceptance.py \
  --candidate --candidate-manifest .cache/sdk-candidate/manifest.json \
  --postgres-version 16 --export reports/candidate-pg16.json
```

The historical build requires a Git checkout containing the recorded Lab 0.2.0
commit. Repeat with PostgreSQL 18. CI separately runs both Linux AMD64 and ARM64;
a local run verifies the actual host architecture. All eight lanes require exact
counts, zero skips, installed-payload provenance and verified cleanup. See
[release gates](docs/release-gates.md) and the
[native adoption ledger](docs/verification/native-adoption-2026-10-10.md).
Share the filtered native demo receipt or sanitized gate summaries; private
`.lab` configurations, raw logs and backups stay local.

The eight lanes cover adversarial service inputs, identity, TLS ingress, Lago,
native SQL persistence, native execution/effect recovery, original-release
upgrade and bounded operational qualification. Synthetic fixture success does
not qualify a live provider, deployment authentication/TLS, long soak capacity,
HA/PITR or customer invoices.

## Historical release and operations

Lab **0.2.0** and its original SDK family are recorded in the
[2026-10-09 release ledger](docs/verification/release-train-2026-10-09.md).
To reproduce that release, use a separate checkout of tag `v0.2.0` and its own
README and environment. Its manifest and assets remain byte-identical; installing
those pins into this candidate branch does not enable the new native APIs.

For service deployment and operation, read [persistence/migration](docs/persistence.md),
[identity](docs/identity.md), [TLS ingress](docs/ingress.md),
[recovery](docs/recovery.md), [observability](docs/observability.md),
[capacity/retention](docs/capacity-retention.md) and
[qualification profiles](docs/qualification.md). Host-side local inference is
an explicit opt-in described in [configs/README.md](configs/README.md).
Fixture authentication and prices are lab-only. Usage evidence and estimates
do not supply approval, retry authorization or a customer invoice.

Implementation context lives in [AGENTS.md](AGENTS.md), the
[approved design](docs/superpowers/specs/2026-10-09-prosaic-integration-lab-design.md),
[handoff](docs/handoff.md) and
[tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1).

## License

Apache-2.0. See [LICENSE](LICENSE).
