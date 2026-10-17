# Provider-neutral tool outcomes and bounded recovery

User authorization: implement the next milestone; keep current limits; qualify
offline before another live run. Prior native execution/questions opt-out holds.
No live inference, limit increases, push or release in this slice. Preserve all
historic evidence and installed candidates. Core remains unchanged.

Runtime owns tool execution and factual outcome evidence. Harness is sole writer
of workflow/recovery state. Lab consumes installed public APIs and qualifies the
composed behavior. No model IDs, serving imports, private SDK imports or prompt
tuning. Cumulative charge1417requests/574tools/1696913tokens and ceilings
1475/604/1976623 remain unchanged, including seven unknown reservations.

## Runtime contract

Add a public immutable `ToolOutcome(code, replayed=False)` with strict
`to_dict()/from_dict()`. Its closed version1 shape is
`{version,code,phase,effect,recovery,replayed}`. Fixed codes derive the other
fields; invalid combinations/versions/bools/unknown fields reject. Categories:
ok; invalid_arguments; not_granted; authorization_denied; controlled_failure;
handler_error; invalid_result; result_limit; execution_failed;
tool_identity_conflict; tool_journal_failed; tool_effect_uncertain; unclassified.
Phases admission/authorization/execution/result/journal; effect
not_started/completed/unknown; recovery none/correct_arguments/stop/reconcile.
Effect describes the tool handler/operation, not arbitrary host authorization
code. Replay is explicit and cannot authorize another dispatch.

Derive evidence at trusted dispatch branches, never from free-form error text,
model fields or an ordinary callback dictionary. A controlled ToolFailure with
code `invalid_arguments` remains a completed controlled failure, not a repairable
admission failure. Preserve existing model envelopes and v1 journal bytes.
Never publish raw arguments, result values, schema exception messages or host
exception text through the new contract.

Attach `tool_outcome` to native `tool_completed` events, carrying existing call
ID and tool version. Propagate validated owned copies through conversation
events and best-effort observers. Builtin failures lacking proven semantics are
unclassified/unknown; do not infer safety from their message text. Ordinary
OpenAI-compatible and Anthropic execution share the same dispatcher.

Add `RunPolicy.bounded_tool_recovery=False` (strict bool) and capability flags
`tool_outcomes_v1`, `bounded_tool_recovery_v1`. In bounded mode, known pre-handler
invalid arguments may reach model correction under existing limits. Denied
grants/authorization and completed controlled failures stop. Unknown handler,
result or journal effects stop and require reconciliation, never automatic
retry. No callback is retried by this feature. Existing journal uncertainty,
cancellation/deadlines and budgets remain authoritative; an interrupted path
without terminal evidence never becomes a proven safe failure. Default behavior
and existing serialized result/journal formats remain compatible.

## Harness contract

Add `WorkflowPolicy.bounded_tool_recovery=False`, omitted from identity when
false for default compatibility. Opt-in requires both Runtime capabilities and
passes the public RunPolicy flag through native execution. A missing required
tool with a valid, version-matching invalid-arguments outcome gets fixed bounded
machine-code feedback and may use only its already-permitted next attempt.
Missing required tools with no attempted call may use the same bounded retry.
Unclassified, malformed, foreign-version or non-repairable failure evidence
blocks recovery. Already successful required tools are not retried solely for
an earlier resolved invalid request. Runtime failures, exhausted budgets,
pending/interrupted calls and unknown effects cannot gain another attempt.
No raw tool error message enters feedback. Preserve receipt/pending-call
recovery and original public Harness state formats.

## Lab adoption and qualification

Create opt-in `bounded_recovery=False` hooks on native memory execution/freeze/
recovery, binding enabled behavior into frozen identity. Do not silently change
default experiments or rerun prior cases. Scoped trace consumes validated public
tool outcomes, retaining `unclassified` for legacy or absent evidence rather
than inventing causes for the seven historic tool errors.

Fixed case caps4requests/2tools/8192tokens/600seconds/output512 remain. Qualify
synthetic argument correction, authority denial, controlled failure, callback
exception after an effect, malformed/oversized results, journal uncertainty and
commit replay, budget exhaustion and interrupted/receipt-only recovery. Test
two provider wire formats, streaming where applicable, privacy canaries, mutated
event inputs and legacy default behavior. No new live inference.

Use immutable Runtime0.9.7+tools.1, Harness0.9.1+tools.1, Lab0.5.1+tools.1 candidates
with exact public manifests. Run source suites, build wheel/sdist, verify fresh
installed payloads, native loopback fixtures, denied-network replay, consumer
image and one fresh whole-change code review. Preserve prior candidates and
history bytes. Record limits, actual test evidence and remaining coverage.
