# Codex handoff

## Direct worker/critic offline qualification — 2026-10-18

Opt-in Lab 0.5.1+direct.2 adds explicit model-visible JSON contracts, host-prepared
assignments and invocation-scoped host evidence for the critic. Worker-only,
critic-only controls and full handoffs skip the model planner.
[Guide](direct-handoffs.md), [qualification](verification/direct-handoffs-2026-10-18.md).
Final: 1,478 source tests, 76 installed both-wire scenarios, 36 unchanged-counter
offline trajectories. One fresh review; three material findings fixed with
RED→GREEN regressions. Largest quoted path: 5,287 tokens. Zero live requests.
Prior 2,596 files / 37 ledgers / eight unknown reservations verified unchanged.
Ceilings 1,500 requests / 617 tools / 1,976,623 tokens; charged usage
1,476 / 601 / 1,776,439. Per-case four / two / 8,192 / 600 seconds / output 512.
No push, release, SDK source change or memory rollout. Real-model contract
compliance and critic benefit remain unmeasured. Next: a small frozen direct-role
live study with full reservations under current limits.
Executable source 7c77df8; candidate environment
`/private/tmp/prosaic-direct-final-env/bin/python`; results
`/private/tmp/prosaic-direct-final-study-20261018`. Previous live environment and
initial candidate/evidence remain intact.

## Eight-sample real-model handoff evaluation complete — 2026-10-18

The [live result](verification/real-handoffs-live-2026-10-18.md) ran all8frozen
samples, four per model, under unchanged caps. All stopped at planner: smaller
4/4schema descriptions instead of values; larger4/4incomplete JSON at512output
tokens. Worker/tool/critic reached0; critic benefit unmeasurable, not negative
efficacy evidence. No new unknown, overrun, timeout or counter violation.
Study8requests/0tools/7268tokens; cumulative1476/601/1776439 versus approved
1500/617/1976623, remaining24/16/200184;8old unknown reservations retained.
Auditor reconciles all receipts/observations and copied-state recovery with
network denied. No model/prompt/graph changes or extra probes during the study.
Next: provider-neutral model-visible output contracts, deterministic host-owned
assignment preparation, and direct worker/critic qualification before another
fresh live evaluation. Memory remains experimental; no push/release.
Preserved450new files;37canonical ledgers,36prior hashes unchanged. Latest ledger
SHA256b87e25f97d522d3a89fb2dd953cc64ee09813d26dcbfc53f3ded9606f31aa17e.
Closed operators expect their original36-ledger baseline and cannot be reused
for a new run; create a fresh study root using the current37-ledger baseline.

## Real-model handoff evaluation frozen; allowance pending — 2026-10-18

[Prepared study](verification/real-handoffs-2026-10-18.md) uses local experimental
Lab0.5.1+handoffs.4, exact sourcefef4182. Full1388tests and15installed regressions
pass;8fixture trajectories use actual qualified counters,4reporting/interruption
phases pass. All3Important review findings fixed; one one-use-audit-path minor
deferred. No live requests. Graph/prose/models/per-case caps unchanged; memory off.
Bindingcd6988b2f6f89197ed25a4a0f731dc657a257c96a4caee2692137374df78eb5d
freezes4fresh cases×2models and3155guard files. Full reservation32requests/16tools/
65536tokens needs25requests/13tools beyond current headroom; token ceiling stays.
Question sent to user; no approval yet. Do not create allowance-approval.json or
dispatch until explicit approval arrives. Cumulative charge1468/601/1769171,
ceilings1475/604/1976623,8unknown retained. Requested new ceilings1500/617/1976623.
Private host operators `/private/tmp/prosaic-real-handoff-{common,live,audit,analyze}.py`,
installed environment `/private/tmp/prosaic-handoff-real-env/bin/python`, root
`/private/tmp/prosaic-real-handoff-study-20261018`. Preserve all prior evidence.

## Offline typed handoffs qualified — 2026-10-18

Lab0.5.1+handoffs.2 adds experimental request-bound planner/worker/critic
contracts and full-trajectory scoring using the same installed SDK candidate
family. [Qualification](verification/typed-handoffs-2026-10-18.md):1373source tests,
40focused regressions,30installed both-wire scenarios and3review regressions pass.
Both independent Important reporting findings closed with RED/GREEN tests;
no deferred minors. Missing/unread/conflicting evidence and disagreement cannot
approve; human review offers stop only. Four-request cap permits no extra repair.
Saved final critic receipt adopts without calls; missing receipt blocks;
earlier interruption is inspection-only. Exact source dc69d1f and wheel audited.
No live calls, SDK changes, push or release. Memory remains experimental with no
new efficacy claim. All1902prior evidence files and36ledgers verify; charge still
1468/601/1769171 versus1475/604/1976623,8unknown retained. Next: frozen real-model
handoff evaluation once its full reservation fits authorized remaining allowance;
full four-sample comparison cannot fit7requests/3tools. Prior checkpoints retained.

