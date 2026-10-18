# Provider-neutral continuation budgeting

User authorization: publish reviewed Runtime/Harness changes first, keep Lab
memory experimental, then implement continuation budgeting under current limits.
Native execution and the established planning opt-out continue to apply.

## Problem and outcome

The balanced twelve-sample study refused three smaller-model continuations that
exceeded a fixed quotation slot by 27 or 59 input tokens. The actual next request
would fit the shared case allowance. Memory changed rounding slack and therefore
admission, confounding its apparent benefit. Preserve these results unchanged.

Use a new opt-in version-2 context plan. Quotation remains an estimate used to
select optional memory and reserve planning headroom; it is not a hard limit on
each later request. Count each owned final native request with the qualified
base counter, enforce its context capacity and fixed output bound, then let the
public Runtime ExecutionBudget atomically admit its input plus maximum output
against reported and in-flight usage. One scope spans every Harness attempt.
No provider/model names, heuristic estimates or feedback-specific tuning belong
in this policy. No new Runtime/Harness release is needed for this consumer fix.

## Constraints

- Keep default version-1 plans, serialized contracts and refusal semantics.
- Opt-in changes context identity and frozen provenance; no rewriting old plans.
- Case caps: 4 provider requests, 2 tools, 8,192 tokens, 600 seconds, 512 maximum
  output tokens per request. Cumulative ceilings: 1,475 requests, 604 tools,
  1,976,623 tokens. No live dispatch in this milestone.
- Runtime remains the sole authority for dispatch, settlement, unknown usage,
  overrun fencing and concurrent reservations. Proposal logs are diagnostics.
- ALWAYS require a shared trusted Runtime budget for version-2 execution. NEVER
  infer paid usage from a model message or diagnostic observer.
- Preserve mandatory current evidence; optional recall still requires an admitted
  full quotation. Dynamic admission does not promise arbitrary future completion.
- Removing optional recall must not create a smaller hard continuation slot:
  actual request admission depends on real counts and shared allowance.
- Receipt-only recovery performs no inference, quotation or retrieval and leaves
  saved context traces unchanged. Model errors are never authorization to retry.

## Verification

Watch regressions fail before implementing: variable tool results above a quote
fit under the unchanged case cap; identical continuation counts with and without
optional recall receive identical domain admission; context/output/counter drift
still rejects; unknown usage, concurrent in-flight reservations, cap exhaustion
and Harness repair cannot replenish allowance. Exercise both provider wire
formats with synthetic local fixtures. Preserve v1 tests and strict malformed
v2 validation. Build and inspect an installed wheel against released SDK bytes;
run offline acceptance and receipt replay, and preserve all historic ledgers.

Memory stays experimental. No new efficacy conclusion or production readiness
claim follows from these synthetic checks. A later fresh held-out live comparison
requires its own frozen protocol and allowance proof under the existing ceiling.
