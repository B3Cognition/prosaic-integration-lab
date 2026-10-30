# Prosaic integration lab

For the independent, unpublished **Prosaic Castle** fork, start with the
[enable/use guide](docs/prosaic-castle.md): lean worker setup, separately opt-in
memory and SUE, selected-source review, and qualification limits. Both features
remain disabled by default. The older [Castle quickstart](docs/castle-quickstart.md)
retains its historical r7 package profile and evidence.

The opt-in [unified Runtime pool lab](docs/unified-runtime-pools.md) tests Claude
Code, Codex CLI and local/API selection with explicit policies and pre-work-only
fallback using released Runtime 0.9.8. Retained [27-run benchmark results](docs/verification/unified-cli-realistic-2026-10-23.md)
and [provider-rejection/no-replay tests](docs/verification/unified-provider-fallback-2026-10-23.md)
separate real model observations from simulated failures.
The [PR qualification ledger](docs/verification/unified-pool-pr-finalization-2026-10-23.md)
records the earlier candidate checks and exact provenance. The
[released adoption ledger](docs/verification/runtime-unified-release-2026-10-24.md)
separately records public artifact checks and fresh release validation.

The experimental [sandboxed CLI blueprint](docs/sandboxed-tools.md) composes
host admission/approval with Runtime's native confinement and independently
witnessed cleanup. Unsupported hard resource controls refuse admission; memory
and correction remain experimental. Linux platform qualification remains a CI gate.

The experimental [trajectory evaluation blueprint](docs/trajectory-evaluation.md)
joins safe public SDK observations to host-verified outcomes, with a second-domain
parcel example and offline report inspection. It makes no live model efficacy claim.

Reference service for consuming Prosaic's validated workflow factory, private
host bindings, durable multiuser execution and owner-scoped usage accounting.
The native demo discovers approved specialists, admits a proposed graph, runs
two specialists, pauses for a structured human decision and resumes on another
HTTP replica.

Start with [the consumer guide](docs/consume-native-workflows.md) for the API and
host integration patterns. [Current delivery status](docs/current-status.md)
records the exact qualified SDKs and release evidence.

This branch prepares Lab **0.6.0**. The latest published Lab release is **0.5.0**;
for its packages and final verification, use the
[release page](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.5.0).
The experimental [agent-quality](docs/agent-quality.md) and
[retrieval-memory](docs/retrieval-memory.md) examples have separate capability
claims and retained model-study evidence.

The experimental [durable failure isolation blueprint](docs/failure-isolation.md)
adds conservative host admission and explicit receipt-only recovery around public
SDK operations. It preserves reservations and never automatically replays work.
The experimental [tool approval blueprint](docs/tool-approval.md) binds exact
actions to trusted host review and one-shot consent through public Runtime APIs.

The next experimental milestone adds an opt-in
[typed evidence consumer pattern](docs/verification/typed-evidence.md). It
classifies verified, absent and unread facts without supplying a model decision.
Its fresh live comparison stopped on a token-budget overrun; the verification
note records the incomplete results. Released Lab 0.5.0 remains unchanged.

