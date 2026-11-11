# Optional SUE review

SUE reviews a proposed interpretation of explicitly selected requirements. It
asks about definitions, distinctions, criteria, consequences and counterexamples,
then returns an advisory report with attributed quotations and open questions.
It is a structured self-check by the answering model. It does not independently
verify truth, implementation correctness or permission to act.

**Review is disabled by default and is independent of memory.** Omitting the
review configuration means disabled; `{"review":{"enabled":false}}` explicitly
disables it. Other review settings are rejected while disabled. Installing the
engine does not enable review, record chats, retrieve sources or start a model.
The disabled session constructor loads no SUE engine or SDK execution machinery.

An experimental requirements-review profile also supports an explicit
`SueReviewSession(..., cycle_guard=True)` and a start-time `review_context`
mapping with `purpose`, `issueDefinitions` and `instructions`. The trusted host
supplies these bounded criteria; they are signed and frozen with the source
snapshot and reused on resume. They cannot provide identity, tools or new source
evidence. The default session retains its existing examination policy.

The opt-in guard stops exact repeated examination cycles without gaining
coverage or resolving an earlier issue. Its result is `BOUNDED_STOP`, with
reason `repeated_cycle_no_progress`; missing dimensions remain missing. It does
not make repetitive or unsupported answers valid. The raw turn evidence stays
available. New comparison workflow v3 deduplicates only the model-facing final
handoff and checks final assessment/issue consistency with bounded retries.
Older comparison versions, canonical guidance and the strict scorer remain
available unchanged. These features do not establish semantic entailment or
make an advisory terminal a quality certificate.
The new engine candidate has a distinct content identity. Resume older reviews
with their original pinned engine; a different installation must fail binding
checks. Start a fresh review ID to opt into the new profile.

**Live review quality remains unqualified.** The latest
[review-fix comparison](verification/sue-review-fixes-2026-10-25.md) measures all
24 cells: direct passes 4/8, critic/author 5/8 and SUE 3/8. SUE uses 43% fewer
tokens than the preceding run but loses one strict pass. Case 4 uses only 3,480
tokens and still misses the failure-behavior issue. Strict validators retain
all rejected outcomes and usage. Keep the new profile disabled for routine use.

The preceding separate
[360-second Qwen comparison](verification/sue-qwen360-2026-10-25.md) completed
all24workflows: SUE passes4/8strict reviews, direct3/8, critic2/8. SUE uses about
11.7times direct tokens; the14-turn case still fails the scorer. This one small
trial does not establish general benefit. The earlier
[120-second v1.5 study](verification/sue-grounding-schema-2026-10-24.md) remains
safety-stopped at12/24cells with its unknown reservation fully retained. Both
studies keep strict validation and disabled defaults; the360-second limit is
an explicit experiment setting. The preceding
[constrained Qwen comparison](verification/sue-constrained-json-2026-10-24.md)
and Qwen27B invocation-limit failure remain preserved. Keep review disabled for normal work. The
[earlier failed comparison](verification/review-contract-fixes-2026-10-24.md)
and matching candidate wheels remain available for inspection. New generation
settings cannot silently upgrade saved runs or reinterpret old sealed bindings.

## Get the optional engine

Use the Lab's normal [public SDK setup](../README.md#install-packages-for-an-embedding-service)
in a separate Python 3.12 environment, called `.venv-sue` in the examples below.
Keep the current public SDK pins; there is no required Runtime, Harness or Core
release for this workflow. The additional engine is **an unpublished candidate**:
obtain its exact wheel from the maintainer rather than substituting a package
with the same version from another source.

[`dependencies/sue-review-source.json`](../dependencies/sue-review-source.json)
pins `cognitive-castle-sue` 0.1.0, importing as `castle_sue`. The MIT package has
no third-party runtime dependencies. It maps Castle's canonical engine and
pinned Echelon policy bytes into a separate namespace; it does not install
Castle's retrieval stack, embedding models, spaCy, Torch or SOAR.

| Candidate | SHA-256 |
| --- | --- |
| `cognitive_castle_sue-0.1.0-py3-none-any.whl` | `fdfb1690505a85b4cbb49e2b4845c91e318efe945068a379ac230c3b4ebf9b75` |
| `cognitive_castle_sue-0.1.0.tar.gz` | `8846789e9c8534a33dd73807bf6e34543b64b24c1ace26ead05d503515a5cf8a` |

