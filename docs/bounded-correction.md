# Provider-neutral bounded correction

**Experimental.** The fresh live evaluation stopped on unknown usage and found
a separate offline guard defect for unsupported usage formats with numeric totals.
The v2 candidate fixes the guard; see the
[offline qualification](verification/usage-guard-2026-10-18.md).
[Partial live results and release gates](verification/correction-live-2026-10-18.md)
remain applicable; model benefit and production readiness are unproven.

This opt-in Integration Lab blueprint shows how a consumer can correct one
well-formed draft using verified field diagnostics, then measure the extra value
of a critic against a no-critic baseline. It uses public Runtime and Harness APIs.
It does not certify a model or change SDK execution policy.

The reusable helpers in `lab_runner.bounded_correction` prepare closed feedback
and compare host-scored results. The separate rollout example in
`lab_runner.handoffs.correction` supplies a domain policy, record grants, workflow
and evaluator. Consumers replace those domain parts with their own evidence and
acceptance rules; the generic helpers contain no rollout or provider logic.

## Workflow and authority

`execute_correction(case, config=..., output=..., sample_id=..., arm=...)` runs
either `no-critic` or `critic`. A worker fetches its granted records once. A
correct draft goes directly to the host gate. A wrong, well-formed draft gets
one correction request; the critic arm first asks a separate critic. Invalid
JSON or an invalid assignment binding stops instead of entering correction.

Both arms receive identical host field diagnostics and the same fetched records.
`correction_feedback` binds assignment, draft and evidence digests and permits
only closed field diagnostics with evidence references. It excludes expected
answer values. Critic suggestions survive only when they name fields already
verified as wrong by the host. Raw critique, arbitrary validation prose and
hidden answer keys never enter the corrector packet. The critic cannot grant
records, authorize acceptance or replace host verification.

The corrector returns a complete artifact, has no tools and gets no new lookup.
The host rechecks all fields against the public task and scoped records,
including fields not mentioned by the critic. A correction can introduce new
errors; `score_correction` reports those separately from resolved errors.
Truthful missing-evidence output can be artifact-correct while still requiring
host review. Artifact correctness and task acceptance are separate measures.

## Limits and accounting

Each arm retains the existing limits: **4 provider requests, 2 tool calls,
8,192 reported tokens, 600 seconds and 512 output tokens per response**. One
outer public Runtime budget covers the entire arm. Critic and corrector each
also have a nested one-request, zero-tool budget. These caps debit the enclosing
budget; they never replenish it. There is at most one correction and no retry
loop. Unknown usage, failed admission or a component token overrun stops work.

The v2 policy interprets count completeness separately from pricing support.
Normalized `reported` and `unsupported` observations both enforce input/output
bounds when all three counts are consistent nonnegative signed 64-bit integers.
Their raw status remains unchanged: known counts do not imply known pricing.
Missing, partial, contradictory or untrusted counts latch `usageUnavailable`,
stop continuation and acceptance, and remain unknown in role summaries.
Complete unsupported counts remain visible in role costs. The scorer reconstructs
the same checks. Policy v2 cannot be paired with v1; recover historical v1 runs
using their original pinned environment rather than migrating saved evidence.

Outside the explicitly named synthetic loopback fixture, execution requires a
matching qualified token-counter registration. That registration is not live
consent or a durable allowance. Before live use, consumers must independently
qualify worker, critic and corrector roles with their own model/configuration,
native request framing and counter assets, then authorize and reserve the full
per-arm allowance in their durable ledger. A pair requires **two** independent
sample reservations, including all retry headroom. Preserve unknown reservations
and honest overruns. See [role qualification](role-qualification.md).

`recover_correction` reads persisted SDK state without driving the workflow.
It never resumes a model node. Duplicate execution of a claimed sample is
refused. Diagnostics distinguish receipted counts, observed calls and unresolved
intents. An observed but unreceipted response keeps its known usage visible;
an unresolved intent does not become a fabricated request count or zero token
usage. Corrector reachability includes receipts, observations and unresolved
intents. Interrupted and unresolved execution have separate effects; unusable
final artifacts have unavailable field deltas and receive no verified repair
credit. Incomplete accounting prevents a known cost comparison. A consumer must
keep the full unknown reservation charged and reconcile it externally before
choosing any new sample. Persisted evidence is host-owned, not an untrusted input
that these helpers authenticate cryptographically.

## Matched no-critic comparison

Score each arm with `score_correction(case, evidence)`, then call
`compare_corrections(baseline_score, critic_score)`. It checks the exact public
task, profile, worker/corrector contracts, initial draft, initial correctness,
fetched evidence, host diagnostics, counter policy and serialized limits.
Different starting points yield an unmatched result without an answer or cost
delta. Unknown usage likewise cannot produce a known comparison.

Both workers currently execute independently. Real models can produce different
drafts or fetched evidence, so a pair may be unmatched. Do not pool unmatched
runs, fork active Harness state or treat repeated attempts as free. A future
consumer-controlled seed-draft adapter would need its own explicit provenance
and qualification. Keep evaluation case identifiers opaque and expected answers
outside transmitted requests. This blueprint's named scenario identifiers are
only scripted plumbing fixtures.

Matched, fully accounted runs report acceptance and artifact deltas plus extra
requests, tools and tokens. These are measurements of those runs, not causal
proof or a recommendation to enable a critic. Include critic failures and
regressing corrections in consumer studies; do not select only repaired cases.

## Offline qualification

Run the installed package smoke with its source directory excluded from import
resolution:

```text
python -I scripts/bounded_correction_smoke.py --source-root REPO \
  --evidence-dir PRIVATE_STUDY/lanes --output PRIVATE_STUDY/result.json
python -I scripts/usage_guard_smoke.py --source-root REPO \
  --evidence-dir PRIVATE_STUDY/usage --output PRIVATE_STUDY/usage.json
```

Use a new private study directory. The fixture independently specifies both
OpenAI-compatible and Anthropic wire contracts, validates transmitted feedback,
and scripts correct, incorrect, missing/unread evidence, misleading/partial
critic, ignored/regressing corrections, malformed critic, unknown usage,
unexpected tools and admission breaches. Recovery is checked with network
access denied. Unit tests also use another consumer domain.

This proof qualifies bounded control flow and evidence reporting offline. It
uses synthetic responses and synthetic token units. It establishes no live
model quality, counter accuracy, memory benefit or critic benefit. SDKs, existing
experiments and historical allowances remain unchanged. The blueprint and Lab
memory remain experimental; no live dispatch is part of this milestone.
