# Compare Castle with file search on your own material

This is an **experimental, explicitly invoked Lab benchmark**. It compares an
agent's literal `rg` search plus bounded file reads with Castle raw FTS and
Castle with bounded context expansion. It can also add the bounded consumer
completeness critic and author. SUE and SOAR are outside this workflow.

Installing Lab enables neither memory nor review. Existing application defaults,
the canonical requirements-review workflow and the earlier private 16-question
pilot are unchanged. Nothing here publishes packages or automatically collects
sessions. Keep real sources, keys and results in a private directory outside Git.

## What you need

- Python 3.12+, this matching Lab wheel, and `rg` on PATH.
- The Lab's checksum-verified SDK family for offline preparation and replay.
- **Execution currently requires the separately qualified Runtime candidate
  with `json_schema_v1`** used in the preserved constrained-generation study,
  plus its matching Harness. Published Runtime 0.9.8 does not supply that API.
  Do not edit version guards or silently substitute an editable sibling SDK.
  See [the constrained SDK evidence](verification/sue-constrained-json-2026-10-24.md)
  and obtain its exact checksummed bundle from the maintainer. The ordinary
  released dependency manifest remains unchanged. A public-index execution
  recipe is blocked until that API is published and qualified.
- For a real Castle arm: the separately installed adapter and worker described
  in [Prosaic Castle](prosaic-castle.md), an explicitly prepared private palace,
  and its exact record-to-source map. The read worker does not import sources,
  repair indexes, run embeddings or grant model tools.
- For live inference: an existing model endpoint, a private secret file and
  explicit finite request/token/time ceilings. Source context is sent to the
  selected endpoint; fixture mode uses only its local synthetic responder.

Run the examples from outside source checkouts with the chosen environment's
`python` on PATH. `python -m lab_runner.memory_benchmark` by itself reports
`enabled: false, executed: false` and starts nothing.

## First: a small credential-free walkthrough

Replace `/absolute/private` with a private directory you own. Each output
directory must be new; the CLI refuses to overwrite an earlier run.

```sh
python -m lab_runner.memory_benchmark init --directory /absolute/private/example
python -m lab_runner.memory_benchmark validate \
  --dataset /absolute/private/example/dataset.json \
  --policy /absolute/private/example/policy.json
python -m lab_runner.memory_benchmark freeze \
  --dataset /absolute/private/example/dataset.json \
  --policy /absolute/private/example/policy.json \
  --output /absolute/private/example-frozen
python -m lab_runner.memory_benchmark run --fixture \
  --frozen /absolute/private/example-frozen --output /absolute/private/example-run
python -m lab_runner.memory_benchmark replay \
  --frozen /absolute/private/example-frozen --run /absolute/private/example-run
```

Expected: nine scheduled samples (three questions × three retrieval arms),
nine synthetic provider requests, no review, and semantic quality `unmeasured`.
These responses exercise the real SDK transport and validation; they are not
model answers. The fixture's literal synthetic ordering is **not Castle FTS**.

To exercise critic→repair too, choose a new run directory and add `--review`
to `run --fixture`. The same accepted base answer and frozen retrieval are
retained alongside the reviewed candidate; at most three requests per sample.
Running the identical completed command again returns verified saved results
with zero calls. `replay`, `report` and `grade-template` never dispatch models
or workers. Review is off unless explicitly selected.

For an offline scale smoke, `init --questions 200` produces 200 synthetic
questions cycling through three examples. It checks throughput/denominators,
**not 200 independent quality cases**. Replace them for a meaningful study.

## Use your notes or session exports

Export sessions to UTF-8 text or Markdown first. Choose only authorized files;
there is no folder crawl or chat-history API. Preserve original bytes and known
export omissions. Put the manifest and host policy in separate files:

`dataset.json`:

```json
{
  "version": 1,
  "sources": [{"id": "database-notes", "path": "database.md", "wing": "notes"}],
  "cases": [{
    "id": "q001",
    "question": "Why did this project choose SQLite, and what was still unverified?",
    "queries": ["SQLite", "unverified"],
    "sourceIds": ["database-notes"]
  }]
}
```

`policy.json`, selected by the trusted host/operator:

```json
{
  "version": 1,
  "namespace": "owner-project",
  "root": "/absolute/private/exports",
  "allowedWings": ["notes", "sessions"]
}
```