The package source is Castle commit
`53637196cc215e9bd5b85b9253b3430b2781b884`; its unchanged canonical engine
origin is `58f4242080212c2bebcca0c685af0f5e1090aa94`. Direct and rebuilt-sdist
wheels have identical bytes. This optional profile preserves the existing r7
memory profile and selected archives; it changes no normal Lab dependency pin.
It is separate from Castle #107–#109 and does not authorize publication.

Verify the candidate before installing it into your prepared environment:

```sh
export SUE_WHEEL=/absolute/path/to/cognitive_castle_sue-0.1.0-py3-none-any.whl
.venv-sue/bin/python - <<'PY'
import hashlib, json, os
from pathlib import Path
profile = json.loads(Path('dependencies/sue-review-source.json').read_text())
expected = next(item for item in profile['artifacts'] if item['kind'] == 'wheel')
wheel = Path(os.environ['SUE_WHEEL'])
assert wheel.name == expected['filename']
assert len(wheel.read_bytes()) == expected['size_bytes']
assert hashlib.sha256(wheel.read_bytes()).hexdigest() == expected['sha256']
print('Optional SUE wheel identity verified.')
PY
.venv-sue/bin/python -m pip install "$SUE_WHEEL"
.venv-sue/bin/python -m pip check
```

`castle_sue.capabilities()` reports API 1, schema 2 and policy `2026-09-24`.
Its engine identity is
`bbde4669d1eb069dcb8c72e121cd08be4ca953b349f9243b9e650e0d1b596f0b`.
That identity binds the canonical resources, their manifest, the wrapper and
the private loader. The separate canonical manifest digest is
`7b14272b3720261d71a472aadaa8b6a23fa8ec0e07f07c7a4c23aa75a887b892`.
An engine change blocks a saved review rather than silently resuming under
different execution code or policy.

## Try the credential-free walkthrough

Run from this checkout's root with the prepared environment. Without opt-in,
the demonstration prints `enabled: false` and `executed: false`; it imports no
SUE engine, starts no server and writes nothing:

```sh
PYTHONPATH=src .venv-sue/bin/python -m examples.sue_review_demo
```

For the explicit synthetic walkthrough, choose a new directory. This creates
private fixture files and a file-backed run store, starts an owned loopback
server, freezes a small requirements document and verifies that start pauses
with zero provider calls. `--enable` also authorizes this demonstration to
continue its own synthetic review after that check:

```sh
mkdir -p .lab
PYTHONPATH=src .venv-sue/bin/python -m examples.sue_review_demo \
  --enable --directory "$PWD/.lab/sue-demo"
```

The fixture supplies scripted JSON answers; it is not an LLM. The demonstration
deletes its original document before resume, then disables review and writes
`advisory.md` from the retained run without another call. Its JSON summary
records calls, accepted turns, reported tokens and the report path. The fixture
server is closed before exit. Use another new directory for another run; retain
private evidence rather than overwriting an uncertain run.

This proves workflow mechanics on synthetic data. It does not demonstrate SUE's
benefit, a live model's compliance or a deployment's readiness.

## Review your selected documents

The trusted operator CLI is `python -m lab_runner.sue_review`. It intentionally
accepts only a synthetic HTTP loopback endpoint and model `sue-fixture` in this
version. It rejects remote endpoints and credentials. The walkthrough above
owns the fixture server; the following commands assume an equivalent fixture
is already running.

Copy [`configs/sue-review.example.json`](../configs/sue-review.example.json)
to a private, operator-owned mode-600 file. Choose a private store path and
trusted namespace/principal, set the actual fixture port, then explicitly set
`"review":{"enabled":true}`. Tenant, actor, billing account and namespace
come from this trusted host configuration. A document or model answer cannot
choose or override them.

Create a request containing only the documents you intend to review:

```json
{
  "seed": "Administrators export only with current consent.",
  "sources": [
    {"sourceId": "requirements", "path": "/absolute/requirements.md", "revision": "r1"}
  ],
  "lens": "euthyphro",
  "max_turns": 14
}
```

Paths must be explicit absolute paths to regular UTF-8 files. Symlinks, duplicate
source IDs, malformed input and oversized sources are rejected. Exact text,
including CRLF, its hash, revision/reference and source-local line mapping are
frozen at start. Later status, resume and report do not reopen those files or
retrieve fresh material. Changed source bytes or metadata require a new review.
Absolute document paths are not included in owner-facing reports.

