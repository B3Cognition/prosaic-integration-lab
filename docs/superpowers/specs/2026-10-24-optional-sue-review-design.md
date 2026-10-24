# Optional SUE review workflow

Date: 2026-10-24. Status: revised after independent design review; implementation pending.

## Intent and scope

Add a separately enabled advisory review workflow to the Prosaic integration
Lab. The first use is examining a proposed interpretation of requirements:
definitions, exceptions, conflicting readings, counterexamples and questions a
human must settle before planning. It can review supplied specifications or a
host-selected Castle snapshot. Ordinary memory retrieval never starts a review.

The maintainer approved adding SUE as another optional review workflow after
the existing guide, `cognitive-castle/docs/prosaic-sue.md`, described the ownership
boundaries. The implementation choices below make that direction concrete; they
are proposed engineering choices, not additional user requirements.

Deliver a trusted operator CLI and an embeddable host session API first. No
public HTTP grants, automatic chat interception, background reviewer, automatic
rewrites or mandatory merge/quality gate are added. Qualification is synthetic;
live usefulness, recall and false-positive rates remain unmeasured.

## Ownership

| Component | Owns |
| --- | --- |
| Castle | Existing pure SUE engine; authorized immutable memory snapshots when selected |
| Lab review consumer | Source admission, host identity, reviewed policy, deterministic projection, source-linked advisory reports |
| Runtime | Exactly one tool-free provider attempt per Harness attempt; original output and usage evidence |
| Harness | Accepted answer prefix, bounded attempts, checkpoints, leases, receipts and resume |
| Prosaic Core | Existing artifact/prose/configuration contracts; no new execution |

Do not execute `castle sue review`, Ollama, Codex or Claude subprocesses from
this workflow. Do not copy the vendored reducer or import `cognitive_castle._vendor`.
Reuse the documented public `cognitive_castle.brain_engine` functions
`initial_state`, `question`, `schema`, `advance` and `coverage` from an exact
qualified installed Castle wheel. SOAR and retrieval engines are outside review
execution. Existing standalone Castle SUE commands and stored runs are unchanged.

No SDK change is expected. Review verified the exact hashed public Runtime
0.9.8 and Harness 0.9.4 wheels: `RuntimeAdapter`, versioned `runtime_adapter`
WorkflowBindings and deterministic validators are available. A generic 32-step
graph with the revised dependency chain passes public factory admission. This
is contract/admission evidence, not completed SUE execution or platform proof.
See [review findings and probes](../../verification/sue-design-review-2026-10-24.md).

## Installation and defaults

Default configuration is `{"review":{"enabled":false},"memory":{"enabled":false}}`.
Omitting review is equivalent to disabled. Reject other review settings when
disabled. Disabled construction performs no Castle/SUE import, provider launch,
store initialization or model call. Enabling review does not enable memory;
enabling memory does not enable review. No SUE import is added to application
startup or the default memory path.

Use the already qualified worker wheel from r7, source
`58f4242080212c2bebcca0c685af0f5e1090aa94`, worker 3.4.2, SHA-256
`4c0d6723d6f305639c14c51ae0327dcdcd75547ad8e2be89180a833df33ff027`.
It is an unpublished candidate; installation instructions must say so. Preserve
the selected archives and publication_authorized=false. Runtime/Harness/Core
public pins and normal Lab dependencies do not change.

The initial optional environment installs the full Castle distribution and its
dependencies, even though importing the pure engine needs only the standard
library. This is an explicit packaging cost, not a claim of a lightweight new
engine package. Keep the review dependency profile independently hashed and
qualify its complete installation with pip check. Do not use --no-deps to hide
unsatisfied requirements. A lightweight upstream extraction is later work,
outside Castle #107–#109 and this milestone.

## Host API and frozen sources

`SueReviewSession(settings, store, config, principal, namespace, accounting=None)`
exposes `start(run_id, *, seed, sources, lens='euthyphro', max_turns=14)`,
`status(run_id)`, `resume(run_id, *, expected_revision, choice=None)` and
`report(run_id)`. `choice` is continue/reject only at the initial pause; no choice
is supplied for recovery of an already approved execution. Version 1 exposes no
missing-receipt retry flag. Identities come exclusively from
the trusted host Principal and namespace, never a source, model answer or request.

The initial CLI is `python -m lab_runner.sue_review`, with start/status/resume/
report actions and private host configuration. Initial CLI model endpoints are
synthetic loopback fixtures only, following the existing memory workflow CLI.
The host API accepts an explicitly supplied RuntimeConfig; a future live CLI
needs its own allowlist, input-fit qualification and shared allowance, rather
than silently inheriting existing historical live budgets or credentials.

Host-selected document sources have unique logical source IDs and UTF-8 text.
At CLI admission, read each explicitly supplied local file as bounded bytes;
reject symlinks, invalid UTF-8 and non-regular files. Do not permit the model to
choose file paths. Retain exact UTF-8 bytes through JSON text, including CRLF,
SHA-256, source ID and optional caller-owned revision/reference metadata. Do not
save the absolute local path in public reports. A changed source requires a new
run, not refreezing an existing run during resume.