In a normal comparison, `sourceIds` should list **the whole authorized corpus**,
not just the source that contains the expected answer. Otherwise the benchmark
gives retrieval an oracle filter. Narrower grants belong in explicitly labelled
scope tests. Namespace, paths, grants and worker command come from host policy;
source text, clients and models cannot grant themselves access.

Limits are 1–1,000 cases, 1–3 fixed queries per case, 5,000 explicit sources,
4 MiB per source and 64 MiB total source bytes. The frozen JSON manifest is at
most 16 MiB. Symlinks, escaping paths, duplicate IDs and unknown grants reject
before the output snapshot is created. Unicode quotation offsets index Python
characters, not UTF-8 bytes. CRLF is preserved exactly.

Use the same validate/freeze commands with these files. Changing source data,
questions, scope or benchmark code requires a new freeze/run; never edit old
evidence to improve its score. Frozen copies can replay after originals move.

### Choose a declared retrieval policy

The default remains `literal-first-v1`, preserving the original literal-phrase
file search and first-query-first open selection. For a new keyword comparison,
explicitly select the balanced policy while freezing:

```sh
python -m lab_runner.memory_benchmark freeze \
  --dataset /absolute/private/dataset.json --policy /absolute/private/policy.json \
  --retrieval-policy terms-round-robin-v2 \
  --output /absolute/private/balanced-frozen
```

Add the same flag to source `validate` if needed. A frozen snapshot carries its
policy; `run` cannot replace it. Add `--key` and `--castle-map` normally.

The new policy extracts unique Unicode alphanumeric words from each query,
without stop-word removal or grading-key access. Punctuation-only queries
reject before freezing. File search uses whole-word, case-insensitive literal
OR and retains at most five matching line anchors per query, prioritized by
distinct query-word coverage, then source path/line. Each keyword is checked
independently by rg, including overlapping terms; this costs additional local
scans within the unchanged task deadline. Its JSON byte anchors are checked
against the frozen UTF-8 bytes and converted to character offsets. Source line
numbers use LF, preserving CRLF and other Unicode separators exactly. Castle receives the same
normalized words and retains its native FTS ranking. Tokenizers, stemming,
line/chunk units and ranking still differ; this is a declared bounded keyword
baseline, not a claim of identical analyzers or adaptive human/agent search.

Both arms distribute five open slots round-robin across the visible candidates
for each query, preserving candidate order within each query. Equivalent file
path/line or Castle record candidates use only one slot. Expanded Castle reuses
the raw arm's exact ranks and selections. Context, cache, provenance, scope and
output limits stay unchanged. Create new snapshots/runs for this policy; do not
edit old datasets or relabel their results.

## Add an independent scoring key

Without a key, provided information supports retrieval and operational tests;
it does not support an answer-completeness claim. Before either arm searches,
have an authorized reviewer specify each question's positive required facts,
exact source spans and expected abstention. Keep this separate from the dataset.

```json
{
  "version": 1,
  "cases": [{
    "id": "q001",
    "expectedAbstention": false,
    "facets": [{
      "id": "reason",
      "description": "The documented reason for SQLite, with its historical scope",
      "sources": [{"sourceId": "database-notes", "start": 10, "end": 28,
                   "quote": "REPLACE EXACT TEXT"}]
    }]
  }]
}
```

The placeholder above is intentionally invalid until replaced with a real exact
quote and offsets. Every question needs 1–32 facets. Abstention facets may have
no source quotes when absence/scope is the expected result. Describe substantive
answer requirements; do not demand ritual export-history disclaimers unless the
question actually needs that detail. Do not generate gold from a retrieved hit
or let the answering model see the key.

Add `--key /absolute/private/key.json` to freeze. The key is bound separately
under `grading/key.json`; answering and review use only public frozen packets.
Changing the key is a new scoring version, with the old one retained.

## Attach an existing Castle import

Import and prepare the selected source copy through the existing authorized
Castle import operation first. Record any normalization/import coverage loss;
it is a failure, not permission to silently replace the source. Use a frozen
palace copy and keep the original import environment/evidence.

Supply a host-produced `castle-map.json` with every source and record, in source
order. This example has one record; real files may require many:

