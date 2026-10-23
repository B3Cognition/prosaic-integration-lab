# Continuation Budgeting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Admit affordable variable native continuations without quotation-slot artifacts, preserving every current hard limit.

**Architecture:** Lab selects optional context with a complete planning quotation. An opt-in v2 plan distinguishes that quotation from dispatch admission: a qualified counter enforces the native context/output domain, while one public Runtime ExecutionBudget atomically reserves actual input plus maximum output across all Harness attempts. Existing v1 contracts remain the default.

**Tech Stack:** Python 3.11+, installed released Runtime/Harness, pytest, synthetic loopback providers.

**Spec:** `docs/superpowers/specs/2026-10-17-continuation-budgeting.md`

## Global Constraints

- Publish reviewed Runtime/Harness releases before implementation; Lab memory stays experimental.
- Case caps: 4 provider requests, 2 tools, 8,192 tokens, 600 seconds, 512 output tokens per request.
- Cumulative ceilings: 1,475 requests, 604 tools, 1,976,623 tokens; no live dispatch.
- Preserve v1 serialized plans and behavior, historic evidence, and receipt-only replay.
- Public installed SDK APIs only; Runtime owns usage and dispatch; no model/provider special cases.
- ALWAYS require a shared trusted Runtime budget for version-2 execution. NEVER infer paid usage from diagnostics.

## Review Focus

- A valid larger tool response must fit the actual shared remainder, independent of a smaller quotation slot.
- Unknown usage, concurrent in-flight work and overrun evidence must never replenish allowance.
- A second Harness attempt must share the first attempt's paid usage and request/tool caps.
- Malformed policy flags, v2 fields, output bounds or counter provenance must fail closed.
- Frozen v1 recovery must retain its trace bytes and never reconstruct counters or retrieval.

### Task 1: Versioned planning and continuation domain

**Files:** `lab_runner/memory_policy/{budget,assembly,native}.py`, `tests/unit/test_memory_context_budget.py`, `tests/unit/test_scoped_memory_recovery.py`.

**Interfaces:** Add strict `continuation_budget=False` to make_plan, assemble_context and ScopedContext. True creates plan version 2 with `dispatchPolicy='shared-execution-budget-v1'`; false emits identical v1 structure. Guard v2 enforces `min(contextCapacityTokens, tokenCeiling)-outputTokens` rather than inputBounds[index]. Preserve full quotation in plan and log quotedInputBound for v2 only. Trace reason `withinContext` means counted, not dispatched. Context identity binds opt-in policy; v1 omits it.

- [x] Write regressions for v2 variable counts above slot, arm-independent domain admission, strict version/policy validation, mandatory rejection, context/output limits and unchanged v1 behavior.
- [x] Run focused unit tests; expect new assertions fail before implementation.
- [x] Implement versioned plan, guard and context binding; keep validation exact and bounded.
- [x] Run focused unit tests; expect all pass.
- [x] Commit versioned continuation policy.

### Task 2: Shared execution, installed qualification and evidence

**Files:** `tests/functional/test_scoped_memory_execution.py`, new `tests/functional/test_continuation_budgeting.py`, `scripts/continuation_budget_smoke.py`, candidate dependency manifest, version metadata, docs/handoff.md and verification report/data.

**Interfaces:** execute_case consumes the v2 frozen plan through its existing guard and execution_scope. No new live runner default. Smoke uses installed public Runtime/Harness and both provider wire formats; no private SDK imports. Candidate manifest binds downloaded release artifacts; existing release manifest and historic tool candidate remain unchanged.

- [x] Write functional regressions for the observed 1,307/1,280 and 1,211/1,152 slot mismatches, shared repair attempts, unknown usage, capacity/output errors, budget exhaustion, concurrent reservations, and receipt-only replay.
- [x] Run those tests; expect failures before integration or new fixture completion.
- [x] Complete integration, add installed smoke for both providers, and retain exact limits.
- [x] Run focused and full Lab suite, build wheel/sdist, inspect source payload and installed smoke; expect green with all skips/limits reported honestly.
- [x] Verify all historic ledger hashes and current ceilings unchanged; record zero live calls and qualification limits.
- [x] Commit implementation/evidence, then one fresh whole-branch review required by executing-plans; fix Important/Critical findings via one RED/GREEN pass and full suite. Preserve ledger.

Self-review: both tasks share plan/guard semantics; Task 2 consumes Task 1's v2 format and same v1 default. Every review-focus input has a named regression above. This plan implements the spec without changing SDK execution semantics or requiring another model-specific fix.

Final review: no Critical/Important findings; minor derived-count numeric typing gap deferred and recorded in qualification. Full Lab suite1329passed; installed and Linux ARM64 both-wire14-scenario qualification plus legacy10-scenario replay passed. No live inference or Lab publication.
