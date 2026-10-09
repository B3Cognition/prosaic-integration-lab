# Lago billing robustness acceptance lane

Date: 2026-10-09. Status: reviewed and corrected; implementation awaits approval.

## Purpose

Extend the integration lab with repeatable local acceptance tests that reconcile
Prosaic Runtime usage evidence with Lago metering and fixture charges through
duplicate delivery, crashes, outages and cross-worker execution. The maintainer
requested this integration to test billing robustness. No paid inference,
customer invoices, payment collection or production billing certification is
included. Existing accounting evidence remains billing-ineligible.

## Approach and ownership

Use a Python application-owned durable PostgreSQL outbox and Lago's REST API.
Runtime remains the source of usage evidence through its installed public
recorder API. Harness remains the workflow owner. No sibling library changes,
private imports or model-client instrumentation are required.

Prosaic core remains the canonical Markdown distribution dependency: no billing
hooks belong in prose parsing, rendering, manifests or catalogue discovery.
The exporter is a separate lab application process, outside Harness callbacks
and the model-call critical path. Lago failure must not alter run authorization,
approval, token-budget enforcement or model dispatch decisions.

Verify the installed five-wheel baseline before implementation. The released
Runtime PostgreSQL adapter and the unpublished candidate are distinct dependency
modes; record which is exercised and never silently select the candidate. If a
required public API is absent, report a library prerequisite rather than query
its private tables or patch installed code.

The review identified no required Prosaic core, Runtime or Harness fix. Unknown
cache detail, paginated calls and rejected conflicting observations are contracts
the lab must handle. Snapshot-consistent pagination and durable conflict audit
records are possible future Runtime enhancements, not prerequisites for this
lane. Any defect discovered by executable acceptance needs a regression in its
owning library and separate authority for upstream changes or releases.

An in-memory SDK wrapper would be simpler but cannot establish crash-safe
delivery. A report-only exporter would establish pricing compatibility but omit
the recovery behavior requested here. The durable outbox is the selected design.

The optional billing lane adds an independently owned Lago fixture to the
existing synthetic stack. It must preserve the current runner's ownership,
sanitized receipts and exact-ID cleanup contracts. Existing uncommitted
operational-recovery work must be preserved and inspected before integration.

## Evidence projection and pricing

Read owner-scoped call evidence with the public recorder API. Resolve customer
and subscription from trusted, frozen application attribution, never request
headers or model output. Account scope includes namespace, environment,
application, tenant and billing account; actor attribution remains in local
evidence. Tests include separate tenants with the same account-name string.

Enumerate application-owned reservations through a new narrow metadata API that
returns only frozen attribution and run IDs, never request bodies. Construct a
recorder for each reservation's frozen namespace/environment and query with all
of application_id, tenant_id, actor_id, billing_account_id, request_id and run_id.
Validate returned intent context against that reservation. Do not scan using
mutable principal defaults or trust provider-supplied identity. Account-to-Lago
mapping is persisted before projection and shared across actors in one account.

The installed recorder's calls() accepts at most 1000 rows per page and each page
is a separate snapshot. Scan every page in deterministic order and rescan from
the beginning on subsequent passes; never advance a permanent started_at cursor
past unresolved calls, since observations can arrive later. Outbox uniqueness
handles overlap. At quiescence compare projected/excluded call identities and
counts against an owner-scoped report(), whose aggregate uses one snapshot.
Concurrent scans offer eventual convergence, not a single atomic ledger view.

Admit only complete, non-quarantined observations with supported token semantics.
Missing, quarantined, unsupported or unresolved evidence is explicitly excluded
with a reason; it never becomes zero usage. An exporter-detected payload or
attribution conflict blocks delivery and fails reconciliation; it is not a
normal exclusion. Final ledger state is rechecked
before initial submission. Changes after an event has been sent fail
reconciliation and require operator resolution rather than silent replacement.
The installed adapter rejects conflicting replacement observations and retains
the first observation; it does not automatically quarantine that first record.
Test an explicit untrusted observation for quarantine separately from rejected
conflicting writes. An exporter cannot detect a rejected write absent public
evidence; do not claim it can. A pre-send read is not an atomic transaction with
Lago; concurrent evidence invalidation remains a reconciliation incident.

Project exclusive uncached input, cached input and output quantities. Subtract
cached input from inclusive input only when supported by the recorder's public
contract; reject inconsistent counts. Never sum overlapping total/reasoning
fields into additional chargeable quantities. Include every eligible provider
attempt, including rejected-output attempts, under an explicit fixture policy.
Workflow approval itself produces no usage. This policy is only for test pricing.