For Castle input, the host passes a snapshot obtained under its existing
authorized memory binding, not an arbitrary client-provided snapshot JSON.
Add `MemoryProviders.capture_selected(principal, selections, *, maximum_bytes)`
for explicit selected IDs plus expected revision/text hashes. It delegates to
the existing authorized provider's snapshot operation and preserves its scope,
completed-revision and provenance checks. The returned host capture attaches
trusted principal, namespace and a binding/scope identity to the bundle. The
Castle SourceBundle itself contains no owner/namespace attestation: never infer
authorization from its digest or a client-supplied scope field. Unlike ordinary optional recall,
selected-source review fails closed on disabled/unavailable/empty evidence;
it never silently reviews a substitute or partial set. The document-only path
does not construct MemoryProviders. Resume needs neither a live provider nor
the original local files.

Freeze 1–16 nonempty sources, total at most 65,536 UTF-8 source bytes, plus a
nonempty seed of at most 2,048 UTF-8 bytes. Derive a stable global line table
using splitlines without line endings, with each line mapped to source ID and
one-based source-local line. Preserve original text separately; the presentation
line table does not redefine its hash. Digest the complete canonical frozen
source records: exact text bytes/hash, record/source IDs, caller revision and
reference, all Castle provenance fields and original bundle identity, together
with the trusted capture identity, line map, seed, lens, limits and engine
identity. A revision-, reference-, provenance- or scope-only change conflicts
with an existing run even when source text is identical. Reject duplicate IDs,
duplicate JSON keys, nonfinite values, booleans as counts, malformed hashes,
mixed ownership and inconsistent byte/hash/revision declarations before calls.

## Deterministic questions through public SDKs

Build an acyclic graph of up to fourteen answer/check pairs, preceded by one
review pause. Each answer after the first requires only its immediate predecessor;
older answers are transported as optional inputs. The predecessor's chained
receipt dependencies transitively bind the entire accepted history. Folding
and validation reconstruct the complete prefix by numbered step IDs, never JSON
member insertion order, and reject missing, extra or inconsistent entries;
optional transport is not permission to
omit evidence. Avoid all-prior required dependencies: Harness recursively nests
their bindings, exceeding the invocation cap by turn twelve even for tiny data.
Each answer step allows two validation attempts; RuntimeAdapter max_attempts=1,
provider requests per invocation=1 and tool calls=0. No adapter-level retries.

The versioned adapter reconstructs engine state from the frozen request and
the accepted response prefix. It obtains the exact current question/schema
from the engine, then calls its supplied Runtime `execute` once with those
values, numbered source lines, current state context and untrusted-data
instructions. It never asks the model to select the next operator, lens,
question, schema, tools, identity or budget.

Keep each within-limit original Runtime stdout byte-for-byte as `rawResponse` in a host
envelope, alongside a host-computed terminal and next-state SHA-256. Preserve
the Runtime Result's real exit status, metadata, usage and adapter attempt
evidence. A failed provider call must never become a successful host result.
RuntimeAdapter clears stdout on failure or incomplete usage; preserve any
available bounded raw output in private metadata before returning, alongside
the failed result. For oversized output retain its digest/length and a bounded
diagnostic, not an unlimited copy or a claim of complete preservation. An
otherwise successful but invalid within-limit answer remains an ordinary
envelope for Harness validation and its bounded retry policy.
Strictly decode the response; invalid JSON or a rejected SUE turn stays in the
saved attempt receipt and cannot enter accepted history. The envelope may carry
null derived fields for invalid output so Harness validation can reject it.

An independent Harness Validator reconstructs the same prior state and runs
`advance` itself; it validates the raw answer and compares all derived envelope
fields. Only accepted Harness outputs become the next answer's input. The
following gate branches on that validated terminal: continue to the next slot
or finish. At fourteen accepted turns the engine must produce its bounded stop
unless already terminal. Status and report fold accepted outputs only and may
not execute a model or retrieve new sources.

This keeps state in Harness without adding a parallel application dialogue
store, modifying a private SDK engine or relying on a model-generated state.
Reconstruction is deterministic, bounded and pinned to engine/policy/schema
identity. An engine mismatch blocks resume without consuming a call.

## Budgets, confirmation and recovery

Default proposal: one selected lens, 1–14 accepted turns, at most two validation
attempts per turn, 28 total provider calls, 65,536 reported tokens, a 900-second
wall-clock lifetime from run creation and 60 seconds per attempt. The deadline
includes the initial human pause, process downtime and resume. It is not active
execution accounting. An expired zero-call approval requires an explicitly
created new review; never reset or extend the saved deadline on resume.
Long-lived approval or active-time accounting would require a separate design.
Host policy may reduce these values,
never expand them via model arguments. Keep all nine existing lenses available:
euthyphro, meno, parmenides, cratylus, theaetetus, sophist, gorgias, republic and
philebus. Running all nine is nine separate explicitly approved reviews.

