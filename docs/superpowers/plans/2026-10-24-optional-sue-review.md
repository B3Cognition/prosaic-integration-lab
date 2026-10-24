# Optional SUE review implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an independently disabled advisory SUE workflow with exact frozen
sources, bounded tool-free inference, Harness recovery and source-linked reports.

**Architecture:** The Lab composes the installed public Castle pure engine with
RuntimeAdapter and an acyclic Harness graph. Runtime executes one answer per
attempt; a separate Harness validator recomputes each proposed transition.
Accepted Harness outputs are the only durable dialogue history. Neither Core
nor Runtime/Harness/Castle SDK source needs a change.

**Tech Stack:** Python 3.12; public Core 0.4.1, Runtime 0.9.8, Harness 0.9.4 and
their current PostgreSQL adapters; exact Castle 3.4.2 candidate wheel; existing
FileRunStore/PostgresRunStore and Runtime recorder; synthetic loopback inference.

**Spec:** [Optional SUE review design](../specs/2026-10-24-optional-sue-review-design.md).
That document records the approved direction and proposed implementation calls.
Fresh builder check: no important unanswered questions.

## Global constraints

- Both review and memory are disabled by default and independently enabled.
- No SUE, SOAR or model call enters memory retrieval; no legacy mode changes.
- Use installed public APIs, exact hashed wheels and no copied engine/private imports.
- Preserve Castle #107–#109 heads, r7 selected bytes, existing assertions and evidence.
- Synthetic loopback qualification only; no live inference, merge or publication.
- One selected lens; default euthyphro; 1–14 accepted turns; two attempts per turn.
- RuntimeAdapter max_attempts=1; provider requests per invocation=1; tool calls=0.
- Maximum 28 calls, 65,536 reported tokens, 900 active seconds, 60 seconds per attempt.
- Source count 1–16, total source bytes ≤65,536, seed bytes ≤2,048.
- Response bytes ≤16,384; invocation bytes ≤262,144; receipt bytes ≤1,048,576;
  state bytes ≤4,194,304. Resource/uncertainty stops never imply completion.
- Source/policy/engine/identity bindings are frozen across resume. No automatic retry
  of a possibly dispatched call without a recoverable receipt or explicit consent.

## Review focus

- Duplicate JSON keys, booleans as integers and Unicode/CRLF must not change bindings.
- Caller mutation and source/provider disappearance must not alter a saved review.
- Receipt adoption must not repeat inference; missing receipts must retain uncertainty.
- A plausible model-produced terminal/state must never bypass engine validation.
- Enabling review must not broaden memory scope or load optional engines by default.

## File structure

New files under `src/prosaic_integration_lab/sue_review/`:

- `contracts.py`: closed settings, limits, bounded strict JSON and stable digests.
- `sources.py`: exact document admission, Castle snapshot conversion and line mapping.
- `engine.py`: lazy public engine loading and exact installed identity verification.
- `workflow.py`: deterministic projection/validation and fixed Harness graph.
- `session.py`: owner-bound start/status/resume/report host API.
- `reporting.py`: explicit terminal semantics and escaped source-linked JSON/Markdown.
- `__init__.py`: small lazy public surface, no optional import side effects.

New `lab_runner/sue_review.py` provides the trusted synthetic operator CLI.
`configs/sue-review.example.json`, `examples/sue_review_demo.py` and
`docs/sue-review.md` teach installation, first use, limits and recovery.

Modify `src/prosaic_integration_lab/memory_provider.py` only to add explicit
selected-source capture; keep existing capture behavior and memory defaults.
Add an independent SUE source/dependency profile and qualification runner/CI
workflow following the existing Castle native qualification patterns. Normal
dependency pins and the selected memory release profile remain unchanged.

## Task 1: Frozen input and engine admission

**Files:** New contracts/sources/engine modules; selected-source capture method;
new `tests/unit/test_sue_review_sources.py`, `test_sue_review_engine.py` and
`test_sue_review_settings.py`; extend `test_memory_provider.py` additively.

**Interfaces:**

- `ReviewError(ValueError)` exposes a bounded `code`, never raw source/path data.
- `ReviewSettings.from_mapping(value)` returns immutable validated host settings;
  missing settings mean disabled. Settings include limits and exact engine identity.
- `freeze_documents(sources: list[dict]) -> dict`: each input has sourceId/text,
  optional revision/reference; output owns text, byte hash and global line mappings.
- `freeze_castle_snapshot(snapshot: dict, *, expected_scope: dict) -> dict`: internal
  conversion after trusted capture, preserving exact record IDs/revisions/text hashes.
