# Controlled retrieval-memory milestone

Date:2026-10-16. Status: proposed implementation design; direction authorized by
the maintainer's "Proceed with controlled retrieval-memory milestone". Detailed
implementation design awaits review. No memory feature or live run exists yet.

## Intent and ownership

Test whether read-only recall of prior episodes improves grounded decisions,
without allowing old notes to override current evidence or leak across tenants.
Build a separate Integration Lab consumer experiment using public installed
Runtime/Harness APIs. Core remains a Markdown distribution engine; no model,
retrieval engine or manifest execution enters Core. Native implementation is the
previously selected method. Preserve existing quality suites and all22allowances.

The approved direction is a bounded read-only retrieval experiment with source
versions, tenant isolation, freshness/conflict checks and a memory-disabled
comparison. Choices below are the implementer's proposal, not prior user choices.

## First slice and explicit limits

Use a small immutable synthetic corpus of earlier task episodes, frozen before
evaluation answer keys are authored. Persistence means reopening the same
content-addressed corpus across runs; no automatic memory creation or learning.
No real user/run history is imported. Each episode contains episodeId, tenantId,
observedAt, topic/entity tags, a bounded note, and sourceRefs containing sourceId,
sourceVersion and sourceSha256. The note may describe an earlier outcome but
never contains the held-out task's private expected answer or scorer feedback.

Select deterministic lexical retrieval as the first reference implementation:
casefolded ASCII alphanumeric tokens, overlap of unique query and note/tag tokens,
positive scores only; sort descending score then descending observedAt then
ascending episodeId. This is episodic text retrieval, not vector/semantic memory.
It adds no embedding provider, dependency, index service or unpriced inference.
An embedding retriever can be a later separately measured implementation.

Corpus JSON:version1, maximum256KiB/128episodes globally; notes at most1024UTF-8
bytes, at most4sourceRefs each, IDs use the existing bounded identifier contract,
timestamps explicit UTC RFC3339. Reject duplicate episode IDs within a tenant,
unknown fields, invalid hashes/times and oversized data before model dispatch.
Never execute note text, paths or referenced manifests. No query-time corpus write.
Package a separate historical-source fixture store, at most256KiB, keyed by
tenantId/sourceId/sourceVersion. Validate every reference against canonical bytes
of its historical source snapshot; reject dangling references or hash mismatch.
A historical snapshot is synthetic host evidence, not provider attestation. The
model receives only bounded notes/references, not the whole historical store.
Current-source verification still uses the separate current snapshot.

A trusted host supplies tenantId, task and asOf. Model arguments cannot choose
tenant, corpus path or asOf. Filter tenant and observedAt<=asOf before scoring,
then return at most3episodes and4096encoded UTF-8 bytes. Sort/whole-record packing
is deterministic; if a candidate exceeds the remaining byte cap, omit it and
continue without truncating its fields. Zero overlap/no eligible episodes yields
an empty result. Foreign-tenant episodes must not affect rank, counts or digests
exposed in model/public views. Malformed corpora fail closed, not as empty memory.
This noninterference guarantee applies between valid admitted corpus artifacts.
Global parsing, size/lineage validation and partitioning occur as trusted host
artifact admission, before request processing. An invalid global artifact blocks
admission for the operator; it is not a tenant-facing query endpoint. Do not claim
protection from hostile operators, constant-time isolation or independent tenant
availability under malformed global configuration. Future real-history services
would require their own separately partitioned admission design.

After admission, retrieval and recovery use a tenant-local corpus identity derived
only from that tenant's episodes and historical sources. Model/public identities,
results and contexts must remain unchanged when only valid foreign-tenant content
changes. A global artifact root is private operator evidence and must not enter
model/public digests or tenant checkpoint identity. Foreign-only corpus changes
do not block a tenant's resume; local corpus/current-source changes do. Exclude
measured durations from byte-identical context assertions; no timing guarantee.

## Context assembly and source verification

Retrieve once on the host before constructing the model invocation. Both arms
receive the same public task and current-source index plus a clearly delimited
untrusted recalledEpisodes field. Enabled receives bounded retrieval results;
disabled receives an empty array. Query text is deterministically constructed
only from public task/entity/topic fields, never expected answers or required
source assertions. The host retrieval operation is separately metered; it is
not misreported as a Runtime native tool dispatch or a model-generated action.

This choice preserves the current one-lookup-round provider setup: adding a
model-selected search tool would need another native round and would confound
this first comparison with changed tool policies. Corpus assembly is measured
as host retrieval, with its own duration, counts, query/result and corpus digests.

A recalled note is a navigation hint. It conveys neither authorization nor
proof of a current fact. The model must call lookup_records against the current
host-owned source store; final fact/citation claims must join the actual current
lookup journal, successful native events and receipt. Index and tool IDs are
identical across arms; notes grant no extra source access. The current index has
public labels/versions but no fact values. It remains usable without memory;
a no-memory arm is not deliberately deprived of required sources.

Source validation uses current returned records and explicit public authority/
revision rules, including insufficient evidence. A stale note/reference cannot
override a newer source; old content digests are retained for lineage, not treated
as proof that a current fetch matches them. Missing/revoked current sources cannot
be filled from a note. Hostile note instructions remain untrusted. Any unsupported
or ambiguous current evidence fails closed. No model-produced answer is replaced
by a host answer. Private expected answers remain final-scoring inputs only.

Use one ordinary reviewer workflow with at most2attempts and public validation.
A retry may identify malformed/missing evidence using public closed categories;
it must not inject an answer target or the retrieved gold episode/source IDs.
Report first-attempt outcomes separately so retries cannot hide memory effects.
Existing host-target-corrected quality results keep their distinct identity.