```json
{
  "version": 1,
  "sources": [{
    "id": "database-notes",
    "sourceId": "REPLACE_ORIGINAL_64_HEX_SOURCE_ID",
    "revision": "REPLACE_ORIGINAL_REVISION",
    "capturedAt": "2026-10-26T00:00:00Z",
    "records": [{"recordId": "REPLACE_ORIGINAL_RECORD_ID", "start": 0, "end": 100,
                 "capturedAt": "2026-10-26T00:00:00Z"}]
  }]
}
```

Take identities/timestamps from the actual import metadata; do not invent them
from a filename. Per-record `capturedAt` overrides the source default and must
retain distinct original timestamps. Records must cover each exact source
contiguously, with chunks of at most 800 characters. This profile cannot qualify
an import whose chunks differ from those bytes; retain the failure and prepare
a separately versioned compatible corpus/import rather than relax checks.

Pass `--castle-map /absolute/private/castle-map.json` to validate and freeze.
During execution, public adapter `search`, `fetch` and `snapshot` results must
match the map's namespace, wings, source/record identities, revisions, timestamps,
exact bytes and digests. Wrong scope/provenance stops the batch; empty and
unavailable are different outcomes. This benchmark does not repair a palace.

## Authorize and run a real comparison

`init` writes `live.example.json` with `enabled: false` and `review: false`.
Copy it outside the example and replace **all** paths, endpoint/model and limits.
The credential file and config must be private. Set `enabled: true` deliberately.
For review, set `review: true` and also pass `--review` on the command.

```sh
chmod 600 /absolute/private/live.json /absolute/private/model-key
python -m lab_runner.memory_benchmark run --live --review \
  --config /absolute/private/live.json \
  --frozen /absolute/private/study-frozen --output /absolute/private/study-run
```

There are three samples per question. Each sample reserves one answer request
and 32,768 reported tokens; enabling review reserves two additional requests
and 65,536 additional tokens. For 100 questions with review, admission for all
samples needs at most **900 requests and 29,491,200 reported tokens**. These are
ceilings, not expected consumption. A smaller explicit shared allowance may
stop early; remaining scheduled cases stay blocked in the report.

Each call has at most 4,096 output tokens and 60 seconds, one attempt and no
model tools. Initial answer/review each have at most 120 seconds and the whole
sample at most 300 seconds. Each sample sees at most 32 KiB of rendered retrieval
context, with at most five selected opens and 5 KiB per open; source qualification
quotations add at most 8 KiB to the returned answer. Larger corpora or question
counts do not enlarge per-task context. Strict and expanded reuse identical raw
search ranks/selections; expansion does not rerun search. The allocator reserves
the original local evidence floor before extras, and the per-open validated cache
prevents duplicate provider fetches. Selection is deterministic first-visible
selection, unlike the original operator-selected 16-case study; do not compare
these as an unchanged end-to-end treatment.

Under `literal-first-v1`, the file arm runs each query as a **literal phrase**, while Castle FTS tokenizes
it. The same multiword string can therefore return no file hits and many FTS
hits. This measures the declared fixed search policies, not an adaptive agent
that splits or revises `rg` queries. Inspect empty-hit counts and query wording
before interpreting a Castle advantage; report this limitation and precommit a
separate balanced query policy for any broader comparison. Do not change failed
run queries after seeing outcomes.

Unknown usage/completion stops further dispatch and holds the entire sample
reservation. Rejected output still incurs known usage. A failed review preserves
the accepted base answer separately and is **not a review pass**. No implicit
retry or settlement is provided. An interrupted pending execution is unresolved,
not permission to run it again. Start a separately authorized/versioned study
for changed budgets or prompts; preserve all earlier unknown reservations.

This benchmark's explicit snapshot policy is separate from the ordinary Lab's
released capture limit; it does not increase that application limit. Both
application features remain disabled by default after the benchmark exits.

## Inspect, score and preserve

```sh
python -m lab_runner.memory_benchmark status --frozen /absolute/private/study-frozen --run /absolute/private/study-run
python -m lab_runner.memory_benchmark replay --frozen /absolute/private/study-frozen --run /absolute/private/study-run
python -m lab_runner.memory_benchmark grade-template --frozen /absolute/private/study-frozen \
  --run /absolute/private/study-run --output /absolute/private/judgments-template.json
```

