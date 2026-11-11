# Label accounted requests with a run and variant

Copy the `accounting-metadata` blueprint. Its trusted host uses Runtime0.9.17
`accounting_request_metadata_v1` with Core0.5.0, Harness0.9.12 and the original
published recorder0.3.0/store0.4.1. The complete active manifest pins exact public
URLs, source commits and SHA256; do not substitute one SDK into an older family.

```sh
python -m lab_runner.blueprints copy accounting-metadata /private/benchmark-host
cd /private/benchmark-host
prosaic inspect subagents/benchmark.md --source .prosaic --json
```

Listing, copying, inspecting and constructing the workflow make no model call.
The default endpoint is inert loopback port9. Running `host.py` refuses unless
`--live` explicitly authorizes a call to the privately configured endpoint.
The CLI is a non-durable demonstration; synthetic acceptance uses owned loopback
providers only. No provider credentials or live inference are needed for tests.

## Prepare-time labels

From the copied directory, an authenticated application can use:

```python
import os
from host import LabelingRecorder, build_runtime, load_agent, run_benchmark, trusted_context
from prosaic_runtime_postgres import PostgresRecorder

backend = PostgresRecorder(os.environ['ACCOUNTING_RUNTIME_DSN'],
    namespace='accepted-deployment', environment='benchmark')
backend.check_ready()  # migration/owner initialization is a separate operator task

def before_dispatch(labels):
    # Route safe diagnostics using labels.get('run') / labels.get('variant').
    # Do not derive tenant/payer/rates, grant a retry, or print arbitrary secrets.
    pass

recorder = LabelingRecorder(backend, before_dispatch)
runtime = build_runtime(accounting=recorder)
context = trusted_context(tenant_id=accepted_tenant, billing_account_id=accepted_payer,
    benchmark_run='benchmark-42', variant='cold-cache')
result = run_benchmark(runtime, load_agent(), context=context)
```

`accepted_tenant`/`accepted_payer` come from authenticated host authorization,
never a model/client identity field. The backing recorder's `prepare(intent)` sees
`intent['context']['request_metadata'] == {'version': 1, 'labels': {...}}` before
HTTP dispatch. Existing requested model/profile/artifact/run/step facts remain
available. V1 does not expose raw requests, prompts, tool arguments or headers.
The wrapper passes a copy of labels to its callback and delegates prepare/observe,
rates, scope and durability to the original recorder. Callback/storage failure
stops dispatch; usage evidence is never consent to reissue uncertain work.

Runtime owns the immutable snapshot: later changes to caller maps or callback
copies cannot relabel later tool/repair/acquisition requests. Both API wires and
run/turn/prepared-turn calls share this contract. The blueprint permits one
ordinary request/no tools; its workflow permits two separately bounded agent
invocations separated by explicit human approval. Existing per-call headers are
a separate host transport option; labels do not travel in the request body or
headers and do not alter provider caching behavior.

## Frozen workflow resume

Construct `Harness(flow, ..., runtime=runtime, context=context)` using
`flow = workflow(runtime)` from the host. The diagnostic `benchmark_run` label is
separate from actual workflow run identity. Let Harness bind its run UUID by
omitting actual `ExecutionContext.run_id`, or provide the same lowercase UUID hex
as the explicit RunStore/Harness ID. A friendly benchmark label cannot rebind a
stored run. Runtime/recorder deployment defaults inherit attribution only, not
metadata.

Reopen with the same admitted workflow, storage scope and recorder. Saved context,
including original labels, remains authoritative even if a new caller supplies
different observational labels or recorder defaults change. New variant means new
run. A persisted receipt may be adopted without another provider request; never
use accounting uncertainty to authorize a replacement call. Tenant/actor/payer
rebinds retain their existing refusal rules. Public output must be allowlisted,
such as `public_view`; raw Harness/operator state and recorder `calls()` can
contain private labels and are not a customer API.

## Bounds, identity and migration

At most16 string labels; ASCII keys `[A-Za-z][A-Za-z0-9_.-]{0,63}`; printable,
nonempty values at most256characters and256UTF8bytes; sorted compact escaped JSON
at most4096bytes. Identity/scope/raw-request/credential keys are reserved,
case-insensitively. Nested/nonstring/control/duplicate inputs and malformed or
unknown persisted versions fail before effects with sanitized errors. See the
[Runtime contract](https://github.com/B3Cognition/prosaic-runtime/blob/v0.9.17/docs/accounting.md#request-metadata-v1)
for the complete reserved set. Hosts must keep secrets out of arbitrary labels.

None/empty metadata is omitted entirely, preserving exact legacy context/intent
bytes and accounting hashes. Artifact/rule, prepared-turn, workflow and bundle
identities gain no fields. Present labels intentionally enter accounting payload
hashes and sealed private checkpoints/receipts. Replaying the same intent is
idempotent; changing labels under an existing call ID conflicts. Labels never
change report filtering, rates, authorization, storage scope or billing eligibility.

Recorder0.3.0 uses Runtime's public decoder and existing JSONB storage; no DDL,
privilege expansion, adapter republish or old-row rewrite. Deploy Runtime>=0.9.17
readers before producing labeled records/saved runs; older readers of the new
extension are not promised. Old unlabeled records stay readable. Native CLI
accounting keeps its existing unsupported measurement scope. This is synthetic
integration evidence, not live-provider, customer-billing or durability certification.

## Qualification

Required acceptance uses actual installed released SDKs, copied external hosts,
both synthetic wires, real PG16/18 and file-store reopen/receipt recovery, callback
and recorder failures, frozen defaults/labels, payload isolation and restricted
runtime roles with exact-owned cleanup. Wheel and rebuilt-source consumers must
repeat feature checks. Final LinuxAMD64/ARM64 ordinary/rule matrices, reasoning,
public-index, original archive/tree and public-consumer proofs remain mandatory.
Source-only or candidate-wheel tests do not certify that final train.

Remaining Cerebro work: per-call actual sent effort evidence, a separate explicit
rule-repair allowance, comprehensive versioned identity policy and release-note
publisher enforcement. Existing ValidatorV1, workflow tags and headers remain
available through their separate [blueprints](feature-blueprints.md).