```sh
PYTHONPATH=src .venv-sue/bin/python -m lab_runner.sue_review start \
  --config /private/sue-host.json --request /private/sue-request.json
PYTHONPATH=src .venv-sue/bin/python -m lab_runner.sue_review status \
  --config /private/sue-host.json --run-id RUN_ID
PYTHONPATH=src .venv-sue/bin/python -m lab_runner.sue_review resume \
  --config /private/sue-host.json --run-id RUN_ID \
  --expected-revision REVIEWED_REVISION --choice continue
PYTHONPATH=src .venv-sue/bin/python -m lab_runner.sue_review report \
  --config /private/sue-host.json --run-id RUN_ID --format markdown
```

Use the returned run ID and current revision. Inspect the frozen source digest,
policy and finite allowance before continuing; `--choice reject` ends the
initial pause with zero calls. Only the owning tenant/actor/payer and namespace
can inspect or resume the run. A stale revision cannot authorize continuation.
Recovery of an already approved run omits `--choice`; it retains the same
sources, attribution, policy, accepted history and deadline.

The JSON `proposal` in status/start/report contains the saved request signature,
seed, lens, turn limit, engine identity, source hashes and policy. Inspect that
saved proposal rather than assuming a later host configuration changed the run.

## Limits and recovery

| Boundary | Default and host maximum |
| --- | --- |
| Run lifetime | 24 hours (86,400 seconds); configurable up to 7 days (604,800 seconds) |
| Accepted turns | 14; a host may select 1–14 |
| Attempts | At most two validation attempts per turn, 28 total provider calls |
| Reported tokens | 65,536 per run |
| Attempt timeout | At most 60 seconds |
| Sources | 1–16 nonempty sources; 65,536 total UTF-8 bytes |
| Seed | 2,048 UTF-8 bytes |

Lifetime is wall-clock time from creation, including the approval pause, process
downtime and resume. It is not active execution time. Resume never resets or
extends the saved deadline. An expired zero-call proposal needs a deliberately
created new review. Host policy can lower call, token, turn and timeout limits;
model arguments cannot expand them. The reported-token cap does not establish
a monetary bound or make unknown usage known. Serialized prompt/state limits
can stop a run before the turn limit even when source admission succeeded.
JSON escaping also counts toward serialized output and event caps. If Runtime
returns output too large to retain safely, the Lab retains its byte length and
hash. If Runtime stops earlier at its event boundary, the receipt records that
failure and available usage; the Lab cannot recover text Runtime did not return.

Each Harness attempt permits one tool-free Runtime provider request. A model
does not select the next operator or terminal: the pure engine supplies the
question/schema, and an independent Harness validator recomputes transitions.
Only accepted answers become the next turn's history. Invalid answers retain
their attempt evidence and consume the bounded validation allowance.

A recoverable saved receipt can be validated and adopted without repeating its
attempt. An interrupted attempt that may have dispatched but lacks a recoverable
receipt remains uncertain; there is no automatic retry or missing-receipt retry
switch. Unknown usage remains stopped under the token budget, even with retry
consent. Inspect the retained evidence and preserve its reservation; a separate
new review requires its own authorization. Do not infer exactly-once provider
execution from a resume operation.

Set review back to `{"enabled":false}` to prohibit new starts and continuation.
Owner-scoped status and report remain read-only and make no provider calls.
They still need the retained store, versioned workflow binding and matching
engine; a missing or changed binding reports `binding_unavailable`. Disabling
review does not rewrite a saved run or erase its evidence.

## Host integration, memory and SOAR

### Experimental constrained JSON generation

The unpublished Runtime `0.9.8+jsonschema.2` candidate can request a bounded
generation JSON Schema for each SUE turn, with canonical validation remaining
independent. Normal public SDK pins and the CLI
settings format remain unchanged. Use a separate environment with the
checksum-verified Runtime and Lab candidate wheels from the
[current grounding qualification](verification/sue-grounding-schema-2026-10-24.md).
The public Runtime 0.9.8 fails closed if this option is requested.

The trusted embedding host opts in explicitly:

```python
review = SueReviewSession(
    settings={"enabled": True},
    store=store,
    config=runtime_config,
    principal=trusted_principal,
    namespace=trusted_namespace,
    constrained_json=True,
)
```

