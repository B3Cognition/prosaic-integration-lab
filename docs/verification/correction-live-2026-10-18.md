# Frozen bounded correction comparison — partial, 2026-10-18

The run stopped safely after **6 of16samples**:5known and1unknown. **No pair
qualified for matched inference**, so critic benefit is unmeasured. The one
critic that ran gave an incomplete warning and its correction still failed.
A separate offline fault reproduction found a provider-neutral Lab guard gap
that blocks a stable release. [Audited data](data/correction-live-2026-10-18.json),
[preparation](correction-live-preparation-2026-10-18.md).

## Frozen experiment and stop

Four fresh opaque cases crossed both models and both arms, counterbalancing
arm/model order. Each arm used an independent worker with identical task,
contracts and settings. Matching required the same actual initial draft and
fetched evidence. No prompts, models, SDKs, executable Lab code, per-case limits
or schedule changed after approval. Installed Lab0.5.1+correction.2, Runtime
0.9.8+diagnostics.1, Harness0.9.4 and previously qualified counters were frozen.
Binding `c6eb88f5bc6128992ebec81bcc4de92bada8c9c9674edac2ffd6effdfa8b08dd`.

The larger model's reject-case no-critic worker received an HTTP200
`providerError` envelope,221bytes, with missing usage. Its result failed with
`usage_unknown` before lookup or a usable artifact. Body hash
`0b90c449e8bcb12a33a4169c34f362a1348e3f4371f9e971a7246c5805e7b67c`.
Retained diagnostics establish the error envelope and missing usage, not the
underlying server cause. This was not recorded as a timeout. The frozen rule
stopped all further dispatch;10samples, including every missing/conflict case,
never ran. The unknown sample was not retried or replaced.

## What the models did

| Executed group | Outcome |
| --- | --- |
| Smaller, approve, no critic | Worker had facts/citations flaws; correction unchanged and incorrect.3requests,5986reported tokens. |
| Smaller, approve, critic | Worker had facts/citations flaws; critic named only facts; correction changed but remained incorrect.4requests,7696reported tokens. |
| Larger, approve, both arms | Both workers reached512output tokens with `finish_reason=length`; no trusted artifact, lookup or critic.1request/2151tokens each. |
| Larger, reject, critic arm | Worker was correct and accepted directly; critic/corrector skipped.2requests,3799tokens. This success cannot be credited to a critic. |
| Larger, reject, no-critic arm | Provider error with missing usage; full reservation retained. |

Smaller workers omitted required output facts/citations despite having a ready
source snapshot. The critic correctly escalated but identified only1of2wrong
field categories. Neither of the two actual corrections repaired the answer.
Larger-model critic and corrector effectiveness remain unmeasured: neither role
was called. Its single successful worker also rules out a blanket incapability
claim under these limits. Groups are tiny and uneven; do not rank models from
these counts.

All three executed arm pairs are unusable for matched benefit inference. The
smaller pair had the same evidence but different initial citation values, hence
different `initialDraftDigest`. Both larger pairs contain an unusable initial
artifact, and one includes unknown accounting. The mismatch was not
canonicalized away or retried. No acceptance/artifact gain or marginal paired
cost is claimed. The one actual critic cost1request/1704reported tokens; neither
path produced a correct smaller-model final artifact. The total arm difference
1710tokens is descriptive, not a matched causal critic-cost estimate.

Both paths already received complete verified host field diagnostics. The
critic's filtered hints added no new verified evidence; this task does not
measure the value of a critic on open-ended work without a deterministic
field oracle. Keep the critic optional; these results do not justify enabling
it by default. Memory was not tested here and remains experimental.

## Accounting, audit and preserved limits

Observed12provider calls. Five known samples reported11requests/3tools/
21783tokens. The uncertain sample retains its full4requests/2tools/8192tokens,
so the study is **charged15requests/5tools/29975tokens**; that token figure is
not measured actual usage for the failed call. Cumulative charged usage is
**1509/610/1835168** against approved **1558/637/1976623**, leaving49requests/
27tools/141455tokens. All8old unknowns stay charged; there are now9total.

