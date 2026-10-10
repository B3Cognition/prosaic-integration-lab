# Consume native Prosaic workflows

The Lab is a reference embedding service: an authenticated client proposes a
graph, the service admits it against host policy, and Harness executes the
admitted workflow. A prompt or LLM can generate the same proposal envelope.
The host controls which specialists, schemas, tools and capabilities it offers.

[Run the native demo](../README.md#try-the-native-workflow) first. It installs
the five original qualified SDK candidate wheels, builds a clean consumer and
exercises the actual HTTP service with synthetic inference and owned PostgreSQL.
The candidate profile is [dependencies/sdk-candidates.json](../dependencies/sdk-candidates.json).
It selects successful SDK qualification runs and exact source commits rather
than mutable SDK branches. The patch recipe uses `.cache/sdk-hardening/manifest.json`
and a fresh `.venv-hardening` environment; previous candidate evidence stays
under its original manifest and receipts. Public-index release and Lab 0.3.0 remain pending;
see [current status](current-status.md). Actions artifacts have 90-day retention.

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
