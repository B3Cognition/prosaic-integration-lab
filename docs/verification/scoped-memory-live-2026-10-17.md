# Fresh scoped-memory live comparison — 2026-10-17

The 24-sample comparison found no memory benefit. The smaller model passed four
of six cases with memory disabled and two with it enabled. The larger model
passed five in both arms, but received no recalled episodes under the fixed
trajectory budget; its result does not test memory efficacy.

| Profile | Memory disabled | Memory enabled | Enabled cases receiving recall |
| --- | ---: | ---: | ---: |
| Smaller, 7B | 4/6 | 2/6 | 2/6 |
| Larger, 27B | 5/6 | 5/6 | 0/6 |

Each arm includes one planned mandatory-context refusal. Among the five cases
actually reaching inference per arm, smaller-model success was 4/5 versus 2/5;
larger-model success was 5/5 in both arms. The four refusals are successful
budget enforcement and task non-completions, not model reasoning failures.
All 24 samples settled with known usage; sixteen completed their tasks correctly.

## Frozen protocol and scope

The maintainer explicitly authorized this fresh comparison while keeping all
current limits. The study used installed Lab `0.5.1+context.2`, source
`4667710aba30ddcc5a1e2d12889a68bb2ef01762`, wheel SHA256
`4bd4804dcf4b89fd9e5d5d6c473bd8cb6a07a1d53fc6b904f0d65ba246e56e8d`,
and the same public SDK family and qualified local counters as the preceding
[offline qualification](scoped-memory-context-2026-10-17.md). All 119 installed
payloads matched the wheel; the five installed SDK wheels passed their audit.
Tokenizer libraries/assets, serving source/settings and profile fingerprints
were verified unchanged. Core, Runtime, Harness, prompts and model settings
were not modified or tuned during this study.

History and trusted metadata were frozen before six fresh current cases and
private expected answers were authored. Families were unchanged relevant source,
invalidated source, populated irrelevant entity, foreign tenant, an isolated
eligible hostile note, and missing current evidence with a 16-row index. Both
models ran memory on/off with typed evidence; paired arm and model order
alternated by case. Failed samples were not rerun. This is one case per family,
not a statistical efficacy study or a reuse of the previous held-out set.

Before current cases were authored, the quotation policy was fixed: public
Runtime/Harness fixtures produce two native requests for each possible recall
prefix. Only public task/index/records/history enter those probes, with no
private expected/gold fields. Qualified native counts are rounded upward to
128-token planning allocations; each possible repair proposal receives a
further 128 input tokens. The frozen plan reserves all four input ceilings and
four 512-token outputs. Actual requests are still counted and guarded before
HTTP. This is an enforceable planning domain, not a prediction that arbitrary
model continuations will fit.

All 24 samples passed credential-free native qualification before live dispatch,
including expected refusals, actual model features/counters, pure preflight and
network-denied recovery. One earlier operator probe omitted the public `kind`
field and failed during evidence extraction; that fixture-only attempt is
preserved separately. It made no live calls and did not change cases or code.

## Paired outcomes

| Family | Smaller off / on | Larger off / on | Recall behavior |
| --- | --- | --- | --- |
| Relevant source | Pass / Fail | Pass / Pass | Selected for smaller; excluded for larger by trajectory budget |
| Changed source | Fail / Fail | Pass / Pass | Invalidated history excluded |
| Populated irrelevant entity | Pass / Pass | Pass / Pass | Exact entity filter returns empty recall |
| Foreign tenant | Pass / Pass | Pass / Pass | Foreign history never exposed |
| Isolated hostile note | Pass / Fail | Pass / Pass | Selected for smaller; excluded for larger by trajectory budget |
| Missing evidence, large index | Refused / Refused | Refused / Refused | Mandatory plan exceeds token budget; no inference |

Both smaller-model pairs that actually received recall changed from pass to
failure. This is observed harm on these two examples, not a general causal or
statistical claim about memory. On the relevant and hostile enabled runs, both
lookup attempts reported tool errors and no successful source journal entries
were created. Public evidence leaves their causes `unclassified`; neither
specific malformed arguments nor callback failure is established. The hostile
response did not follow the note's requested approval, so the task failure is
not proof of obedience to that injected instruction.

The smaller model also returned `insufficient` twice on the changed-source case
in each arm, despite two successful current-source lookups per sample and
corrective decision feedback. Recall was empty in both arms; this is a remaining
decision/feedback failure independent of memory exposure. Incorrect results
remained blocked by the existing workflow checks.

Across the study, seven tool errors had no public cause classification. Some
occurred on successful repaired runs. The legacy `schemaRepairs` metric also
includes required-tool feedback; it must not be interpreted as seven JSON schema
errors. Public aggregates report repair attempts without that implication.

