# Bounded multi-agent coordination

The maintainer approved the proposed two-worker milestone. Native execution
and the earlier question opt-out persist. Implement the complete bounded
blueprint in Integration Lab; maximum means the complete protocol within the
unchanged limits, with exactly two workers. No live run, push, merge, package
publication or sibling SDK change is included. Branch codex/bounded-coordination
starts from PR22 head5c888bf in the existing isolated worktree. PR22's remaining
CI/release closure is separate and must not be silently merged or published.

## Outcome and boundaries

Demonstrate two genuinely overlapping independent public Harness runs, each
with its own Runtime, recorder, store and trusted host assignment. Compare the
same frozen domain/evaluator against a sequential baseline. Public
ExecutionBudget explicitly supports activating one shared object in worker
threads; use that API, never copy its implementation or import private APIs.
Harness remains owner of each worker's execution and durable receipts.
This is a single-host application composition blueprint, not a new Harness
graph step, distributed scheduler, consensus protocol or claim of model benefit.

Use Python3.12, current checksum-pinned public SDKs, no new dependencies or
model-specific tuning. Core remains read-only distribution/discovery. Memory
and correction remain experimental. Trusted callbacks/cooperative cancellation
cannot forcibly preempt arbitrary Python code; no extra sandbox claim is made.

## Closed host protocol

The host freezes exactly two assignments ordered by workerId, each containing
workerId, sourceId, sourceRevision and assignmentDigest. The digest binds the
case/domain/evaluator/configuration and worker's source snapshot. Workers never
choose identities, budgets, sources, peers, retry policy or permissions.

A small private local CoordinationJournal binds the whole plan digest and
persists one launch claim per worker under a file lock before public SDK entry.
Claims cannot be repeated after restart. It stores only bounded host-verified
worker reports and digests, with atomic owner-only writes. There is no worker
retry/resume method. Journal inspection grants no execution. Existing
FailureIsolation reserves one full pair, never one full allowance per worker.
No reservation is refunded or reused by this blueprint.

Reports contain assignmentDigest, status (completed/failed/unknown), source
fields, fact (boolean/null), usage (complete numeric counts or null), and
evidenceDigest. Completed requires the exact assignment/source binding and
host verification against the current tool receipt/source snapshot. Reports
are supplied by trusted host adapters, never accepted directly from model JSON.
Only completed reports have a fact; unknown usage cannot become completed.
Duplicate identical settlement is idempotent; conflicting settlement or a
foreign assignment is rejected. Once both terminal reports exist they are
immutable. A launch without a terminal report remains uncertain on inspection.
Raw receipts and source contents stay private; safe summaries contain statuses,
diagnostic categories and counts/digests, not prompts, IDs or exception strings.

## Admission, cancellation and join

One parent public ExecutionBudget covers the entire pair:
4provider requests/2tool calls/8192reported tokens/600seconds.
Each worker also activates a child budget of2requests/1tool/4096tokens with the
remaining parent deadline and the same cancellation Event. Both budgets use
the host-qualified counter. The synthetic counter is fixture-only; consumers
must qualify their counters. Every provider response has max_tokens512.
The parent is created once before either launch and never recreated for join
or recovery. Actual unknowns/overruns are retained honestly; already admitted
in-flight work may finish, but no new call is admitted after cancellation or
unknown usage is observed. Cancellation is cooperative, not retroactive.

The host sets cancellation on a failed/unknown worker and joins all owned
threads before accepting the pair. A host-supplied cancellation before launch
causes zero dispatch. Per-worker stores/recorders are constructed in that
worker, never forked from active Harness execution. No shared recorder mutation.
No supervisor/critic inference or automatic retries fit this initial protocol.

The deterministic join sorts by workerId, requires both expected assignments
and known in-bound usage, and never treats partial success as authorization.
Domain example: independently read two current release-authority records for
the same parcel/revision. Two verified true facts produce a ready recommendation;
two verified false facts produce hold; differing verified facts produce conflict;
absent facts produce missing-evidence hold; malformed, failed, unknown, overrun
or unfinished workers block a ready recommendation. No parcel effect executes.
The host evaluator checks worker output against actual scoped lookup evidence;
model confidence, matching output schemas and agreeing workers are insufficient.

## Durable inspection and recovery

Reconstruct fresh public Harness/store objects and call recovery_evidence only;
never run/resume/turn during inspection. Validate workflow/assignment/source
bindings and compare immutable saved reports with independently reassessed
public receipts and tool evidence. Missing/corrupt/aliased/oversized or foreign
state refuses a passing report. Active/missing worker receipts stay incomplete;
never launch a replacement or release allowance. Completion with a saved receipt
before journal settlement remains incomplete for explicit host reconciliation,
not an automatic execution retry. New admission after uncertainty is out of scope.
Existing FailureIsolation explicit quarantine/recovery APIs demonstrate the
separate host decision; they do not prove worker termination or authorize retry.
Saved safe-summary replay denies network and performs no SDK execution.

## Qualification

Unit regressions cover strict protocol/plan binding, exactly-once concurrent
claims, immutable settlement, deterministic joins, missing/conflicting evidence,
known/unknown/over-cap accounting, private bounded files and restart uncertainty.
Actual public-SDK fixtures run sequential and parallel on both scripted
OpenAI-compatible and Anthropic formats. Cases: ready, hold, conflict, missing,
wrong output, malformed output, tool error, provider unknown usage, pre-cancel,
shared request/tool/token exhaustion and process loss before/after worker receipt.
Use barriers/events and actual HTTP/tool witnesses to prove overlap and that
caps hold; wall-clock speed alone does not prove concurrency. Resource-exhaustion
probes may use stricter sublimits but never raise current limits. Preserve
complete denominators, unknowns and costs; no efficacy or speedup claim.

Use watched RED-to-GREEN tests, the full source suite, installed wheel and
rebuilt-sdist adoption (including the new recipe), network-denied inspection,
owned thread/server cleanup, and one fresh whole-branch review. Existing
platform/stack gates remain mandatory; local tests do not replace later CI.
Freeze the review/qualification evidence before any later live evaluation.

Cumulative ceilings1558requests/637tools/1976623tokens and charges
1509/610/1835168 remain unchanged. Preserve39canonical ledgers and all nine
unknown reservations. Offline fixture calls are synthetic, not live allowance.
