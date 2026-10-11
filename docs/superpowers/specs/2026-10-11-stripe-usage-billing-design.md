# Stripe usage billing acceptance lane

Date: 2026-10-11. Status: proposal for maintainer review; not implemented.
Read-only provider-contract and local-integration reviews are complete and their
findings are incorporated. No Stripe account capability has been exercised.

## Intent and recommended scope

The maintainer has a Stripe Billing test account and selected usage-based billing
for Prosaic tokens or calls as the first integration. Demonstrate that recorded
Prosaic usage can reach Stripe once, retain its original owner and billing period,
and reconcile to an actual test invoice despite retries and process failures.

The recommended first measure is **total reported tokens**, using one raw sum
meter and a uniform fixture price. Call-based pricing and differentiated input,
cache, output or model-tier prices are separate future policies. This slice tests
the accounting and delivery boundary; it does not authorize customer billing or
change Runtime's `billing_eligible=False` assessment.

There is an important product choice to approve. Stripe currently recommends
Metronome for new usage-based integrations and describes direct Billing Meters
as appropriate for existing meter integrations. The proposed direct-Meters lane
is a deliberately bounded compatibility test of the account the maintainer
already has, rather than a recommendation to build a new production billing
system around Meters. [Stripe's current guidance](https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage)

The alternatives are:

| Approach | Value | Tradeoff |
| --- | --- | --- |
| Direct Billing Meters, recommended for this account test | Exercises Stripe ingestion and invoices with the existing Billing account | Requires application-owned delivery and reconciliation; differs from Stripe's recommendation for new production integrations |
| Metronome with Stripe | Follows Stripe's current direction for new usage billing | Requires confirming separate access and researching another provider contract before implementation |
| Local billing simulation only | Cheap deterministic development feedback | Cannot demonstrate that this account accepts usage or produces the expected invoice |

Approval of this spec selects the first approach. If Metronome is preferred,
revise the provider contract before writing an implementation plan. Do not
silently substitute either provider during implementation.

## Ownership and deployment

Implement this in the Integration Lab as an application-owned exporter and
acceptance lane. Core remains the Markdown distribution engine. Harness owns
workflow state. Runtime owns inference and recorded usage evidence. The Lab owns
trusted attribution, the fixture pricing policy, delivery and reconciliation.
No changes to Core, Runtime or Harness are currently required.

Use released, checksum-pinned Prosaic packages and their public APIs. Read usage
through the public PostgreSQL recorder, never its private tables. Keep Stripe
delivery outside model execution and Harness callbacks. A billing outage must
not change workflow authorization, review decisions or model budget enforcement.

Pin the optional Lab Stripe dependency profile to `stripe==16.0.0` and explicitly
pin API version `2026-09-30.endive`; include transitive dependencies in a hash
lock. Verify request headers and SDK behavior in transport tests. The version
pair is published in the [official SDK changelog](https://github.com/stripe/stripe-python/blob/v16.0.0/CHANGELOG.md).
Normal application replicas require neither the extra nor Stripe credentials.
The Stripe test job installs the extra explicitly; absent dependencies fail a
selected lane rather than cause skips.

Use a separate `lab_stripe` schema, migration version 1 and restricted exporter
role. Keep the existing `lab_billing` Lago schema, payloads, identifiers and
permissions compatible. Share only small pure evidence-validation helpers
where useful; do not introduce a generic billing framework. Any extraction must
preserve existing Lago projections and hashes exactly.

Provision migration credentials separately from exporter credentials. Grant the
exporter narrowly scoped public-recorder and frozen-attribution reads plus its
own schema access. Service replicas cannot write the Stripe outbox. Migration,
fixture provisioning and exporting remain separate effect boundaries.

## Trusted bindings and source admission

Host configuration supplies the Stripe account identity, isolated sandbox/test
scope, secret environment-variable name and approved fixture mapping. The API
key stays in secret-managed process configuration, outside public run state,
receipts and Git. Client requests and model instructions cannot select a billing
account, customer, meter, price, credential or remote endpoint.

The client uses Stripe's official HTTPS API origin. Endpoint injection exists
only in offline test constructors. Disable SDK automatic retries
(`max_network_retries=0`), and route every HTTP request through the shared
allowance and deadline controller, including pagination and cleanup.

Before any Stripe write, perform read-only preflight that verifies the expected
authenticated account through `GET /v1/account` and non-live mode using provider
responses, confirms the pinned API and
required thin-event APIs, and rejects mismatched bindings. Key prefixes alone
are insufficient mode evidence. The authenticated balance must report
`livemode=false`; do not mistake an account's live-charge capability for the
current request mode. [Authenticated balance contract](https://docs.stripe.com/api/balance/balance_retrieve)
Record the configured sandbox scope and verify
ownership and mode on created resources. Do not fall back from an isolated
sandbox to another account or live mode. Reject Connect/account-context header
overrides. Verify the pinned Python SDK's singular current-account route in
transport tests; retrieving an arbitrary `/v1/accounts/{id}` does not prove the
key's authenticated destination. [Official current-account route](https://github.com/stripe/stripe-go/blob/master/account_service.go)
Some API v2 endpoints do not support
legacy test-mode sandboxes; this is an explicit capability prerequisite, not a
reason to omit asynchronous error checking. [API v2 limitations](https://docs.stripe.com/api-v2-overview#limitations)

Enumerate application-owned reservations using the existing narrow metadata API.
Use their frozen namespace, environment, application, tenant, actor, billing
account, request and run identity for every public-recorder query, and compare
returned intent attribution against that reservation. Actor changes and resumed
runs cannot change billing ownership. Multiple actors may share an account only
through a trusted account mapping.

Page through all calls, respecting the recorder's maximum page size. Each page
is a separate snapshot: rescan from the beginning on later passes, including
previously unresolved calls. Durable uniqueness makes overlapping scans safe.
At quiescence compare projected/excluded source identities with the paginated
`calls()` set, then compare call and measurement-state counts with the
owner-scoped public `report()`, which exposes aggregates rather than call IDs.
Claim eventual convergence rather than snapshot-consistent scanning.

The first policy admits complete, non-quarantined synthetic `test-model`
observations with the supported OpenAI-compatible normalization version,
platform payer and default service tier. Require known input, output and total
counts, nonnegative integers no larger than 1,000,000 per call excluding booleans, and
`input_tokens + output_tokens == total_tokens`. Validate any reported cache or
reasoning quantities against their inclusive parent quantities. Unknown cache
detail is allowed for uniform total-token pricing because no cache discount is
applied. Unsupported providers, local Qwen and production model usage are outside
the initial billable fixture policy.

Missing, quarantined, unsupported or unresolved evidence has a recorded exclusion
reason and is revisited; it is never converted to zero. A source with no final
observation can acquire its first valid observation atomically under the identical
intent, attribution and route, without creating a second source. A provably stale
unresolved scan cannot erase that observation. Any persisted observation,
including partial or unknown measurements, remains immutable; inconsistent
replacement evidence is a conflict.
Every supported provider
attempt counts under the explicit fixture policy, including rejected-output
attempts. Human review and approval generate no additional token usage. Pricing
is independent of provider-cost estimates and workflow success.

## Projection, identity and periods

Create one immutable event per admitted provider call with the raw total-token
quantity. Do not add input, output, cache or reasoning quantities to that total.
Use `event_name`, `payload[stripe_customer_id]`, `payload[value]`, an explicit
`identifier`, and the original observation finish time in Unix seconds. Keep
the original timestamp precision locally. Never substitute send or retry time.
Stripe accepts timestamps within the past 35 calendar days or up to five minutes
in the future; an out-of-window event fails explicitly. The Lab's integer-token
rule is its own policy, not a restriction on Stripe's supported value types.
[Meter event contract](https://docs.stripe.com/api/billing/meter-event/create)

Derive a stable opaque identifier, such as a 64-character SHA-256 digest, from:

- destination account, sandbox/test scope and mode;
- frozen application namespace, environment, application, tenant and billing account;
- provider-call identity and metric identity.

Exclude quantity, price, mapping revision, worker, lease and retry time from the
identifier. A changed projection must conflict with the original event rather
than create another charge. Freeze the canonical payload and its hash, complete
source-observation evidence, original finish time, destination, customer, meter,
event name, price, subscription item and policy/mapping revision in one local
transaction before transmission.

Separate stable account mapping from immutable period routing. Select the
half-open billing period `[start, end)` by the original finish time, not by the
current subscription or scan time. Renewal cannot reinterpret historical calls.
The first remote fixture uses one open period; recurring subscription automation
is not included. Offline tests cover historical rescans after a new period is
installed, boundaries and conflicting routes. Missing routing blocks delivery.

Use a raw sum meter, avoiding preaggregated hourly/daily overwrite semantics.
Freeze a run-unique event name of at most 100 characters before meter creation;
reuse it only to recover that creation attempt. Deactivation must not be assumed
to free a previous meter's event name for a subsequent run.
Seed one zero-base-price USD subscription item with a fixture price of one cent
per token. Disable taxes, discounts, tiering, transformations and prorations.
Compute expected quantities and minor-unit amounts independently using integer
or Decimal arithmetic. This deliberately simple price is not a retail-pricing
recommendation. Meter configuration and raw/preaggregated behavior follow
[Stripe's meter documentation](https://docs.stripe.com/billing/subscriptions/usage-based/meters/configure).

## Durable delivery and uncertain outcomes

Persist sources, exclusions, immutable events, attempts and routing separately.
Use transactional bounded claims, database-time leases and generation-fenced
acknowledgement/failure updates. Never hold a database transaction open during
HTTP. Recheck public source evidence before a first submission; a detected
conflict blocks delivery. A subsequent change fails reconciliation and requires
operator resolution. This check is not atomic with Stripe ingestion.

Serialize sends per customer and meter with a durable lease whose duration
exceeds the HTTP timeout and recovery margin. Local fencing cannot cancel an
already running remote request; handle remote concurrency throttling explicitly.
All retries use the original payload, identifier and HTTP idempotency key.

Stripe event-identifier uniqueness and v1 HTTP idempotency both have finite
retention: identifier uniqueness is guaranteed for at least 24 hours, while
HTTP keys may be pruned after 24 hours. HTTP idempotency can also replay a cached
500 response. This is not an indefinite exactly-once contract.
[Event identifier](https://docs.stripe.com/api/billing/meter-event/create),
[HTTP idempotency](https://docs.stripe.com/api/idempotent_requests)

Persist the database-time first POST attempt and a conservative **23-hour replay
deadline before opening the connection**. Do not reset them on restart, lease
recovery or retry. Before each replay require enough time for the configured
request timeout and margin to finish inside that deadline. A never-submitted old
event may have its first attempt if its usage timestamp remains valid; an
uncertain previously submitted event may not restart its duplicate window.

Use durable states with explicit meanings:

| State | Meaning |
| --- | --- |
| `pending` | Frozen locally; no submission attempt yet |
| `in_flight` | Leased, with first-attempt/deadline persisted |
| `retry_wait` | Exact replay permitted within deadline after a retryable outcome |
| `acknowledged` | Stripe returned a matching successful response; aggregation is still unverified |
| `rejected` | Deterministic provider validation or asynchronous rejection |
| `conflict` | Source, mapping, payload or response disagrees with frozen evidence |
| `needs_resolution` | Submission may have occurred but safe automatic replay cannot establish the outcome |

Bound backoff and response sizes, allow at most six delivery attempts per event,
and set a ten-second HTTP timeout within the shared lane deadline. Retry
transport ambiguity and documented concurrency/rate failures only inside the
deadline. Honor `Stripe-Should-Retry: false` across the application retry loop.
A cached/indeterminate 500 response, expired replay window or exhausted retry
allowance becomes `needs_resolution`; never rotate the key to evade the cached
result. Permanent malformed requests fail rather than retry unchanged forever.
Sanitize errors and retain only necessary response evidence and request IDs.
[Stripe's low-level error guidance](https://docs.stripe.com/error-low-level)

There is no documented individual meter-event retrieval operation on which to
base recovery. Period aggregate equality cannot prove a particular ambiguous
identifier was accepted. Persist acknowledgement, aggregate reconciliation and
invoice verification as separate facts. The MVP has no automatic refunds,
adjustments or operator button that blindly resends an uncertain event.

## Asynchronous rejection and reconciliation

Meter ingestion is asynchronous. A successful POST alone does not establish
valid aggregation or invoicing. Poll thin errors through `/v2/core/events` for
`v1.billing.meter.error_report_triggered` and
`v1.billing.meter.no_meter_found`, with pagination, overlapping time windows and
persisted event identities. Use an owned-meter filter when applicable, but omit
that filter for the no-meter-found type. Correlate through a frozen event
identifier, HTTP idempotency key or captured request ID, within the configured
account/scope. Preserve unmatched reports for an owned meter as unresolved;
sampled errors are not a complete per-event acceptance ledger. An unrelated
event cannot mutate the fixture ledger. [Thin-event list API](https://docs.stripe.com/api/v2/core/events/list),
[Documented error payloads](https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api#handle-meter-event-errors)

Polling avoids an external webhook endpoint in the MVP. The lane does not claim
webhook signature or public-delivery coverage. Negative transport fixtures cover
asynchronous rejection, unrelated reports and missing capabilities; account
canaries must establish that error polling works in the selected environment.
Place deliberate negative canaries on separate owned resources, with their own
expected rejection records, so they cannot contaminate the happy-path source set
or meter. Never treat a known negative fixture's error as normal usage delivery.

At quiescence require every expected source to be projected or explicitly
excluded, no unexpected exclusions/conflicts/unresolved delivery, and matching
remote meter aggregates for the owned customer and period. Use minute-aligned
summary queries with inclusive start and exclusive end, iterate all pages, and
test boundary behavior. Store a reconciliation record with its cutoff, expected
source/event set and remote evidence rather than marking individual ambiguous
events acknowledged from the total. [Summary query contract](https://docs.stripe.com/api/billing/meter-event-summary/list)

Require actual finalized invoice line quantity and amount to match that same
source set. Record preview-only results as `invoice_preview_verified`, which
cannot pass the `invoice_verified` acceptance requirement. Usage arriving after
invoice finalization is a discrepancy even if the meter total eventually grows;
never assume it will be billed on the next invoice. The fixture omits thresholds
and mid-cycle subscription changes. [Invoice grace-period behavior](https://docs.stripe.com/billing/subscriptions/usage-based/configure-grace-period)

## Bounded account fixture

Remote execution requires an explicit Stripe test-lane selection and private
host binding. Default CI remains credential-free. The single Dashboard user is
an account operator; it does not weaken tenant/account attribution tests.

Use a shared, durable per-run allowance of **300 HTTP requests over ten minutes**,
with normal work ending by minute eight and the last two minutes plus 60 requests
reserved for cleanup. No SDK-hidden retries are allowed. Every API read,
write, page and cleanup action consumes allowance before HTTP. Worker restarts
do not reset it. Exhaustion or unavailable allowance state fails closed. Remote
account execution is separate from the local synthetic model allowance.

Create only owned test resources and journal exact returned IDs and creation
idempotency keys before proceeding. Freeze creation attempts before HTTP too;
lost creation acknowledgements follow the same finite replay discipline. Verify
account, non-live mode and ownership before every mutation. Do not reuse or
modify an existing customer, subscription, meter or price from the user's account.

The intended scenario is:

1. Create an owned test clock near the current wall time, aligned to a minute,
   then its customer, raw sum meter, product, price and subscription. Set
   `billing_mode[type]=flexible` with only the metered item and no backdating or pending invoice
   items, avoiding an initial subscription invoice. The period must contain
   actual observation timestamps. Use manual collection
   (`collection_method=send_invoice`, `days_until_due=30`), no customer email or payment
   method, and disable automatic advancement on each owned draft invoice.
   Verify this state before advancing the clock beyond invoice generation.
2. Run the existing approved native workflow: admission/replay consumes no model
   calls; finder and reviewer produce two synthetic observations of 125 tokens
   each; confirmation pauses execution.
3. Exercise read/replay, invalid/stale review requests and cross-actor access.
   Valid resume completes without another call. Export exactly two events and
   reconcile **250 tokens / 250 USD cents ($2.50)**. Review/resume adds zero usage.
4. Resolve aggregate convergence and asynchronous errors before advancing the
   clock. Advance to period end and wait for ready status. Retrieve the generated
   draft and disable automatic advancement. Explicitly finalize the draft with
   `auto_advance=false`, then verify its actual lines, non-live mode, finalization
   timestamp, `status=open`, quantity 250, total and amount due 250 cents, and
   amount paid zero. Do not invoke send or pay.
   Do not send more wall-time usage into this clock after advancing it.
5. Retain a sanitized receipt, then delete or retire only journaled owned
   resources. Remove clock-owned resources through their documented cascade;
   archive prices/products and deactivate meters where deletion is unavailable.
   Record retained invoice history and retired objects accurately.

Clock behavior, metering and finalization in this particular account require an
early remote canary. The sequence is proposed, not already verified. If the
account cannot support it, fail the qualification and revise the design; do not
silently claim success from a preview. Query invoices by explicit customer or
subscription because general listings can omit clock-generated objects.
[Test-clock API guidance](https://docs.stripe.com/billing/testing/test-clocks/api-advanced-usage)

Manual finalization verifies Stripe's calculated invoice, rather than the automatic
collection lifecycle. `auto_advance=false` disables automatic invoice emailing,
payment attempts and finalization; the explicit finalize operation retains that
setting. [Automatic advancement](https://docs.stripe.com/invoicing/integration/automatic-advancement-collection),
[Manual finalization](https://docs.stripe.com/api/invoices/finalize)
Flexible subscriptions containing only metered items omit the initial invoice
under these constraints. [New subscription invoices](https://docs.stripe.com/billing/invoices/subscription#new-subscription-invoices)

Persist a private cleanup journal independently of transient worker state.
Perform Stripe cleanup before removing the owned database/allowance store.
Before local stack teardown, write and verify a private recovery snapshot with
frozen event payloads and hashes, source/route identities, attempt states and
first-attempt deadlines, allowance consumption and the resource journal. Exclude
credentials and prompts; restrict file permissions and keep it outside public
artifacts and Git. A resource journal alone is insufficient. If the snapshot
cannot be verified, preserve the owned durable store and fail cleanup instead of
erasing uncertain delivery evidence. Normal runner teardown must honor this
checkpoint rather than unconditionally remove database volumes.
Recovery uses exact IDs and ownership checks, never broad account deletion or
guessed matches. A lost create acknowledgement that cannot be resolved safely,
cleanup failure or residual active resource fails the lane and leaves explicit
operator recovery evidence. Some provider history cannot be deleted; retirement
is a distinct recorded outcome. Receipts omit secrets, raw prompts, account and
customer identifiers and private run state.
Recovery after the original allowance expires is a separate explicit operator run
with a new bounded cleanup allowance. It retains the original submission deadlines
and cannot restart or resend uncertain meter events beyond their replay window.

## Verification and milestones

### Milestone 1: contract and offline adapter

Implement the optional dependency lock, pure projection, separate schema and
roles, SDK boundary, fenced outbox and thin-event/summary parsers. Use the real
pinned SDK with an injected offline HTTP transport, asserting exact wire
encoding, API-version headers, identifiers and no automatic retries. No Stripe
account credentials or writes are needed in this milestone.

Required cases include complete/unknown-cache usage, malformed/unsupported
evidence, owner mismatch, missing/changed mapping, historic period rescans,
second boundaries, payload conflicts, HTTP success with mismatched mode/payload,
cached 500, retry headers, asynchronous rejection, pagination and pricing.
Preserve all existing Lago behavior and serialized projections.

### Milestone 2: owned PostgreSQL and native-workflow robustness

Exercise public installed recorder evidence and the new outbox against real
owned PostgreSQL fixtures on existing AMD64/ARM64 and PostgreSQL 16/18 lanes.
Run two exporters and restart workers at projection, send and acknowledgement
boundaries. Verify lease fencing, same-customer serialization, allowance sharing,
restricted roles, late observations and original attribution across resume.
Include races between stale unresolved scans and the first delayed observation.

Test a lost acknowledgement, replay immediately before the deadline, refusal at
and after expiry, preserved first-attempt time after restart, never-submitted old
events, quota exhaustion, cleanup time reservation, verified recovery snapshots
and failed cleanup. Verify the two-call/250-token
workflow and a pause-only workflow with absolute zero usage. Assert that delivery
failure does not change workflow results and no private SDK access is introduced.
These tests use credential-free transport fixtures and establish local robustness,
not successful Stripe account ingestion.

### Milestone 3: owned account qualification and consumer documentation

Run the bounded capability canary, then the full non-live account scenario and
actual-invoice reconciliation. Capture source commit, installed wheel hashes,
architecture, database/SDK/API versions, configured mode, quantities, amounts,
request allowance, unresolved outcomes and cleanup/retirement results.

Document installation, public exporter inputs, secret delivery, provisioning,
explicit opt-in, running the lane, reading receipts and recovery after ambiguity.
Label example commands as proposed until implemented. Package the fixture and
test inputs through the source-distribution allowlist and public-build manifest;
verify a fresh wheel/sdist consumer without sibling checkouts or local caches.
Only then consider a Lab version/release. No Prosaic SDK release is expected.

## Completion criteria and limits

Completion requires all three milestones, passing existing Lab regressions,
source/wheel verification, the required real PostgreSQL matrix, an actual account
receipt proving 250 tokens and a $2.50 finalized test invoice, and verified owned
resource cleanup/retirement. A missing account capability remains a qualification
blocker with its exact reason; synthetic success does not replace it.

This slice omits real inference, real charges, subscription lifecycle automation,
Connect, refunds, multiple pricing tiers, webhook hosting and a general billing
platform. It provides an application integration example and concrete reliability
evidence. Production usage policy, customer consent, retention requirements and
the Meters-versus-Metronome decision remain host responsibilities before any
customer rollout.
