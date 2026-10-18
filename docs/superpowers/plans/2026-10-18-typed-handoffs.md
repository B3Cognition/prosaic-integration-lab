# Typed handoffs implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the already selected native execution method.

**Goal:** Qualify typed planner/worker/critic handoffs and full-trajectory scoring offline.

**Architecture:** Lab owns typed synthetic task contracts and semantic validators.
Installed Harness owns graph/state/receipts; installed Runtime owns native tool
execution and shared budget admission. Reuse the existing closed task grammar.

**Tech Stack:** Python 3.12, installed SDK candidate family, jsonschema, pytest.

**Spec:** `docs/superpowers/specs/2026-10-18-typed-handoffs.md`.

## Global Constraints

- Offline synthetic only; zero live allowance, no release/push.
- Public installed APIs only; keep memory experimental and old evidence intact.
- Caps: 4 requests /2 tools /8192 tokens /600 seconds /512 output tokens.
- No extra model repair; disagreements pause for human review.

## Review Focus

- Wrong binding or identity must not advance (assignment/result tests).
- Unread source must not become absent (incomplete lookup test).
- Colliding current revisions must not become authoritative (conflict test).
- A critic that misses a worker flaw must not approve (missed-flaw test).
- Unknown usage and replay must not dispatch again (fault/reconstruction tests).

### Task 1: Offline handoff consumer, trajectory scoring and qualification

**Files:** create `lab_runner/handoffs/{contracts,execution,fixture,scoring}.py`,
`tests/functional/test_typed_handoffs.py`, `scripts/typed_handoff_smoke.py`,
`docs/typed-handoffs.md` and verification ledger; update handoff/progress.

**Interfaces:** consume public WorkflowFactory, Harness, FileRunStore,
ExecutionBudget and existing task assessment. Produce `execute_case` and
`recover_case` receipt evidence; `score_trajectory` reports quality separately
from safe stopping, first failure, counts and role order.

- [ ] Write behavior tests for good approval/rejection, missing/conflicting/unread
  evidence, wrong assignment/result binding, wrong worker decision, missed/false
  critic finding, invalid JSON, unknown usage and receipt-only reconstruction.
- [ ] Run focused tests and observe missing implementation fail (RED).
- [ ] Implement closed contracts, trusted case validation, graph/validators,
  shared budget, synthetic both-wire transport and evidence scoring.
- [ ] Run focused tests: all pass. Run the full Lab suite: no failures.
- [ ] Build an isolated private Lab wheel, install with unchanged SDK family;
  run installed both-wire smoke and payload/provenance checks.
- [ ] Obtain one independent whole-change review; fix important findings with
  RED/GREEN regressions and rerun suite. Record limitations and actual evidence.
- [ ] Commit local changes and final verification ledger. No push/release.

Preflight: contracts/execution/scoring share assignment and result schema;
single task keeps this interface atomic. Native execution and prior planning
opt-out persist; no redundant review menu. Existing linked Lab worktree reused.
