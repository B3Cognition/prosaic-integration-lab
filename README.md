# Prosaic integration lab

Reference service for consuming Prosaic's validated workflow factory, private
host bindings, durable multiuser execution and owner-scoped usage accounting.
The native demo discovers approved specialists, admits a proposed graph, runs
two specialists, pauses for a structured human decision and resumes on another
HTTP replica.

Start with [the consumer guide](docs/consume-native-workflows.md) for the API and
host integration patterns. [Current delivery status](docs/current-status.md)
records the exact qualified SDKs and release evidence.

The [conversation adoption guide](docs/conversations.md) documents the new
authenticated host boundary, public SDK memory/durable examples, exact workflow
replies and bounded full history. Lab 0.5.0's candidate passed installed Linux
AMD64/ARM64 × PostgreSQL 16/18 qualification. Its new SDK train remains
unpublished; current published pins below do not supply the conversation API.
See the separate
[verification evidence](docs/verification/conversation-adoption-2026-10-11.md#final-source-platform-qualification--2026-10-12)
before selecting a candidate.

The [optional Castle memory guide](docs/optional-memory.md) adds a separate,
disabled-by-default candidate lane. It freezes scoped evidence before a Harness
review pause and verifies resume after Castle is changed or unavailable.
Its [local verification](docs/verification/optional-memory-2026-10-23.md)
records the tested platforms, artifacts and limits.

## Install packages for an embedding service

All five patch packages are published on PyPI. Their actual public downloads
match the original qualified wheels and GitHub release assets. Create a fresh
Python environment or container image and install the coherent five-package
family:

```sh
python3.12 -m venv .venv-public
.venv-public/bin/python -m pip install --index-url https://pypi.org/simple \
  'b3-prosaic==0.4.1' \
  'b3-prosaic-runtime==0.8.1' 'b3-prosaic-runtime-postgres==0.2.1' \
  'b3-prosaic-harness==0.7.1' 'b3-prosaic-harness-postgres==0.2.1'
.venv-public/bin/python -m pip check
.venv-public/bin/prosaic --version
.venv-public/bin/prosaic-runtime --help
.venv-public/bin/prosaic-harness --help
```

Imports retain `prosaic`, `prosaic_runtime`, `prosaic_runtime_postgres`,
`prosaic_harness` and `prosaic_harness_postgres`; their existing CLI names also
remain unchanged. The public distribution names now begin with `b3-`. Rebuild
the environment rather than installing these over the legacy GitHub packages,
which own the same import paths. PyPI's unrelated `prosaic` package is not a
migration dependency. The PostgreSQL adapters are optional for services that do
not need durable SQL storage/accounting; the Lab uses both.

The [construction example](docs/consume-native-workflows.md#construct-a-workflow-in-memory)
admits a generated graph using public SDKs without a filesystem workspace or
model call. The Lab demo below adds the actual HTTP service, two replicas,
owned PostgreSQL and measured synthetic inference.

## Try the native workflow

The [Lab 0.4.0 release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.4.0)
consumes the five published `b3-prosaic`
patch wheels through the exact-version [active manifest](dependencies/releases.json).
The patch train contains seven upstream reliability fixes. Use a new environment;
historical manifests, candidate caches and verification receipts are preserved.
The [release closure](docs/verification/production-readiness-m1-m2-2026-10-11.md#lab-040-release-closure)
records [run 38147824985](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38147824985)
at source `f47328d2d5a8e7253ad6cb199583f9f0d311fd60`: all four Linux
AMD64/ARM64 × PostgreSQL 16/18 cells, 920 required cases, zero failures/errors/
test skips and all 32 lane plus four separate demo cleanups verified. Each cell
passed 744 source tests and ordinary public-index adoption. This release adds
native fault/restoration qualification and tier-routing checks; SDK pins stay
unchanged.

The historical [Lab 0.3.0 release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.3.0)
remains recorded in the
[public adoption ledger](docs/verification/public-release-adoption-2026-10-11.md#released-package-native-qualification):
successful [run 38119573605](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38119573605)
at release source `59ea44b97224415e22fec64c2b9bf39bd9503276`: all four native
cells, 864 required cases, zero failures/errors/skips and all 32 lane plus four
demo cleanups verified. The earlier
[hardening checkpoint](docs/verification/hardening-2026-10-10.md#native-hardening-closure)
retains its original candidate source and receipts. The recipe below uses the
stable released tag and actual verified public SDK downloads. Python imports
and CLI names remain unchanged.

You need Python 3.12 and a running Docker daemon. Use a fresh environment: legacy and `b3-prosaic`
distributions share import paths and must not be installed together. Podman is
accepted by the runner but is not a verified path here.

```sh
git clone --branch v0.4.0 https://github.com/B3Cognition/prosaic-integration-lab.git
cd prosaic-integration-lab
python3.12 -m venv .venv-public
.venv-public/bin/python -m pip install --require-hashes -r dependencies/requirements.lock
.venv-public/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases.json
.venv-public/bin/python scripts/install_dependencies.py --manifest dependencies/releases.json
.venv-public/bin/python scripts/audit_install.py --manifest dependencies/releases.json
.venv-public/bin/python -m pip check
export PATH="$PWD/.venv-public/bin:$PATH"
.venv-public/bin/python scripts/build_consumer.py \
  --manifest dependencies/releases.json --dependency-mode released \
  --tag prosaic-integration-lab:dev
.venv-public/bin/python -m lab_runner demo --mode native --postgres-version 16
```

The active manifest selects these exact published artifacts:

| Distribution | Version |
| --- | --- |
| `b3-prosaic` | 0.4.1 |
| `b3-prosaic-runtime` | 0.8.1 |
| `b3-prosaic-runtime-postgres` | 0.2.1 |
| `b3-prosaic-harness` | 0.7.1 |
| `b3-prosaic-harness-postgres` | 0.2.1 |

Preparation downloads the actual pinned public URLs and verifies the original
wheel hashes. Installation uses only those five wheels after the locked
third-party dependencies; the audit verifies their installed payloads.
Manifest-specific caches and an isolated public image build
exclude other wheels, sibling checkouts, credentials and local run data.

The demo allocates fresh loopback ports, an owned PostgreSQL database and two
replicas. It handles generated fixture credentials privately, drives the public
HTTP APIs, records a filtered result and verifies exact-owned cleanup. Invalid
human input and foreign-owner access are also checked. Missing infrastructure,
execution failure or failed cleanup returns a nonzero exit code. No paid or local
real-model calls are made. Repeat with `--postgres-version 18` if needed.

The normal package-index channel no longer depends on retained Actions artifacts.
[The publication checkpoint](docs/current-status.md#publication-and-deployment-boundaries)
records the SDK and Lab release evidence. The earlier documentation-only
checkpoint `e283752` records the qualified Lab 0.3.0 source `59ea44b`; its tag
and original assets remain unchanged. The current documentation records the
separate Lab 0.4.0 source and original builds.

### Retained candidate recipe

For reproducing the earlier candidate lineage, keep a separate environment and
use the unchanged profile. This requires authorized `gh` access to the original
successful Actions artifacts, which have 90-day retention:

```sh
python3.12 -m venv .venv-hardening
.venv-hardening/bin/python -m pip install --require-hashes -r dependencies/requirements.lock
.venv-hardening/bin/python scripts/prepare_sdk_candidates.py \
  --profile dependencies/sdk-candidates.json \
  --manifest .cache/sdk-hardening/manifest.json
.venv-hardening/bin/python scripts/install_dependencies.py --manifest .cache/sdk-hardening/manifest.json
.venv-hardening/bin/python scripts/audit_install.py --manifest .cache/sdk-hardening/manifest.json
.venv-hardening/bin/python -m pip check
export PATH="$PWD/.venv-hardening/bin:$PATH"
.venv-hardening/bin/python scripts/build_consumer.py \
  --manifest .cache/sdk-hardening/manifest.json --dependency-mode candidate \
  --tag prosaic-integration-lab:candidate
.venv-hardening/bin/python -m lab_runner demo --mode native \
  --candidate --candidate-manifest .cache/sdk-hardening/manifest.json --postgres-version 16
```

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

The accounting demo uses the same released-SDK image and a fresh owned synthetic
stack. It shows accepted and rejected outputs, missing usage, exact fixture
estimates and two-replica approval. The HTML/JSON reports survive verified
teardown; `--open-report` opens the saved accounting report.

```sh
.venv-public/bin/python -m lab_runner demo --postgres-version 16 --open-report
```

For a bounded multiuser terminal workload:

```sh
.venv-public/bin/python -m lab_runner run \
  --postgres-version 16 --users 10 --runs-per-user 20 --concurrency 2
```

Its first line prints a command for another terminal. Copy that command, or use
the printed exact ownership directory:

```sh
.venv-public/bin/python -m lab_runner watch \
  --directory .lab/PRINTED_OWNER_ID --stream accounting
```

The watcher replays existing owner-scoped events and exits after cleanup.
Use `--stream requests` for HTTP operation/status/latency events. The workload
checks foreign-owner isolation and reconciles independent provider counters with
recorded calls; it is a closed-loop fixture, not an arrival-rate benchmark.
See [capacity and retention](docs/capacity-retention.md) and the
[SDK accounting contract](https://github.com/B3Cognition/prosaic-runtime/blob/3566731c39a3fff2837acd93a96baa2187764206/docs/accounting.md).
These demonstrations make no real-model calls or customer charges.

## Run the required acceptance gates

After public-manifest setup and image build above:

```sh
.venv-public/bin/python -m pytest -q
.venv-public/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases-lab-0.2.0.json
.venv-public/bin/python -c 'from lab_runner.legacy_upgrade import build_baseline; build_baseline()'
.venv-public/bin/python scripts/required_acceptance.py \
  --postgres-version 16 --export reports/required-pg16.json
```

The historical build requires a Git checkout containing the recorded Lab 0.2.0
commit. Repeat with PostgreSQL 18. CI separately runs both Linux AMD64 and ARM64;
a local run verifies the actual host architecture. All eight lanes require exact
counts, zero skips, installed-payload provenance and verified cleanup. See
[release gates](docs/release-gates.md) and the
[hardening ledger](docs/verification/hardening-2026-10-10.md). The
[earlier native adoption ledger](docs/verification/native-adoption-2026-10-10.md)
preserves its original qualification evidence.
Share the filtered native demo receipt or sanitized gate summaries; private
`.lab` configurations, raw logs and backups stay local.

To verify ordinary consumer installation independently of the locked image:

```sh
.venv-public/bin/python scripts/verify_public_adoption.py \
  --manifest dependencies/releases.json --export reports/public-adoption.json
```

This resolves the supported five public packages with dependencies enabled in a
fresh isolated environment, audits the exact wheel bytes and import ownership,
and runs CLI, `pip check` and public workflow construction checks. Released CI
requires it. Native transport/SQL fault tests and populated native logical restore
are described in [release gates](docs/release-gates.md) and
[qualification](docs/qualification.md). Their new collection contract is 230
cases per platform/database cell; the Lab 0.3.0 release retains its original
864-case evidence. Current milestone evidence and remaining limits are in the
[production readiness ledger](docs/verification/production-readiness-m1-m2-2026-10-11.md).
The original milestone checks passed all 920 cases on Linux AMD64/ARM64 ×
PostgreSQL 16/18 at source `8f60c587ce36a9bb5d9b65c3ca1876f1de93b9bc`; the
ledger retains that source's pinned checkout instructions. Lab 0.4.0 passed its
own exact-source matrix at `f47328d` as recorded above. Actual local routing passed
default/balanced Qwen 7B and strong Qwen 27B. SDK release pins remain unchanged.
The newer conversation candidate has [separate actual local Qwen evidence](docs/verification/local-conversation-2026-10-12.md):
the complete journey passed with balanced chat/interpretation and explicit strong
workflow execution. Quoted approval was denied and duplicate approval caused no
new call or effect. The observed 7B/server native-tool failure stays documented;
the host selects an approved working profile, with no automatic fallback.

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
those pins into the current source does not enable the new native APIs.

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
