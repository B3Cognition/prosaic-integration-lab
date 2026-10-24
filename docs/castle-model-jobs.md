# Optional Castle model jobs

`prosaic_integration_lab.castle_jobs` provides three explicit consumer jobs:
`judge`, `entity_refinement`, and `corpus_origin`. They are independent of
ordinary retrieval, deterministic SOAR, and SUE review. Nothing calls them
automatically. `JobSettings()` and a missing settings mapping are disabled;
disabled start/resume dispatch no models. Importing the package needs neither
Castle's legacy engine nor Runtime/Harness. Enabling execution requires the
installed public Runtime 0.9.8 and Harness 0.9.4 APIs.

The trusted host selects candidates and authorizes their text before calling
this Python API. It supplies its authenticated `Principal`, namespace, public
Harness store, Runtime configuration and accounting recorder. Client/model
identity fields and source provenance never grant authority. Do not expose this
API directly to unauthenticated request bodies. It does not read source files,
perform retrieval, scan a corpus, invoke Castle manifests, or write corpus data.

```python
from prosaic_integration_lab.castle_jobs import CastleJobSession

# All arguments here are constructed by the trusted application host.
jobs = CastleJobSession(
    {"enabled": True}, store, runtime_config, principal, namespace,
    accounting=recorder,
)
waiting = jobs.start(
    run_id, kind="judge", query="current export consent", top_n=2,
    candidates=[
        {"sourceId": "spec", "text": authorized_spec_text,
         "revision": "r1", "reference": "fixture://spec"},
        {"sourceId": "notes", "text": authorized_notes_text,
         "revision": "r3", "reference": "fixture://notes"},
    ],
)
# Display the frozen proposal/status to the authorized caller first.
done = jobs.resume(run_id, expected_revision=waiting["revision"], choice="continue")
advice = jobs.report(run_id)
```

Use a fresh 32-character lowercase hexadecimal run ID. `start` creates a
zero-call Harness pause; `reject` ends it without a call. Duplicate start with
identical input returns current status. Changed input under the same ID fails
with `job_request_conflict`. Source text, revision, reference, optional
provenance, text SHA-256, policy and owner are frozen together in the request
signature. Mutating the caller's original objects afterward has no effect.
If an input `textSha256` is supplied, it must match the exact UTF-8 text, including
CRLF and Unicode. Provenance is retained as caller-authorized evidence, not
independently attested source authenticity. Never claim arbitrary supplied text
was authenticated by Castle merely because a job accepted it.

The jobs accept 1–100 unique source IDs and at most 64 KiB of source text within
a 128 KiB JSON request. They reject duplicate JSON keys, nonfinite numbers and
excessive JSON structure. Default limits are one provider request, zero tool
calls, 4,096 reported tokens, 60 seconds per invocation and 24 hours per run.
Host settings can select at most 16,384 tokens, 60 seconds and seven days. No
adapter or workflow corrective retry is allowed. The host must select its
endpoint output-token ceiling to fit its total allowance; exceeding the total
allowance produces a blocked run rather than usable advice.

## Ranking

`top_n` defaults to `min(10, candidate_count)` and must be an integer between one
and `min(50, candidate_count)`. Only the first `top_n` candidates are sent to
the model, with their first 600 characters, mirroring the legacy judge bound.
The response must be exactly `{"ranked_indices": [...]}` with a complete
permutation of `range(top_n)`. The model is instructed to rank snippets by
relevance to the query, from most to least relevant. Booleans, floats, partial lists, duplicates,
extra indices, negative indices and extra fields fail validation. A valid
permutation reorders only that prefix; the untouched tail retains its original
order. `rankedSourceIds` identifies the frozen candidates; the host decides
whether to display/use the advisory ordering.

Malformed output yields the entire original ordering with
`audit.fallback=true`, a specific reason and response digest. A failed,
unknown-usage, interrupted or unapproved run also yields original ordering
with an explicit status/reason; it never treats such a result as a model
recommendation. The audit includes the accepted receipt digest when available.
Harness completion means a bounded response was retained, not that it passed
the ranking/classification contract. Always inspect `audit` and `result`.

