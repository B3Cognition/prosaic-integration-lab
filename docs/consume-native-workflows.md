# Consume native Prosaic workflows

The Lab is a reference embedding service: an authenticated client proposes a
graph, the service admits it against host policy, and Harness executes the
admitted workflow. A prompt or LLM can generate the same proposal envelope.
The host controls which specialists, schemas, tools and capabilities it offers.

[Start with the guided quickstart](quickstart.md) for a credential-free admission
example and optional service/browser demonstrations. The native service demo installs
the five verified public SDK wheels, builds a clean consumer and
exercises the actual HTTP service with synthetic inference and owned PostgreSQL.
The active [release manifest](../dependencies/releases.json) pins actual public
download URLs, exact versions, original wheel hashes and qualified source
commits. The current Lab 0.6.2 train selects Core 0.4.1, Runtime 0.9.8/recorder 0.3.0 and Harness
0.9.4/store 0.4.0. The same
family also supplies the [conversation API](conversations.md).
Use a fresh `.venv-public` environment. The historical
[earlier Lab 0.4.0 release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.4.0)
is at source `f47328d2d5a8e7253ad6cb199583f9f0d311fd60`, qualified by
[run 38147824985](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38147824985):
920 required cases across four Linux/database cells, zero failures/errors/test
skips and all 32 lane plus four separate demo cleanups verified. See its
[release closure](verification/production-readiness-m1-m2-2026-10-11.md#lab-040-release-closure).
That historical release's SDK pins remain in
[`releases-lab-0.4.0.json`](../dependencies/releases-lab-0.4.0.json). The current
checkout adopts the new published SDKs; see the
[adoption ledger](verification/published-conversation-adoption-2026-10-13.md).

The historical [Lab 0.3.0 release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.3.0) was published
at source `59ea44b97224415e22fec64c2b9bf39bd9503276`, qualified by released-mode
[run 38119573605](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38119573605).
Its original source and artifacts remain preserved; see
[current status](current-status.md). The separate
[candidate profile](../dependencies/sdk-candidates.json), candidate cache and
earlier receipts remain available for reproducing their original evidence.

## What the client sends

1. Discover authorized aliases and the authoring schema through
   `GET /workflow-catalogue`.
2. Submit `{"definition": ...}` to `POST /workflow-proposals` with an
   owner-scoped idempotency key. Optional `inline_agents` requires a separate
   host grant. Successful admission stores an immutable proposal and returns its
   public reference; it makes no model calls.
3. Submit the returned `proposal_id` and JSON `inputs` to `POST /native-runs`
   with a run idempotency key. Inputs are validated and snapshotted before the
   service reserves a run or dispatches inference.
4. Read `GET /runs/{run_id}`. A waiting run contains the curated `interaction`,
   including its committed revision, actual choices and approved review content.
5. Send a choice and schema-conforming response to
   `POST /runs/{run_id}/resume`, using that exact interaction revision. The demo
   resumes on the other replica and completes without another provider call.
6. Read owner-scoped `GET /runs/{run_id}/usage`. The synthetic two-specialist
   example records two complete calls; all estimates are billing-ineligible.

The fixture graph follows `finder → reviewer → check → gate → pause → finish`.
The [native demo client](../lab_runner/native_demo.py) shows the complete request
sequence and checks in executable Python. Its fixed synthetic receipt is safe
to share; the owned runner keeps authentication and service configuration private.
The same API accepts admitted graphs built from the host's offered aliases.
The [manual HTTP example](native-workflows.md#catalogue-proposal-execution-and-human-response)
shows request bodies and responses. Generated graphs never provide endpoints,
credentials, filesystem paths, executable code or a `base_dir`.

## What the host supplies

| Responsibility | Public SDK API | Lab implementation |
| --- | --- | --- |
| Approved agents, schemas and public descriptions | `ProsaicArtifact`, `WorkflowCatalog` | [`NativeExecution.material`](../src/prosaic_integration_lab/native_execution.py) |
| Private Runtime endpoints, validators and tool implementations | `RuntimeConfig`, `WorkflowBindings`, `Validator`, `CustomTool` | [`native_execution.py`](../src/prosaic_integration_lab/native_execution.py) |
| Allowed aliases, independent composition/inline/tool grants and finite budgets | `WorkflowPolicy`, `WorkflowFactory` | [`NativeExecution.factory`](../src/prosaic_integration_lab/native_execution.py) |
| Exact retained construction and proposal identity | `WorkflowBundle.prepare_json`, `WorkflowReference`, `WorkflowBundle.reconstruct` | [`bundles.py`](../src/prosaic_integration_lab/bundles.py), [`proposals.py`](../src/prosaic_integration_lab/proposals.py) |
| Input preparation, execution and revision-checked human response | `workflow.prepare_inputs`, `Harness.run`, `Harness.interaction`, `Harness.resume` | [`NativeExecution.start_request/status/resume`](../src/prosaic_integration_lab/native_execution.py) |
| Durable checkpoints and measured usage | `PostgresRunStore`, `PostgresRecorder`, `ExecutionContext` | [`execution.py`](../src/prosaic_integration_lab/execution.py), [`native_execution.py`](../src/prosaic_integration_lab/native_execution.py) |
| Application authentication, ownership, idempotency and filtered HTTP transport | Application code around public SDK calls | [`identity.py`](../src/prosaic_integration_lab/identity.py), [`metadata.py`](../src/prosaic_integration_lab/metadata.py), [`app.py`](../src/prosaic_integration_lab/app.py), [`views.py`](../src/prosaic_integration_lab/views.py) |

Start a product integration by replacing the synthetic catalogue material and
Runtime configuration with your own approved registrations. Keep tenant, actor,
billing account and namespace derived from authenticated host context. Authorize
the client before offering aliases, accepting proposals or reading a run.
Tool registrations and business operation keys are host-owned; client prose
does not grant permission to invoke a registered tool.

Admission and binding are separate from execution. Building a factory or
preparing a proposal validates and seals the supplied graph without model or
product callback execution. Execution uses the admitted workflow and current
host authorization. Preserve old bundle definitions, assets and semantic callback
versions while proposals or runs refer to them. Reconstruct from the original
proposal/reference; missing bundles fail explicitly instead of selecting newer
bindings. A version label alone does not change semantic bundle identity.

Specialist composition, introducing inline instructions and tool access have
independent grants. Omitting `model_tier` selects the configured host default
when policy allows it; an explicit named tier also needs a configured route and
authorization. Canonical prose validation checks structure, while the host
policy and execution limits enforce capability access.

The detailed SDK contract is in the qualified
[Harness workflow factory guide](https://github.com/B3Cognition/prosaic-harness/blob/cba77d09d1844ff624911295aecd58021b457c08/docs/workflow-factory.md).
Its examples cover trusted in-memory assembly, composition, inline agents,
retained bundles, input snapshots, structured human interaction and contextual
tools. See the qualified
[Runtime accounting guide](https://github.com/B3Cognition/prosaic-runtime/blob/3566731c39a3fff2837acd93a96baa2187764206/docs/accounting.md)
for usage and invocation scope, and the Lab
[persistence guide](persistence.md) for explicit schema migration and separate
database roles.

## Construct a workflow in memory

This runnable admission example uses one registered agent, a closed result
schema and a human pause. Its illustrative endpoint is host-owned configuration;
construction never contacts it. Replace it with your authorized model binding
before execution. The JSON proposal contains only logical references and graph
data. No `base_dir`, provider credential or executable registration comes from
the client.

```python
import json
from prosaic_harness import (
    WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy,
)
from prosaic_runtime import EndpointConfig, ProsaicArtifact, RuntimeConfig

finder = ProsaicArtifact.from_inspection({
    "id": "approved/finder.md", "type": "subagent",
    "frontmatter": {"name": "finder", "description": "Find an approved entity", "tools": []},
    "body": "ALWAYS return one JSON object with entity_id. NEVER invent an entity.",
})
result_schema = {
    "type": "object", "properties": {"entity_id": {"type": "string", "maxLength": 64}},
    "required": ["entity_id"], "additionalProperties": False,
}
config = RuntimeConfig({
    "service": EndpointConfig("https://models.example.invalid/v1", "host-model",
                              features={"streaming": False}),
}, {}, "service", allowed_tools=frozenset())
factory = WorkflowFactory(
    catalog=WorkflowCatalog(agents={"finder": finder}, schemas={"result": result_schema}),
    bindings=WorkflowBindings(config=config),
    policy=WorkflowPolicy(
        allowed_agents=frozenset({"finder"}), allowed_schemas=frozenset({"result"}),
        max_calls=1, max_attempts=1, timeout_s=30, max_tokens=256, max_run_s=60,
        max_provider_requests_per_invocation=1, max_tool_calls_per_invocation=0,
    ),
)
proposal = {"definition": {"version": 1, "start": "find", "steps": {
    "find": {"kind": "agent", "agent": "finder", "schema": "result", "next": "review"},
    "review": {"kind": "pause", "question": "Accept the selected entity?",
               "choices": {"accept": "done", "reject": "rejected"}, "requires": ["find"],
               "response_schema": "result"},
    "done": {"kind": "finish", "requires": ["find"]},
    "rejected": {"kind": "finish", "outcome": "rejected"},
}}}
workflow = factory.build_json(json.dumps(proposal))
inputs = workflow.prepare_inputs({"query": "sample"})
print(workflow.fingerprint)
```

Admission validates and seals the workflow; input preparation owns a bounded
snapshot. Neither operation invokes a model, tool or validator. In a service,
authenticate the caller and choose its host policy before admission, then
persist the immutable proposal/reference and use `Harness` with the authorized
store for execution. The Lab's [native execution binding](../src/prosaic_integration_lab/native_execution.py)
and [native demo client](../lab_runner/native_demo.py) show that execution and
revision-checked human-resume path, including measured synthetic calls.

## Handle retries and recovery deliberately

Proposal and run keys replay the original owner-scoped operation. Reusing a key
with a different body returns 409. Invalid human responses return safe 422
diagnostics and preserve the revision; stale revisions return 409 and require a
fresh interaction. Current revocation is checked before start or resume.

An uncertain start or tool effect requires operator reconciliation. No automatic
redispatch is authorized by a missing checkpoint, HTTP response or usage receipt.
Explicit inference retry uses its own `retry_interrupted` consent. Unknown usage
under a finite budget stays blocked; human approval cannot turn it into known
usage or waive the budget. The Lab's consequential fixture uses an application
SQL journal and unique business-effect key; product integrations must retain
their own domain-specific authorization and recovery rules.

The native demo is an adoption example. The
[required eight-lane matrix](release-gates.md) additionally verifies SQL fencing,
effect loss, original-release upgrades, limits and owned cleanup. Passing
synthetic fixtures does not qualify a real provider or a production deployment.
