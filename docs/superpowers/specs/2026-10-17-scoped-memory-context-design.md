# Scoped memory and bounded context assembly

Implement the maintainer-approved next milestone in Lab, through public installed
SDKs. The previous comparison found no recall benefit, missed the stale gold
episode and returned hostile prose across every populated-tenant case. Fix the
host selection/admission boundary before further model experiments.

Use Python and existing dependencies. Reuse the isolated Lab checkout. Native
execution and the earlier opt-out of design questions remain in effect. Core,
Runtime and Harness source stay unchanged. No release/push, autonomous memory
writes, vector service, model prompt changes or new live inference is included
in this implementation/qualification slice. Remaining live allowance is retained
for a separately prepared fresh comparison, not spent by offline qualification.

## Trusted selection

Add `lab_runner.memory_policy`, leaving v1 corpus/source formats and legacy
retrieval behavior untouched. `ScopedCorpus(document, historical_sources,
metadata)` admits a v1 corpus plus a separate, host-authored v1 metadata document:

`{version, episodes: [{tenantId, episodeId, entityId, topics, expiresAt}],
currentSources: [{tenantId, sourceId, sourceVersion, sourceSha256}]}`.

Each corpus episode requires exactly one metadata row. Unknown/duplicate rows,
unknown fields, invalid identifiers, duplicate topics, inconsistent expiry and
ambiguous current source references fail admission. The host registry supplies
current source versions/hashes independently of notes and model requests.

`retrieve(tenant_id, entity_id, topics, as_of)` first partitions by trusted tenant.
It then filters exact entity, observation time, expiry, matching current source
references and positive exact topic overlap. Missing/changed references are
excluded. Rank by trusted topic overlap, newest observation, then episode ID.
Ignore free-text notes and legacy tags for eligibility and ranking. Preserve
whole episodes, at most three and 4,096 encoded bytes. Do not upgrade historical
notes to authoritative current evidence. Return owned data and private exclusion
reasons; foreign IDs, counts and changes cannot affect local query output.

## Context and trajectory admission

`assemble_context(mandatory, retrieval, *, quote_inputs, counter_identity,
max_requests, output_tokens, token_ceiling, reported_tokens=0,
inflight_tokens=0)` preserves all mandatory fields and owns its JSON inputs.
The caller may not supply the reserved `recalledEpisodes` field. Start with empty
recall, then try whole ranked episodes in order. A failed optional fit is recorded;
smaller later candidates may still fit. Counter failures or invalid quotations
fail closed, never become zero costs or an unqualified fallback.

The trusted, provider-neutral `quote_inputs(context)` callback supplies one
nonnegative input ceiling for each permitted provider proposal. Its provenance
is supplied by a host `quote_identity` digest. All request output ceilings and
all input ceilings, plus reported/inflight usage, must fit the token ceiling.
These are a host planning domain, not a prediction that arbitrary model-generated
continuations fit. To make the bound enforceable, `guard_registration(base,
plan)` wraps the qualified public Runtime registration: each proposed native
request must meet its next input ceiling and exact output ceiling. It never
returns a fabricated count or refunds a proposal slot. Reject overflow, changed
base descriptor, unsupported native input or additional proposals before HTTP.
Runtime still enforces actual shared budgets and honestly settles unknown/breached
usage. Input planning can therefore refuse completion, but cannot enlarge limits.

If mandatory context cannot fit, return it intact with empty recall and a rejected
plan. Its guard refuses every request. This produces an explicit known zero-call
Runtime failure in the native workflow rather than trimming current evidence.
The guard is stateful, lock-protected and single-execution; it is never serialized
or reconstructed to authorize retries after an uncertain outcome.

## Native integration and evidence

An opt-in `ScopedContext` adapter owns `ScopedCorpus`, a qualified base descriptor,
host quotation callback/digest and fixed case limits. It prepares the existing
public request with scoped recall and a frozen context-assembly report. Its
identity binds tenant-local metadata/current registry, quotation identity,
counter descriptor, policy/implementation and exact case scope. Other tenants'
valid changes do not change that identity. Callbacks/credentials are never saved.

Add optional `context_builder` to memory preparation, native execution and receipt
recovery; default execution remains the legacy path. Use the selected plan's
guard throughout Harness retries. Bind the plan into frozen context and recovery
identity. Recovery reads the saved selection/plan without retrieval, quotation or
provider execution; changed source/scope/policy rejects replay. No new benchmark
scorer or private expected answer enters selection, quotation or native input.

Persist private proposal/admission trace, public Harness events and SDK-owned
recorder snapshots. A small adapter around public `MemoryRecorder` saves its
intents/observations atomically; it does not normalize usage or implement an SDK
engine. Actual dispatch/usage comes from native receipt counters and recorder
observations, not from counting proposals. Tool errors without a public cause
are explicitly unclassified. Unknown/partial outcomes remain unknown. Replay
does not rewrite traces or infer missing usage. This is local evidence, not an
invoice, external provider attestation or a distributed memory service.

## Qualification

Watch failing tests before implementation. Cover populated-tenant irrelevance,
isolated same-entity hostile notes, note/tag ranking invariance, tenant/entity
boundaries, future/expired/changed/missing sources, ownership, bounded packing,
stable ordering, quotation failure, mandatory refusal, output/proposal/input
guards, shared limits and recover-only behavior. Use public Runtime/Harness and
credential-free loopback providers, with two provider wire formats at the guard
boundary. Fixed memory case limits remain 4 requests / 2 tools / 8,192 tokens /
600 seconds and output 512. Do not raise any current live ceiling.

Run the full Lab suite, build immutable wheel/sdist, match installed payloads,
exercise scoped native fixtures/recovery in an isolated installed environment,
and replay with sockets/dispatch disabled. One fresh whole-change reviewer checks
the completed branch. Offline results establish host contracts, not live memory
efficacy. Prepare future live evaluation only after these controls are qualified.