For the three-rate fixture, complete measurement is necessary but insufficient:
cached_input_tokens must be explicitly known, including an explicit zero.
None means unknown, not zero. Require integer quantities (excluding booleans),
nonnegative bounds, consistent total tokens and cached input <= inclusive input.
Only the synthetic OpenAI-compatible text model and supported normalization
version are admitted in this slice; missing cache detail, different models or
unsupported service tiers remain excluded with reasons. Do not infer customer
charge eligibility from assessment.status, fully_costed or billing_eligible.

Persist exclusion reasons as scan results, not permanent completion markers.
Revisit unresolved intents on every subsequent scan and project them when a
supported observation becomes available. Missing cache detail in an immutable
observation remains excluded unless a future supported public contract supplies
new evidence. Maintain separate counts for all ledger calls, fixture-admissible
calls, excluded calls, projected calls and remotely reconciled calls. Expected
exclusions pass their dedicated negative cases; unexpected exclusions fail a
normal reconciliation case. A successful fixture result never changes Runtime's
billing_eligible=False or asserts customer billing readiness.

Seed three sum metrics and a zero-base-price USD plan with fixed fixture rates.
Compute expected amounts independently using Decimal. Keep provider-cost
estimates distinct from customer-facing fixture prices. Reconcile raw metric
quantities and Lago's documented monetary units/rounding separately; do not
mistake invoice rounding for a token discrepancy.

## Durable delivery

Provision a separate application-owned billing schema and migration contract;
do not modify Runtime recorder tables. Grant the exporter only necessary table
access, never database-owner permissions. Repeated owner-scoped ledger scans
backfill calls that were observed before projection or during a crash.
Use an exporter-specific restricted role for public recorder reads, metadata
attribution reads and billing-schema writes. Replicas need no Lago key and no
billing-table write privileges. Provision and check the billing schema explicitly
when this lane is selected; existing application schema version 2 stays intact.

Persist immutable event payload, canonical payload hash, source call identity,
original observation finished_at timestamp and mapping/pricing version before
transmission.
Stable transaction IDs include fixture/account scope, provider-call identity and
metric dimension. A unique database key makes overlapping scans idempotent.
Payload conflicts fail visibly instead of overwriting the original row.

Persist observation.finished_at as the explicit event timestamp, in a canonical
UTC representation supported by the pinned Lago API. Do not substitute send or
retry time. Event identity includes namespace/environment but not payload hash,
mapping version, pricing revision or worker/lease identity: changing these must
surface a conflict instead of minting a second charge. Retain original subscription
mapping and payload on every replay. Commit all three dimension rows for a call
atomically in PostgreSQL, including known zero quantities; remote delivery may be
partial, so convergence checks must require all dimensions before declaring that
call reconciled. Source attribution is locally retained; Lago receives opaque
account/subscription identifiers and token properties only.

Workers claim bounded batches with transactional locking and recoverable leases.
Never hold a database transaction open during HTTP. Mark delivery acknowledged
only after Lago accepts the event. Lost acknowledgements cause replay of the
same payload and transaction ID. Delivery is at least once; Lago deduplication
must be verified against actual observed usage.
Lease claims carry a generation/token; acknowledgement and failure updates must
match that token so a stale worker cannot overwrite a newer worker's result.
Use database time for leases. Persist attempt count, next retry time and bounded
sanitized failure category. Per-request timeouts and lane deadlines are finite;
retry exhaustion leaves durable pending evidence and fails the lane.

Retry transport failures, throttling and transient server errors with bounded
backoff. Permanent validation failures are retained separately and fail the
lane; they cannot become successful delivery. After an ambiguous individual
POST result, replay that exact event or reconcile its transaction ID before
retrying. Acceptance failures must distinguish missing source evidence, excluded
source evidence, pending delivery, permanent delivery failure and conflict.

Start with individual event POSTs from locally claimed batches, avoiding an
unnecessary remote-batch atomicity dependency. A duplicate transaction can return
a validation error on Lago's PostgreSQL event store. Handle that specific error
by retrieving the existing event in its subscription scope and comparing its
transaction ID, code, subscription, timestamp and token properties. Exact match
is a recovered acknowledgement; mismatch or unavailable evidence is never
success. Other permanent 4xx errors fail visibly; throttling remains retryable.
Authentication/authorization failure stops the exporter without cycling through
the entire pending queue. HTTP acceptance is distinct from processed
usage: poll current usage under a finite deadline and reconcile quantities.

