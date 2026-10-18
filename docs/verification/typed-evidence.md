# Typed evidence consumer pattern

The Lab offers an opt-in, provider-independent evidence envelope. Run
`python -m lab_runner.retrieval_memory --typed-evidence` for preflight; add the
existing explicit fixture/live configuration flags to execute it. Raw records
remain the default. Each format has its own immutable execution identity.

An application supplies the authority, required fact labels, complete bounded
source index and records actually fetched. `memory.evidence.build_summary`
classifies each fact as `verified`, `absent` or `unread`. Absence refers only to
the supplied complete index's scope; it is not a claim about the world. A partial
index must be rejected or treated as incomplete by the application. The Lab
checks that its index matches the complete granted source snapshot before
asserting completeness. Metadata comes from that trusted index; values come
only from fetched records. Wrong-authority and superseded fetched records remain
visible, with explicit exclusion reasons. Tied current revisions fail closed.

The envelope does not calculate a decision or carry a private expected answer.
The model applies the public task rules. The independent consumer validator can
reject a wrong answer and provide bounded feedback; it cannot silently rewrite
the answer. Typed tool results use `lookup-summary-v1`; raw results retain
`lookup-v1`. Replay binds format, implementation, source records and exact
summary digest/size. It cannot adopt another format's run.

Consuming projects should reproduce the **contract and trust boundaries** for
their own domain: define authority, index coverage, current revision selection,
fact types, absence semantics, grants and independent validation. The generic
classifier accepts arbitrary labels and up to sixteen required facts; the Lab's
rollout adapter deliberately supports only its closed public task grammar.
Do not treat that grammar, synthetic corpus or benchmark answer rules as a
general application policy. Execution remains in Runtime and workflow state in
Harness; this retrieval and evidence policy belongs to the application.

This milestone addresses structured tool contracts, context assembly and
trajectory evaluation from the agentic-systems roadmap. It does not establish
durable memory write/forget policy, semantic/vector retrieval, resumable graph
planning, multi-agent protocols or production observability. Current local
models are regression targets. Offline provider-independent contracts are not
live certification of other models or providers.

The original fresh study crosses raw/typed evidence with memory disabled/enabled,
using twelve new cases and the same two profiles: 96 samples. This distinguishes
host evidence assistance from memory effects. A scripted provider validates the
actual envelope for plumbing qualification; its results do not measure model
reasoning. Live results and reservations must be reported separately. If format
runs are sequential, temporal confounding must be disclosed and format effects
described as observed paired differences, not isolated causal estimates. The live
study stopped after 54 samples on a known token-budget overrun; it is incomplete.

## Offline qualification — 2026-10-17

Reviewed implementation/history commit: `358e874`; candidate version
`0.5.1+evidence.1`, with published Core 0.4.1, Runtime 0.9.6 and Harness 0.9.0.
The full source suite passed **1,190 tests** in 165.73 seconds, with one existing
Starlette warning. Independent whole-change review found no actionable issues.
No new model/provider tuning or SDK changes were introduced.

The implementation and expanded history were archived before twelve fresh
current cases were authored. All 26 previous episodes and 48 historical sources
remain unchanged; twelve new episodes and 24 sources were appended. New current
cases cover relevant, stale, no-match, tenant, hostile and missing evidence, two
cases each, with new authority/fact labels, IDs, values and revisions. Frozen
cases are a separate operator bundle; the packaged old suite is a development
regression fixture, not this fresh held-out evaluation.

A fresh environment installed the immutable candidate wheel and checksum-pinned
SDKs. All 249 installed artifact payload files matched their wheels. Both formats
passed all 48 scripted-provider samples each: **96 fixture samples**, 192
independently observed provider requests and 96 tool calls. Every sample was
rescored against current sources. Socket/provider-denied replay preserved every
output byte. The typed scripted provider validates the delivered envelope and
uses public fetched records; fixture success is not evidence of model quality.

Candidate wheel SHA-256:
`03433093ae18db6fdbf1d0e30fcc9146a65983dd0c2cf661059d0f5cfbf2f56e`.
Development freeze: `3fc89aba0cde334cfb9094e13b899915fe05b70090d8f9ebc350688d4bfee003`.
Fresh bundle: `69a8204d98c8b072d2f02e992172f9fa96b084fbceb736a436b5de623f501518`.
Evaluation freeze: `0db5ade3ef215a826321474a48dd9925699cb2a75b55c83688933d2a333599e0`.

Fixture tool results occupied 8,152 bytes raw and 23,240 bytes typed, excluding
Runtime's outer status wrapper. This is evidence presentation overhead, separate
from recalled-memory bytes. Live tokens, latency and answer quality remain to be
measured. Format runs are prepared sequentially, so temporal confounding remains.