## Entity refinement

Start `kind="entity_refinement"` with the frozen source candidates and an
`entities` list. Each of at most 25 unique entries has exactly `name`,
`currentType` (`person`, `project`, `topic`, `uncertain`) and `contexts`.
Each entity has up to three context records with exactly `sourceId`, a
one-based integer `line`, and `quote`. Quotes must be literal substrings of
that frozen source line, at most 240 characters. Names are bounded to 128 UTF-8
bytes. The host chooses candidates and sampled contexts; authoritative
manifest/git classifications should generally be excluded, as in legacy
`llm_refine`.

The response has exactly `classifications`, one `{name,label,reason}` record
per input entity in order. Names must match exactly; labels are `PERSON`,
`PROJECT`, `TOPIC`, `COMMON_WORD`, or `AMBIGUOUS`; reasons have at most 120
characters. The prompt preserves the legacy distinction between a user's own
project and third-party frameworks, APIs and vendors. The result is a separate
advisory record: `COMMON_WORD` deletes nothing, `PROJECT` promotes nothing,
and persona advice never changes a person or corpus record. Invalid output
returns `result=null` with an audit reason.

## Corpus origin

Start `kind="corpus_origin"` with caller-selected frozen samples. The model
sees the first 800 characters of each of the first 20 sources, matching the
legacy classifier's sampling bound. The strict output fields are
`is_ai_dialogue_corpus` (boolean), `confidence` (finite number in [0,1]),
`primary_platform` and `user_name` (nullable strings), `agent_persona_names`
and `evidence` (bounded string lists). The prompt retains the legacy tentative
AI-dialogue hypothesis for thin evidence. It asks whether the samples record
human–AI conversations or ordinary narrative, stories, research notes, journals
or code, using conversational turns, interaction with known AI platforms and
corpus-specific evidence; a platform name alone is not proof. The returned human name is removed
case-insensitively from persona names, preserving the legacy distinction.
Failure yields no classification, with explicit audit evidence; it never
manufactures a confident corpus label or writes origin metadata.

## State, accounting and compatibility

Harness owns all accepted state and invocation receipts. Runtime owns actual
model dispatch and its recorder owns usage evidence. Owner checks bind tenant,
actor, billing account, application and namespace before state access. Resume
reconstructs the frozen workflow/policy and verifies the Runtime fingerprint.
Stale revisions and changed bindings cannot authorize dispatch. A pending
invocation is resumed only by adopting its saved receipt. Without a receipt,
it stays `interrupted_call`; the API offers no interrupted retry flag. Usage
evidence is neither consent to retry nor an invoice. Public reports expose
filtered status, source identities, advisory results, audit digests and token
coverage, never raw Harness state, raw model responses or accounting contexts.

Only the host-provided OpenAI-compatible Runtime HTTP wire is admitted here;
other provider transports are explicitly rejected as
`unqualified_job_transport`. Credential-free tests qualify loopback fixture
mechanics only. They do not establish live provider quality or transport
parity. Castle's legacy `judge`, `llm_refine`, `corpus_origin`, provider clients
and CLI transports remain retained in the independent fork. There is no claim
that this bounded consumer API replaces their interactive, batching,
cancellation, corpus-merging or CLI behavior. Arbitrary custom SOAR remains
outside these jobs and is untouched.

The unit fixture uses the public installed SDKs, a public file run store and a
non-durable public testing recorder. It verifies strict permutations, tail
preservation, malformed/failed/unknown fallback, frozen exact source text,
wrong-owner and stale revision refusal, disabled zero imports/calls, attribution,
Runtime binding drift and saved/missing receipt recovery. Its interruption
test raises at the receipt-save boundary; real process-loss/PostgreSQL and
installed-Lab-wheel acceptance are separate qualification lanes. No live
inference or corpus mutation is part of this evidence.
