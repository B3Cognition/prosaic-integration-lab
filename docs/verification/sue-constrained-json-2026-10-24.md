# Constrained SUE JSON qualification — 2026-10-24

Constrained generation fixes the observed Qwen formatting failures in this pilot:
**16/16 SUE replies are schema-valid plain JSON**, compared with 0/16 in the
[previous corrected experiment](review-contract-fixes-2026-10-24.md). This does
not qualify SUE review quality. The unchanged semantic validator rejects 13 of
those replies; three workflows finish after one accepted turn with
`APORIA_UNDEFINED`. Their final reviews pass **0/8** strict benchmark checks.

Memory, SUE and constrained generation remain **disabled by default**. No public
dependency pin, original Castle source, Core, Harness, pure SUE engine, SOAR
path, model, prompt, answer key, scorer or execution limit was changed.

## Implementation and boundaries

Runtime's unpublished **`0.9.8+jsonschema.2`** candidate is based on released
`v0.9.8` / `a9433a68f60eeecf1946a398267f749c7ff89d8e`. Its public tool-free
`run(..., response_schema=schema)` and trusted `RuntimeAdapter.execute` delegate
encode OpenAI-compatible `response_format` with `type: json_schema`, the exact
owned schema and `strict: true`. Calls without the option retain their previous
wire format; existing endpoint `json_mode` still requests `json_object`.

Schemas must be object JSON Schemas, at most 65,536 UTF-8 bytes, depth64 and
32,768 JSON nodes, with local references only. Actual native schema bytes share
the existing input cap. Tools, acquisition and native Anthropic are unsupported
for this first interface and fail before HTTP. Conversation `turn()` does not
accept the option. A provider HTTP rejection never triggers an unconstrained
fallback. Runtime retains raw output and usage rather than repairing or
declaring it semantically valid. Results and adapter attempts retain schema
SHA-256 alongside existing request/argument/usage evidence.

An adapter inherits an outer caller's schema and cannot replace it. Independent
review found that Python equality aliases `true` and `1`; real-wire const/enum
regressions reproduced the bypass. Canonical JSON byte comparison fixes it.
Callback mutation, existing grants, attempt/token budgets and zero-request
boundaries remain checked. No other actionable review finding was reported.

Lab adds the explicit trusted host option
`SueReviewSession(..., constrained_json=True)`. It sends the pure engine's
current per-turn schema through Runtime. True is frozen into `reviewPolicy`
and adapter v1.3; false is omitted, preserving existing v1.2 policy and binding
identities. The legacy `ReviewSettings` dataclass and JSON/CLI format stay
unchanged. A first attempt to add a dataclass field failed an existing frozen
v1 policy assertion; it was replaced by the constructor option without editing
that assertion or the frozen v1 consumer.

Harness still owns accepted state and receipts. The pure engine still owns
questions, schema, grounding and transitions. Lab owns the opt-in, frozen
documents, owner/revision checks and evaluation. Strict raw JSON parsing,
canonical guidance, semantic validators and source/provenance checks are
unchanged. AST and byte comparisons are retained in `invariants.json`.

## Candidate artifacts

| Artifact | SHA-256 |
| --- | --- |
| Runtime `0.9.8+jsonschema.2` wheel | `0f5a6ab9ffbd150f3b0cbe5aae9e0491ea760ba38816f521f0312318361eb341` |
| Lab `0.6.0` wheel | `5e598d856c6fb5f42bd0541a5791e7ff2244dfa7188c022b3e60c2057009ba1c` |
| Unchanged standalone SUE `0.1.0` wheel | `7dfe0697de596e745b5934570d449238d28db380e5e800a96a606d01eed0bc4d` |
| Unchanged Castle adapter `0.1.0` wheel | `7131c12e9b1bc36cb302874d7c5dbbd349de42d74581f8b5ec9c2981aabbbc35` |