An authorized independent adjudicator fills a copy of the template. Every
accepted answer, base and full rendering, needs every facet's explicit judgment,
reason, exact answer quotations and displayed-source quotations. Also judge
contradictions, unsupported claims and correct abstention. Headers, omitted
paragraph ledgers and keyword matches earn no semantic credit. Exact citation
validity does not prove entailment; the adjudicator must read the actual answer
and contrary source passages. The tool verifies proof attachment, bindings and
denominators, not the truth of an adjudicator's reasoning.

```sh
python -m lab_runner.memory_benchmark report --frozen /absolute/private/study-frozen \
  --run /absolute/private/study-run --verdict /absolute/private/judgments-v1.json \
  --output /absolute/private/report-v1.json
```

Without `--verdict`, quality stays `unmeasured`. Failed/blocked cases remain in
the denominator; zero accepted reviews means review quality is unmeasured.
Keep fixture/live origin, citation validity, semantic completeness, base/full
answers, usage and execution failures separate. Preserve initial judgments and
add a new named version for adjudication; reports refuse overwriting existing
files or writing inside the sealed input/result trees.

Keep the entire frozen directory, run directory, separate keys/judgments/reports,
package checksums and import evidence privately. `results-seal.json` binds raw
receipts, input packets, outcomes and allowance. Replay verifies them without
touching the model or worker. Do not upload private corpora or raw run state to
GitHub, CI artifacts or issue comments.

For useful quality evidence, prefer 100–200 distinct questions from multiple
projects, with held-out cases and independent adjudication. Repeated questions,
source-familiar constructed tasks or a larger document pile do not establish
generalization, human time savings or production readiness.

The [first qualification and 100-question attempt](verification/memory-benchmark-2026-10-26.md)
records passing mechanics, failed live execution, query-policy limits and the
distinction between source visibility and answer quality.

The [balanced-policy follow-up](verification/memory-benchmark-balanced-2026-10-26.md)
records the fairer keyword baseline, per-query selection, preserved legacy
behavior and the separately failed strict Qwen preflight. Its complete source
visibility result is not a completed model/critic comparison.
# Optional compact model handoff

`freeze` and source `validate` accept `--generation-profile compact-citations-v1`.
Omit it to retain the existing `canonical-v1` model transport. The selection is
part of the frozen dataset and cannot be changed at run time. For the current
balanced retrieval comparison, combine it with
`--retrieval-policy terms-round-robin-v2`.

The compact profile sends each displayed source passage once, with paragraph
addresses and citation IDs. The model selects those IDs rather than copying
quotation text, hashes, source identities and evidence offsets. The host resolves
each ID against the immutable full packet and runs the unchanged canonical answer
schema, source grounding, scope/provenance and output-byte checks before Harness
accepts the stage. Critic feedback still uses the canonical critic schema and
critic-then-independent-author composition. Source text and feedback remain
untrusted data; no tools or additional source access are granted.

Raw compact responses remain in Runtime receipts and Harness checkpoints.
Reported candidates contain the resolved canonical answer. Replay verifies both
representations and their exact relationship. Invalid IDs fail; no fuzzy matching
or automatic citation repair occurs. Compact drafts must use complete indexed
paragraphs and supplied open-window/whole-record citations; arbitrary canonical
subspan drafts require the existing profile. Canonical output limits still apply
after expansion, so smaller wire output does not authorize larger answers.

This profile is experimental and does not establish model quality or enable
memory/SUE by default. Live execution still needs explicit configuration, the
checksummed constrained-JSON Runtime candidate, and finite shared allowance.
Unknown usage stops the run and retains its full reservation. Keep prior studies
and unknown reservations separate; a new profile is not a retry of an old call.

The [26 October compact-profile qualification](verification/memory-benchmark-compact-2026-10-26.md)
passes transport/regression checks but fails the local Qwen readiness gate: its
first request still times out at 60 seconds. Do not treat this as a qualified
answer-quality comparison or evidence that the completeness critic helps.

## Question-first experiments

Two additional explicit freeze options require the separately checksummed
Runtime `0.9.8+jsonschema.3` candidate and its `json_schema_order_v1` capability:

- `--generation-profile compact-question-first-v1` keeps compact guidance and
  sends the schema in its declared order, starting with `questionParts`.
- `--generation-profile compact-question-focused-v1` adds guidance to answer the
  requested parts with distinct necessary facts, deduplicate repeated support,
  and finish the object instead of enumerating every displayed paragraph.

