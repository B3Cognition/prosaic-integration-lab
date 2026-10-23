# Tool outcomes and bounded recovery implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline; one fresh whole-change reviewer at the end.

**Goal:** Qualify portable tool failure evidence and opt-in bounded recovery.

**Architecture:** Runtime classifies trusted dispatch outcomes; Harness controls
bounded workflow recovery; Lab consumes exact installed candidates and traces.

**Tech Stack:** Python, existing dependencies, public SDKs, pytest/native fixtures.

**Spec:** `docs/superpowers/specs/2026-10-17-tool-outcomes-recovery-design.md`.

## Global Constraints

- Core unchanged; no model/serving-specific logic or prompt tuning.
- Default behavior, result envelopes and historic journal bytes compatible.
- No live inference, push, release or limit increases. Preserve old candidates.
- Case4requests/2tools/8192tokens/600seconds/output512 unchanged.
- Charge1417/574/1696913; ceilings1475/604/1976623, sevenunknown remain charged.
- Use apply_patch; public installed SDK consumption only in Lab.

## Review Focus

- Controlled ToolFailure('invalid_arguments') must not impersonate pre-dispatch failure.
- Uncertain effect or missing/malformed outcome never grants a retry.
- Outcome mutation, private error messages and model dictionaries cannot alter authority.
- A corrected required tool is not repeated after its successful execution.
- Pending/receipt-only recovery cannot reset budgets or redispatch effects.

### Task 1: Runtime outcome evidence and bounded execution

**Files:** Runtime create `src/prosaic_runtime/tool_outcomes.py`,
`tests/test_tool_outcomes.py`, `tests/test_tool_outcome_transport.py`; modify
tools.py, tool_registry.py, execution.py, policy.py, runtime.py, turn_capture.py,
telemetry.py, structured_tools.py, __init__.py and pyproject.toml; add public docs.

**Interfaces:** Public ToolOutcome strict version1 contract. Internal trusted
on_outcome callback preserves model/journal result envelopes. Native events
carry owned tool_outcome. RunPolicy.bounded_tool_recovery bool defaultsFalse;
new Runtime capability flags gate consumers.

- [x] Watch failing unit/privacy/transport regressions, implement classifications.
- [x] Verify native and conversation/structured event ownership, replay, strict
  stop, legacy continuation and both provider formats; budgets remain shared.
- [x] Run Runtime full suite, build candidate wheel/sdist; record/commit evidence.

### Task 2: Harness recovery policy

**Files:** Harness factory.py, engine.py, public docs, version files;
new `tests/test_bounded_tool_recovery.py`.

**Interfaces:** WorkflowPolicy.bounded_tool_recovery flag omitted from identity
whenFalse; true requires capabilities and passes Runtime flag. Required-tool
feedback uses validated fixed categories only. Non-repairable evidence blocks.

- [x] Watch failing tests for correctable failure, missing tool, malformed or
  wrong-version evidence, uncertain effects, completed repair and exhausted caps.
- [x] Implement public policy and receipt consumption; retain existing recovery.
- [x] Run full suite against installed Runtime candidate; build/commit Harness.

### Task 3: Lab opt-in adoption

**Files:** Lab memory/execution.py, memory/freeze.py, memory_policy/trace.py,
new bounded-recovery native tests; candidate manifest/provenance, public build
inputs and packaged freeze metadata; version/guide.

**Interfaces:** bounded_recovery=False execution/freeze/recovery option binds
policy identity; trace saves only validated ToolOutcome evidence, legacyunknown
is unclassified. No memory prompt/scorer/model settings changes.

- [x] Watch failing native tests, implement installed-public-API hooks.
- [x] Test shared unchanged limits, no inferred historical causes, zero-effect
  argument correction, unknown stop and immutable receipt-only trace replay.
- [x] Run full suite against installed candidates; build/commit Lab candidate.

### Task 4: Installed qualification and final review

**Files:** Lab installed smoke script, qualification guide/report; exact manifests
and immutable private evidence. Candidate versions per spec.

- [x] Qualify fresh wheel/sdist installation and payload matching; exercise both
  wire formats, privacy, cap exhaustion and recovery with external network denied.
- [x] Build/run isolated consumer image checks; distinguish external service lanes.
- [x] Fresh whole-change review spanning all three repositories; one watched
  RED→GREEN fix pass for Important/Critical findings, full suites green after fixes.
- [x] Preserve artifacts/ledgers, record actual qualification/readiness and commit.
