# Synthetic native workflow HTTP example

For a complete runnable example, follow the
[released-package installation and native demo](../README.md#try-the-native-workflow).
The demo creates its own database, model fixture and replicas, drives the routes
below, handles generated credentials privately and verifies cleanup. The
[consumer guide](consume-native-workflows.md) maps these routes to supported
public SDK integration patterns.

Native execution is opt-in private service configuration. The example in
`configs/native.example.json` illustrates the `lab_runner.model` fixture on
`model:8000` and two packaged specialists. It contains illustrative fixture identities
and DSNs; provision separate migration/runtime roles and deliver the real private
configuration using the existing secret-delivery path. Fixture tokens are
lab-only authentication. The example uses the shipped `/srv/lab/assets` directory
in both consumer images. These endpoints exercise synthetic find, review, check,
gate, pause and finish; they access no product data or external business service.

This implementation consumes the new public SDK factory/bundle/interaction APIs.
The active manifest uses Core 0.4.1, Runtime 0.9.3/recorder 0.3.0 and Harness
0.8.2/store 0.3.0. The [timeout patch ledger](verification/conversation-timeout-patch-2026-10-14.md)
records the latest adoption. Earlier released-mode use is recorded in the
[adoption ledger](verification/published-conversation-adoption-2026-10-13.md).
The historical [Lab 0.4.0 release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.4.0)
retains its patch pins in `dependencies/releases-lab-0.4.0.json`. Its released-package Linux AMD64/ARM64 ×
PostgreSQL 16/18 matrix passed at source `f47328d` in
[run 38147824985](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38147824985),
with 920 required cases, zero failures/errors/test skips and all 32 lane plus
four separate demo cleanups verified. See the
[release closure](verification/production-readiness-m1-m2-2026-10-11.md#lab-040-release-closure).

The historical Lab 0.3.0 was published. Its released-package native Linux
AMD64/ARM64 × PostgreSQL 16/18 matrix passed at source `59ea44b` in run
`38119573605`; see [public adoption](verification/public-release-adoption-2026-10-11.md).
Use the active release manifest for the released-package recipe. The earlier
candidate train and its retained profile remain recorded in the historical
[adoption ledger](verification/native-adoption-2026-10-10.md) and
[original ecosystem checkpoint](verification/ecosystem-production-2026-10-10.md).
Synthetic fixture qualification does not certify a live provider or deployment.

## Host authority and retained bundles

`native.bundles` contains immutable historical host definitions. Each definition
has a version, owned fixture endpoint, optional host model-tier `routes`, optional
private native `assets` directory, private
`operation_namespace`, optional `journal_identity` and frozen tenant `policies`.
Keep old definitions and their exact packaged assets and callback versions while
their proposals/runs remain live. The SDK seals configuration, content, policy,
validator versions and operation/journal bindings into the bundle identity.
The application reconstructs from the exact persisted reference and fails with
`bundle_unavailable` when it cannot find that bundle. It never substitutes the
newest bundle. Rotate changed content/bindings by retaining separate definitions
and using each definition's private `assets` directory for its exact historical
native content. Omission selects the packaged `assets/native` fixture. These paths
are host configuration and never accepted in client proposals.

`native.tenants` selects each tenant's current bundle version and current grants.
Grant fields are `composition`, `inline`, `agents`, `schemas`, `validators`,
`model_tiers` and `tools`. Catalogue and proposal-schema discovery project the intersection
of current grants and the selected retained bundle's frozen admission grants,
using its exact captured public catalogue/bindings without rereading files.
Current authorization cannot expand a frozen bundle's capabilities. To enable a
new capability, register an explicit new host bundle and select its version in
current tenant grants. The original bundle identity and owner/key replay remain
unchanged. Composition and inline instructions are separate permissions:
composition does not grant inline agents, and a single granted inline agent does
not grant multi-agent composition. The approved specialist prose omits model tiers
and uses the host default. Explicit inline tiers must be both configured through
`routes` and allowed through `model_tiers`. Current revocation is checked before
native start/resume. Owner/key proposal replay returns the original admitted
reference under changed grants without new admission.

Tenant, actor, billing and application namespace come from authenticated host
context; execution context comes from the frozen reservation. Clients cannot
choose endpoints, bindings, validator callbacks, filesystem paths, operation
namespaces, journal identities or invocation scope. This lab supplies no
filesystem `base_dir`; native proposals cannot opt into one. No application code
imports private SDK APIs or executes catalogue manifests.

The example host selects three workflow invocations, 4,096 reported tokens and
120 seconds per workflow; its no-tool catalogue allows at most one provider
request and zero tool calls per invocation. The owned native fixture separately
registers a consequential tool with its own grants, journal and finite call caps.
The SDK forwards remaining time/tokens and derives invocation/run/step
references from persisted execution state. Input snapshots are owned JSON values
with a 4 KiB workflow cap; the HTTP run/resume transport cap remains 8 KiB.

## Catalogue, proposal, execution and human response

The following requests assume an already running native-enabled fixture service.
Set `LAB_URL` to its loopback HTTP replica origin and `LAB_API_TOKEN` to an owner
token supplied by that service's trusted fixture setup. Its host operator must
select provider scenario `native` before these requests. The native demo does
this automatically and tears its stack down; it does not leave a service running
for later curl requests. The illustrative JSON configuration alone does not
provision a service. From this checkout's candidate environment:

```sh
: "${LAB_URL:?Set the configured native service origin}"
: "${LAB_API_TOKEN:?Set its owner token}"
curl --fail -sS "$LAB_URL/workflow-catalogue" \
  -H "Authorization: Bearer $LAB_API_TOKEN"
```

Use the same authenticated owner for every request. The gateway authenticates
before consuming a body. Only exact `POST /workflow-proposals` accepts 64 KiB;
other POST routes retain 8 KiB. Keys are required for proposals and starts and
are bounded to 128 UTF-8 bytes. Unknown fields are rejected.
Pause-choice names are limited to 64 characters by the host transport contract.
The catalogue's proposal schema includes that constraint, and admission rejects
unsupported names before persistence. A retained unsupported proposal keeps its
original reference but fails before a native run is reserved. Unicode and
escaped names within the limit round-trip through the existing 8 KiB resume
body limit.

1. `GET /workflow-catalogue` with that owner's bearer token returns
   `bundle_version`, `manifest` and `proposal_schema`. The current tenant's public
   aliases/permissions are projected from the actual SDK factory. Descriptions are
   explicitly synthetic metadata; private prose, endpoints and journal bindings
   are absent. Schemas are excluded from the manifest by default.
2. Save the fixture proposal with the public application helper:

   ```sh
   PYTHONPATH=src .venv-candidate/bin/python -c 'import json; from prosaic_integration_lab.native_execution import approved_proposal; print(json.dumps(approved_proposal()))' > proposal.json
   curl --fail -sS "$LAB_URL/workflow-proposals" \
     -H "Authorization: Bearer $LAB_API_TOKEN" \
     -H 'Idempotency-Key: synthetic-proposal-1' \
     -H 'Content-Type: application/json' --data-binary @proposal.json
   ```

   The exact envelope is `{"definition":...}` with optional `inline_agents` only.
   Admission calls no models, validators or Harness store. Success returns
   `{"proposal_id":"...","reference":{...}}`. Save this response. Replaying the
   same owner/key/canonical body returns this original reference; changing its
   body returns 409.
3. Start using that `proposal_id`:

   ```sh
   curl --fail -sS "$LAB_URL/native-runs" \
     -H "Authorization: Bearer $LAB_API_TOKEN" \
     -H 'Idempotency-Key: synthetic-run-1' \
     -H 'Content-Type: application/json' \
     --data '{"proposal_id":"REPLACE_WITH_SAVED_ID","inputs":{"entity_id":"sample-1"}}'
   ```

   SDK input preparation happens before reservation or dispatch. The worker
   reserves immutable attribution, claims start, then runs the owned input. A
   matching owner/key replays the original reservation without more model calls.
   A `starting` record whose SDK checkpoint is absent returns `start_uncertain`
   and requires operator reconciliation; it never automatically redispatches.
4. `GET /runs/{run_id}` returns curated status and `interaction` or null. At the
   fixture pause, interaction contains `runId`, `revision`, `stepId`, question,
   actual `accept`/`reject` choices, deadline and response schema digest. Human
   projection uses one verified SDK snapshot. Both `review_outputs` and
   `response_schema` are independent host opt-ins, disabled by default. With the
   example opt-ins, only the approved `review` step's `entity_id` and `approved`
   fields and the host-approved decision schema are included. Inputs, binding
   records, history, evidence and arbitrary outputs are excluded. Public
   catalogue/interaction views use the SDK's 256 KiB output bound; the 8 KiB
   run/resume limit applies only to incoming request bodies.
5. Resume with the exact interaction revision and schema-conforming response:

   ```sh
   curl --fail -sS "$LAB_URL/runs/REPLACE_WITH_RUN_ID/resume" \
     -H "Authorization: Bearer $LAB_API_TOKEN" \
     -H 'Content-Type: application/json' \
     --data '{"expected_revision":"REPLACE_WITH_INTERACTION_REVISION","choice":"accept","response":{"confirmed":true}}'
   ```

   Invalid responses/choices return a safe 422 code and bounded structural issues;
   stale revisions return 409. Neither changes state or revision. Retry requires
   the separate explicit `retry_interrupted: true` field; a response, usage record
   or arbitrary choice never supplies retry consent. Current revoked grants deny
   start/resume before any SDK execution.

`GET /runs/{run_id}/usage` keeps the original frozen owner-scoped accounting
projection. Ownership is checked before SDK status or recorder queries. Usage
evidence supplies neither retry consent nor billing/approval authority.

Existing `POST /runs` still accepts only `approval`/`synthetic` and the original
`task` semantics. Existing approve/reject projections remain unchanged. Optional
monitoring is delivered through SDK `observer`; ordinary monitoring exceptions
cannot suppress accepted work. The receipt-crash fixture's `on_event` callback
remains a critical evidence gate.
