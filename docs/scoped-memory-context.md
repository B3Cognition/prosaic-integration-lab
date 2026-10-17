# Scoped memory context

`lab_runner.memory_policy` is an opt-in host policy reference. Applications own
trusted tenant/entity/topic metadata, expiry, the current source registry and
context quotations. Core remains a Markdown distribution engine; public Runtime
and Harness APIs own execution and workflow state. No model or serving engine
is named by this policy. Existing v1 history and default Lab retrieval remain
compatible; the new adapter is programmatic, not a CLI option or memory service.

Construct `ScopedCorpus(document, historical_sources, metadata)`. The unchanged
v1 history is accompanied by a host-authored sidecar:

```json
{"version":1,"episodes":[{"tenantId":"alpha","episodeId":"prior","entityId":"orchid","topics":["rollout"],"expiresAt":null}],"currentSources":[{"tenantId":"alpha","sourceId":"metrics","sourceVersion":1,"sourceSha256":"<current record SHA256>"}]}
```

Every episode requires exactly one metadata row. Retrieve with
`retrieve(tenant_id, entity_id, topics, as_of)`. Tenant and exact entity filter
before ranking; matching current source hashes/versions, observation time,
expiry and positive trusted topic overlap determine eligibility. Rank by topic
overlap, newest observation and ID. Notes and legacy tags cannot improve rank.
Selected notes remain untrusted hints, including hostile notes that legitimately
match the scope. Whole episodes are capped at three and 4,096 encoded bytes.
There are no embeddings, automatic writes or semantic relevance guarantees.

`ScopedContext(corpus, counter_descriptor=registration.descriptor.to_dict(),
quote_inputs=quote, quote_identity=sha256, limits=LIMITS, output_tokens=512)`
prepares the native request and an owned context plan. Pass it as
`context_builder=builder` to `execute_case`, together with the matching qualified
`token_counter=registration`. Use `recover_case` with the same builder for
receipt-only replay; recovery needs no executable counter and never calls the
quote callback. `scripts/scoped_memory_smoke.py` is a complete synthetic example.

The trusted `quote_inputs(request)` callback must return four integer input
ceilings, one for each permitted native proposal. `quote_identity` binds the
host's quotation implementation and assets; do not reuse it for changed logic.
The plan reserves their sum plus four output ceilings of 512 under the unchanged
8,192-token case cap. Optional recall is packed only when the complete plan fits.
Mandatory task/index fields are never trimmed. A rejected mandatory plan is
retained intact and its guard refuses all requests before HTTP.

These are enforceable planning bounds, not estimates that guarantee arbitrary
continuations will complete. A qualified Runtime counter measures each actual
native proposal; the guard refuses input/output/proposal drift before dispatch
and returns the true bound. No bytes-to-token heuristic or fabricated count is
used. The same guard covers Harness repairs; Runtime additionally owns shared
actual limits, reservations, overrun and unknown-usage handling. Four requests,
two tools, 8,192 tokens, 600 seconds and output 512 remain fixed. Consumers
wanting different limits must define and qualify a separate application policy.

Frozen context binds trusted scope, current records, local history/metadata,
full counter provenance, quotation identity and implementation. Foreign valid
changes cannot alter local identity. Existing execution claims force recovery;
an uncertain call cannot gain fresh proposal slots by invoking execution again.
Recovery uses stored selection/plan and rejects drift. Keep trusted metadata
outside model/client control; digests detect local changes, not a malicious host
rewriting all of its own evidence.

Private `*-context-trace.json` files retain actual SDK intents/observations,
proposal decisions, public Harness events and receipt failure categories.
Proposals do not prove dispatch; usage comes from receipts and recorder
observations. Missing usage stays unknown; tool errors without a public cause
are `unclassified`. Traces are local qualification evidence, not billing records
or invoices. Recovery preserves their bytes and never reconstructs the guard.
Treat these files as sensitive and retain them with workflow receipts.

Qualification establishes these host contracts with synthetic providers. A fresh
held-out live comparison is still required to measure efficacy and refusal rates
for both models. The previous live comparison is preserved and is not reused as
a new test set. Production distributed memory, write governance and broader
multi-agent/operational milestones remain separate work.
