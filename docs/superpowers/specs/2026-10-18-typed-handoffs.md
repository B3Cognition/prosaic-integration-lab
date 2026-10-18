# Offline typed handoffs and trajectory qualification

Continue the roadmap beyond model-specific corrections with an experimental Lab
consumer of installed public Runtime/Harness APIs. No SDK engine changes,
production HTTP endpoint, memory rollout, release or live inference is included.

A host-owned, bounded synthetic case supplies a complete current source index
and the existing public rollout task grammar. A planner emits a typed assignment
bound to that exact request. An evidence worker must perform a real native lookup
and emits a typed result with the same binding. A critic receives both artifacts
and emits a typed review. Host checks independently verify every handoff and the
critic's claims against fetched current evidence. No private expected answer is
used for acceptance. Missing, unread or ambiguous evidence and disagreements
route to a human-review pause. Schema-invalid output blocks. Human review is
an escalation boundary, never an automatic approval mechanism.

Preserve 4 provider requests, 2 tool calls, 8,192 reported tokens, 600 seconds
and 512 output tokens per case. Planner/worker/critic plus one lookup uses four
requests, so do not introduce an extra model repair round. Use a shared Runtime
ExecutionBudget with explicit synthetic token admission; no qualified live
counter or new live allowance is implied. Unknown usage fences continuation.

Score the entire receipt trajectory: ordered roles, binding correctness, worker
correctness, critic correctness, first failing stage, safety outcome, complete
usage and efficiency. A safe escalation can pass the safety check while failing
task quality. Test real synthetic HTTP on both supported wire formats. Saved
receipts must survive reconstruction without dispatch or changed evidence.
Memory stays experimental and all historical artifacts/allowances stay intact.