## Fresh four-sample missing-evidence comparison complete — 2026-10-18

The [audited held-out comparison](verification/missing-evidence-memory-live-2026-10-18.md)
completed all four samples with known usage under unchanged limits. Both enabled
arms actually recalled relevant history. Smaller off/on failed both after the
permitted correction; fact/citation fields were correct but decision remained
approve despite missing-authority feedback. Larger off/on passed first attempt.
No observed memory benefit; recall added608/221tokens without fewer requests or
tools. All6tools succeeded, no continuation refused, one quote overage correctly
admitted by shared budgeting. New diagnostics show message/unsupported usage
details; numerical totals reconcile, no pricing/cost qualification claimed.
Cumulative1468requests/601tools/1769171tokens; remaining7/3/207452. Eight unknown
reservations and35previous ledgers unchanged;36thledger appended,178new evidence
files preserved. No product/model/default changes, push or release. Ready for
offline provider-neutral typed multi-agent handoff/trajectory qualification;
memory remains experimental. Another full4sample study cannot fit remaining
request/tool reservations. Prior checkpoints below retain original state.

## Response diagnostics qualified offline — 2026-10-18

Runtime0.9.8+diagnostics.1 and Lab0.5.1+diagnostics.1 are local unreleased
candidates. The [qualification ledger](verification/response-faults-2026-10-18.md)
records portable response/usage classifications, sticky contradictory-error
fencing, strict bounded SSE UTF8 and preserved receipt diagnostics. Harness
requires no change. Runtime1345passed/2documented skips; Lab1333passed;
installed57checks,36fault/replay,14continuation and10legacy scenarios pass.
All five independent review findings closed. Exact candidate payloads audited;
active releases and prior manifests/evidence unchanged. No live inference,
push or publication. All35live ledgers still charge1456requests/595tools/
1752686tokens, eight unknown reservations retained; remaining19/9/223937.
Ready for a fresh bounded live comparison that fits full reservations, not a
memory efficacy or live-provider certification claim. Eight full samples do
not fit the current remaining request/tool allowance. Preserve old checkpoints.

## Strict validation fixed; fresh comparison stopped safely — 2026-10-17

Lab0.5.1+continuation.2 fixes derived integer-field validation in both plan
versions. Source b0072fa: full1333passed, installed four regressions,
14both-wire continuation and10legacy scenarios; exact-source payloads audited.
The [fresh eight-sample study](verification/continuation-memory-live-2026-10-17.md)
completed four samples, then stopped on larger-model missing/on unknown usage.
Three samples remain unexecuted; no retry or forgiveness. Approval pairs pass
both arms; smaller memory/on saves one correction, larger has no recall exposure.
Memory benefit remains unproven. Charge1456requests/595tools/1752686tokens;
remaining19/9/223937, eight unknown reservations retained across35ledgers.
Next: provider-neutral response/usage failure diagnostics and synthetic fault
qualification before another live efficacy run. Lab remains experimental;
no new push/release. Prior checkpoints below retain their original state.

## SDK releases and experimental continuation budgeting complete — 2026-10-17

Runtime0.9.7 and Harness0.9.4 are merged and publicly released, with downloaded
bytes matching their exact-source qualification receipts. Core/adapters unchanged.
Lab0.5.1+continuation.1 remains an unreleased local experimental candidate.
Its explicit manifest pins the new public SDKs; the active release manifest and
historic candidates/evidence remain unchanged. Opt-in version2 uses quotation for
context planning and public Runtime shared-budget admission for actual native
continuations; version1 stays default and current caps are unchanged.

Read the [release/qualification ledger](verification/continuation-budgeting-2026-10-17.md)
and [usage contract](continuation-budgeting.md). Full Lab1329passed; final focused35;
installed and network-none Linux ARM6414both-wire scenarios plus10legacy replay
scenarios per platform. Independent review: no blockers, one derived-count type
validation minor deferred. No new live inference. Charge1442/588/1731251 versus
ceilings1475/604/1976623, seven old unknown reservations retained;34ledger and
428prior evidence hashes preserved. Next: frozen held-out validation that fits
remaining33requests/16tools/245372tokens. Memory efficacy remains unproven.

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