Before dispatch, a numerical allowance extension was required. The 24 historical
ledgers charge 1,091 requests, 412 tools and 1,190,191 tokens, including all five
unknown reservations. Existing cumulative ceilings are 1,171 / 452 / 1,417,565.
The 96-sample schedule reserves at most 384 / 192 / 786,432, including retries;
the required extension is **304 requests, 152 tools and 559,058 tokens**, giving
new ceilings **1,475 / 604 / 1,976,623**. Per-case limits and profiles stay fixed.
The user approved this exact extension with “Ok continue.” The study then ran
with unchanged per-case limits, models and settings.

## Live run stopped on a known budget overrun

The raw control completed all 48 samples. Every receipt, current-source join,
prepared context, usage total and scoring result was independently audited.

| Model | Memory disabled | Memory enabled | Missing-evidence samples passed |
| --- | --- | --- | --- |
| Qwen2.5-Coder 7B | 5/12 | 6/12 | 0/4 |
| ThinkingCap-Qwen3.8 27B | 12/12 | 12/12 | 4/4 |

All larger-model control answers passed on their first attempt. The smaller
model had ten first-attempt passes and one successful correction. Native
execution reported no failure reasons in the control; the remaining failures
were answer validation failures. Memory increased reported tokens from 42,846
to 70,666 for the smaller model (65%) and from 31,274 to 47,640 for the larger
(52%). A single extra smaller-model pass on twelve cases does not establish a
reliable benefit. The larger model gained no accuracy on this control.

The typed run recorded six smaller-model samples: two passed, three exhausted
answer-correction attempts, and one stopped on a token limit. It did not reach
any missing-evidence cases or larger-model samples. These unequal, incomplete
subsets cannot establish that typed summaries help, fix missing-evidence
handling, or improve memory efficacy. Forty-two scheduled samples did not run.

The stopped sample, `stale-31-p1-enabled`, reported 4,217 tokens on its first
invocation and 4,299 on its second: **8,516 total**, exceeding its unchanged
8,192-token reservation by **324**. Runtime correctly reported `token_limit`
after receiving usage, but a post-response stop threshold does not guarantee
that the response itself stays under that threshold. The Lab allowance refused
to settle an actual above the reservation and stopped the run. Treating that
reported-token threshold as a guaranteed hard reservation ceiling was an
incorrect assumption in this protocol.

All actual spend is preserved. The original reservation was fully retained
using the existing public settlement API, without enlarging its maximum or
clipping recorded actuals. A separate standard reconciliation ledger charges
only the known 324-token excess. It authorizes no inference. The original five
historic unknown reservations remain charged; the new retained reservation is
a **known policy breach**, not unknown native usage. The frozen runner's
evidence-flag-based `retainedUnknownSamples` projection does not capture this
already-published row's later settlement state; the independent ledger audit
records it explicitly. Both reporting and settlement need a general solution.

The terminated study used **144 provider requests, 72 tools and 226,559 reported
tokens**. Cumulative charges are **1,235 / 484 / 1,416,750**, within the approved
**1,475 / 604 / 1,976,623** cumulative ceilings. That does not waive the per-case
breach. No inference was dispatched after the stop. All 54 executed samples
were rescored and replayed with sockets and dispatch disabled; original evidence
bytes stayed identical. The 27 authoritative archived ledgers reproduce the
cumulative totals, including the separate excess-token entry. Tool-result byte
measurements use canonical inner JSON, excluding transport wrappers/formatting.

Private evidence is archived under the existing research checkout's
`reports/retrieval-memory-evidence-live-20261017-study`, with separate flat raw,
typed and token-reconciliation ledgers. Archived configs retain their historical
absolute paths and are not rerun entry points. The reviewed candidate and source
freeze remain unchanged. This was not a completed 96-sample live comparison.

## General gap exposed and next decision

The useful next target is budget admission and truthful overrun accounting,
before another live quality study. A complete contract must distinguish hard
request/tool bounds, a reported-token stop threshold and a pre-dispatch token
reservation; account for input growth, recalled context and correction attempts;
record known excess without hiding it or allowing further dispatch; and derive
public retained-reservation views from durable settlement state. Offline fixtures
must include known overspend and changing prompt size, rather than only constant
150-token usage. Any hard admission claim needs a trusted input-cost bound and
reserved output headroom; if those are unavailable, fail closed or require an
explicit best-effort policy. Raising a threshold alone is not this fix.

That work is provider-independent operational hardening from the
[agentic-systems roadmap](https://www.kdnuggets.com/the-roadmap-to-mastering-agentic-ai-systems-in-2026),
not a new prompt or oMLX exception. Typed summaries remain an experimental
consumer pattern with qualified contracts and incomplete live quality evidence.
Broader task/provider evaluation, versioned memory writes and expiry, stale-data
handling, and multi-step graph execution remain distinct roadmap work. Existing
Harness graph admission/checkpoints/resume should be reused. Any implementation
or policy change requires a new development freeze and fresh held-out cases
before making another confirmatory comparison claim. Further work is pending
the user's decision on this general budget milestone.