Omitting `constrained_json` keeps it off. It is a host API argument, not a
field accepted by the existing review JSON/fixture CLI. Enabling it does not
enable memory. SUE still pauses before the first model call. Its saved proposal
shows `policy.constrained_json: true`; inspect and approve that frozen proposal
before continuing. Later configuration changes cannot upgrade an older review:
resume reconstructs the saved policy and binding. Choose a new review to change
generation mode.

The current v1.5 adapter keeps the exact current engine schema in the prompt
and sends a separate generation-only schema through Runtime's
`response_format` (`type: json_schema`, `strict: true`). Its alternatives express
canonical result/verdict pairs, empty SILENT evidence, premise kinds, required
claim/witness/revision fields, operator answer types and trusted citation/turn
bounds. All canonical-valid branches remain available; the model must choose
from source support. This candidate supports tool-free
OpenAI-compatible calls. Missing capability or unsupported provider fails
before model dispatch, and HTTP rejection never triggers a request without the
schema. Check actual provider enforcement when qualifying a deployment: some
servers downgrade structured-output requests to prompting.

Schema-constrained generation addresses formatting and representable field
relationships. It
does not establish truthful evidence, correct interpretations or useful review
quality. SUE's raw JSON parser, exact quotation checks, semantic transition
validator, provenance, owner/revision checks and finite budgets remain required.
Invalid responses remain rejected and retain their receipts. Both memory and
SUE remain disabled by default.

The [grounding qualification](verification/sue-grounding-schema-2026-10-24.md)
separates generation success from review quality. Earlier v1.3/v1.4 constrained
runs retain their original candidate wheels and evidence. Inspect those runs
with their original binding; the new candidate rejects a binding mismatch and
does not silently migrate or redispatch an old review. Start a separately
authorized new run to try the new generation policy. Normal unconstrained v1.2
runs retain their existing binding and behavior.

The programmatic `SueReviewSession` API exposes `start`, `status`,
revision-checked `resume` and `report`. A host supplies a public Runtime config,
store, trusted Principal, namespace and optional recorder. It may select its own
approved local or external deployment through that Runtime config; the synthetic
CLI restriction is intentional. That flexibility is not live certification:
qualify provider context fit, credentials, usage completeness and a bounded
shared allowance before live use. No historical live allowance is inherited.

Document-only review needs no Castle provider. For selected Castle evidence,
trusted host code first calls `MemoryProviders.capture_selected` with exact
record IDs, expected text hashes and revisions under its existing authorized
binding. It freezes the complete capture with its trusted principal, namespace,
binding/scope and original provenance. The host API accepts that frozen input;
the CLI does not accept Castle captures or client-supplied snapshot JSON. Missing,
changed, disabled or unavailable selected evidence fails closed. There is no
automatic recall, fallback source set, palace scan or background review.

SUE examines a selected interpretation; Castle memory retrieves selected stored
words; SOAR is a separate symbolic reasoning facility. This workflow invokes
neither SOAR nor Castle's standalone provider-running SUE commands. Enabling
review does not enable memory, and enabling memory does not start a review.
The nine lenses are euthyphro, meno, parmenides, cratylus, theaetetus, sophist,
gorgias, republic and philebus. One run selects one lens; running all nine means
nine separately authorized reviews.

JSON and Markdown reports retain the reviewed claim, examined/missing dimensions,
attributed quotations, inferred/assumed premises, witnesses, open questions,
attempt counts and usage completeness. `RESOLVED` means required dimensions of
the current claim were examined. Aporia, bounded, interrupted, rejected and
resource stops remain distinguishable. No terminal certifies truth, correctness,
complete historical coverage, release approval or permission for automatic edits.
The [design](superpowers/specs/2026-10-24-optional-sue-review-design.md) and
[implementation plan](superpowers/plans/2026-10-24-optional-sue-review.md) track
the broader integration and qualification work separately from this guide.

## Test profiles

The normal `python -m pytest -q` suite keeps disabled and absent-engine coverage
and needs no optional engine. After installing the pinned SUE candidate, the
explicit enabled profile is mandatory for SUE changes:

```sh
PYTHONPATH=src .venv-sue/bin/python -m pytest -q \
  tests/unit tests/functional tests/sue_review tests/requirements_review
```

The separate SUE CI workflow also qualifies direct/rebuilt installed wheels with
owned PostgreSQL 16 and 18 on Linux AMD64 and ARM64. Its configuration is not
evidence that those CI cells have run; the new Castle package source must first
be made available through an authorized push. Local verification is recorded in
the dated verification note.
