# Current delivery status

## Visual Explorer in this checkout — 2026-10-25

[Explorer](explorer.md) adds bundled React Flow documentation, user/developer
inspection, eight deterministic playback scenarios and explicit single-agent
unified-pool controls. The default launcher uses no models or Docker. Live
admission, durable allowance, filtered receipts and offline acknowledgment stay
host-owned; Runtime 0.9.8 owns provider selection. The existing Harness browser
service remains separate. This is post-0.6.2 work, not a published release or
new live model benchmark. See the
[implementation verification ledger](verification/explorer-2026-10-25.md) for scope.

## Lab 0.6.2 published and verified — 2026-10-25

The [0.6.2 release verification](verification/release-0.6.2-2026-10-25.md)
records four green exact-source CI cells, original CI archives and verified
public downloads. Clean public-wheel/rebuilt-source installs with Runtime 0.9.8
each passed 51 standalone checks plus 3 deadline checks, including default 180s and
explicit 240s, with cleanup verified and zero live model calls. The
[guided quickstart](quickstart.md) and standalone first-workflow example are
post-release onboarding additions in this checkout, not changes to released bytes.

## Configurable benchmark deadline and 240s study — 2026-10-25

The unified benchmark now accepts a finite `--local-timeout` from 1–300s,
defaulting to 180s. The [0.6.2 release preparation](release-0.6.2.md) includes it; native60s,
pool300s, grants, attempt/request/tool/token caps and allowance remain fixed.
The [recipe](realistic-runtime-benchmark.md) describes invocation and metadata.

The preceding authorized [240s live study](verification/unified-cli-lab061-local240-2026-10-25.md)
used released Lab 0.6.1 and Runtime 0.9.8 with a disclosed private deadline-only
consumer driver. All 27 assignments passed on unchanged Markdown, inputs and
graders. Claude/Codex/local medians were 10.86s/21.73s/62.37s; all nine local
runs finished within 180s. It retained 27 controlled skips, zero provider
fallbacks/timeouts and 45/243 known mixed units, with cleanup verified. The
implementation uses credential-free tests; this follow-up makes no new live calls.

## Lab 0.6.1 release and clean-install verification — 2026-10-25

Lab [0.6.1 is published](release-0.6.1.md), fixing the standalone installed
evaluation CLI by packaging the SDK payload auditor. The compatibility source
command retains the same payload, ownership and executable-cache checks.

All four Linux AMD64/ARM64 × PostgreSQL 16/18 CI cells passed 1,899 source tests
each and 1,336 required real-stack checks across 36 lanes. Original qualified CI
wheel/source bytes were published with checksums and exact-source verification.

The [post-publication verification](verification/release-0.6.1-2026-10-25.md)
downloaded all four assets and verified their bytes. Clean public-wheel and
rebuilt-public-source installs on macOS ARM64/Python 3.12.15 each passed all 51
standalone CLI checks with Runtime 0.9.8, including quota fallback, persisted
cooldowns and no partial-work replay. Isolated imports, 176 installed Lab files
per consumer and cleanup were verified; no repository `scripts` package was
available and no live provider calls were made. SDK pins, earlier artifacts and
historical model measurements remain unchanged.

## Lab 0.6.0 release — 2026-10-24

The [0.6.0 release notes](release-0.6.0.md) describe the unified pool examples,
public Runtime 0.9.8 train, two successful live CLI studies and accumulated
consumer blueprints. Publication requires the final source's four-cell
Linux AMD64/ARM64 × PostgreSQL 16/18 acceptance matrix, including installed
distributions and verified cleanup. The release assets' `VERIFICATION-0.6.0.json`
and `SHA256SUMS-0.6.0.txt` bind the exact qualified CI wheel/source archive,
SDK manifest and source. Earlier study reports and experimental boundaries
remain unchanged; release preparation makes no new live model calls.

## Released Runtime live benchmarks — 2026-10-24

