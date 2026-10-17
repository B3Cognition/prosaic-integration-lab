# Codex handoff

## Fresh balanced memory comparison complete — 2026-10-17

All12 fresh held-out samples settled with known usage under unchanged limits.
Smaller model off/on success is0/3 versus1/3; larger is3/3 versus3/3. The smaller
gain is confounded by quotation-based continuation admission, not demonstrated
reasoning improvement. All14 tools succeeded; three continuations were refused
by fixed planning bounds despite available outer-budget headroom. Read the
[audited comparison](verification/balanced-memory-live-2026-10-17.md).
Cumulative charge1442requests/588tools/1731251tokens; remaining33/16/245372.
Allseven historic unknown reservations remaincharged;34canonical ledgers preserved.
Next recommended milestone: provider-neutral adaptive continuation planning
under the same caps. Generic Runtime/Harness fixes are candidates for normal
release qualification; Lab memory/planning remains experimental. No push/release
was performed by this comparison.

## Provider-neutral tool outcomes and bounded recovery candidate — 2026-10-17

The next operational-hardening milestone is implemented in local Runtime
`0.9.7+tools.1`, Harness `0.9.1+tools.1` and Lab `0.5.1+tools.1` candidates.
[`dependencies/tool-outcome-candidate.json`](../dependencies/tool-outcome-candidate.json)
pins the exact SDK family; the released manifest is unchanged. Read the
[qualification and review record](verification/tool-outcomes-recovery-2026-10-17.md)
before another live run. Recovery is opt-in, provider-neutral and bounded by the
existing case limits. Historic tool errors remain unclassified. No live
inference, merge, push or publication is included in this milestone.

## Native tool and experimental memory release preparation — 2026-10-17

The active train adopts published Runtime 0.9.6 with Core 0.4.1, Runtime recorder 0.3.0, Harness 0.9.0 and Harness store 0.4.0. The previous context train is preserved in `dependencies/releases-lab-context-0.5.0.json`. Agent-quality and controlled retrieval memory examples are opt-in; memory remains experimental. Historical live findings retain their original candidate identity. See [the release ledger](verification/release-0.5.0-2026-10-17.md) for final qualification and publication.

## Published timeout patch adoption — 2026-10-14

The active manifest now pins published Runtime 0.9.3 and Harness 0.8.2, retaining
Core 0.4.1 and both PostgreSQL adapters at 0.3.0. Use `.venv-latest` for this
checkout's audited installed family; `.venv-published` preserves the earlier
demo environment. The full local suite passes 955 tests. Required conversation
acceptance now has 97 cases, adding real provider timeouts for ordinary and
interpretation turns with no redispatch on replica replay/recovery.

Read the [patch ledger](verification/conversation-timeout-patch-2026-10-14.md)
for exact publication, manifest hashes and acceptance results. Older checkpoints
retain their original versions and counts.

## Published SDK adoption — 2026-10-13

Runtime 0.9.0/recorder 0.3.0 and Harness 0.8.0/store 0.3.0 are now published.
The active release manifest selects their exact verified PyPI wheels alongside
unchanged Core 0.4.1. The former patch manifest is preserved in
`dependencies/releases-lab-0.4.0.json`. Ordinary released acceptance now selects
the conversation lane without candidate flags. Start with the README's assistant,
workflow and approved-conversation recipes, and read the separate
[fresh adoption ledger](verification/published-conversation-adoption-2026-10-13.md).
Lab release and hosted-provider qualification are separate remaining work.
The checkpoints below preserve their original publication state and evidence.

## Conversation adoption checkpoint — 2026-10-12