## Local Lago fixture

Use a release-pinned Lago API/worker, its required PostgreSQL and Redis services,
and an optional UI. Record immutable upstream source and image digests in the
dependency manifest; verify platform availability before implementation selects
the exact supported release. Do not execute mutable upstream demo scripts.

Allocate random ownership IDs and generated fixture-only credentials. Bind any
published ports to loopback. Provision a disposable organization, customers,
subscriptions, metrics and plan through supported interfaces. Disable external
payment providers and telemetry where supported. Store credentials outside
reports and Git. No connections to Lago Cloud or existing billing environments.

Record resource intentions before creation, reconcile immutable labels and IDs
after lost responses, and verify removal in finally blocks. Infrastructure,
readiness, migration, missing images and cleanup failures are failures, not skips.
Readiness waits and asynchronous usage convergence have finite deadlines.

Use Lago's PostgreSQL event store in this slice; do not extrapolate deduplication
results to ClickHouse. Seed subscriptions before synthetic calls with explicit
UTC timezone, a start preceding their timestamps, no prepaid/immediate charges,
and no taxes, minimums or allowances. Require events to remain in the open period
reported by current usage. Crossing a period boundary or restarting after the
period closes is a visible out-of-scope result, never silently retimestamped.
The API contract and exact monetary fields/rounding must be captured from the
selected release, rather than assumed from a mutable latest OpenAPI document.

## Acceptance criteria

1. Normal multiuser runs reconcile independent model counters, recorder call
   quantities, exported events, customer usage and expected fixture charges.
2. Rejected-output attempts retain their measured usage; approval and workflow
   resume do not add duplicate events or dispatches.
3. Missing and quarantined usage remains visible and excluded. Unsupported cache
   semantics fail projection rather than produce a guessed charge.
4. Repeated scans and concurrent exporters create one immutable event per call
   dimension. Duplicate transaction delivery leaves usage unchanged.
5. Stop Lago while workflows complete. Outbox rows persist; a reconstructed
   exporter drains them after restart without additional model calls.
6. Crash before send, after remote acceptance but before local acknowledgement,
   and after lease acquisition. Recover and reconcile with no lost quantities
   or duplicate charges. Faults use explicit fixture barriers.
7. Invalid payloads, mapping conflicts and permanent API errors remain observable;
   transient retries are bounded. Changed duplicate payloads cannot silently
   replace accepted evidence.
8. Distinct tenants/accounts remain isolated. Exported payloads and retained
   receipts contain no prompts, private workflow state, credentials or DSNs.
9. Repeat the lane on lab PostgreSQL 16 and 18; record actual Lago dependency
   versions and host/container architectures. Verify exact-owned cleanup.
10. Exercise more than 1000 calls, delayed observation after an earlier unresolved
    scan, and a crash after observation but before projection. Rescans recover
    every eligible call without advancing past delayed evidence.
    The pagination case must exceed 1000 calls within one reservation/run filter,
    since 1001 one-call runs do not exercise recorder pagination. Create that
    bounded synthetic ledger fixture through public prepare/observe APIs and
    label it separately from actual Harness/model-dispatch evidence.
11. Complete input/output with unknown cached detail produces an explicit
    exclusion; known zero cache, nonzero cache and included reasoning tokens
    reconcile without overlap. A changed mapping/pricing revision cannot mint
    replacement events for already projected calls.
12. A stale lease holder cannot change outbox state; duplicate validation errors
    recover only after exact remote-payload comparison. Ledger completeness,
    export completeness and remote processing are separately reported.

## Integration and verification

Add an explicit Lago runner lane following the existing test-mode conventions,
plus unit tests for projection, conflict handling and retry classification, and
real PostgreSQL/Lago acceptance tests for durable recovery and reconciliation.
The exact CLI shape is chosen in the implementation plan after inspecting the
current uncommitted runner changes. Existing default lanes remain usable without
Lago. Documentation must provide reproducible build/run commands and sanitized
evidence with limitations. Run the full host test suite and required real-stack
lanes; report failures accurately and retain historic receipts.

## References

- Lago engine and maintained demo: https://github.com/getlago/lago
- Exact API schema: https://swagger.getlago.com/openapi.yaml
- Agent SDK buffering model: https://github.com/getlago/lago-agent-sdk-python

Public documentation establishes feasibility, not verification of this lab's
integration. Invoice generation, wallets, credit exhaustion, refunds, payment
webhooks and subscription-period boundaries are subsequent lanes; this slice
establishes reliable metering and current-usage charge reconciliation first.
