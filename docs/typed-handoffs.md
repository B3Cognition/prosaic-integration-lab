# Experimental typed handoffs (offline only)

This Lab example exercises the roadmap's multi-agent collaboration gap through
the installed public SDKs. Harness owns the graph, validation, state and receipts;
Runtime owns model/tool execution and shared budget admission. Core is unchanged.
It does not add a general agent communication protocol or a production endpoint.

The planner returns an assignment with a digest of the host's exact task, complete
current source index and source snapshot hash. The evidence worker must actually
look up records; its typed result carries the same digest, status, answer and
fetched records. The critic receives these artifacts with Harness dependency
bindings. A host check verifies the critic and worker independently against the
worker's invocation-bound lookup journal and public task grammar. A supplied
private answer key cannot control approval. Missing and unread are different;
colliding highest authoritative revisions require review rather than selecting
an arbitrary record. Unsupported task grammar or incomplete index fails admission.

Only a correct, fully read, unambiguous result and truthful accepting critic can
finish successfully. Missing/conflicting evidence or any semantic disagreement
pauses for human review. The sole human choice is **stop**, producing a rejected
finish; this example does not authorize a human or model to override evidence.
Schema or binding errors block. There is no automatic repair round: planner,
worker lookup/final and critic already use four requests. Shared caps stay at
4 requests, 2 tools, 8,192 reported tokens, 600 seconds and 512 output tokens.

`score_trajectory` separates task quality from safe stopping. A missed worker
flaw still fails quality even when a host gate prevents approval. Reports include
the earliest failing role, role order, receipt-derived request/tool/token counts
and accepted/escalated/blocked outcome. Unknown usage is never zero. Reported
overruns remain visible; they stop continuation and fail qualification instead
of raising the cap. Counts for a missing receipt describe observed receipts only;
the interrupted operation remains uncertain, not a zero-cost call.

`recover_case` reconstructs and verifies stored evidence without new model/tool
dispatch. A saved final critic receipt can be adopted because only deterministic
check/pause/finish nodes follow it. A missing final receipt blocks without retry
consent. Earlier-stage interruptions are inspection-only; there is no automatic
continuation into another agent and no production failover claim.

Run the installed wheel's Python in isolated mode:

```text
python -I scripts/typed_handoff_smoke.py --source-root /absolute/lab/checkout --output /private/output.json
```

The entry point accepts only the named synthetic model at numeric loopback over
HTTP. Its fixed token counter measures synthetic units, not real tokenization.
OpenAI-compatible and Anthropic fixture messages exercise transport differences;
scripted agents do not demonstrate real-model reasoning or memory improvement.
Memory remains experimental. Live comparisons, hosted providers, PostgreSQL,
container platforms and release qualification are separate work.
