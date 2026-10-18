# Frozen direct-role live evaluation plan

> **For agentic workers:** Use superpowers:executing-plans; native already selected.

**Goal:** Measure direct worker/critic behavior on12fresh samples without changing limits.

**Architecture:** Private host consumes unchanged installed direct-v2 APIs and
BenchmarkAllowance. Immutable guards bind source/assets/profiles/inputs. Independent
oracle and accounting audit separate controls, natural mistakes and host safety.

**Tech Stack:** Python3.12, pinned installed SDKs/counters, synthetic HTTP, local live profiles.

**Spec:** `docs/superpowers/specs/2026-10-18-direct-live-design.md`.

## Global Constraints

- Per-case4requests/2tools/8192tokens/600seconds/output512 unchanged.
- No live call before new allowance approval; proposed ceilings1524/625/1976623.
- No SDK/product source changes, model-specific tuning, memory, retry, push/release.
- Keep37old ledgers,2596historical files,1996offline files and8unknowns unchanged.

## Review Focus

- Gold/source authenticity and natural-versus-control denominators.
- Interrupted reservations and evidence written before settlement never become free.
- Changed source/profile/case/approval cannot dispatch; claimed samples never retry.
- Unknown usage, counter violation or overrun blocks all subsequent calls.
- Critic disagreement and independent host safety are not credited as task repair.

### Task 1: Freeze and qualify the complete study host

**Files:** private `/private/tmp/prosaic-direct-live-{common,inputs,fixture,qualify,freeze,run,audit,analyze}.py`,
private host tests; sanitized preparation in `docs/verification/direct-live-2026-10-18.md`.

**Interfaces:** `build_inputs(seed)` produces cases/gold/schedule; `oracle(case,rows,rules)`
independently computes a compact worker value; `guard(authorized=False)` binds all
immutable inputs; runner reserves each full case and settles receipt-derived counts.

- [ ] Write/observe RED for independent oracle, fresh schedule and budget/approval gates.
- [ ] Implement private host, six seeded cases, controls and source-bound oracle.
- [ ] Qualify all12frozen samples with actual counters on synthetic HTTP; reject
  mutated bindings, unknown/overrun/retry and interruption phases; deny recovery sockets.
- [ ] Audit installed code/wheels, historical ledgers/evidence and serving guards.
- [ ] One fresh whole-host review; fix material findings with RED/GREEN evidence.
- [ ] Freeze final binding and ask precisely24requests/8tools; no token increase.

### Task 2: Execute the frozen operational evaluation and report

**Files:** private live ledger/receipts/audit/analysis/archive; sanitized result and handoff.

**Interfaces:** consumes Task1 frozen proof and explicit allowance approval. Uses
unchanged installed `direct.execute_case`/`recover_case` and immutable receipts.

- [ ] After approval only, persist consent bound to proof; reserve/run12samples,
  no redispatch, halt on unknown/overrun/counter violation.
- [ ] Reconcile receipts with accounting/diagnostics; copied-state recovery with sockets denied.
- [ ] Count actual worker flaws reviewed, critic detections/false alarms and costs;
  report controls separately, including unreached stages and small-sample limits.
- [ ] Preserve new evidence and canonical ledger, verify all old hashes and charged unknowns;
  commit sanitized report locally and retain branch/worktree.

Preflight: Task1 produces the exact frozen proof, schedule and driver consumed by
Task2. Implementation/review finish before operational dispatch; no code tuning
after observing live results. Existing package suite1478 remains unchanged;
new private-host qualification is its own complete test suite.