Direct and rebuilt-sdist wheels have identical bytes under fixed
`SOURCE_DATE_EPOCH=1792800000` and matching build file modes. Installed admission
verifies actual payload bytes before the study. Separate new environments keep
both prior installed candidates intact. No package publication is authorized.
Preliminary candidate1, packaging diagnostics and failed test runs are retained.

## Verification

| Check | Result |
| --- | --- |
| Full public-SDK Lab source scope, including frozen v1 and new legacy fail-closed tests | **2,132 passed**, zero skips; one existing Starlette warning |
| Focused Runtime schema/adapter/transport regressions | **82 passed** |
| Final full Runtime source suite | **1,459 passed**, one separately mandatory installed-package witness skipped in the source process; that installed gate passes below |
| Isolated installed Runtime schema regressions | **26 passed** |
| Explicit installed Runtime metadata gate | **1 passed**, zero skips |
| Clean committed Git-archive distribution and source-package contracts | **2 passed** |
| Existing installed Runtime smoke gates | Wheel ownership/CLI/no-Node, conversation/history/context assembly, and production journaling/recovery passed |
| Isolated installed Lab SUE/guidance/v2 comparison regressions | **36 passed** |
| SDK-only disabled/unavailable boundaries, no Castle or SUE installed | **105 passed** |
| Existing installed Castle/memory/SUE acceptance, public SDKs | **76/76** on PostgreSQL16 and **76/76** on PostgreSQL18; zero skips, exact inventory and cleanup |
| New installed constrained SUE acceptance, candidate SDK | **6/6** on each PostgreSQL16/18; both stores, frozen resume/owner checks, strict missing-field/false-quote rejection, exact inventory, usage and cleanup |
| New constrained comparison fixture | **24/24**, 88 scripted requests /1,320 tokens, 56 exact constrained SUE requests, zero live calls |
| Network-denied fixture/live replay and live wire audit | Zero additional calls; all **43** physical calls joined to Runtime evidence and Harness receipts |

Full Runtime source verification delegates its installed-package witness to a
separate mandatory gate. The gate was run explicitly, along with wheel smoke;
it is not an untested optional skip. Version-specific expectations retain exact
equality and explicitly identify the local candidate. Initial version-witness
and setup failures remain in the archive rather than being erased.

Runtime implementation commit is `f6f0c76`. Clean Git-archive distribution
checks are rerun against that committed candidate with exact local-version
expectations. Refreshed source archives include those expectations; their
Runtime wheel bytes remain identical to the frozen benchmark wheel.

Consumers are **macOS ARM64**; owned databases are **Linux ARM64**, PostgreSQL
16.15 and18.6, with separate migration/runtime roles. Native Linux AMD64/ARM64
consumer qualification and remote CI were not performed here.

A broad preliminary Runtime candidate1 Lab run produced **2,064 passes and
43 failures**. Existing closed quality/retrieval SDK qualification profiles
reject that unpublished version: 35 direct `unqualified SDK versions`, one
frozen public-SDK closure failure, and seven downstream CLI preflight failures.
They are preserved with full node names in `preliminary-candidate-failures.json`.
Those gates and historical memory/review freezes remain unchanged. General
Lab SDK adoption is therefore **not qualified** by this experiment. The explicit
candidate SUE study admits exact wheel bytes separately; the normal public SDK
train remains green. No guard was weakened to make an unpublished candidate
look like an approved public release.

## Same live Qwen comparison

The study uses the same eight requirements cases, three strategies, rotating
24-cell order, source hashes, canonical guidance, public issue definitions,
hidden host keys and strict scorer. Model remains
**`mlx-community--Qwen2.5-Coder-7B-Instruct-4bit`** on authenticated numeric-loopback
oMLX, temperature0.2, maximum4,096 output tokens and explicit thinking-disabled
request settings. Only SUE attempts request schema generation. Direct, critic
and final synthesis receive no response-format override. All eight actual
direct prompts match the prior run byte for byte. Runtime's declared local
version is the only SDK version change.

