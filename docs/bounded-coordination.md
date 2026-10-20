# Consumer blueprint: bounded multi-agent coordination

This experimental Lab recipe composes two independent public Harness runs in
one host process. Each worker owns its Runtime, recorder and store. One public
Runtime ExecutionBudget is explicitly activated in both threads. The consumer
owns assignments, launch admission, cancellation, evidence assessment and the
join; Harness still owns each worker's execution and durable receipts. This
adds no parallel Harness graph step or model-specific behavior.

The whole pair has4provider requests,2tool calls,8192reported tokens and a
600second deadline. Each worker gets2requests,1tool and4096tokens; each response
is capped at512output tokens. Child deadlines use the remaining parent time.
No model supervisor, critic or automatic retry is added. Sequential and parallel
examples use the same sources, output contracts, evaluator and total limits.

## Adapt the host protocol

Freeze two trusted host assignments with workerId, sourceId, sourceRevision and
assignmentDigest. The digest should bind your actual source snapshot, domain
rules and execution configuration. Source/worker identities are host decisions.

```python
from lab_runner.coordination import CoordinationJournal, make_plan, join_reports

plan = make_plan(configuration_digest, host_assignments)
journal = CoordinationJournal(private_path, plan=plan)
claim = journal.claim(worker_id)  # durable intent before public SDK execution
# Verify public SDK receipts, current scoped tool evidence and complete usage.
journal.settle(worker_id, claim, host_verified_report)
result = join_reports(plan, verified_reports)
```

These functions provide no authentication or dispatch/retry permission. Never
pass raw model JSON as a host report. A terminal report binds its assignment,
source/revision, verified fact, accounting and evidence digest. Unknown usage
stays null; a correct-looking answer cannot complete unknown accounting.
Identical settlement is idempotent; changed settlement/foreign bindings fail.
Claims cannot repeat after restart. Reports are immutable once settled.

The example reserves one full pair using existing FailureIsolation, not one
full case allowance per worker. It never refunds that reservation. Recorder
intent, admitted requests, actual HTTP delivery and reported token usage are
distinct evidence: intent can be written before admission denies a call.
In-flight reservations and incomplete receipts remain unresolved. Safe summaries
include observed HTTP counts separately and label usage completeness. Token
totals from incomplete lanes are known partial quantities, not complete cost.

## Execute and join conservatively

The complete adaptation example is `lab_runner/coordination_fixture.py`.
Construct resources inside each worker, then activate the same parent object
and a bounded child around that worker's public Harness.run call. Do not copy
budget counters or construct a fresh parent in each worker. Public budgets
perform admission across the active scopes; a consumer journal is not a
replacement budget engine.

A failed/unknown worker sets a shared cancellation Event. Join all owned
workers before accepting the pair. Cancellation is cooperative: already
admitted calls can finish, and arbitrary trusted callbacks cannot be forcibly
preempted. The example makes no hard resource-limit or distributed scheduler
claim. SDK/provider timeouts and existing admission limits still apply.

The parcel example reads two independently scoped current authority records.
Two verified true facts mean ready; two false facts mean hold; differing facts
mean conflict; an absent fact means missing evidence. Wrong/malformed outputs,
tool/provider failures, unfinished work and over-budget evidence cannot become
ready. A known worker failure remains failed when its peer is unfinished, with
aggregate usage still null. Fault scheduling may yield failed or incomplete;
individual status and accounting uncertainty remain visible. No parcel effect
executes, and agreement between models never substitutes for source validation.

For another domain, replace sources, schemas, workflow, tool adapter and host
evaluator. Keep the binding, launch, budget, settlement and inspection protocol.
The join's status list follows frozen plan order without exporting worker IDs.
Private receipts retain detailed correlation; summaries omit prompts, source
contents, raw assignment identifiers and exception messages.

## Inspect without redispatch

Reconstruct fresh public Harness/store objects and call recovery_evidence only.
The recipe checks saved reports against public receipts and current frozen
source/lookup evidence. Journal inspection cannot run/resume workers or renew
allowance. A launch with no terminal host report stays incomplete, including a
saved SDK receipt before journal settlement. There is no automatic replacement
worker. Explicit host reconciliation remains a separate decision.

Lab sidecar reads reject symlinks, public/non-regular files and data above64KiB;
FIFO opening cannot block inspection. Public SDK receipt validation remains
owned by Harness; protect the enclosing worker directories. Hard links are
not independently rejected when intact evidence still validates. Saved-proof
replay also checks closed fields, types, limits, fixed assertions and reconciled
worker usage; a matching join alone cannot qualify contradictory claims.
Hashes detect accidental corruption, not
a malicious trusted host rewriting all state. Protect storage, source snapshots,
configuration and operator identities in your application. Existing local
FailureIsolation fences journal writes, not arbitrary running processes.

## Qualify adoption

With the public SDK train installed, source execution is:

```sh
python scripts/coordination_smoke.py --source-root . --output /absolute/private/fresh-proof
python scripts/coordination_smoke.py --source-root . --output /absolute/private/fresh-proof --replay
```

Installed consumers omit source-root and run with `python -I`. The recipe runs
48lanes:12scenarios ×2provider wire formats ×sequential/parallel execution.
Owned HTTP barriers prove actual overlap; elapsed time alone is not proof.
Faults include missing/conflicting evidence, wrong/malformed output, tool and
provider errors, cancellation, and stricter request/tool/token admission caps.
Separate process-loss probes cover launch intent and a saved worker receipt.
Replay denies sockets and performs no SDK execution. The wheel and rebuilt
sdist gates both run the installed recipe and replay.

These scripted responses qualify protocol behavior, not live model quality,
speedup, critic/memory benefit or general production readiness. Consumers must
qualify their own models, counters, domain rules and deployment topology. Keep
memory/correction experimental and all existing limits/unknown charges intact.
See the [qualification record](verification/bounded-coordination-2026-10-20.md).
