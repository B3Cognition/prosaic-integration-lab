# Prepared small answer-span comparison

This is a frozen diagnostic study, prepared without model calls. It does not
enable memory or SUE, retrieve new context, regenerate answers or repair them.
The prepared private packets are separate from public CI fixtures and artifacts.

## Fixed inputs and denominators

Reuse the controlled comparison's six questions: `q006`, `q022`, `q039`, `q064`,
`q095`, `q098`. Retain its file-search (`manual`) and expanded Castle (`expanded`)
contexts and its saved `old`, `minimal`, `current` author profiles.

The original schedule contains 108 slots: 90 structurally accepted originals
and 18 rejected outputs. All 108 retain their original status and provenance.
Rejected originals remain unauditable; they are neither repaired nor backfilled
and stay in the original answer-quality denominator.

Exact frozen question, answer, source and trusted-scope bindings identify 30
unique valid original audit packets. Preserve the 90-to-30 alias mapping; identical
draft aliases are not independent observations. Deduplication changes execution
cost, never the original denominator or scope/provenance checks.

Add 16 newly frozen controls in eight correct/faulty pairs:

- An omitted resume condition, even when the attached source quote contains it.
- Reversed negation about retrying an uncertain invocation.
- A correct fact attached to the wrong selected citation.
- A supported sentence with an unsupported additional clause.
- Correct scoped abstention versus unsupported global absence.
- Explicit conflicting notes versus an invented resolution.
- Correct versus swapped artifact-to-digest associations.
- Source instructions that attempt to change facts or claim host approval.

Controls use opaque packet identifiers. Expected outcomes and fault categories
are stored separately from model views. They are matched constructed controls,
not independent real-world questions or a population-quality sample.

## Predeclared execution

There is one audit repeat per unique packet: **46 physical audits**, with a fixed
order seed of `20261031`. The original 108 slots and the 16 controls remain
separately reportable. No new author generations or SUE calls are scheduled.

| Boundary | Maximum |
|---|---:|
| Separate serving-generation preflight | 1 request, 4096 reported tokens, 128 output tokens, 120 seconds |
| Each audit | 2 requests, 65536 reported tokens reserved, 270 seconds |
| Each audit stage | 120 seconds, 4096 output tokens, 16384 raw/canonical output bytes |
| Frozen packet | 262144 UTF-8 bytes |
| Entire preflight plus study | **93 requests, 3,018,752 reported tokens, 12,540 seconds** |
| Tools / retries / automatic repair | **0 / 0 / 0** |

These are admission ceilings, not estimated consumption or already-funded live
reservations. The existing native audit bounds remain unchanged. The original
600-second author runs retain their own budgets and evidence; this is a new
audit cohort, not a rerun with a changed author deadline.

The intended model is the saved cohort's `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`.
Endpoint and serving details remain private and unqualified. Before dispatch,
pin the actual advertised model/settings, qualify constrained generation and
retain its native usage evidence. A healthy GET or matching model name alone
does not prove serving health or identical weights. Do not clear caches or infer
causal speed improvements from cache-dependent latency.

Stop the cohort on unknown completion/usage, timeout, token/request overrun or
serving drift. Keep pending work unstarted and report it at the fixed denominator.
Never retry or settle an earlier unknown invocation. Preserve raw stage outputs,
native receipts and both inner timeout and outer observer/unknown reasons.

## Labels, scoring and advancement gates

Preparation does not authorize live execution. The sealed protocol currently has
`liveExecutionAuthorized=false`, `servingQualified=false` and
`adjudicationComplete=false`.

Before any audit output, two independent semantic readers must establish the
audit labels with exact answer and displayed-source proof. Resolve the disputed
`q022` labels explicitly, preserve both historical and later judgments, and
retain unresolved disagreements. Apply the same independent check to the new
control labels. Historical judgments are evidence, not automatically adopted
gold labels. In particular, an old incomplete-answer score does not automatically
make a correct scoped abstention an audit failure.

The existing strict scorer, canonical validation and fixed denominators are
unchanged. Label files never enter either model stage. Report omission detection,
misses, false alarms, selected-citation and status errors, invalid/unresolved
audits, latency, observed tokens and held allowances separately. An invalid or
unresolved audit does not count as successful error detection.

Require all targeted faulty controls to receive accepted findings and all correct
controls to remain clear before considering any repair experiment. Real-case
misses and disputed labels remain visible. A selected six-case study establishes
neither broad reliability nor answer improvement: the audit leaves every answer
unchanged. Repair requires a separately reviewed design and comparison.

## Reproducibility and preservation

The private preparation ran under verified OS network denial and revalidated
frozen originals through the unchanged canonical contract. It verified all 30
historical durable archives and all 13 held historical reservations before and
after preparation. No provider was contacted and no live allowance was settled.

The prepared study has 148 indexed files, manifest SHA256
`79aacf4d3f7f30c6a002f136650acb02ae51596d3c8138a3dd5dee319759e15c`.
It retains packets, source-only and answer views, every original slot, aliases,
the randomized schedule, separate pending adjudication material and a sealed
protocol. Corpus, raw outputs, labels and operator state stay outside Git/CI.

[PR #38](https://github.com/B3Cognition/prosaic-integration-lab/pull/38) records
current CI qualification and remaining gates. See [audit usage](answer-span-audit.md)
for the host/runtime/harness boundaries and installed fixture command.
