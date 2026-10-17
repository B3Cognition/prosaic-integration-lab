# Runtime final-answer phase proposal

Status: reviewable proposal only; upstream implementation awaits the requested
scope authorization. Current Integration Lab rerun continues unchanged.

## Evidence

The preceding live baseline had 26 repeated lookup round failures after all
required records were already fetched. Instruction-only fixes have enabled
successful draft corrections and removed observed fact encoding and irrelevant
read failures, but native round-limit failures still occur. Runtime currently
offers tools again after a successful lookup; max_tool_rounds rejects the next
tool request rather than directing the next request to a final-answer phase.
Native WorkflowFactory forbids acquisition bindings, and Runtime acquisition
itself does not remove tools after its first round.

## Proposed change

Add an opt-in, host-configured endpoint feature
`finalize_after_tool_rounds: 1`. After the configured number of tool rounds,
the next provider request offers no tools and receives a host-owned instruction
to return the requested final answer using the available evidence. Do not claim
that the evidence is sufficient or provide any answer key. Validate the feature
as an integer from one through the effective maximum tool rounds. Default
behavior remains unchanged.

If a provider nevertheless requests a tool during finalization, reject it before
dispatch with a distinct closed failure code. Preserve actual request, token,
tool, timeout and cancellation evidence; never refund unknown usage or retry an
uncertain request. Keep no-progress shutdown distinct from explicit finalization.
Core and Harness engines need no change if the existing endpoint-feature path
is sufficient.

## Regression witnesses

1. A scripted provider repeats its lookup while tools are offered, but returns
   final JSON when tools are absent. Current code fails at the round limit.
   With finalization, expect two requests, one handler execution and accepted
   final JSON.
2. A provider ignores the final-only request and sends another tool call:
   closed failure, no second handler, known usage preserved.
3. Missing feature preserves the existing multi-round wire payloads and behavior.
4. A threshold of two permits two rounds then a final-only request, subject to
   unchanged provider/tool/token/time budgets.
5. Invalid values reject before provider dispatch; terminal failure and cancel
   paths preserve existing accounting contracts.

## Qualification and limits

Use an isolated Runtime worktree and a checksummed candidate wheel, never edit
the installed SDK or silently use an editable sibling checkout. Verify Runtime's
full suite, installed wheel smoke and consumer fixture integration. Record the
candidate wheel and manifest identity explicitly. No publication is proposed.
Any further live verification uses only the remaining approved capacity, with a
new coherent identity and fresh allowance that deducts all prior reservations.
If that capacity cannot cover the full prior schedule, report the reduced
schedule explicitly rather than merging unlike measurements.