Two authorized [live unified CLI studies](verification/unified-cli-released-2026-10-24.md)
used the verified public Runtime 0.9.8 wheel and unchanged neutral Markdown,
synthetic inputs, graders and deadlines: native 60s, local 180s, pool 300s.
Each study passed 27/27 assignments (nine per model). Latest medians were
Claude Sonnet 11.37s, Codex gpt-6.1-sol/low 23.07s and local ThinkingCap Qwen
27B 60.69s; the preceding released study measured 10.38s, 23.61s and 66.21s.

Each study verified 27 controlled cooldown skips, zero provider-triggered
fallbacks, zero timeouts and known allowance accounting. Output regrading and
owned-resource cleanup passed. These are small factual/workspace studies;
timings do not isolate Runtime effects or establish a general model ranking.
The latest run used port 8001 because the desktop local server occupied 8000;
only the private endpoint URL changed. Raw evidence remains private.

## Released Runtime unified pools — 2026-10-24

Runtime 0.9.8 is published with native Claude/Codex execution and unified
native/API/local pools. Lab's active manifest selects the verified public wheel;
Core 0.4.1, Harness 0.9.4 and both PostgreSQL adapter pins are unchanged.
The [adoption ledger](verification/runtime-unified-release-2026-10-24.md)
records public artifact verification, installed/offline acceptance and the
mandatory exact-head Linux AMD64/ARM64 × PostgreSQL 16/18 CI gate.

The previous manifest, SDK profile and memory freeze snapshots are archived
byte-for-byte. Current memory qualification has an explicit new SDK provenance
lineage; corpus, tasks, prose, scoring, limits and historical results are
unchanged. Memory/correction remain experimental. No live inference or new
model efficacy comparison is included in this release adoption.

## Optional Castle integration review — 2026-10-23

Castle is a disabled-by-default host memory provider with scoped FTS recall and
frozen Harness evidence across review/resume. The [beginner guide](castle-quickstart.md)
covers installation, use cases, a synthetic local walkthrough and real-palace
configuration. It grants no new public HTTP operation or model memory tools;
SUE and SOAR remain separate.

On the unchanged public SDK train, [local verification](verification/castle-integration-2026-10-23.md)
passes 1847 source tests, all 97 conversation cases on each PostgreSQL 16/18
lane, and six installed Castle cases per version, with cleanup verified.
The adapter/worker wheels remain explicit unpublished candidates. This is
local ARM64 synthetic qualification, with no new package release or live claim.

## Lab 0.6.0 version and PR preparation — 2026-10-20

The maintainer authorized the version bump and push of the reviewed sandbox
blueprint. Lab advances to0.6.0 for the additive consumer blueprints; public SDK
pins stay unchanged. Memory/correction remain experimental, all limits and
historical charges are preserved, and no live run or package publication is
included. Exact-head Linux/platform CI remains a merge/release gate.
The [version qualification](verification/sandbox-version-0.6.0-2026-10-20.md)
passes1824source tests and clean public wheel/rebuilt-sdist consumption, with
142matching package payloads and all five verified SDK payloads.

## Trajectory merged; sandboxed CLI blueprint — 2026-10-20

PR21 merged at5a966ae with four green CI cells. The next experimental
[sandboxed CLI consumer blueprint](sandboxed-tools.md) reuses public Runtime
confinement, explicit unsupported-control admission and independent OS witnesses.
[Offline qualification](verification/sandboxed-tools-2026-10-20.md) distinguishes
native macOS enforcement from the mandatory Linux CI gate. The branch is now
authorized for a review PR; memory/correction remain experimental, no SDK release/live calls
or changes to current limits/charges.

## Approval merged; next consumer milestone — 2026-10-19

PR20 merged at5bd896a with four green exact-head CI lanes. Tool authorization and
durable isolation are integrated experimental Lab blueprints on the public SDK
train; no new stable release was created. The provider-neutral trajectory
evaluation blueprint passes1769source tests and12installed both-wire scenarios;
independent review found no defects. Later PR/platform CI remains. Memory/correction stay
experimental and current live limits/charges are unchanged.

## Experimental blueprint CI on published SDKs — 2026-10-18

