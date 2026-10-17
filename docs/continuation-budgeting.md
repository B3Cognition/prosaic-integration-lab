# Experimental continuation budgeting

Lab now offers `ScopedContext(..., continuation_budget=True)`, built on public
Runtime 0.9.7 and Harness 0.9.4 APIs. It is opt-in and provider-neutral. Memory
remains experimental; this policy does not establish an accuracy benefit.

Default version-1 plans still enforce each frozen quotation slot. The opt-in
version-2 plan includes `dispatchPolicy: shared-execution-budget-v1`. Its
`inputBounds` and `requiredTokens` describe the full planning quotation used to
select optional memory, rather than a guaranteed bound on every possible later
response. Mandatory current evidence is preserved; an unaffordable mandatory
quotation still refuses execution.

The qualified counter measures each final native request, including the actual
tool results. The guard enforces model binding, fixed output, context capacity
and proposal count. One Runtime `ExecutionBudget` then atomically reserves the
measured input plus maximum output against the shared remaining allowance. Known
usage releases unused reservation; in-flight and unresolved usage cannot be
reallocated. The same scope spans every permitted Harness repair attempt.

ALWAYS run a version-2 guard inside the shared Runtime budget, as `execute_case`
does. NEVER treat a successful counter proposal as evidence of dispatch or paid
usage. `withinContext` means only that counting and domain validation succeeded;
the subsequent Runtime admission may still reject it. Private traces retain
both the quoted slot (`quotedInputBound`) and the enforced context domain
(`inputCeiling`). Receipts and Runtime recorder observations retain authority.

Case limits stay at four provider requests, two tools, 8,192 tokens, 600 seconds
and 512 output tokens per request. Removing optional recall cannot manufacture a
smaller hard continuation slot. Actual counts and actual remaining allowance
still determine admission; optional context may legitimately cost more tokens.
An admitted next request does not guarantee that all future requests will fit.

The policy is bound into frozen context identity. Existing evidence cannot be
reopened with a different policy. Receipt-only recovery reconstructs neither the
counter nor retrieval and preserves saved trace bytes without inference.

`dependencies/continuation-candidate.json` pins the five public SDK wheels and
their hashes. The packaged experimental benchmark provenance uses this manifest;
the default release manifest and historic candidate manifests remain unchanged.
No Lab release or new live comparison is included in this milestone.

Run installed-wheel qualification with:

```sh
python -I scripts/continuation_budget_smoke.py \
  --source-root /absolute/path/to/prosaic-integration-lab \
  --output /private/tmp/continuation-qualification.json
```

It exercises OpenAI-compatible and native Anthropic fixtures, variable tool
responses, exact shared-budget fits, exhaustion, unknown usage, overruns,
concurrent reservations and request caps. Counts are synthetic fixture units;
this is not live tokenizer or provider certification. See the
[design](superpowers/specs/2026-10-17-continuation-budgeting.md) and
[implementation plan](superpowers/plans/2026-10-17-continuation-budgeting.md).