The user's Qwen/unlimited-token authorization is retained. Operator bounds stay
unchanged: 24 cells, at most720 aggregate requests and1,572,864 reported tokens;
per cell30requests/65,536tokens/120seconds. SUE retains14turns/28calls,
60seconds per invocation and two attempts per step. No post-observation prompt
tuning, semantic schema rewriting, output repair, extra retry or limit increase
was performed. Shared server settings, credentials and caches were not changed.

| Strategy | Completed | Strict passes | Requests | Reported tokens | Median elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 8/8 | 4/8 | 8 | 8,434 | 4.05s |
| Critic-author | 8/8 | 3/8 | 16 | 14,923 | 6.89s |
| Constrained SUE + final synthesis | 3/8 | 0/8 | 19 | 26,110 | 18.95s |

All **43 requests /49,467 reported tokens** reconcile. All24 cells ran, with
zero tools, new unknown reservations, pending samples or overruns. Offline
grading/replay and independent joins run with networking denied. The owned
gateway closes after the run; the shared Qwen server remains available.

All16 SUE replies are plain, strict raw JSON matching the exact canonical turn
schema. No required field is missing and none uses Markdown fences. All16
schema requests have no provider enforcement warning. Bundled oMLX0.7.2 source
inspection shows that unavailable grammar enforcement is exposed through a
Warning header; source file hashes and observed headers are retained. This is
endpoint evidence for this pilot, not a universal guarantee of logit enforcement
or provider correctness. Client-side validation remains mandatory.

All16 replies choose `UNKNOWN` with `SILENT`. Thirteen nevertheless cite answer
evidence, violating the unchanged requirement that `SILENT` has empty evidence.
All13 are rejected; no citations are discarded to make them pass. Three retries
produce acceptable empty-evidence responses and stop at **one DEFINE turn** with
`APORIA_UNDEFINED`. They demonstrate no sustained multi-turn examination and
none of their final reviews passes the strict issue/assessment checks. Five
SUE cells produce no final review at all. Mixed successful/aborted SUE timing
is not successful-review latency.

Before constraints, direct passed5/8 and critic2/8; now they pass4/8 and3/8
despite unchanged prompts/settings. A single trial per short synthetic case,
warm shared server, unreset prefix caches and different workflow completions
cannot establish general review benefit or speed improvement. SUE remains
unqualified for promotion. A later experiment could improve coherent semantic
responses or compare a stronger model under the same validators; it must use
fresh evidence and must not silently extend this run. Qwen27B's earlier timeout
failure and two charged unknown reservations remain untouched.

## Recovery and preserved evidence

Copied failed v1.2 stores remain inspectable and idempotent under both the old
and new candidates with networking denied. The new host option cannot silently
upgrade their saved mode: attempting to start the same run with constraints
raises `review_request_conflict`. Existing saved policy controls resume.
Original failed-store hashes are unchanged. Older v1.1 bindings still require
their matching retained candidate as previously documented.

Fresh logs, all RED/GREEN/setup/version/profile failures, exact candidate wheels,
source archives, PostgreSQL receipts, model responses without authorization
headers, frozen plan/operator/allowance, saved Harness stores, replay/audits,
classifications and source-invariant proofs are preserved separately in
`reports/castle-sue-constrained-json-20261024/` with a SHA-256 manifest.

All five prior archives remain immutable: `prosaic-castle-fork-20261024`,
`prosaic-castle-retest-20261024T170359Z`, `castle-sue-qwen-pilot-20261024`,
`castle-sue-contract-fixes-20261024` and `castle-sue-contract-fixes-ci-20261024`.
Their manifests and every retained file are checked before sealing the new
archive. No failed model response, allowance or reservation is overwritten.

The [operator guide](../sue-review.md#experimental-constrained-json-generation)
documents the explicit host opt-in and current limits. Changes remain local:
no push, merge, release, general SDK profile adoption or default enablement.
