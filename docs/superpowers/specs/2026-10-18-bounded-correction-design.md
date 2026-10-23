# Consumer bounded correction with a matched no-critic baseline

Implement in Integration Lab, using public installed Runtime/Harness APIs.
No Core/SDK changes, named-model tuning, live run, automatic retry, new evidence
grant, push or release. Existing direct-v2 APIs remain unchanged. Native
execution and the user's question opt-out persist; this is the requested scope.

Two independently budgeted arms use the same task, profile, worker instructions,
scoped evidence, corrector contract, host diagnostics and acceptance policy.
`no-critic`: worker→host check→at most one corrector→host gate.
`critic`: worker→host check→at most one critic→at most one corrector→host gate.
Correct drafts skip correction (and unnecessary critic); correct non-ready
drafts stop for human review. Only schema-valid, correctly bound drafts can be
corrected. Invalid artifacts and accounting/admission failures stop safely.

The worker has one lookup and at most two requests. Critic and corrector each
have at most one request and zero tools, enforced with nested public budgets.
One outer ExecutionBudget covers the entire arm:4requests/2tools/8192reported
tokens/600seconds/output512. Nested activation never renews the outer budget.
No extra lookup occurs during correction. Unread evidence can yield a correct
insufficient result, but cannot become task acceptance by inventing a value.
Unknown usage, component input/output breaches and exhausted continuation
reservations halt further dispatch; preserve actual reported usage and receipts.

Generic `lab_runner.bounded_correction` constructs sanitized feedback from
trusted host diagnostics, validates critic advice against host field failures,
and compares matched reports. No domain grammar/provider/model branches.
The rollout adapter owns graph, scoped lookup, deterministic diagnostics and
correction instructions. Feedback contains field paths/codes, scoped source
references, assignment/draft/evidence bindings and supported critic issue hints;
it never contains hidden expected answers, arbitrary critique text or new records.
Original receipts remain intact; correction is a separate named step, not a
replacement of the original output. Host checks decide final acceptance.

Pair comparison requires identical initial draft/evidence, task/profile,
worker/corrector contracts, host diagnostics, limits and policy revisions.
Mismatches must be reported as unmatched, not pooled as critic benefit. The
critic arm's only additional input is verified advisory information. A pair is
two samples, each needing its own full reservation for any future live study.
Report initial/final field correctness, safe escalation versus task acceptance,
ignored/regressing corrections, critic reachability and marginal request/token
cost. Scripted tests prove plumbing/measurement, not causal model improvement.

Recovery only reads verified copies and makes zero requests. Existing claims
cannot redispatch. Adoption documentation shows consumer replacement points,
role qualification, trusted authorization and budgets. Full offline suite,
both-wire installed smoke, recorded faults/interruption checks and one fresh
whole-change review precede completion. Preserve all prior evidence/environments,
38live ledgers,8unknowns, charges1494/605/1805193 and ceilings1524/625/1976623.
