# Bounded coordination implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan natively, task by task. The earlier native choice and
> question opt-out persist; one fresh whole-branch review follows implementation.

**Goal:** Qualify a reusable two-worker consumer protocol with shared bounds,
independent durable SDK runs, deterministic join and receipt-only recovery.

**Architecture:** Lab owns typed assignments, a private single-host launch
journal and independent host assessment. Public Harness/Runtime own execution,
receipts and shared execution budgets; the example composes two independent
instances in threads and compares a sequential baseline.

**Tech Stack:** Python3.12, pytest, current pinned released SDKs, stdlib threads,
file locking and loopback HTTP; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-20-bounded-coordination.md`

## Global Constraints

- Exactly two workers; pair4requests/2tools/8192reported tokens/600seconds.
- Per worker2requests/1tool/4096tokens; response output512.
- Provider-neutral protocol, public installed APIs only; trusted host bindings.
- No live requests, SDK edits, push/merge/publication or new allowance.
- Cumulative1558/637/1976623; charged1509/610/1835168;39ledgers/9unknowns.
- Memory/correction remain experimental; retain existing CI/stack gates.
- Cooperative cancellation; do not claim arbitrary-code preemption or benefit.

## Review Focus

- Restart between launch intent, SDK receipt and journal settlement must never
  cause replacement dispatch (Task1/2 process-loss and replay tests).
- A completed peer cannot hide unknown usage, missing evidence or a foreign
  assignment (Task1 joins and Task2 scoped receipt reassessment).
- Cancelled in-flight work may finish; no later call may start once stopped
  (Task2 barrier-controlled cancellation/exhaustion witnesses).
- Shared counters/deadlines must not be copied or renewed in worker threads
  (Task2 observed overlap, aggregate ceilings and original-deadline checks).
- Corrupt, aliased or foreign saved state cannot produce passing inspection
  (Task1 bounded-file tests, Task2 actual public receipt reconstruction).

---

### Task 1: Host protocol, launch journal and deterministic join

**Files:** Create `lab_runner/coordination.py`,
`tests/unit/test_coordination.py`.

**Interfaces:** `make_plan(binding_digest, assignments) -> dict` validates
exactly two closed assignment dicts {workerId,sourceId,sourceRevision,
assignmentDigest} (all identifier strings except SHA256digest), sorts workerId,
and returns {version:1,bindingDigest,assignments}. `CoordinationJournal(path,
plan=plan,create=True)` owns one private bounded JSON file/lock. `claim(worker_id)
-> token` durably launches once; `settle(worker_id, token, report) -> dict`
records one verified terminal report; `inspect() -> dict` is read-only and
excludes tokens. `join_reports(plan,reports) -> dict` is pure, deterministic,
and returns {version:1,status,usage,workerStatuses}; statuses ready/hold/
conflict/missing/incomplete/failed/budget. Report fields are workerId,
assignmentDigest,status,sourceId,sourceRevision,fact,usage,evidenceDigest.
Only completed may have a boolean fact or null (verified missing); failed and
unknown use null. Unknown usage is null and requires unknown status; completed
needs known counts. Report usage numeric fields providerRequests/toolCalls/
reportedTokens reject booleans. Failed known counts are retained. No raw output.

- [x] Write tests for closed plans/reports, reversed result order, ready/hold/
  missing/conflict, partial/unknown/failed/over-cap counts, binding changes,
  concurrent duplicate claims, immutable/idempotent settlement, restart after
  claim, strict existing-file inspection and private/corrupt/symlink files.
- [x] Run focused tests; watch missing protocol fail before implementation.
- [x] Implement interfaces using existing Lab canonical/private-write helpers,
  bounded owner-only reads and fcntl lock; cap journal to64KiB. Unknown remains
  null; report success requires both assignments and sums within parent/child
  ceilings. Persist no retry API and never refund reservations.
- [x] Run `PY tests/unit/test_coordination.py -q`; require all pass and diff check.
- [x] Commit protocol, tests and task ledger evidence.

### Task 2: Actual public-SDK pair and sequential baseline

**Files:** Create `lab_runner/coordination_fixture.py`,
`tests/functional/test_coordination.py`, `scripts/coordination_smoke.py`.

**Interfaces:** Consumes Task1. `qualify(output, *, provider, scenario,
mode='parallel') -> dict` admits a fresh private synthetic case. `inspect_pair(
output, *, provider, scenario, mode) -> dict` reconstructs public SDK objects
for read-only reassessment without execution. `replay(root) -> int` validates
all saved case reports with network denied. Providers openai/anthropic;
modes sequential/parallel; scenarios ready/hold/conflict/missing/wrong/
malformed/tool-error/provider-error/cancel/request-cap/tool-cap/token-cap.
Smoke runs48lanes and saved inspections, emits a safe summary with all outcomes,
costs and unknown denominators. Process-loss tests use separate bounded
subprocesses at launch/receipt boundaries rather than add more study lanes.

- [x] Write functional tests for48actual both-wire/mode lanes and safe replay,
  asserting real overlap for parallel ready with a provider-side event barrier,
  no overlap for sequential, pair counts<=4/2/8192 and original deadline.
  Tests check correct domain categories, honest unknown costs, zero requests
  for pre-cancel, actual counter exhaustion, no post-stop continuation and
  drained owned resources. Add before/after-receipt process-loss inspections.
- [x] Watch the fixture/recipe tests fail before implementation.
- [x] Implement independent per-worker resources and one shared public
  ExecutionBudget activated explicitly in each worker, plus child budget.
  Use one FailureIsolation full-pair reservation. Bind expected source/facts
  to actual scoped lookup and public recovery evidence. Typed outputs include
  assignment/source fields; host checks the observed lookup, not model claims.
  Use strict exceptions so checks survive Python optimization. Set cancellation
  on failure/unknown and join all worker threads before final assessment.
- [x] Save private source/lookup/public receipt evidence, journal and safe proof.
  Fresh inspection rebuilds only public objects, compares receipts and saved
  terminal reports, and refuses launch gaps; it calls no run/resume/turn.
  The safe summary has no raw IDs/prompts/source contents/exception messages.
- [x] Run focused unit+functional tests; require all pass. Verify recipe in
  source mode and separate network-denied replay; retain commands/results.
- [x] Commit the fixture/recipe/tests and ledger results.

### Task 3: Consumer documentation, package adoption and final qualification

**Files:** Create `docs/bounded-coordination.md` and
`docs/verification/bounded-coordination-2026-10-20.md`; modify README,
docs/handoff.md, docs/current-status.md and
`scripts/conversation_distribution_smoke.py` to run the installed new recipe.

**Interfaces:** Uses Task2 smoke with `--output PATH`, `--replay`, and optional
`--source-root PATH` for source-only imports. Installed commands use -I and
omit source-root. Existing manifest/version/pins stay unchanged.

- [x] Add an adoption regression demonstrating the new installed gate is
  required, then run it RED. Integrate the recipe in both wheel/sdist consumers
  without skipping or weakening any existing gate; run GREEN.
- [x] Document exact copy/adaptation points, trust boundaries, caps and known
  limits. Describe unsupported distributed scheduling/forced preemption and
  evidence-based model efficacy separately from protocol qualification.
- [x] Run the full source suite once after implementation. Build fresh wheel
  and sdist, run clean public-consumer distribution smoke and verify installed
  source payload equality, import isolation, dependencies and owned cleanup.
- [x] Freeze verification evidence and request one fresh whole-branch review.
  Regrade findings by user effect; fix Important/Critical with watched RED to
  GREEN and a green full suite. Record all decisions/deferred minors, no repeat
  review. Preserve private evidence and keep this branch local.
- [x] Commit final qualification/docs. Record exact branch/base, tests, artifacts,
  unchanged limits and any remaining platform/live gates in the final handoff.
