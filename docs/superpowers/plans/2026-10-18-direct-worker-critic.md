# Direct worker/critic implementation plan

> **For agentic workers:** Use superpowers:executing-plans (native execution already selected).

**Goal:** Close the model-visible output contract gap and qualify worker/critic directly offline.

**Architecture:** Opt-in Lab version2 consumes installed public SDK graph,
adapter projection and shared budget APIs. Host assignment/evidence metadata
does not require model generation; independent validators remain authoritative.
Retain the old path and artifacts. No SDK engine reimplementation or private imports.

**Tech Stack:** Python3.12, installed qualified Runtime/Harness, jsonschema, pytest.

**Spec:** `docs/superpowers/specs/2026-10-18-direct-worker-critic.md`.

## Global Constraints

- No live inference or new allowance. Preserve current per-case4/2/8192/600/output512.
- Provider-neutral, opt-in; no model names or serving-engine behavior in implementation.
- Keep v1 graph/prose/defaults and prior evidence intact; no push/release.

## Review Focus

- Actual transmitted schema/value guidance, not a fixture oracle ignoring prompts.
- Invocation-scoped critic evidence cannot be replaced by worker claims.
- Critic controls must remain separate from naturally produced worker results.
- Incomplete evidence and unknown accounting remain visible; neither authorizes success.
- Reconstruction and conflicting identity must not launch a model or change receipts.

### Task 1: Explicit contracts and direct execution

**Files:** create `lab_runner/handoffs/direct_contracts.py`, `direct.py`,
`direct_fixture.py`, `direct_scoring.py`; tests `tests/functional/test_direct_handoffs.py`.

**Interfaces:** `materials(case, config, output, sample_id, mode='handoff',
draft=None, record_ids=None)` builds an installed public workflow and host request;
`execute_case(..., token_counter=None)` is synthetic-only unless an explicitly
qualified matching counter is supplied; `recover_case(...)` is no-dispatch;
`score_direct(case,evidence)` separates role outcomes and safety.

- [x] Write failing both-wire tests for contract delivery, no planner, worker/
  critic/full modes, source isolation, controlled flaws and malformed output.
- [x] Observe RED; implement compact schemas, role guidance, trusted evidence
  projection, host validators and budgets; focused tests GREEN.
- [x] Test unknown/overrun/shared exhaustion, claim reuse and receipt-only recovery;
  run the complete Lab suite and commit locally.

### Task 2: Installed and real-counter offline qualification

**Files:** `scripts/direct_handoff_smoke.py`, guide/verification ledger and handoff;
private counter/payload/preservation operators under a fresh temporary root.

**Interfaces:** consume Task1 public entry points and receipts. Installed smoke
must prove import isolation and all adversarial both-wire outcomes. Counter
qualification reuses unchanged descriptors/assets on synthetic HTTP only.

- [ ] Build private candidate, install separately, audit exact payloads and SDKs.
- [ ] Run installed smoke plus controlled request-frame quotation for both existing
  model counters in worker/critic/full modes; preserve result and source identities.
- [ ] One fresh whole-change review. Fix Important/Critical findings with RED/GREEN
  regressions and full suite; defer minors explicitly.
- [ ] Record actual coverage, limitations and unchanged37ledgers/2596old files;
  commit locally. No live dispatch or claim of real critic effectiveness.

Preflight: contracts→execution→wire fixture/scorer→installed qualification share
compact schema and host evidence identity. Keep this interface atomic in Task1.
Ruling: compact output omits raw evidence copies; host transfers verified records
to critic. Cost: added host adapter integration, tested at actual HTTP boundary.
Ruling: direct qualification is offline; future live efficacy needs a fresh
frozen study and full reservations within remaining24requests/16tools/200184tokens.