PR18 now selects public Runtime 0.9.7 / Harness 0.9.4 with Core 0.4.1 and the
unchanged PostgreSQL adapters. [CI repair and qualification](verification/pr18-ci-2026-10-18.md)
separates this public train from the unpublished diagnostics candidate and
historical studies. Memory and correction remain opt-in and experimental;
model efficacy and stable release acceptance remain separate. The checkpoints
below describe their original release state.

## Native tool and experimental memory release preparation — 2026-10-17

The active train adopts published Runtime 0.9.6 with Core 0.4.1, Runtime recorder 0.3.0, Harness 0.9.0 and Harness store 0.4.0. The previous context train is preserved in `dependencies/releases-lab-context-0.5.0.json`. Agent-quality and controlled retrieval memory examples are opt-in; memory remains experimental. Historical live findings retain their original candidate identity. See [the release ledger](verification/release-0.5.0-2026-10-17.md) for final qualification and publication.

## Published optional context assembly adoption — 2026-10-14

The active manifest selects Core0.4.1, Runtime0.9.4/recorder0.3.0 and
Harness0.9.0/store0.4.0. The three new distributions were published from exact
qualified artifacts; actual public wheel and source downloads match their
hashes. Fresh ordinary PyPI consumer adoption and the978-test Lab suite passed.
The previous manifest remains in
[`releases-pre-context-2026-10-14.json`](../dependencies/releases-pre-context-2026-10-14.json).
See the [context assembly ledger](verification/context-assembly-2026-10-14.md#published-sdks-and-public-consumer-adoption)
and [Lab PR16](https://github.com/B3Cognition/prosaic-integration-lab/pull/16)
for released-package acceptance and merge evidence.

Context policies are optional and host controlled. The demonstration uses
synthetic byte counts; no production tokenizer is certified. Drain old writers
and explicitly migrate existing storage before enabling context policies.
The context-capable conversation lane requires103 cases. Lab0.5.0 publication
is separate from this SDK adoption.

## Published timeout patch adoption — 2026-10-14

The timeout-patch manifest selected Core 0.4.1, Runtime 0.9.3/recorder 0.3.0 and Harness
0.8.2/store 0.3.0. The Runtime patch fixes the negative provider timeout status
that caused `store_corrupt` during conversation receipt persistence. All five
public wheels were downloaded, verified by hash and audited in `.venv-latest`.
The lab suite passes 955 tests with no skips. See the
[patch verification ledger](verification/conversation-timeout-patch-2026-10-14.md)
for exact release provenance and stack acceptance results.

That conversation gate contained 97 cases, including real ordinary and
interpretation timeouts followed by replica replay/recovery without redispatch.
Historical evidence below retains the versions and counts actually verified.

## Published conversation SDK adoption — 2026-10-13

The 2026-10-13 checkout selected Core 0.4.1, Runtime 0.9.0/recorder 0.3.0 and
Harness 0.8.0/store 0.3.0 from actual PyPI downloads in
[`dependencies/releases.json`](../dependencies/releases.json). Runtime publication
[38391849639](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38391849639)
and Harness publication
[38393899829](https://github.com/B3Cognition/prosaic-harness/actions/runs/38393899829)
passed the platform gates, public-download hash checks and GitHub release steps.
Core 0.4.1 is unchanged. The previous patch manifest is preserved as
[`releases-lab-0.4.0.json`](../dependencies/releases-lab-0.4.0.json).

Use the [installation and demos](../README.md#install-packages-for-an-embedding-service),
[workflow construction guide](consume-native-workflows.md) and
[conversation guide](conversations.md). The new pins enable the required
conversation lane in ordinary released mode, including the installed Lab
wheel/sdist smoke and both documented demos. Fresh local adoption and stack
evidence is recorded in the
[2026-10-13 ledger](verification/published-conversation-adoption-2026-10-13.md).
Lab 0.5.0 itself has not been released by this adoption change.

## Historical Lab 0.4.0 checkpoint

Checkpoint: 2026-10-11. [Lab **0.4.0**](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.4.0)
is the current release at source `f47328d2d5a8e7253ad6cb199583f9f0d311fd60`.
[Released-package run 38147824985](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38147824985),
attempt 1, passed all four Linux AMD64/ARM64 × PostgreSQL 16/18 cells: 230
required cases per cell / 920 total, zero failures/errors/test skips, 32 lane
cleanups and four separate demo cleanups verified. Each cell passed 744 source
tests with one known Starlette deprecation warning and fresh ordinary-index
adoption. The release retains the same five public SDK pins. Its capacity fixture
measures 18 workflows across two three-second fairness windows while retaining
the two-second latency target and existing correctness/accounting gates; recovery
profiles remain unchanged. The safe CI summaries do not expose an exact measured
P95. Package hashes and reproduction commands are in the
[release closure](verification/production-readiness-m1-m2-2026-10-11.md#lab-040-release-closure).

The prior [Lab **0.3.0** release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.3.0) was published
at source `59ea44b97224415e22fec64c2b9bf39bd9503276` with the verified public SDK
patch train. [Released-package run 38119573605](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38119573605)
passed all four Linux AMD64/ARM64 × PostgreSQL 16/18 cells: 864 required cases,
zero failures/errors/skips, all 32 lane cleanups and four demo cleanups verified.
Each cell also passed 540 source tests with one existing deprecation warning;
each demo reconciled two complete synthetic calls and remained billing-ineligible.
Actual downloaded release assets match the original wheel/sdist bytes. See the
[public adoption ledger](verification/public-release-adoption-2026-10-11.md).

The documentation-only checkpoint `e283752` records the qualified `59ea44b`
source and its original release assets. Prior candidate receipts retain their
original sources.

Milestones 1 and 2 extend native transport/SQL fault coverage,
populated native logical restoration, tier routing and ordinary public-index
consumer adoption. Source `8f60c587ce36a9bb5d9b65c3ca1876f1de93b9bc` passed the
[four-cell matrix](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38128089071):
230 cases per cell / 920 total, zero failures/errors/test skips, 32 lane and four
demo cleanups verified. Each cell passed 744 source tests and fresh public-index
adoption. Actual local Qwen default/balanced 7B and strong 27B routing passed.
These Lab changes are not a new SDK release. That milestone's verification and
limits are recorded in the [milestone ledger](verification/production-readiness-m1-m2-2026-10-11.md).

The earlier candidate train passed all four required native Linux cells in
[run 38061354170](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38061354170),
at Lab source `0feb56b02f4c3dfb21c8fe7487bd1d3216e86dec`. See the
[earlier candidate ledger](verification/ecosystem-production-2026-10-10.md)
for exact artifacts, counts, image identities and publication prerequisites.

The native adoption entry point has a pinned candidate setup recipe and
`demo --mode native`, with a public client walkthrough and host integration
guide. Its new regression extends the native collection contract to 40 cases;
the separate demo CLI also runs in each native CI cell. The earlier 860-case
receipt remains evidence for its original source, not for these additions.
[Native adoption run 38065626859](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38065626859)
succeeded at source `60c6e7bc306b965b5074a536f2bb612d7d567322` in all four
cells: 864 required cases with zero failures/errors/skips, all 32 lane cleanups
and four separate demo cleanups verified. Each cell also passed 537 source
tests. See the
[adoption verification ledger](verification/native-adoption-2026-10-10.md)
for source/archive/installed checks and original native receipts.

The historical patch recipe selected the seven-fix train: Core 0.4.1,
Runtime 0.8.1/recorder 0.2.1 and Harness 0.7.1/store 0.2.1. Its original
SDK bytes passed fresh qualification. Lab
[run 38080612477](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38080612477)
succeeded at `94f313e49707a09e7d0f3abbf818a9861bd6b14a` in all four cells:
864 required cases, zero failures/errors/skips, 32 lane cleanups and four demo
cleanups verified. Each cell passed 537 source tests; each separate native demo
observed two synthetic calls and remained billing-ineligible. The earlier
receipts above apply to their original sources. See the
[hardening ledger](verification/hardening-2026-10-10.md) for exact sources,
artifact hashes and consumer verification. Public APIs and formats are unchanged.

A later Lab CLI correction lets the default container `--version` command report
the actual installed B3 SDK family while retaining the legacy-family command.
Its original checkpoint passed two isolated CLI regressions and all 539 source
tests. The native
hardening receipt above still qualifies its original `94f313e` source. The
later `59ea44b` source completed the released-package matrix and publication
recorded above; the [publication preparation ledger](verification/publication-preparation-2026-10-10.md)
retains the earlier CLI checkpoint.

Start with the [runnable native consumption guide](consume-native-workflows.md),
[native workflow usage](native-workflows.md), [persistence and
migration](persistence.md), [required release gates](release-gates.md) and
[bounded operational qualification](qualification.md). The
[2026-10-09 release ledger](verification/release-train-2026-10-09.md) records
the historical published baseline; its versions and measurements are preserved.

## Historical published SDK patch train

All five distributions are published on PyPI and in their GitHub releases.
Actual downloads from both channels match the original qualified wheel and
sdist hashes. Promotion reran the required native gates on those original bytes.

| SDK | Public release | Original qualification | Successful publication |
| --- | --- | --- | --- |
| Core | [`b3-prosaic` 0.4.1](https://github.com/B3Cognition/prosaic/releases/tag/v0.4.1) | [38077144248](https://github.com/B3Cognition/prosaic/actions/runs/38077144248) | [38116854936](https://github.com/B3Cognition/prosaic/actions/runs/38116854936) |
| Runtime and recorder | [Runtime 0.8.1 / recorder 0.2.1](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.8.1) | [38079159494](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38079159494) | [38117263240](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38117263240) |
| Harness and store | [Harness 0.7.1 / store 0.2.1](https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.7.1) | [38079961529](https://github.com/B3Cognition/prosaic-harness/actions/runs/38079961529) | [38118430476](https://github.com/B3Cognition/prosaic-harness/actions/runs/38118430476) |

Core ran Linux AMD64/ARM64 on Python 3.11–3.13 and Windows ownership checks.
Runtime also ran macOS on all three Python versions. Runtime and Harness ran
owned PostgreSQL 16/18 on both Linux architectures. Their required source,
installed-wheel and dependency-floor gates passed with exact receipt lineage.
Their exact-source qualification contains 15 Core, 24 Runtime and 18 Harness
records. The Lab consumer installs the five original patch wheels into a fresh
Python 3.12 environment with the unchanged hash-locked third-party graph.

Imports and CLI commands retain their existing names. The normal index channel
uses the `b3-prosaic` family; migrate with a fresh environment or image.
The old and new distributions share import paths. The active manifest remains
`dependencies/releases.json`; the immutable 0.2.0 baseline remains
`dependencies/releases-lab-0.2.0.json`. The active manifest contains actual
verified public URLs and has SHA256
`37a7b0dcf7bffa1c64481aafc7173e947c1e083616adcf50112e53022d589aca`.
Historical manifests and receipts are unchanged.

Use Python 3.12 and the hash-locked third-party dependencies in a fresh
environment. This public-manifest path does not require Actions artifact access:

```sh
python3.12 -m venv .venv-public
.venv-public/bin/python -m pip install --require-hashes -r dependencies/requirements.lock
.venv-public/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases.json
.venv-public/bin/python scripts/install_dependencies.py --manifest dependencies/releases.json
.venv-public/bin/python scripts/audit_install.py --manifest dependencies/releases.json
.venv-public/bin/python -m pip check
export PATH="$PWD/.venv-public/bin:$PATH"
```

With Docker running, build the immutable released-SDK consumer and run a required
owned stack cell:

```sh
.venv-public/bin/python scripts/build_consumer.py \
  --manifest dependencies/releases.json --dependency-mode released \
  --tag prosaic-integration-lab:dev
.venv-public/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases-lab-0.2.0.json
.venv-public/bin/python -c 'from lab_runner.legacy_upgrade import build_baseline; build_baseline()'
.venv-public/bin/python scripts/required_acceptance.py \
  --postgres-version 16 --export reports/required-pg16.json
```

Repeat with PostgreSQL 18 on the actual host architecture. The four-cell CI
matrix separately verifies both Linux architectures. The private owned outputs
remain under `.lab`; only the sanitized gate summary is suitable for sharing.
The [retained candidate recipe](../README.md#retained-candidate-recipe) remains
separate, with its original profile, manifest, cache and receipt lineage.

## Implemented application behavior

The service can admit generated graphs composed from approved specialists,
retain exact host bundles and expose owner-authorized catalogue, proposal,
native-run and human-resume routes. SDK admission, input snapshots and human
validation happen through public installed APIs. Host credentials, asset paths,
tool implementations and journal namespaces stay private. Composition, inline
instructions and tool use require separate current grants.

Schema v3 adds immutable owned proposals, native references and a fenced business
operation journal. Migration uses a separate authorized role. Recovery retains
original billing and bundle identity; an uncertain start or effect needs explicit
operator reconciliation. The native fixture tests also cover incurred usage,
provider/tool budgets, receipt adoption and independent SQL effect uniqueness.

The earlier ecosystem candidate source suite passed **522 tests**, locally and in each
native CI cell. The installed application and an exact committed source archive
each passed **153 focused tests** with the five original qualified SDK wheels.
Source/archive/wheel/installed parity covers 50 Python
modules, 78 public build inputs and the five original retained legacy assets.

That historical matrix ran **215 acceptance cases in each of four cells**, Linux
AMD64/ARM64 × PostgreSQL 16/18: **860 cases**, zero failures or skips, with all
**32 lane cleanup and payload/provenance gates verified**. Its eight lanes cover
audit, identity, ingress, Lago, native SQL persistence, native HTTP/effect
recovery, original-release upgrade and bounded operational qualification.
The original Lab 0.2.0 implementation generated five durable upgrade fixtures
per cell; all ten recovery assertions passed after explicit schema v2→v3 migration.
Earlier failed attempts are retained in the verification ledger. Local Docker
preflight timed out at its 15-second bound; the passing native evidence comes
from the hosted CI runners.

## Publication and deployment boundaries

The GitHub `pypi` environments and tag restrictions are configured. The five
scoped Trusted Publishers are registered with owner `B3Cognition`, workflow
`publish.yml` and environment `pypi`. Ordered publication completed for Core,
Runtime/recorder and Harness/store. The
[SDK package-channel guide](https://github.com/B3Cognition/prosaic/blob/codex/ecosystem-production/docs/package-index.md)
documents the staged publisher bootstrap and original-byte promotion checks.

The guarded Core promotion
[38063003741](https://github.com/B3Cognition/prosaic/actions/runs/38063003741)
passed all 15 qualification records on the original bytes, then PyPI refused
the token exchange with `invalid-publisher`: no publisher matched the expected
Core repository/workflow/environment claims. No package files were uploaded;
GitHub release was skipped. This historical failed attempt is preserved; the
successful publication runs above used the final patch sources and original bytes.

The paired SDKs were bootstrapped in stages because PyPI permits only one pending
entry per repository/workflow/environment tuple. The main Runtime/Harness
publisher conversion preceded adapter registration and guarded completion of
the original-byte promotion. The package-channel guide details partial-upload
verification and the complete-pair GitHub release gate.

The patch candidate Lab gate succeeded at its recorded source. Lab 0.3.0 then
adopted the verified public pins and passed its separate four-cell released-mode
gate at `59ea44b`. The remote annotated `v0.3.0` tag resolves to that exact
source. Actual public wheel/sdist, checksum and verification downloads match
the original release assets. Their identities and native receipts are recorded
in the [public adoption ledger](verification/public-release-adoption-2026-10-11.md).

Lab 0.4.0 has a separate tag and original wheel/sdist builds at `f47328d` with
the successful final matrix recorded above. This documentation follow-up records
that release; it does not rebuild its assets or move either Lab release tag.
The earlier `8f60c58` milestone measurements and local Qwen proof retain their
original sources and scope. See the
[release closure](verification/production-readiness-m1-m2-2026-10-11.md#lab-040-release-closure).

Synthetic fixture success does not certify a live provider, customer billing,
deployment identity/TLS, long soak capacity, HA or PITR. Those qualifications
require their explicit profiles, private deployment inputs and actual evidence.