## Evaluation design

Add a separately versioned retrieval-memory-v1 suite:12held-out cases,2per family:
1. Relevant prior episodes that help identify current supporting sources.
2. Stale prior outcomes contradicted by current authoritative source revisions.
3. No matching episode; current sources still support an answer.
4. Same-looking foreign-tenant episodes; isolation leaves only authorized context.
5. Relevant notes containing hostile instructions or misleading source suggestions.
6. Missing/revoked current facts; memory must not fabricate sufficient evidence.

Use an ordered freeze protocol. First qualify retrieval, prose, context assembly,
public checks and source tools using separate development fixtures; then archive
their content hashes together with the corpus/historical source store. Only then
author the12evaluation cases/current sources/private answers and freeze their
manifest. A reviewer checks that prior notes contain no current evaluation oracle
and that queries never use private assertions. The implementation author may
inspect answers to build/test the scorer; this is not a developer-blind study.
Held-out means held out from retrieval/prose tuning, not unknown to every human.

Packaging and scripted fixtures may exercise the final48sample schedule, but no
retriever, corpus, prompt or feedback tuning may follow inspection of evaluation
outcomes while retaining a held-out claim. If a defect forces such changes, keep
the failed artifacts, re-freeze them and create a fresh evaluation set; otherwise
label the study a fixed development-set diagnostic. No live failures are silently
folded back into training cases. Record both freeze manifests in private evidence.
The gold relevant episodes and expected facts/citations are private scorer data.
Required current evidence is at most4records; the source store at most16per case.
Both arms see identical source indexes and execute under identical permissions.
A memory benefit is a measured hypothesis; no improvement is required or assumed.

For each case, run disabled and enabled for each of the two existing profiles,
one repetition initially:48samples. Deterministically alternate arm order by
case within each profile and record order. Do not pool profiles or call repeated
cases independent evidence of a population success rate. Retain counterproductive
memory outcomes; report paired pass/fail transitions and first-pass differences.
A later repeated/expanded study is required for reliability/rate claims.

Every sample has the same limits:4provider requests,2native tool calls,8192reported
tokens,600s; max2invocations,2provider requests and1lookup per invocation. No implicit
fallback, profile escalation, live retry or cap expansion. Retrieval is bounded
separately to1host query/3episodes/4096result bytes. Record it even if inference
fails. Full comparison bounds192requests/96tools/393216tokens,48samples; batch
ceiling28800s. Derive reservation proof from actual graph/policy before dispatch.
No live allowance is authorized by this design. Current retained totals852/293/
870793 under893/314/1130638 leave41/21/259845, including5fully charged unknowns.
Recompute exact residuals and obtain any required extension only after offline
implementation and immutable installed qualification; no old charge is reset.

## Evidence, recovery and reporting

Reuse existing canonical encoding, durable reservation and profile fingerprint
helpers through their public consumer interfaces. Keep the new CLI/resources/
scorer separate so evidence-review-v1 digests and replay remain stable. A shared
helper change requires requalification and must not invalidate historical replay.
New preflight must not construct Runtime, read secrets or make network calls.

Bind suite/tenant-local-corpus/retriever/query-policy/context/prose/source-store/scorer/SDK and
all limits into identities. Freeze tenant-local retrieval results, corpus identity
and current-source snapshot before invocation and use the same prepared context
for recovery. Local corpus/source drift blocks recovery rather than silently reranking.
Never fork a running Harness. Missing receipts block without a model redispatch;
persisted receipts are adopted once. A changed corpus/arm/tenant cannot reuse an
old allowance or resume a foreign run. Keep raw context and full IDs private.

Public reports contain opaque profile IDs, bounded case/arm identities, task and
first-pass success, native tool efficiency, known/unknown usage, retrieval recall@
3 and precision@3, result counts/bytes/duration, stale-source/injection/isolation
checks and paired arm differences. Define recall/precision as null for empty gold
or empty retrieved sets respectively; also report the denominators. Report corpus
coverage separately from retrieval quality and final task correctness. Do not
expose notes, queries, tenant IDs, filesystem paths, endpoint URLs or raw errors.
Raw evidence is private0700directories/0600files with receipt/journal digests.

Full isolation checks include changing only foreign-tenant corpus contents and
proving tenant-local retrieval/model context stays identical. Bad hashes,
future-dated notes, result-byte caps, duplicate/tied results, no hits, malformed
corpora, stale pointers, hostile text and unsupported current records need tests.

## Acceptance and next steps

Before live inference: deliberate failing tests then implementation, full Lab
unit/functional suite, fresh review, wheel/sdist payload audits, isolated installed
smoke and all48fixture samples through public Runtime/Harness. Provider payloads
must prove exact arm differences and no private-answer leakage. Fixture counters
must independently reconcile native requests/tools; retrieval counters/digests
are independently checked. Test saved-receipt adoption, missing-receipt blocking
and corpus drift. Offline re-score/replay must forbid sockets and provider execution
and leave evidence/allowances byte-identical. Fixtures are not live memory efficacy.

This milestone proves a bounded retrieval/context contract and enables measuring
whether recall helps. It does not implement automatic memory writes, vector
search, semantic graphs, parallel scheduling, arbitrary-code execution, production
memory services or real-history ingestion. Preserve the unresolved512token provider
truncation behavior as its own known failure; do not silently raise model settings.
No push/release/merge or Core/SDK extension is implied. After this design is approved,
write the native implementation plan and execute it; seek live budget only at the
qualified, concrete study boundary.