- `MemoryProviders.capture_selected(principal, selections, *, maximum_bytes=65536)`:
  selections have record_id/text_sha256/revision. Return complete authorized snapshot
  or explicit unavailable/forbidden error; never partially selected evidence.
- `load_engine(expected_identity: dict)`: lazy adapter exposing the five documented
  pure functions and verified installed policy identity; no vendor imports in Lab.

- [ ] Write failing tests for disabled no-import/no-call behavior, malformed settings,
  all limits and invalid counts/JSON, source hashes/CRLF/Unicode/line mappings,
  mutated input aliasing, duplicate IDs, mixed scope and missing selected sources.
- [ ] Run the new tests and record the missing implementation failures.
- [ ] Verify public RuntimeAdapter and Harness binding availability in the exact
  installed SDK profile. Verify Castle wheel SHA and package RECORD/source identities.
  Stop for a concrete upstream contract defect rather than using a private fallback.
- [ ] Implement the listed interfaces. Keep local path reading in the CLI; freeze
  functions consume bounded owned values. Reuse current worker snapshot checks.
- [ ] With the installed Castle engine, parameterize all nine lenses over success,
  silence, partial, revision, exhaustion, invalid quotations and claim versions.
  Assert rejected turns leave prior state unchanged and pure calls perform no I/O,
  provider launch, SOAR or neural imports. Run upstream differential tests separately.
- [ ] Run focused tests plus all existing memory-provider unit tests, retain logs,
  inspect the diff and commit only this task's files.

## Task 2: One attempt per Runtime call, accepted state in Harness

**Files:** New workflow module; `tests/unit/test_sue_review_workflow.py` and
`tests/functional/test_sue_review_execution.py`.

**Interfaces:**

- `build_review_workflow(*, config, settings, engine) -> Workflow` builds the fixed
  initial pause, numbered answer/check pairs and terminal finish/rejection paths.
- `fold_accepted(request: dict, artifacts: dict, *, before_step: str, engine) -> dict`
  replays only the contiguous required accepted prefix against frozen lines.
- `project_answer(artifact, arguments, *, execute, **options) -> Result` prepares
  one engine question/schema and calls supplied execute exactly once.
- `validate_answer(output: dict, context) -> list[str]` independently recomputes
  the next state; only closed bounded error codes enter Harness feedback.
- Host envelope: rawResponse (exact stdout), terminal (engine enum or null),
  stateSha256 (canonical next-state digest or null). Model generates only the
  underlying SUE answer; the trusted adapter constructs the envelope.

- [ ] Write failing loopback functional tests: initial review pause/rejection makes
  zero calls; valid path reaches the engine terminal; every prompt contains the
  exact host question/schema and frozen sources; tools are absent and request
  counters equal attempted answers. Use known scripted replies for every lens.
- [ ] Add failures for invalid JSON, duplicate keys, out-of-range/false quotations,
  forged terminal/state digest, wrong previous claim, missing/foreign prefix,
  output/input caps and unknown usage. Assert rejected output never enters the
  accepted prefix; retries consume their own real Runtime/accounting attempts.
- [ ] Run the new tests and record failures before implementation.
- [ ] Implement pure folding and versioned RuntimeAdapter(max_attempts=1). Preserve
  original Result failure, raw output and evidence. Pass engine question/schema
  as prompt data, not a dynamically executed schema/callback selected by the model.
- [ ] Register an independent validator and build up to fourteen static agent/gate
  pairs, with required dependencies on every previous accepted answer. Gate only
  on validated host terminal. Seal engine, policy, artifact and adapter versions.
- [ ] Test early terminal and fourteen-turn bounded stop, max attempts/calls/tokens,
  source injection, cancellation and prompt expansion at its exact boundary.
- [ ] Run focused and existing runtime-adapter consumer regressions, retain actual
  dispatch/usage evidence, review and commit this independently testable workflow.

## Task 3: Owner-bound session, reports and fresh-process recovery

**Files:** New session/reporting/public modules and CLI, disabled example/demo;
`tests/unit/test_sue_review_session.py`, `test_sue_review_reporting.py`,
`tests/functional/test_sue_review_cli.py`, `test_sue_review_recovery.py`.

**Interfaces:**

- `SueReviewSession(settings, store, config, principal, namespace, accounting=None)`
  implements the exact start/status/resume/report signatures in the design.
- Freeze attribution as application `integration-lab-sue-review`, project namespace,
  original tenant/actor/billing account and run/request IDs via ExecutionContext.
- `render_review(request, accepted_state, attempt_summary) -> dict` returns advisory
  report data; `render_markdown(report: dict) -> str` escapes source content.
