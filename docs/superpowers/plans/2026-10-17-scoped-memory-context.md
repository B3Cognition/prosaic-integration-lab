# Scoped Memory Context Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. Implement natively; one fresh whole-branch reviewer at the end.

**Goal:** Add scoped retrieval and enforceable whole-trajectory context admission
with frozen native execution/recovery evidence.

**Architecture:** New pure `lab_runner.memory_policy` components select by trusted
metadata and compose optional recall within host-quoted input ceilings. A public
Runtime counter wrapper enforces those ceilings; an opt-in memory adapter binds
the plan into Harness execution and receipt-only recovery.

**Tech Stack:** Python 3.12, existing installed public SDK candidates, pytest;
no new dependencies, serving-engine imports or model-specific logic.

**Spec:** `docs/superpowers/specs/2026-10-17-scoped-memory-context-design.md`.

## Global Constraints

- Existing v1 corpus/source formats and default retrieval remain unchanged.
- Core/Runtime/Harness source unchanged; no private SDK imports or monkeypatches.
- Trusted host scope/metadata and source registry; notes never authorize scope.
- Case caps 4 requests / 2 tools / 8,192 tokens / 600 seconds, output 512 unchanged.
- No new live inference, release/push or automatic memory writes in this slice.
- Cumulative charged 1,363 / 547 / 1,621,526; ceilings 1,475 / 604 / 1,976,623.
- Use apply_patch, preserve old evidence/unknown reservations and unrelated files.

## Review Focus

- Populated tenants with no eligible entity/topic return empty recall (Task 1).
- Foreign policy changes do not alter local output or frozen identity (Tasks 1/3).
- A quote mutating its argument or returning booleans cannot corrupt admission (Task 2).
- Guard callbacks rejected before dispatch must not become paid requests (Tasks 2/3).
- Recovery with a throwing quotation callback must reuse the saved plan (Task 3).

### Task 1: Trusted scoped retrieval

**Files:** Create `lab_runner/memory_policy/__init__.py`, `scoped.py`;
`tests/unit/test_scoped_memory.py`.

**Interfaces:** `ScopedCorpus(document, historical_sources, metadata)` produces
`tenant_digest(tenant_id)` and `retrieve(tenant_id, entity_id, topics, as_of)`;
result has v1 retrieval fields plus private `decisions` and `policyDigest`.

- [ ] Write tests with literal expected IDs/reasons for hard tenant/entity scope,
  topic ranking independent of prose/tags, stale/expired/future/missing refs,
  ownership, stable order, complete metadata admission and bounded packing.
- [ ] Run targeted pytest; observe missing behavior/import before implementation.
- [ ] Implement admission/tenant partitions and stable selection; no model logic.
- [ ] Run targeted then full suite; record actual results and commit.

### Task 2: Whole-trajectory assembly and guard

**Files:** Create `lab_runner/memory_policy/budget.py`, `assembly.py`;
`tests/unit/test_memory_context_budget.py`.

**Interfaces:** `assemble_context(...)` consumes the scoped result and trusted
quote callback, returns `{request, retrieval, plan, decisions}`. Plan binds
request digest, base counter identity, full input ceilings/output ceiling and
admission arithmetic. `guard_registration(base, plan)` returns an object with
`.registration` (public SDK registration) and owned `.proposals` trace.

- [ ] Write failing tests for exact fit, mandatory preservation/refusal, optional
  recall exclusion, later smaller candidates, existing/inflight usage, invalid
  or mutating quotations and limits; test actual counter input/output/proposal
  enforcement, descriptor binding and owned trace across both provider formats.
- [ ] Watch targeted failures, implement pure assembly and lock-protected guard.
- [ ] Verify true counts are returned; rejected calls produce no provider debit
  using public Runtime fixtures, not a copied backend.
- [ ] Run targeted/full suite, record results and commit.

### Task 3: Frozen native integration and portable trace

**Files:** Create `lab_runner/memory_policy/native.py`, `trace.py`;
modify `lab_runner/memory/context.py`, `execution.py`, `freeze.py` and packaged
freeze manifests; add `tests/functional/test_scoped_memory_execution.py` and
`tests/unit/test_scoped_memory_recovery.py`.

**Interfaces:** `ScopedContext(scoped_corpus, *, counter_descriptor, quote_inputs,
quote_identity, limits, output_tokens)` exposes `identity(case)` and
`prepare(case, arm)`. Add optional `context_builder=None` to `prepare`, `freeze`,
`materials`, `execute_case`, `recover_case`. Selected plan's counter guard is
activated throughout the current native workflow. `TraceRecorder(path)` delegates
to SDK `MemoryRecorder`, saving owned intent/observation snapshots atomically.

- [ ] Write native fixture tests for populated irrelevant context, isolated
  hostile same-entity recall, full-trajectory recall denial and zero-call
  mandatory refusal. Assert unchanged public task/index and no private answers.
- [ ] Write freeze/recovery tests: saved plan reused with throwing quote,
  local drift blocks, valid foreign drift preserves identity, rejected/unknown
  attempts cannot restart through recovery, trace bytes stay unchanged.
- [ ] Watch failures; implement optional integration and recorder-derived trace.
  Bind new source hashes in development manifests; retain historical data bytes.
- [ ] Run targeted/full suite, regenerate only current packaged freeze metadata,
  record actual commands/results and commit.

### Task 4: Installed qualification and final review

**Files:** Update `pyproject.toml`, `dependencies/public-build-inputs.json`;
create `scripts/scoped_memory_smoke.py`, `docs/scoped-memory-context.md` and
`docs/verification/scoped-memory-context-2026-10-17.md`.

**Interfaces:** Candidate `0.5.1+context.1` uses the same SDK manifest and optional
counter libraries. Installed smoke consumes public programmatic context APIs;
does not contact existing live endpoints or require credentials.

- [ ] Add behavioral packaging/installed smoke coverage, build wheel/sdist and
  install into a separate environment; preserve all earlier candidates/envs.
- [ ] Verify every installed payload and run scoped native fixture/recovery
  scenarios with pure preflight and byte-identical network-disabled replay.
- [ ] Run final full suite after executable changes and independent branch
  review; fix important findings with watched RED→GREEN tests and a green suite.
- [ ] Record provider-neutral scope, enforceable planning-domain limits,
  unchanged live allowance and readiness for a fresh live comparison; commit.
