# Ecosystem production candidate verification

Checkpoint: 2026-10-10. The candidate implementation and required native
qualification have passed. Public package-index publication, ordinary index
installation and Lab 0.3.0 adoption remain pending. This ledger records the exact
qualified sources; a later documentation commit does not change their identity.

## Milestone delivery

| Area | Implemented and verified behavior |
| --- | --- |
| Core | Cooperative process locks, public validation/CLI, compatible canonical prose and read-only catalogue discovery. |
| Runtime | Bounded telemetry, invocation/provider/tool budgets, contextual tool authorization and fenced durable effect recovery. |
| Harness | Validated in-memory construction and generated-workflow admission, private host bindings, independent default-tier/inline/composition/tool policy, immutable bundles, input snapshots and structured human validation. |
| Distribution | Five consistently named `b3-prosaic` packages, compatible imports/commands, isolated source builds, original-byte promotion, metadata/license/ownership audits, platform and dependency-floor qualification. |
| Integration lab | Public SDK consumption, owned catalogue/proposal/native-run/resume routes, schema v3 migration, retained bundles, immutable proposals, application-owned PostgreSQL journal, bounded capacity/restore qualification and actual Lab 0.2.0 upgrades. |

Usage starts with [native workflows](../native-workflows.md),
[persistence and migration](../persistence.md),
[release gates](../release-gates.md) and [operational profiles](../qualification.md).
The [current status](../current-status.md) includes an executable candidate
installation/curation recipe and the publication order. The SDK factory and
package-channel guides live with their owning SDKs.

## Original qualified SDK bytes

