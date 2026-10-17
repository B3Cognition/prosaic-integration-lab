# Provider-neutral tool outcomes and bounded recovery

This candidate milestone adds portable tool failure evidence in Runtime, opt-in
recovery policy in Harness, and a consuming reference in Integration Lab. Core
remains unchanged. There are no model IDs, serving-specific branches or prompt
changes in the implementation.

Use `bounded_recovery=True` with memory `materials`, `execute_case`, and
`recover_case`. The enabled policy is bound into the saved execution identity;
changing it during replay fails admission. The default remains off. Runtime
and Harness must come from the exact tool-outcome candidate SDK family in
`dependencies/tool-outcome-candidate.json`.

Runtime distinguishes argument rejection before dispatch, authority denial,
completed controlled failure, and unknown effects after dispatch or journal
failure. Harness validates the public version 1 `ToolOutcome` contract and tool
version before granting another existing attempt. Handler error strings and
ordinary dictionaries cannot authorize recovery. A successful corrected call
already present in the invocation satisfies the required-tool check.

ALWAYS preserve existing attempts, request/tool/token caps and the deadline.
NEVER retry an uncertain effect or interrupted call automatically.

ALWAYS reconcile unknown effects through application-owned authority.
NEVER infer safety from missing completion evidence or a generic error message.

ALWAYS treat scoped traces as local diagnostic evidence and native receipts as
usage authority. NEVER relabel historic unclassified failures from speculation.
Validated categories contain no arguments, result values or exception text.

The memory case limits remain four provider requests, two tool calls, 8,192
reported tokens, 600 seconds and 512 output tokens. Argument correction can use
the already-permitted second attempt. It cannot create another allowance.
Receipt-only replay preserves saved trace bytes and denies new inference.

The installed synthetic qualification entry point is:

```text
python -I -B scripts/scoped_memory_smoke.py --source-root <checkout> --output <new-private-directory> --bounded-recovery
```

Run the script from outside the checkout using the isolated candidate Python.
It verifies installed package ownership before executing credential-free local
provider fixtures. It does not authorize or perform a live model comparison.
See the milestone qualification report for exact candidate hashes and coverage.

This milestone improves diagnosis and bounded failure handling. It does not
establish better model decisions, successful memory use, distributed effect
reconciliation, or production database/auth/billing acceptance.