Both preserve the same full displayed context, compact IDs, strict canonical
validation and scorer. There is no hard claim cap or hidden relevance filter.
Every source frame must still be reviewed. Material numbers, qualifications,
contradictions, uncertainty and missing evidence still belong in the answer.
The critic remains canonical feedback followed by an independent author; SUE
is not involved. Defaults and previous generation modes remain unchanged.

The frozen request includes the order-sensitive wire-schema digest. Changing
the profile or the declared property order requires a new frozen run; a saved
workflow cannot silently switch. These are candidate experiments, not a claim
that Qwen or the critic is qualified. Use a small preflight and inspect strict
acceptance, semantic scoring, latency and reported usage before a large run.

The [question-first qualification](verification/memory-question-first-2026-10-26.md)
passes mechanical verification but still fails the first local Qwen deadline.
The full model comparison remains gated; these profiles are not a quality claim.

## Host-resolved bookkeeping (opt-in)

Freeze with `--generation-profile compact-host-resolved-v1` to let the host
calculate question offsets and frame claim links. This requires the same
qualified `json_schema_order_v1` Runtime candidate as the question-first modes.
Without this option, existing generation behavior is unchanged.

In this format, the model quotes an exact, uniquely occurring part of the
question. The host derives Unicode character offsets; it rejects absent,
ambiguous, overlapping repeated, trimmed or normalized matches. Quoting enough
exact context, including the whole question, avoids ambiguous short phrases.
It also derives each frame's `used` status and claim IDs from the evidence
actually selected by claims. The model still reviews every frame and supplies
its reason and `unreferencedDisposition` (`duplicate`, `irrelevant`, or
`insufficient`), used only when that frame has no selected claim evidence.

The host then applies the existing canonical answer schema, exact grounding,
scope, provenance, reference and coverage checks. It does not repair an old
profile's rejected answer or infer semantic relevance. Nonexact/foreign quotes,
missing frames and inconsistent references still fail. Used-frame links follow
claim-array order in this new profile; all prior profiles retain their format.
Freeze a new run to adopt it; an existing workflow cannot switch on resume.

This removes bookkeeping from generation, not the need to evaluate answer
quality. Keep the same scorer and compare accepted answers before relying on it.
Memory and SUE remain disabled by default. The separate 360-second operator
diagnostic is not a new CLI execution profile or a cold-performance claim.

The [host-resolved qualification](verification/memory-host-resolved-2026-10-26.md)
records passing mechanics and an incomplete 360-second Qwen request. Do not treat
the profile as live-qualified or use that timeout as a scored answer.

## Explicit call timeout experiment

To test a slower endpoint with the same generation guidance, add
`--execution-profile bounded-120s-v1` when freezing the dataset. This selects
120 seconds per model call, up to 150 seconds for the initial answer, 270 for
critic plus author, and 450 for one retrieval/answer/review sample. The enclosing
limits include bookkeeping time. Request/token/output limits and strict scoring
stay unchanged; the live configuration's shared overall deadline still applies.

Omitting this option retains `bounded-60s-v1` and the previous deadlines. The
execution choice is frozen independently of `--generation-profile`; run/resume
has no timeout override. A new mode needs a new run. Smaller explicit stage
deadlines remain reductions. Memory and SUE stay disabled by default.

## Host-resolved evidence selection costs

The explicit `compact-host-resolved-v1` request now includes advisory
`evidenceBudget` metadata outside its unchanged source packet. It reports the
16384-byte canonical answer limit and exact expanded quote/citation costs. The
model is guided to choose sufficient support for each requested fact, reuse
evidence, and avoid copying the complete index into each claim. All displayed
bodies remain available; there is no evidence-count cap, source filtering or
host pruning. The unchanged validator rejects an oversized expansion.

Freeze a new run for the revised code/guidance; existing frozen runs retain
their own code identity and cannot silently resume with it. Other profiles,
schemas, strict scoring, memory/SUE defaults and ordinary execution deadlines
are unchanged. The separate 600-second diagnostic is not a CLI timeout mode.

The [evidence-selection verification](verification/memory-evidence-budget-2026-10-26.md)
records one accepted Qwen answer, both frozen answer requirements covered, and
remaining evidence/review-reason imperfections. It does not qualify the full
100-question study or establish general memory benefit.