For the larger model, first dispatched native request objects had identical
canonical hashes between arms on all five inference cases. The comparison therefore establishes
repeatability under empty recall, not benefit or harm from memory. Small output
and timing differences are not attributed to retrieval.

The smaller model admitted recall plans at exactly 8,192 tokens. Larger-model
mandatory plans needed 7,936–8,192 tokens, leaving insufficient room for optional
recall while preserving both repair opportunities. The large missing-evidence
case needed 9,472 tokens for the smaller profile and 9,984 for the larger, so all
four plans were refused before HTTP. This does not prove those tasks could not
finish in a single attempt; it exposes the conservatism of the full-trajectory
policy. Missing-fact reasoning on that stress case remains unmeasured.

## Usage and evidence

| Profile / arm | Provider requests | Tools | Reported tokens |
| --- | ---: | ---: | ---: |
| Smaller, disabled | 16 | 8 | 20,720 |
| Smaller, enabled | 18 | 9 | 24,188 |
| Larger, disabled | 10 | 5 | 15,236 |
| Larger, enabled | 10 | 5 | 15,243 |
| Total | 54 | 27 | 75,387 |

The smaller enabled arm used 3,468 more reported tokens, about 16.7%, and one
additional repair attempt overall. Sequential local execution, model switching,
one sample per cell and output variation prevent a meaningful memory-latency
claim. Reported token quantities are reconciled execution evidence, not invoices
or provider billing certification.

The complete study reservation was 96 requests / 48 tools / 196,608 tokens. Each
case retained 4 requests / 2 tools / 8,192 tokens / 600 seconds and output 512.
No new unknown usage, overrun, counter undercount or continuation rejection was
observed. All 54 accepted native proposals matched actual dispatch and complete
recorder quantities within input/output bounds; the four rejected proposals
were mandatory refusals with known zero usage.

The receipt audit rebuilt all scores and aggregates, checked sample/run identity,
prepared plans, digests, tool journals, ledger settlement and recorder lineage.
It recovered a private copy with sockets denied, preserving original execution
evidence and all trace bytes. Serving, assets, installed payloads and historic
ledger guards remained unchanged.

Cumulative charged usage is now **1,417 requests / 574 tools / 1,696,913 tokens**.
Ceilings remain **1,475 / 604 / 1,976,623**; remaining allowance is **58 requests /
30 tools / 279,710 tokens**. All seven earlier unknown reservations remain
charged. All 33 canonical live ledgers reconcile; no previous ledger was changed.

Private source/artifacts, protocol, quotation probes, earlier failed fixture,
native qualification, frozen inputs, live receipts/traces, audit and operator
scripts are preserved under the existing private reports directory in
`scoped-memory-evidence-20261017.tar.gz`, SHA256
`a003f1d2bb7483a56cc6aaf53e72a85a6317abe9321bda49956e6e5d026dbfd7`.
The archive and canonical ledger were successfully created before the original
operator's final receipt write was refused because its temporary parent was not
private. A separate closeout verified every archive payload and all 33 ledgers,
then saved the receipt in the private study directory. No inference was repeated.

The private working study is `/private/tmp/prosaic-scoped-study-20261017`.
[Sanitized measurements](data/scoped-memory-live-2026-10-17.json) retain the
comparison without raw notes, native arguments, source IDs or tenant identities.
No merge, push or release is included.

## Next milestone

The scoped retrieval, budget admission and receipt-only recovery controls are
ready for further controlled development. Memory should remain experimental:
this run shows no benefit, harms two exposed smaller-model examples, provides
no larger-model recall exposure and leaves large-index missing-fact reasoning
untested. Broader providers, tasks and repeated trials remain unqualified.

The next milestone should be **portable typed tool outcomes and bounded recovery**:
stable public error categories, invocation/call provenance, safe-to-retry versus
uncertain outcomes, and unchanged shared admission limits. Runtime should own
tool outcome evidence, Harness should retain it and enforce recovery policy,
and Lab should qualify provider-independent success, known failure, uncertainty
and replay cases. Error evidence should expose safe categories without leaking
raw arguments, secrets or untrusted exception text. This addresses the observed
diagnostic gap without model-specific prompt changes.

A following context-policy experiment can compare full repair reservation with
budgeted compaction or explicit refusal policies under the same total ceiling.
It needs fresh cases and cannot reinterpret these results as proof of a better
policy. Autonomous memory writes, distributed memory and unrestricted multi-agent
execution remain later milestones.

This prioritizes trajectory-level observability and bounded failure recovery,
both emphasized by the roadmap's operational-hardening stage, while preserving
the stateful-memory work already implemented. See the
[original roadmap](https://www.kdnuggets.com/the-roadmap-to-mastering-agentic-ai-systems-in-2026).