Lab target 0.5.0 implements authenticated bounded conversations, a fixed host-only
selection/review workflow, actual diagnostic conformance, and a ninth required
acceptance lane. Read [the conversation guide](conversations.md) and
[its qualification evidence](verification/conversation-adoption-2026-10-11.md#final-source-platform-qualification--2026-10-12).
Exact source `34f291e8c7f7dd3809767c2fbf518b55e50204d6` passed
[run 38212165309](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38212165309):
325 required cases per Linux AMD64/ARM64 × PostgreSQL 16/18 cell, plus 95
extracted-sdist conversation checks on ARM64/16. All 1,395 acceptance executions
passed with zero skips and verified cleanup, including 475 conversation checks
and both documented candidate demos per cell. Closed capacity diagnostics
reconcile 18 requests/ledger calls with p95 0.2085–0.2469 seconds.

The final local suite passed 943 candidate tests and 921 applicable published
baseline tests with zero skips; only three functional files requiring the absent
conversation API are excluded from the old baseline. The earlier failed
`0f7791c` capacity qualification and its unidentified cause remain recorded;
the earlier `018425b` commit improved diagnostic reporting without claiming a
capacity bug fix. Subsequent CLI, interpreter-format and native-call clarifications
retain their separate historical results in the live ledger.
[Actual local Qwen evidence](verification/local-conversation-2026-10-12.md)
records the original blocked 7B native-tool run and subsequent successful closure
at `34f291e`: explicit strong effecter binding, 943 candidate/921 applicable
published-baseline tests, a complete live journey plus two independent workflow
sessions, quoted approval denied, and duplicate approval replay with zero calls.
All earlier failed allowances are preserved; the maintainer authorized further
bounded testing and fixes. The final four-cell run qualifies that exact executable
source; this later documentation commit records its result. Runtime/Harness
publication, Lab release, ordinary public-index adoption and hosted qualification
remain pending. Published and
historical manifests below are unchanged.

The subsequent main-branch merge also includes the previously verified prepared-
context handoff, described in the [context ledger](verification/context-handoff-2026-10-12.md#integration-with-the-conversation-candidate).
The combined source passed 948 candidate and 926 applicable published-baseline
tests. Its required contract has 54 native plus 95 conversation cases: 326 per
candidate cell. This newer source needs its own platform receipts; the exact
`34f291e` results above retain their original identity. Harness ordinary CI now
curates the original qualified Core/Runtime artifacts while Runtime 0.9.0 is
unpublished, preserving sandbox and database requirements. Version bumps already
select Runtime 0.9.0/recorder 0.3.0, Harness 0.8.0/store 0.3.0 and Lab 0.5.0.

Checkpoint: 2026-10-09, first working synthetic consumer on a local feature branch.

## Release checkpoint

For the current published ecosystem and Lab 0.4.0 release at `f47328d`, read
[the current delivery status](current-status.md) and
[the release closure](verification/production-readiness-m1-m2-2026-10-11.md#lab-040-release-closure).
The historical Lab 0.3.0 release remains recorded in
[the public adoption ledger](verification/public-release-adoption-2026-10-11.md).
The checkpoint and release ledger below retain their historical versions and
evidence.

The maintainer subsequently authorized committing all repository changes and
publishing new releases. The earlier no-publication statements below describe
their historical tasks. Read [the historical release ledger](verification/release-train-2026-10-09.md)
for the earlier version pins, verification and remote publication status. All Lago
work is now committed; earlier shared-file staging constraints are historical.

## Lago extension checkpoint

The approved Lago design/plan adds `lab_runner test --mode lago`. A separate
application-owned outbox exports public Runtime evidence to digest-pinned local
Lago 1.55.0, with frozen attribution, unknown-cache exclusions, duplicate recovery,
fenced leases, open-period gating and independent fixture-charge reconciliation.
Prosaic core, Runtime and Harness sources remain unchanged.

The required lane passed 25 cases on both PostgreSQL 16 and 18 on Docker Desktop
Linux/arm64, zero skips and verified cleanup. Existing deterministic (21) and
recovery (27) lanes passed on 16. Read `verification/lago-progress.md` for receipts,
review findings/fixes, setup failures and the exact verification checkpoint.
The tests use synthetic inference and separate direct public-ledger fixtures;
no payment collection, customer invoicing or production billing certification.

Shared runner files are also being changed by other authorized lab work. Preserve
those changes; do not stage whole files indiscriminately or assume the latest
consumer image tag equals a recorded immutable image ID.

## Completed

- Maintainer approved the separate integration-lab design.
- Public repository and Apache-2.0 license created.
- Approved design, README, agent instructions and remaining-work checklist saved.
- [Tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1)
  published with staged work and acceptance requirements.
- No existing Prosaic/Harness/Runtime library sources changed for this handoff.

## Implementation checkpoint

Native implementation was authorized by the maintainer's “proceed”. Branch
`codex/integration-lab` contains the consumer image, wheel provenance/audit,
owned runner, explicit grants, owner-only HTTP APIs, zero-call approval and
synthetic inference/accounting. PostgreSQL 16 and 18 acceptance ran on Docker
Desktop Linux/arm64 with verified cleanup. Read `verification/progress.md` for
exact receipts and remaining coverage. No push or release is implied.

The optional host-side local model reads `~/.omlx_token`; its 7B Qwen Coder smoke
succeeded and reported 85 tokens. No cloud/TokenProxy model calls were made.

## Historic initial handoff

At the initial documentation-only handoff, no Python application, dependency lock, image, PostgreSQL fixture, workflow asset,
model stub, test runner, load balancer or CI job exists yet. No container or model
was started. No acceptance test, architecture matrix or live endpoint was run.
Commands in the design are target interfaces, not commands available today.

## Initial next action (superseded)

Read the [approved design](superpowers/specs/2026-10-09-prosaic-integration-lab-design.md)
and [tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1).
Review the [written implementation plan](superpowers/plans/2026-10-09-prosaic-integration-lab.md)
and its execution ledger. The plan was prepared and approved in this checkout
on 2026-10-09. Native execution starts with released-dependency provenance and
exact-owned provisioning. No paid calls are needed for synthetic milestones.

Do not re-request approval of the already approved project direction unless a
material change is needed. The written implementation plan is now approved.

Recommended milestone order:

1. Clean released-package consumer image and exact-owned stack lifecycle.
2. Trusted identity, durable ownership/idempotency and filtered HTTP endpoints.
3. Zero-model-call cross-replica workflow approval.
4. Synthetic inference, public SDK accounting and multiuser acceptance.
5. Fault-gated recovery, overload, accounting failures and repeatability.
6. Non-sticky load balancing and PostgreSQL 16/18 CI on Linux/arm64 and amd64.
7. Explicit live TokenProxy mode and its separate evidence/limitations.

Each milestone needs independently executable tests and a commit with evidence.
Pay particular attention to app ownership reservation versus Harness creation:
they are not one transaction. Never reinterpret a missing response/checkpoint
as permission to redispatch a possibly completed request.

## Released dependency baseline

Initial baseline verified from release metadata on 2026-10-09:

| Distribution | Version | Release source commit |
| --- | --- | --- |
| prosaic-harness | 0.6.0 | 2bd14fd8aa17f30c957ff29f886ffd16b2af52ca |
| prosaic-harness-postgres | 0.1.0 | same Harness source commit |
| prosaic-runtime | 0.6.0 | b13a62eac955b19b13fe2c9dc646a188069f72f2 |
| prosaic-runtime-postgres | 0.1.0 | same Runtime source commit |

- [Harness v0.6.0 assets](https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.6.0)
- [Runtime v0.6.0 assets](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.6.0)

Both releases include core/adapter wheels, source archives and
`SHA256SUMS-0.6.0.txt`. Download the artifacts, verify their checksums and save a
dependency manifest during implementation. Assets have not been downloaded or
checksum-verified by this new repository's handoff task. Install each core
before its adapter and lock the complete service/test dependency graph.

Harness 0.6.0 pins Runtime 0.6.0, which installs Prosaic transitively. Review the
resolved dependency provenance rather than adding a second interpreter or an
editable sibling dependency.

## Operator references

- [Harness PostgreSQL provisioning/grants](https://github.com/B3Cognition/prosaic-harness/blob/v0.6.0/adapters/postgres/README.md)
- [Harness accounting attribution/recovery](https://github.com/B3Cognition/prosaic-harness/blob/v0.6.0/docs/accounting.md)
- [Runtime PostgreSQL recorder contract](https://github.com/B3Cognition/prosaic-runtime/blob/v0.6.0/adapters/postgres/README.md)
- [Runtime measurement and coverage](https://github.com/B3Cognition/prosaic-runtime/blob/v0.6.0/docs/accounting.md)

Read these before defining roles or interpreting unknown evidence. Shared
PostgreSQL does not make workflow and accounting writes atomic. Namespaces are
not authorization, leases are not external-effect idempotency, and estimates
are not customer charges.

## Historic initial verification record

At handoff, verification is limited to documentation/file consistency, Git
publication and public repository/issue visibility. Implementation-specific
test results must be recorded by the next session; do not inherit upstream
test counts as proof that this service works.