- CLI actions start/status/resume/report use --config and --run-id; start takes
  --request, resume takes --expected-revision/--choice and explicit interrupted
  retry consent. Report supports JSON or Markdown, never drives a workflow.

- [ ] Write failing tests for identical start idempotency, changed seed/source/lens
  conflicts, current/stale revisions, owner/tenant/payer denial, independent review
  and memory flags, and disabled status/report without inference permission.
- [ ] Write real-process fault tests at model return before receipt save, after
  receipt save before acceptance, and after acceptance. Use SDK/public store
  wrappers or fixture boundaries; do not patch installed engines. Assert saved
  receipt recovery causes zero redispatch and missing receipt blocks until explicit
  consent; preserve original attempts and unknown usage across retries.
- [ ] Run tests to observe failures; implement the host API with existing public
  Harness stores and recovery. Do not add a second dialogue state machine or store.
- [ ] Implement strict private-file CLI configuration, bounded regular-file UTF-8
  loading and loopback-only model binding. Do not read live credential defaults.
- [ ] Implement source-local citations, explicit inferred/assumed premises, missing
  dimensions and separate RESOLVED/aporia/BOUNDED_STOP/interrupted/rejected states.
  Test Markdown escaping, report ownership and no host path/raw operator disclosure.
- [ ] Run the demo, subprocess resume after original files/provider change, and
  network-denied status/report/recovery. Retain receipt hashes and request counts.
- [ ] Run focused and full existing Lab unit/functional tests; record results and
  commit only the reviewed workflow/session changes.

## Task 4: Installed distributions, PostgreSQL/platform lanes and user guide

**Files:** New `scripts/qualify_sue_review.py`,
`.github/workflows/optional-sue-review.yml`, `lab_runner/sue_review_acceptance.py`,
`tests/acceptance/test_sue_review.py`, independent candidate profile under
dependencies, `docs/sue-review.md`, new dated verification records; additive
README/handoff links. Extend MANIFEST.in only for new demo/config assets.

**Interfaces:**

- Qualification emits source/dependency/artifact hashes, architecture/PG version,
  every case result, independent dispatch counts and verified owned cleanup.
- Test runner owns exact labeled resources, separates migration/runtime roles,
  constructs stores inside processes and fails missing required infrastructure.
- A separate immutable optional profile installs the exact Castle worker plus
  current public SDKs, never editable siblings. Keep normal Lab dependency pins
  and all r7 selected release archives unchanged. New Lab build bytes are separate
  qualification artifacts, not replacements for r7 publication candidates.

- [ ] Add failing installed-wheel/rebuilt-sdist tests for packaged review modules,
  source identities, default-disabled absent-Castle behavior and optional pip check.
  Build source/wheel and prove no optional engine enters normal consumer imports.
- [ ] Add owned PG16/PG18 acceptance for cross-process resume, current/foreign owner,
  stale/concurrent decisions, frozen evidence, unavailable selected memory,
  uncertain dispatch, receipt adoption and recorder reconciliation. Fail on skips.
- [ ] Implement separate Linux AMD64/ARM64 × PG16/18 CI with hashed optional engine
  dependencies, synthetic fixture, exact source receipts and complete cleanup.
  Retain existing full acceptance and enabled-memory CI without weakening gates.
- [ ] Freeze clear/ambiguous/contradictory/insufficient synthetic specs and one-pass
  controls. Test source-bound finding classification and cost/latency aggregation;
  label scripted comparisons as mechanics rather than proof of SUE effectiveness.
- [ ] Write the beginner guide: what SUE is for, candidate installation cost/status,
  independent enablement, explicit source selection, zero-call start, continuation,
  source-linked reports, terminal meanings, resume/uncertainty and removal/disablement.
  Use only commands actually executed in installed qualification.
- [ ] Run `.venv/bin/python -m pytest -q`, `.venv/bin/python -m build`, installed
  wheel/rebuilt-sdist consumers and full existing/optional acceptance lanes. Record
  exact commands, actual counts and all failures, not just successful receipts.
- [ ] Request an independent final regression review; fix findings with observed
  failing regressions. Retain original and final artifacts and verification logs.
- [ ] Commit code/docs/evidence separately as appropriate. Do not push, open/merge
  a PR or publish unless subsequently authorized. Report outstanding gates honestly.

## Implementation handoff

Recommended execution: native in the existing isolated Lab worktree, on separate
branch `codex/sue-review-workflow`, followed by an independent final review.
The tasks share source/policy/engine contracts, making sequential implementation
the simplest way to keep those identities consistent.

This plan adds no runtime behavior yet. Review the design and this concrete plan
before implementation, as required by the writing-plans skill. No new live
allowance or publishing authority is requested by approving implementation.
