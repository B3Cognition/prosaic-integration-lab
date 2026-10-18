# Consumer blueprint: qualify roles and explain evidence failures

This is a reusable **Lab consumer pattern**. It is not a certification of a model
or a change to Runtime/Harness behavior. Core distributes artifacts; Runtime
executes models and records usage; Harness owns workflow state. Your application
owns domain policy, evidence grants, role fitness and call authorization.

`lab_runner.role_qualification` contains no model names, provider branches,
rollout grammar or inference calls. `lab_runner.handoffs.diagnostics` is one
domain adapter you can replace. You do not need the rollout task or these two
tested models to adopt the pattern. Existing direct APIs and prompts are unchanged.

## Supply your domain contract and trusted checks

```python
from lab_runner.role_qualification import FieldCheck, assess_output

shipping_schema = {
    "type": "object", "properties": {"dispatch": {"enum": ["hold", "send"]}},
    "required": ["dispatch"], "additionalProperties": False,
}
assessment = assess_output(
    saved_result.stdout, shipping_schema,
    checks=[FieldCheck("/dispatch", "hold", evidence_refs=("manifest:missing",))],
    exit_code=saved_result.exit_code,
    usage_known=saved_result.token_usage is not None,
    budget_violation=host_budget_breach,
)
```

The expected value comes from your deterministic domain policy and the exact
authorized evidence snapshot—not from the worker, critic, a hidden example
answer, or an arbitrary client field. The reference `manifest:missing` must name
host-verified evidence or a host policy fact. These helpers cannot verify your
business rules or source permissions for you.

Diagnostics return codes, JSON pointers and evidence references. They omit raw
expected/observed values, validation messages and provider payloads. Use a private
operator view for additional source details; do not automatically feed hidden
gold or sensitive evidence back to a model. Schemas must be bounded inline closed
objects; schema references are rejected without network resolution. Canonical
comparison distinguishes booleans from numbers. `comparison="set"` ignores array
order but rejects duplicates. Unknown usage, budget breaches, invalid output and
explicit host-observed abstention never pass qualification.

The rollout adapter verifies saved sample, assignment, invocation, request,
receipt and source-hash bindings before assessing fields. It preserves original
receipts. Correct missing/unread/conflict results are assessed under the task's
policy; they are not automatically counted as bad answers or generic abstention.
Critic diagnostics report `missingIssueFields`, `unsupportedIssueFields`, and
`coarseEscalationCorrect`. A warning can be correct while the review fails for
omitted fields. This avoids treating partial detection as complete verification.
Receipt arguments remain original; evidence projection at transmission is owned
by the separately qualified public Runtime adapter.

## Bind qualification to the configuration consumers actually deploy

```python
from lab_runner.role_qualification import (
    qualification_binding, qualification_report, require_qualification,
)
from lab_runner.quality.contracts import digest

binding = qualification_binding(
    role="shipping-worker", schema=shipping_schema,
    profile_fingerprint=host_profile_fingerprint,
    adapter_revision="shipping-adapter-v1",
    evaluator_revision="shipping-rules-v3",
    evidence_revision="authorized-manifest-v2",
    suite_revision="shipping-role-suite-v1",
)
observation = {
    "caseId": "parcel-case-1", "scenario": "missing-manifest",
    "bindingDigest": digest(binding), "evidenceDigest": verified_receipt_digest,
    "assessment": assessment,
}
observations = [observation]  # collect every case in the predeclared suite
report = qualification_report(
    binding, observations, required_scenarios=required_scenarios,
    origin="synthetic",  # scripted responses cannot qualify a live model
)
```

For live qualification, a separately authorized bounded evaluation collects real
observations from your selected model/profile and records `origin="live"` in
trusted host code. Do not relabel scripted results as live evidence. No live
evaluation runs in this milestone. Author the scenario suite before seeing
outputs; cover valid answers, deliberate flaws, non-ready evidence, abstention,
invalid/truncated output, scope/binding failures and each domain rule. Include
every measured result; do not select only passing samples. This is application
policy: a generic helper cannot know which cases adequately cover your domain.

Changing the schema, profile fingerprint (model/provider/settings), adapter,
evaluator, evidence policy, suite revision or limits invalidates the prior
record. Version changes must include relevant SDK/transport changes. Store reports
in trusted host storage and pin `digest(report)` independently of the report.
Choose an appropriate expiry/requalification policy for mutable serving stacks.

Before using a qualified role, check the host-pinned record:

```python
require_qualification(
    trusted_report, expected_binding=current_binding,
    trusted_digest=host_pinned_report_digest,
    required_scenarios=current_required_scenarios,
)
# Then separately obtain call consent, reserve full budgets, enforce evidence
# grants and run through the public Runtime/Harness APIs.
```

This gate rejects synthetic-only evidence, mismatched configuration, changed
reports, missing scenarios and failed/abstaining observations. **A digest is not
a signature, a report is not authorization, and role qualification does not
guarantee success on a future case.** Never accept report contents, expected
bindings, evidence digests or the supposedly pinned digest from a model/client.
Review correctness and workflow acceptance remain separate host decisions.

## Budgets, tuning and adoption

This Lab blueprint retains4requests/2tools/8192reported tokens/600seconds/
512output tokens per case. Its binding helper accepts lower limits, rejects
higher limits, and never changes admission or cumulative allowance. These are
the current Lab policy bounds, not universal Runtime limits. Consumers own their
approved budget policies and must version any adaptation. Retain unknown
reservations and observed overruns; qualification is not consent to retry.

Consumers can supply other roles, policies, schemas, evidence adapters, suites,
models and providers. Tune prompts/model settings against development cases,
invalidate the old binding, then evaluate on separately frozen held-out cases.
Report invalid outputs, partial reviews, abstentions, costs and unreached roles.
Keep synthetic plumbing coverage separate from actual model quality. A critic
cannot substitute for source checks or turn a wrong worker into a correct answer.
Repair and automatic routing are intentionally separate future consumer policies.

Offline installed proof:

```text
python -I scripts/role_qualification_smoke.py --source-root /path/to/checkout --evidence-dir /private/fresh/evidence --output /private/fresh/result.json
```

The smoke uses scripted OpenAI-compatible and Anthropic wire fixtures, validates
both roles, and demonstrates a second domain without the rollout adapter. It
does not contact real providers or certify those protocols/models in production.