The [conversation adoption guide](docs/conversations.md) documents the new
authenticated host boundary, public SDK memory/durable examples, exact workflow
replies and bounded full history. The active manifest now uses published Runtime
0.9.8/recorder 0.3.0 and Harness 0.9.4/store 0.4.0 with Core 0.4.1.
Lab 0.5.0's earlier candidate passed installed Linux
AMD64/ARM64 × PostgreSQL 16/18 qualification. See the separate
[verification evidence](docs/verification/conversation-adoption-2026-10-11.md#final-source-platform-qualification--2026-10-12)
for that exact candidate's results; fresh public adoption is recorded in the
[published SDK adoption ledger](docs/verification/published-conversation-adoption-2026-10-13.md).
The [timeout patch ledger](docs/verification/conversation-timeout-patch-2026-10-14.md)
records the latest package update and its additional no-redispatch regressions.

For Castle, start with the [step-by-step memory guide](docs/castle-quickstart.md):
use cases, exact package setup, a runnable local walkthrough, and how to enable,
review, resume or disable memory. Castle stays **off by default**. The
[host/operator reference](docs/optional-memory.md) explains the boundaries and
qualification commands; [verification evidence](docs/verification/castle-integration-2026-10-23.md)
records actual tested platforms and limits.

The experimental [own-data memory benchmark](docs/memory-benchmark.md) adds
frozen datasets, file-search/FTS/expanded comparisons, optional bounded
completeness review, strict external adjudication and offline replay. Larger
corpora do not increase per-task context; fixture success is not quality evidence.
Memory and review remain disabled by default, and live constrained generation
requires the separately qualified SDK candidate described in that guide.

The separately opt-in [SUE review guide](docs/sue-review.md) shows a
credential-free requirements-review walkthrough, frozen sources, approval and
recovery with the lightweight engine. Review stays **off by default**, independent
of Castle memory; its reports are advisory and do not certify correctness.
The separate [requirements comparison](docs/requirements-review-eval.md) exercises
direct, critic-author and SUE strategies against frozen synthetic cases while
preserving the original hackathon grader and retrieval checks.

## Install packages for an embedding service

All five packages are published on PyPI. Their actual public downloads
match the original qualified wheels and GitHub release assets. Create a fresh
Python environment or container image and install the coherent five-package
family:

```sh
python3.12 -m venv .venv-public
.venv-public/bin/python -m pip install --index-url https://pypi.org/simple \
  'b3-prosaic==0.4.1' \
  'b3-prosaic-runtime==0.9.8' 'b3-prosaic-runtime-postgres==0.3.0' \
  'b3-prosaic-harness==0.9.4' 'b3-prosaic-harness-postgres==0.4.0'
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
consumed the five published `b3-prosaic`
patch wheels preserved in the [Lab 0.4.0 manifest](dependencies/releases-lab-0.4.0.json).
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
current `main` checkout and actual verified public SDK downloads. Lab 0.5.0
publication is separate from this SDK adoption. Python imports
and CLI names remain unchanged.

You need Python 3.12 and a running Docker daemon. Use a fresh environment: legacy and `b3-prosaic`
distributions share import paths and must not be installed together. Podman is
accepted by the runner but is not a verified path here.

```sh
git clone --branch main https://github.com/B3Cognition/prosaic-integration-lab.git
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
| `b3-prosaic-runtime` | 0.9.8 |
| `b3-prosaic-runtime-postgres` | 0.3.0 |
| `b3-prosaic-harness` | 0.9.4 |
| `b3-prosaic-harness-postgres` | 0.4.0 |

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

## Try a conversation and an approved workflow

### Converse in the browser

After the fresh installation and released consumer build above, keep an owned
local chat service running with:

```sh
.venv-public/bin/python -m lab_runner.chat --live-local --max-calls 32
```

The launcher opens a simple browser chat backed by the approved local Qwen
profile in `configs/runtime-local.example.yml` (`local-strong` by default).
It reads the provider key from that profile's private secret file, uses an owned
PostgreSQL database and binds service ports to loopback. You can type messages,
read retained history, start a new conversation and select or approve the
displayed workflow interaction. The shared provider allowance covers all sessions
in that launch; exhaustion stops dispatch rather than silently extending it.
Workflow tools still operate on synthetic Lab players, even with a real model.

Use `--runtime-config /absolute/private/runtime.yml --profile approved-profile`
to select another approved local Qwen profile. Omit `--live-local` for scripted,
credential-free fixture responses. The model mode is labeled in the page.
Press Ctrl+C in the launcher terminal to stop and verify owned-stack cleanup.
The browser launch code is single-use and expires after ten minutes. API tokens
stay in browser memory; reloading requires a fresh launch or manual token
connection. No token is embedded in the page or saved in browser storage.
The ordinary service also serves the chat shell at `/chat`; its API calls still
require authentication. **Refresh** only reads current state. **Retry same
request** replays an uncertain HTTP request with the original message ID/body;
**Inspect recovery** does not authorize repeating an uncertain effect.

After the installation and released consumer build above, run:

```sh
.venv-public/bin/python -m lab_runner demo --mode conversation --postgres-version 16
.venv-public/bin/python -m lab_runner test --mode conversation --postgres-version 18
```

The demo uses the published packages, two HTTP replicas, durable PostgreSQL
sessions and synthetic inference. It creates an authenticated conversation,
remembers a user correction, starts the host-approved player lookup workflow,
selects the displayed second result and approves its exact current interaction.
The fixture performs one effect; duplicate approval replays add no model call or
effect. Conversation and workflow usage are reported separately. The test lane
also exercises authorization, worker loss, recovery and capacity limits.

Choose the API that matches your application:

- **A small assistant:** use `Conversation` with `MemorySessionStore` for a
  prototype, `FileSessionStore` for a private single-host service, or
  `PostgresSessionStore` for replicas. Follow the
  [public SDK example](docs/conversations.md#build-a-small-assistant).
- **A generated workflow:** admit a proposal with `WorkflowFactory` and trusted
  `WorkflowCatalog`/`WorkflowBindings`; then execute the admitted graph. Follow
  the [construction example](docs/consume-native-workflows.md#construct-a-workflow-in-memory)
  and the native HTTP demo above.
- **A conversation that needs approval:** let trusted host code attach an
  approved workflow and require the displayed `interactionRef` and current
  revision. Follow the [HTTP contract](docs/conversations.md#authenticated-http-contract).

The host owns identity, grants, endpoints, tools and billing attribution. Clients
send messages or graph proposals, and receive filtered public replies. Recovery
does not authorize repeating an uncertain effect. These demos need Docker but no
real-model credentials; live conformance is a separate opt-in operation.

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
historical cases per platform/database cell; the Lab 0.3.0 release retains its original
864-case evidence. Current milestone evidence and remaining limits are in the
[production readiness ledger](docs/verification/production-readiness-m1-m2-2026-10-11.md).
The original milestone checks passed all 920 cases on Linux AMD64/ARM64 ×
PostgreSQL 16/18 at source `8f60c587ce36a9bb5d9b65c3ca1876f1de93b9bc`; the
ledger retains that source's pinned checkout instructions. Lab 0.4.0 passed its
own exact-source matrix at `f47328d` as recorded above. Actual local routing passed
default/balanced Qwen 7B and strong Qwen 27B. That milestone retained its SDK pins;
the active manifest now adopts the published conversation family above.
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

The optional context assembly demonstration uses local synthetic byte units,
not a production tokenizer. With the complete context-capable published SDK
train installed and audited, run:

```sh
python -m lab_runner demo --mode conversation --context-assembly --postgres-version 16
```

The comparison includes recent and older preferences, current interaction
authority and historical injection. It reports `lostContext` where removing
older turns loses useful information. Stored history remains complete; the chat
UI exposes only counts and omitted ranges. See the
[context qualification ledger](docs/verification/context-assembly-2026-10-14.md)
for exact evidence and release limitations.

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

## Experimental agent quality and retrieval memory

See [agent quality](docs/agent-quality.md) and [retrieval memory](docs/retrieval-memory.md) for opt-in local evaluation commands. These consumer examples use public SDK APIs and retain bounded live allowances, immutable evidence and offline replay.

The [typed handoff example](docs/typed-handoffs.md) adds offline planner/worker/critic contracts, independent evidence gates and full-trajectory scoring under the same limits. It remains experimental and makes no live reasoning claim.

The [first real-model handoff evaluation](docs/verification/real-handoffs-live-2026-10-18.md) stopped all eight samples at the planner. The opt-in [direct worker/critic example](docs/direct-handoffs.md) removes host-owned assignment generation from the model. Its [frozen live study](docs/verification/direct-handoffs-live-2026-10-18.md) found partial critic warnings, without complete verification or demonstrated answer improvement.

The [provider-neutral role qualification blueprint](docs/role-qualification.md) gives consumers reusable policy checks, configuration-bound qualification and evidence-grounded diagnostics. Consumers supply their own roles, evidence policies, suites and model settings. [Offline proof](docs/verification/role-qualification-2026-10-18.md) uses scripted responses; it does not certify either local model or admit synthetic qualifications for live use.

The opt-in [bounded correction blueprint](docs/bounded-correction.md) adds one
host-verified correction and a matched no-critic baseline under the same per-arm
limits. Consumers adapt the evidence policy and qualify their own roles; scripted
offline proof does not establish model or critic benefit.
The [fresh live comparison](docs/verification/correction-live-2026-10-18.md)
stopped on unknown usage with no eligible matched pairs. A separate offline
unsupported-usage guard defect is fixed in the experimental candidate and
[qualified offline](docs/verification/usage-guard-2026-10-18.md). This does not
establish critic benefit or production readiness.

The [latest four-sample memory comparison](docs/verification/missing-evidence-memory-live-2026-10-18.md) found no benefit on its one missing-evidence case: the smaller model failed both arms and the larger model passed both. Recall added tokens without saving requests or tools. Memory remains experimental and disabled unless explicitly selected; general efficacy is unproven.
