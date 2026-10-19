# Consumer blueprint: trajectory evaluation

This experimental Lab example joins public Runtime/Harness observations with
your application's evidence checks, approvals and independently verified
outcomes. The collector has no model names or provider-specific branches and
requires no observability vendor. It adds no SDK execution or recovery engine.
Core distributes prose; Runtime executes calls and records accounting; Harness
owns workflow state. Applications own domain truth, authentication and access.

## Attach to the public SDK boundary

```python
import secrets
from lab_runner.trajectory import Trajectory, save_report

trace = Trajectory(trusted_run_id,
    binding_digest=host_configuration_and_evaluator_digest,
    key=secrets.token_bytes(32))
# Pass observer=trace.observe to Harness. Its public integration propagates
# the observer to Runtime. For direct Runtime, pass observer=trace.observe
# with a trusted InvocationScope containing run_id.
```

Bind workflow, rules, adapters, evidence revision and evaluation suite. Authenticate
scope before constructing the collector. It accepts one run. Foreign/malformed
records increment rejection counts without interrupting execution. Keep existing
SDK accounting and execution budgets; observations are best effort.

```python
trace.annotate("worker", kind="evidence", status="missing",
               evidence_digest=verified_manifest_snapshot_digest)
report = trace.report({
    "bindingDigest": host_configuration_and_evaluator_digest,
    "status": "failed",
    "categories": ["model_output", "evidence"],
    "evidenceDigest": verified_checkpoint_and_receipts_digest,
    "usage": {"providerRequests": independently_reconciled_requests,
              "toolCalls": independently_measured_tools,
              "reportedTokens": None},  # unresolved stays unknown
})
save_report(private_report_path, report)
```

The host must verify these inputs. Shape/binding validation does not certify
business truth, authenticity or accounting provenance. Observed completion cannot
override this assessment. Passing requires known usage and no verified failures.
Failed/incomplete assessments require categories from `model_output`, `evidence`,
`provider`, `tool`, `budget`, `accounting`, `host_policy`. Multiple categories can
coexist; they are host findings, not causal deductions from observation order.

Host annotations support evidence verified/missing/conflicting; validation
passed/failed/incomplete; approval pending/approved/denied/revoked/spent;
recovery inspected; and host policy allowed/denied. Record actual host checks.
An annotation is never dispatch permission or effect-completion evidence. Use
the separate [approval](tool-approval.md), [failure isolation](failure-isolation.md)
and public SDK/domain journals for their respective authority.

## Read a trajectory honestly

The report holds bounded observations and host annotations in capture order.
Keyed run/stream/step/evidence references correlate within one run/binding.
Equal step references join host checks to SDK observations. Streams identify
source/invocation; a Harness recovery execution has a separate stream. Capture
order is not causal order; no parent edge is invented. Report integrity digests
are not event identities.

Runtime outcome/reason/tool codes are observation hints. The assessment is the
separately supplied verified host result. Observer token/request counts are
excluded; usage comes from trusted receipts/accounting. Preserve unknowns.
Compare quality by status/category and efficiency by measured requests/tools/
tokens with explicit known denominators. Telemetry grants no allowance, consent,
retry permission or invoice authority.

`monitoring` exposes rejected/dropped records, sequence issues, open streams and
an empty-record flag. Capture is thread-safe and bounded to512SDK records and
128host annotations; overflow records loss. No detected gap certifies completeness:
whole unseen streams and trailing loss may be undetectable. An open observation
stream does not establish that an effect is active or retryable.

Exports omit raw IDs, labels, model/tool names, prompts, outputs, sources and
exception messages. Independent private HMAC keys prevent casual cross-consumer
correlation; rotation changes references. Keys remain in memory. Pseudonyms are
not access controls. Hosts must restrict reports and use safe binding digests.

## Offline inspection and second-domain demonstration

```python
from lab_runner.trajectory import read_report
saved = read_report(private_report_path,
                    binding_digest=host_configuration_and_evaluator_digest)
```

Private atomic writes use owner-only directories/files. Reads require an owned
private regular file, reject symlink paths, bound input and validate the closed
contract, expected binding and integrity. No inference or sockets are needed.
A hash detects accidental corruption; it does not authenticate a malicious
replacement. Protect storage/authentication in your deployment.

`lab_runner.trajectory_fixture` is a second-domain parcel example using actual
public Harness/Runtime calls against credential-free loopback OpenAI-compatible
and Anthropic scripted responses. One manifest lookup precedes a structured
dispatch/hold recommendation. Host rules evaluate current evidence, including
a correct hold when authority is missing. Other cases deliberately return a
wrong decision, invalid JSON, tool error and provider error with unknown usage.
A ready answer creates a pending host approval; no parcel dispatch executes.

With the Lab wheel and released SDKs installed:

```sh
python /path/to/checkout/scripts/trajectory_smoke.py --output /absolute/private/new-proof
python /path/to/checkout/scripts/trajectory_smoke.py --output /absolute/private/new-proof --replay
```

Execution requires a fresh private directory. It runs12synthetic lanes and
network-denied saved-state inspection. Replay reads reports with network denied.
Neither inspection calls Harness.run/resume nor renews approval. Detailed SDK
receipts remain private, separate from safe reports. Synthetic units qualify no
live counter/model, prompt-injection defense, production or distributed host.

For another domain, replace workflow/tool, evidence rules, schemas and evaluator;
retain the collector unchanged. Freeze suite/configuration before evaluating;
include all outcomes, unknowns and costs. Qualify your own models/counters.
Memory/correction remain experimental; no live allowance or limits change here.