Bound the full frozen run input to 131,072 encoded bytes, raw response to
16,384 UTF-8 bytes, encoded invocation to 262,144 bytes,
receipt to 1,048,576 bytes and saved run state to 4,194,304 bytes. Bound JSON
depth/nodes using the public SDK policy and a strict host decoder. Reject an
oversized next prompt before dispatch; reaching a cap is a resource stop, never
successful substantive completion. Source byte/count ceilings do not guarantee
that every combination fits JSON/prompt/state limits or all fourteen turns;
check actual encoded sizes and the rendered prompt. Configure the explicit run
input cap rather than inheriting Harness's 65,536-byte default for the entire
request. The minimal full fourteen-turn case must fit all caps.
Reported-token caps do not establish a hard
monetary cost bound or resolve unknown usage. Before live use, independently
qualify native context fit and reserve a bounded shared allowance.

Start freezes sources and reaches a review pause with zero model calls. The
human explicitly continues the reviewed source/policy digest and finite call
allowance, or rejects with zero calls. Fresh-process resume reuses frozen bytes,
accepted results and original tenant/actor/payer attribution. Stale revisions,
foreign owners and changed request signatures fail without calls. Status and
report remain read-only even if review is subsequently disabled; that does not
grant permission to start or continue inference.

Keep the approved versioned workflow/configuration bindings available separately
from the enablement flag for saved-run inspection. Read-only actions reconstruct
the retained binding and use public Harness status/receipt validation; they never
rewrite a saved run to match current defaults. Missing retained bindings or engine
identity produce an explicit binding_unavailable result, not fabricated output or
permission to dispatch. The disabled constructor itself still loads no engine.

Reuse Harness recovery unchanged: saved receipts can be validated and adopted
without repeating that attempt; continuation may legitimately call subsequent
steps within the original approval and remaining limits. Status/report do not
drive recovery. An attempt that may have reached the provider but has no
recoverable receipt remains blocked. Under the mandatory token budget, an
abandoned unknown-usage attempt causes usage_unknown even with retry consent;
version 1 therefore exposes no such retry path and never disables that guard.
Separate usage evidence does not reconstruct a workflow receipt or grant retry
authority. Operator inspection and a separately authorized new review may be
needed, retaining the original uncertain attempt and reservation. A future retry
feature needs a supported reconciliation/budget contract. Do not promise exactly
once provider execution. Preserve rejected and uncertain attempts in accounting.

## Report semantics and compatibility

Export owner-only JSON and Markdown advisory reports with the reviewed claim,
terminal, examined/missing dimensions, attributed quotations and source-local
line references, inferred/assumed premises, counterexample witnesses, open
questions, attempted/accepted counts and usage completeness. Escape/render
source text as data. Never expose raw operator state, private host paths or
unfiltered accounting rows. Private receipts retain within-limit exact model
output; oversized output retains only its bounded diagnostic and hash/length.

RESOLVED means required dimensions of the current claim were examined. It does
not certify truth, implementation correctness, complete corpus coverage or
approval to publish. BOUNDED_STOP, aporia, interrupted, rejected and resource
stops stay distinguishable; no terminal authorizes automatic edits or effects.

Preserve Castle modes, SUE policy/schema semantics, memory defaults, raw FTS
ranking and dense/recency opt-ins. Preserve existing Lab acceptance assertions,
all historical evidence and nine unresolved live reservations. Leave Castle
#107–#109 heads and their selected release archives unchanged. New SUE work
uses a separate branch and later PR; no publish/merge/live call is included.

## Acceptance and usefulness

Qualify pure-engine behavior across all nine lenses for success, silence,
partial answers, revision, exhaustion, invalid quotations and wrong claim
versions. Compare the consumer's accepted states against the installed public
engine, retaining upstream differential tests as separate upstream evidence.
Add no tests that monkey-patch installed SDK engines.

Real-wire synthetic functional tests cover document-only and selected-Castle
inputs, Unicode/CRLF, initial zero-call pause, rejection, invalid-output retry,
bounded stop, early terminal, input caps, unknown usage, cancellation, concurrent
resume, stale revisions, cross-owner/payer denial and engine mismatch. Inject
process loss after model return, receipt persistence and state acceptance;
inspect fresh-process recovery and independent provider dispatch counters.

Use owned PostgreSQL 16/18 fixtures and both Linux architectures. Preserve the
full existing acceptance and enabled-memory lanes; add a separate SUE lane with
no skips and verified cleanup. Qualify installed wheel and rebuilt-sdist
consumers with pinned optional dependencies, immutable source identities and
hashes. Default-disabled absent-Castle checks run in the ordinary Lab profile.

Include a small frozen synthetic corpus of clear, ambiguous, contradictory and
insufficient specifications plus paired one-pass review controls. Record source
binding, supported/missed/unsupported findings, call/token counts and latency.
Scripted fixtures prove workflow/scoring mechanics, not SUE's benefit. A future
live comparison needs fresh held-out cases, explicit bounded authorization and
separate evidence before recommending SUE as a required quality gate.