Caps stayed4requests/2tools/8192reported tokens/600seconds/output512 per arm.
No observed input/output bound breach or total-token overrun occurred in the
known live observations; the failed call's missing usage is not certified.
The frozen independent audit reconciled receipts, lookup scope, response
diagnostics, recorded observations, claimed counts and public-rule truth.
Copied-state recovery denied network access and made0additional provider calls.
All9853frozen guards and38old ledger hashes were reverified. Offline26hosttests,
16actual-counter scripted lanes and the prior candidate's1581source tests
remain their original qualified evidence; the live run adds no SDK/Core change.

## New offline release blocker

Real responses retained numeric token totals while usage normalization marked
their extra format fields `unsupported`. The Lab correction observer checks
component bounds only for status `reported`; its scorer also handles numeric
unsupported observations. That difference warranted a separate synthetic test.

The isolated loopback test supplied input101against a quoted100bound with an
unknown usage extension. The observer latched no breach, allowed a second
request and completed the workflow. Only post-run scoring then raised
`changed component accounting`. Two synthetic requests, **zero live requests**;
the original benchmark and installed candidate bytes stayed unchanged.
Proof: `/private/tmp/prosaic-correction-unsupported-proof-20261018/report.json`.

This is a **known Lab guard defect**, not evidence of a live overrun or a
model-specific fix. Before promoting the blueprint, unify token-count
completeness, component enforcement and reporting independently of usage-format
or pricing support. Qualify unsupported-but-numeric, missing, inconsistent and
untrusted usage on both wire formats, with denial before continuation. Preserve
unsupported billing provenance; never convert missing usage into known zero.
No production fix or retest of the frozen live study is included here.

`roleCosts.observedTokens` remains unavailable for unsupported-format records;
the separate `receiptedRoleUsage` projection preserves their numeric reported
totals. Count completeness and unsupported billing/format provenance must be
handled separately in the follow-up fix. No unsupported record is relabeled
as a fully supported billing observation.

## Push, release and next work

Push the reviewed Lab work for review, clearly experimental with this known
blocker. It contains reusable contracts, role qualification, evidence diagnostics,
bounded correction and honest comparison tools worth retaining. Do not publish
a stable Lab release yet. First fix and qualify the guard gap, then qualify a
clean consumer install against public immutable SDK artifacts. The active
released manifest still pins Runtime0.9.6/Harness0.9.0, while this experiment
needs Runtime0.9.8+diagnostics.1/Harness0.9.4. Latest published releases checked:
[Lab0.5.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.5.0),
[Runtime0.9.7](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.9.7),
[Harness0.9.4](https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.9.4).
The Runtime diagnostics candidate still needs its ordinary platform/database
release acceptance. No new Core/Harness release is required by this experiment.
Keep memory/correction opt-in and experimental; good scores from these two
models are not a prerequisite for releasing correctly qualified framework APIs.

Move on from critic prompt tuning. Close the generic guard defect offline first;
then the next development milestone should be **durable failure isolation and
explicit recovery**: persist a failure handoff with provenance, retain unknown
reservations, prohibit blind retries, and require an explicit policy decision
before independent work can resume. Keep current limits. The present frozen
stop rule must not be relaxed retroactively. This targets operational hardening
in the [original roadmap](https://www.kdnuggets.com/the-roadmap-to-mastering-agentic-ai-systems-in-2026).
Effectful-tool approval/sandboxing and broader provider qualification follow.
Another live critic comparison should wait for a separately qualified protocol
that can establish identical provenance-bound starting drafts; keep unqualified
roles out of production. No new model tuning is proposed.

Fresh host review scope decisions remain explicit: live quality was assessed
only from these observations; server identity was not attested beyond frozen
profile/asset provenance; final freeze was independently regenerated; prior
SDK acceptance is not exhaustive production certification. Overreading those
boundaries risks false benefit, counter-provenance or release claims. No deferred
review minors. Nothing was pushed or published by this task.

Preserved942files, including all live/offline evidence, the original frozen
host/review,6network-denied recovery copies, the preparation archive and new
synthetic counterexample. Canonical directory `bounded-correction-live-20261018`
adds exactly one live ledger;39canonical ledgers now retain9unknowns. Archive
`prosaic-correction-live-evidence-20261018.tar.gz`, SHA256
`433dad09da08f53c5717a15245b93d7a4141ead392b0c0374fb1ea96a4bcfe89`.
Closing verification checks all preserved file hashes, public projections,
frozen9853guards and38historic ledgers with sockets denied. Frozen operational
entry points are closed on their38-ledger baseline and must not be reused.
