# Durable failure isolation and explicit recovery

**Experimental consumer blueprint.** `lab_runner.failure_isolation.FailureIsolation`
contains bounded work on one host. It provides durable admission, conservative
reservation retention, writer revocation and explicit evidence reconciliation.
It contains no model, provider, task domain or critic policy. Memory and bounded
correction remain experimental; this milestone establishes no model benefit.

The journal surrounds a complete operation through public SDK APIs. Harness
owns workflow state and receipts; Runtime owns dispatch, execution budgets and
usage observations. The journal references their host-verified evidence. It is
neither a durable Runtime recorder nor a substitute for either SDK's storage.
The separate [service adoption guide](consume-native-workflows.md) covers shared
PostgreSQL state and service recovery. This local blueprint is not a distributed
queue or an exactly-once execution guarantee.

## Adoption and limits

The consuming host must authenticate the user, authorize the operation and
reserve its **entire** possible spend in its authoritative allowance before
admission. Set this containment journal's ceilings within those preauthorized
reservations. Its capacity creates no new inference allowance. Preserve existing
allowance stop policies; an existing stop-on-unknown study cannot switch to
isolation midway through a frozen run. Create a separately qualified frozen
study with an audited accounting baseline before any future live use.

Bind `identity` to trusted tenant/actor/namespace, operation and configuration
versions, authorization and frozen study. Bind each work item to its exact
input, evidence grant, profile, counter registration and contract/policy digests.
The host supplies these values; client/model-supplied digests are not authority.
Keep the private directory and tokens away from model and public HTTP views.
An identity mismatch rejects opening the journal. Work identifiers are single
use; duplicate admission and duplicate start both fail after acknowledgement loss.

Each item reserves **4 provider requests / 2 tools / 8192 reported tokens**.
The persisted deadline is admission time plus **600 seconds**. Keep **512 output
tokens per response** in the SDK profile. The journal does not enforce individual
provider calls. Activate an enclosing public Runtime `ExecutionBudget` with the
remaining deadline and those unchanged counters before invoking the SDK operation;
the operation's nested budgets must debit that enclosing budget. Do not start
execution with a fresh 600-second allowance after time spent waiting.

```python
from lab_runner.failure_isolation import FailureIsolation
from prosaic_runtime import ExecutionBudget
import time

# All values and operations below come from trusted host code.
journal = FailureIsolation(private_path, identity=scope_digest,
                           limits=preauthorized_containment_counts)
token = journal.admit(work_id, binding=operation_digest)
intent = journal.start(work_id, token)  # durable before SDK dispatch
remaining = intent['deadline'] - time.time()
if remaining <= 0:
    raise ValueError('explicit recovery required')
budget = ExecutionBudget(timeout_s=remaining, max_provider_requests=4,
                         max_tool_calls=2, max_reported_tokens=8192,
                         cancelled=lambda: journal.status()['admissionBlocked'])
with budget.activate():
    evidence = run_public_sdk_operation()
# Host verifies receipt bindings, complete usage and domain acceptance first.
journal.complete(work_id, token, actual=verified_counts,
                 evidence_digest=verified_evidence_digest,
                 outcome='completed' if host_accepted else 'failed')
```

If execution raises, stops with incomplete usage or the worker disappears, do
not invoke the operation again. Leave its full reservation charged and isolate
it through a separately authorized host action. A sample's failure does not
block another independently authorized identifier if the remaining containment
capacity covers its full reservation. A **known overrun** records actual counts,
retains the larger of actual and maximum in each dimension, marks the work
failed and blocks all new admission. It cannot be erased through recovery.
It also prevents already admitted, queued work from starting. Such work remains
reserved and requires explicit isolation/recovery; it cannot bypass the latch.
Use the enclosing budget's cancellation callback, as above, to stop further
dispatches in already running operations when the shared overrun latch appears.
An in-flight provider request still requires reconciliation.

There are no refunds even for fully reconciled work. This deliberately avoids
letting recovery enlarge a frozen allowance. Known actual counts remain visible
for reporting; unknown counts remain `None`. Existing cumulative ceilings
1558 requests / 637 tools / 1976623 tokens and charges 1509 / 610 / 1835168,
including nine unknown reservations, remain unchanged by this blueprint.

## Explicit recovery

`inspect` and `status` read state without dispatching or exposing writer tokens.
An `active` record means a dispatch intent may have escaped, even when no
observation or receipt exists. An `admitted` record also cannot be reused after
restart. There is no automatic lease expiry, reassignment, retry or SDK resume.

After host authorization, call `isolate(work_id, binding=..., decision_digest=...)`.
This durably revokes the old writer token. The host must separately stop or
quiesce its worker: revocation prevents journal writes, but cannot recall an
already in-flight network request or tool effect. Do not start replacement work
while an old worker can still act. Tool side effects require the SDK/consumer's
own durable idempotency and reconciliation rules.

Read the SDK evidence without driving the workflow; for the experimental
correction example this is `recover_correction`. Verify scope, immutable
bindings, receipts, observed usage and acceptance through trusted host code.
Then call `recover` with a distinct host decision digest:

```python
journal.recover(work_id, binding=operation_digest,
                decision_digest=recovery_authorization_digest,
                actual=None, evidence_digest=None, outcome='unknown')
```

For fully reconciled evidence supply complete nonnegative integer counts, the
verified evidence digest and `outcome='failed'` or `'completed'`. Missing/partial
usage cannot become zero or success. A completion after the persisted deadline
is rejected; evidence can still be recorded as failed. Exact decision replay is
idempotent. Conflicting evidence, a different decision, changed bindings and
stale writers fail. Recovery never dispatches, extends a deadline, accepts model
retry consent or authorizes new work. Any new attempt needs separate host
authorization, a new identifier and its own full reservation.

Only trusted host code may call the API. Digest validation checks format and
binding, not cryptographic authentication of provider evidence or authority.
Use the SDK recorder and consumer receipt checks as evidence sources. The
host-facing status contains private accounting metadata and needs its own
allowlisted public projection if exposed through a service.

## Durability and offline qualification

Writes use a private atomic replacement, file/directory fsync and a POSIX process
lock. Use a private local filesystem supporting those semantics, with a trusted
clock; never put this on a shared/network filesystem or use it across machines.
Deleting/restoring an old journal is not recovery. Preserve it together with
SDK evidence and the authoritative allowance. Host/filesystem loss, clock
rollback and malicious local modification require infrastructure controls and
are not certified by process-loss tests.

From a fresh environment containing the built Lab wheel and the unchanged
public pinned SDKs, exclude the source directory from imports:

```text
python -I scripts/failure_isolation_smoke.py --source-root REPO \
  --evidence-dir PRIVATE_FRESH_ROOT/lanes --output PRIVATE_FRESH_ROOT/result.json
```

The smoke exercises both wire fixtures, unknown usage and persisted SDK evidence
before journal completion, unrelated healthy work, network-denied receipt-only
recovery, exact replay and process loss after admission/start/completion.
Source tests add concurrent admission, writer fencing, binding conflicts,
deadline preservation, malformed evidence and honest overrun containment.
Synthetic responses and token units do not qualify live models, counters,
distributed operation or production storage. No live calls are part of this
milestone. Consumers must qualify their own authorization, receipt verification,
storage deployment and fault boundaries before adoption.
