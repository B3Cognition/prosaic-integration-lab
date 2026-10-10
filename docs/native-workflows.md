# Synthetic native workflow HTTP example

Native execution is opt-in private service configuration. The example in
`configs/native.example.json` selects the exact-owned `lab_runner.model` fixture
and two packaged specialists. It contains illustrative local fixture identities
and DSNs; provision separate migration/runtime roles and deliver the real private
configuration using the existing secret-delivery path. Fixture tokens are
lab-only authentication. These endpoints exercise synthetic find, review, check,
gate, pause and finish; they access no product data or external business service.

This implementation consumes the new public SDK factory/bundle/interaction APIs.
The historical release manifest remains unchanged until the later installed-stack
qualification and public artifact promotion. This example is not evidence of
PostgreSQL/architecture qualification or a live provider certification.

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
Grant fields are `composition`, `inline`, `agents`, `schemas`, `validators` and
`model_tiers`. Composition and inline instructions are separate permissions:
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

The host selects three workflow invocations, 4,096 reported tokens and 120 seconds
per workflow; each invocation has at most one provider request and zero tool
calls. The SDK forwards remaining time/tokens and derives invocation/run/step
references from persisted execution state. Input snapshots are owned JSON values
with a 4 KiB workflow cap; the HTTP run/resume transport cap remains 8 KiB.

## Catalogue, proposal, execution and human response

Use the same authenticated owner for every request. The gateway authenticates
before consuming a body. Only exact `POST /workflow-proposals` accepts 64 KiB;
other POST routes retain 8 KiB. Keys are required for proposals and starts and
are bounded to 128 UTF-8 bytes. Unknown fields are rejected.

1. `GET /workflow-catalogue` with `Authorization: Bearer tenant-a-token` returns
   `bundle_version`, `manifest` and `proposal_schema`. The current tenant's public
   aliases/permissions are projected from the actual SDK factory. Descriptions are
   explicitly synthetic metadata; private prose, endpoints and journal bindings
   are absent. Schemas are excluded from the manifest by default.
2. Save the fixture proposal with the public application helper:

   ```sh
   python -c 'import json; from prosaic_integration_lab.native_execution import approved_proposal; print(json.dumps(approved_proposal()))' > proposal.json
   curl -sS "$LAB_URL/workflow-proposals" \
     -H 'Authorization: Bearer tenant-a-token' \
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
   curl -sS "$LAB_URL/native-runs" \
     -H 'Authorization: Bearer tenant-a-token' \
     -H 'Idempotency-Key: synthetic-run-1' \
     -H 'Content-Type: application/json' \
     --data '{"proposal_id":"REPLACE_WITH_SAVED_ID","inputs":{"task":"synthetic"}}'
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
   records, history, evidence and arbitrary outputs are excluded.
5. Resume with the exact interaction revision and schema-conforming response:

   ```sh
   curl -sS "$LAB_URL/runs/REPLACE_WITH_RUN_ID/resume" \
     -H 'Authorization: Bearer tenant-a-token' \
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