| Repository | Exact source | Successful Publish SDK run | Qualification records |
| --- | --- | --- | --- |
| Core | `aad4bf45ae1c242f4451700ca59b27280010573a` | [38047286885](https://github.com/B3Cognition/prosaic/actions/runs/38047286885) | 15 |
| Runtime | `da3b43e12027b78d60b846c427021559b4927ba4` | [38054282584](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38054282584) | 24 |
| Harness | `5b1e2bc0f56041122014a70e5865ff925e6559ab` | [38055081837](https://github.com/B3Cognition/prosaic-harness/actions/runs/38055081837) | 18 |

| Distribution | Version | Original wheel SHA256 |
| --- | --- | --- |
| `b3-prosaic` | 0.4.0 | `120a956fd009ac7db7319a6a2493079441533818320d8adfdcba7b94b47be602` |
| `b3-prosaic-runtime` | 0.8.0 | `0b0373a3926615bdf28315615ffe30ec1a07a43176eae7997eca68a68e535d4e` |
| `b3-prosaic-runtime-postgres` | 0.2.0 | `b2a01e30f8567f4459a04edec0440cd8a884958a43fc3de5868060d2c78fb110` |
| `b3-prosaic-harness` | 0.7.0 | `24a559eb78b0433cd70e15ea0172fec4041b67a853869abba20ca387ffb82f90` |
| `b3-prosaic-harness-postgres` | 0.2.0 | `46ed101a95aab93d240a185e32f312d8d30cd69bc649b2f6104ed2b358152be4` |

All 57 SDK qualification records match the original wheel/sdist hashes and exact
source commits. Runtime's nested Core receipt and Harness's nested Core/Runtime
receipts match the selected upstream runs. Qualification includes Linux AMD64
and ARM64 with Python 3.11–3.13, Core Windows ownership checks, Runtime macOS,
and Runtime/Harness PostgreSQL 16/18 on both Linux architectures. Required Linux
Harness sandbox cases executed without skips.

A separate fresh Python 3.11 installation of all five original wheels passed
payload/RECORD/unique-import-owner audits, compatible dependency resolution,
`pip check`, public CLI and factory/human/reconstruction/tool smokes. Direct
dependency floors passed, including Runtime's Psycopg 3.2.1/libpq 16 floor and
Harness's Psycopg 3.2.3/libpq 17 floor. These local smokes used credential-free
loopback fixtures; native SQL/platform evidence comes from the SDK CI runs.
No qualified wheel was rebuilt for this closure.

## Lab native acceptance

[Run 38061354170](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38061354170)
succeeded at exact Lab source `0feb56b02f4c3dfb21c8fe7487bd1d3216e86dec`.
Each cell passed 522 unit/functional regressions, built its immutable consumer
and original Lab 0.2.0 baseline, and passed these exact acceptance collections:

| Lane | Cases per cell |
| --- | --- |
| audit | 88 |
| identity | 20 |
| ingress | 5 |
| Lago | 25 |
| native-persistence | 26 |
| native | 39 |
| legacy-upgrade | 10 |
| qualification | 2 |

All four cells passed **215 cases each, 860 total**, with zero failed/skipped
cases, successful process returns, and all **32 cleanup and installed-payload
provenance gates verified**. Every lane in a cell used the same immutable consumer
image and pinned PostgreSQL image. The candidate manifest SHA256 is
`e963b7a1e4b00194b8fdf6fbebb1d0dbcba659befe96a7144ebf204a608dfc1b`;
lineage SHA256 is `34b5769f7ae7ef5f8a620d99549c0a442226707c28df8c301359fa289cb0b721`.
The [sanitized JSON checkpoint](ecosystem-production-2026-10-10.json) records
the four original safe receipt hashes, artifact identities and consumer/baseline
image hashes. Private logs, configurations, tokens, raw JUnit capture and backup
data are excluded.

- [ARM64 PostgreSQL 16](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38061354170/job/114240101485)
- [ARM64 PostgreSQL 18](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38061354170/job/114240101314)
- [AMD64 PostgreSQL 16](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38061354170/job/114240101498)
- [AMD64 PostgreSQL 18](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38061354170/job/114240101490)

The SQL lane covers actual owned persistence, immutable grants/storage bounds,
concurrent migrations and reservations, all supported finite JSON inputs,
journal fencing and lost acknowledgements. Native HTTP cases exercise independently
granted specialists/tools, current authorization, retained references, validated
human responses, finite budgets and recoverable domain effects. The original
Lab 0.2.0 source `59752bef3e6b3ffde0ecbf38f34815d184043e20` and manifest
`f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472`
generated five historical durable fixtures per cell. Explicit schema v2→v3
migration and all ten legacy recovery assertions passed, preserving original
views, revisions, unknown accounting and effect/dispatch counts.

The exact candidate source also passed 522 local tests, 153 focused installed-app
checks and 153 checks from its immutable committed archive outside Git. Parity
covers 50 Python modules, 78 public build inputs and five byte-identical historical
assets. These are implementation checks, not a public Lab 0.3.0 release.

## Retained earlier attempts

The preceding failed runs remain historical evidence:

- [38055696518](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38055696518): installed Core CLI was absent from CI PATH; no native lanes ran.
- [38055931623](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38055931623): private delivery rejected new host binding keys before native/legacy startup.
- [38057437866](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38057437866): replacement-resource teardown inventory and recovery/accounting assertions failed.
- [38059429620](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38059429620): three remaining fixtures assumed incorrect inline-tool authority, label-only bundle identity and finite-budget unknown-usage recovery. This seven-lane run did not include the subsequently required SQL lane.

Corrections have behavioral regressions and preserved failed outputs. The final
matrix added the planned 26 SQL cases to the required contract, retained every
existing count and zero-skip/cleanup requirement, and used unchanged original SDK
bytes. Local Docker preflight remained unavailable at its 15-second bound;
remote native evidence is recorded separately.

## Remaining publication work

GitHub `pypi` environments restrict deployment to version tags. The authenticated
PyPI owner must verify or create the five pending trusted publishers listed in
the [package-channel guide](https://github.com/B3Cognition/prosaic/blob/codex/ecosystem-production/docs/package-index.md).
No public-index or stable-release publication has been verified at this checkpoint.

Once registration is present, promote these original qualified bytes in order:
Core 0.4.0; Runtime 0.8.0 and recorder 0.2.0; Harness 0.7.0 and store 0.2.0.
Verify complete index and GitHub artifact sets against the receipts, then adopt
verified public pins in Lab 0.3.0 and rerun all four eight-lane cells against the
published bytes. Current active/historical manifests and Lab 0.2.0 version are
preserved. The ordinary released-mode PR workflow depends on that adoption and
is not qualified by this explicit candidate dispatch; draft PRs remain open.

The bounded synthetic capacity/restore profile passed its required fixture
checks. Live provider capabilities, real customer billing, identity/TLS staging,
long soak, HA and PITR require separate deployment inputs and actual observations;
they are not certified by these fixtures.
