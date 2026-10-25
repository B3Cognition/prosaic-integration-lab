# SUE review quality and bounded cost implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, task by task.

**Goal:** Implement the five approved recommendations, verify each separately,
then rerun the same eight-case, strict-scored, 360-second Qwen comparison.

**Architecture:** The pure SUE adapter owns an opt-in repeated-cycle stop;
Lab owns frozen review criteria, model-facing report projection and final
consistency validation. Harness remains responsible for accepted history and
resume; Runtime remains responsible for execution and usage.

**Tech stack:** Python, installed public SDKs plus explicitly admitted existing
Runtime JSON-schema candidate; separately built immutable SUE and Lab wheels.

**Spec:** User-approved recommendations in this conversation, 2026-10-25;
baseline `docs/verification/sue-qwen360-2026-10-25.md`.

## Global constraints

- Keep every canonical turn/provenance validator and the original cases/scorer.
- Memory and SUE remain disabled by default. New engine behavior is opt-in.
- Never mutate prior environments, run IDs, archives, ledgers or reservations.
- No SOAR, copied SDK engines, private imports, push, release or backport.
- Live run retains 360 seconds, 30 requests/65,536 tokens per cell; 60 seconds
  per request, 14 turns/28 SUE calls/two attempts and existing aggregate limits.
- Store raw RED/GREEN, build, fixture, replay and wire/receipt evidence separately.

## Review focus

- Valid but repetitive turns must stop conservatively, without becoming resolved.
- New evidence, answered questions or revised claims must not trigger that stop.
- Frozen task criteria must survive resume and reject changed same-ID requests.
- Compact advice must retain every distinct provenance and unresolved finding.
- Final consistency rejection must retain incurred usage and bounded retries.

### Task 1: Opt-in engine cycle guard

**Files:** Castle `cognitive_castle/brain_engine.py`, SUE source manifest,
`tests/test_brain_engine.py`, package distribution tests.

- [ ] RED: repeat a partial DISTINCT/successful DIVIDE cycle; expect bounded
  stop, unchanged missing coverage and reason `repeated_cycle_no_progress`.
- [ ] GREEN: add `initial_state(..., cycle_guard=False)`; detect two identical
  adjacent operator cycles, ignoring bookkeeping but preserving substantive
  response, claim version and addressed unresolved issues. Keep legacy state
  and transition behavior identical when omitted. Canonical validation first.
- [ ] Verify non-repetitive progress, invalid replies, all lenses and pure wheel
  rebuild/provenance. Update manifest only for changed adapter bytes; commit.

### Task 2: Frozen task-specific review context

**Files:** Lab SUE session/workflow, new `context.py`, focused execution tests.

- [ ] RED: signed host criteria reach actual wire; same-ID changed criteria
  conflict; new session resumes using frozen criteria and cycle policy.
- [ ] GREEN: optional session cycle guard and start-time `review_context`;
  bounded closed context with purpose, public issue definitions and criteria.
  Bind mode into workflow identity and actual bytes into request signature.
  Keep source evidence and canonical guidance distinct and unchanged.
- [ ] Verify source projection, owner checks, disabled behavior and legacy
  fingerprints; run focused suite; commit before next task.

### Task 3: Compact model-facing final advice

**Files:** Lab SUE reporting and new comparison v3 projection/workflow tests.

- [ ] RED: repeated report entries collapse with all originating turn refs;
  distinct premises/questions/evidence remain, raw report stays unchanged.
- [ ] GREEN: deterministic compact advice projection for the new comparison
  workflow only. Retain terminal, missing coverage, open issues, source hashes,
  claim and advisory meaning; omit transport/accounting bookkeeping.
- [ ] Verify exact provenance, input immutability and bounded projection;
  original comparison v1/v2 unchanged; commit.

### Task 4: Final consistency and task guidance

**Files:** Comparison v3 workflow and real Harness fixture tests.

- [ ] RED: `missing_context` plus ISSUES_FOUND is rejected then corrected;
  two invalid replies exhaust existing attempts and retain usage/receipts.
- [ ] GREEN: public custom validator, no response rewriting; clarify category
  boundaries, seed hypothesis, independent advice review and trigger-plus-gap
  citations without case IDs, keys or hard-coded outcomes.
- [ ] Verify accepted final bytes unchanged and strict original scoring;
  all source/installed tests; commit.

### Task 5: Separate reasoning diagnostics and qualified rerun

**Files:** New comparison diagnostics/tests, verification guide/handoff;
private fresh operator, frozen plan, allowance, replay/audit and archive.

- [ ] Add case-neutral outcome diagnostics separating schema/provenance,
  final strict checks and SUE examination completion. Held-out fixtures exercise
  progress, false conflict candidates and additional findings; never grade
  natural-language entailment as proven by mechanical checks.
- [ ] Build wheels and verify payloads, full suites, absence/default checks,
  installed 24-cell matrix and network-denied replay. Fresh independent review.
- [ ] Freeze all declared policy/prompt changes and same cases/scorer/model/
  limits. Verify nine prior archives and the unchanged old unknown reservation.
- [ ] Run one fresh 360-second Qwen comparison. Stop on unknown usage or
  enforcement warnings; keep maximum reservation. Audit every wire/receipt,
  replay without calls; report failures honestly and seal fresh evidence.

## Execution ledger

Native execution is already authorized by the user. Existing clean linked
Castle/Lab worktrees are reused. Task 1 -> 2 consumes the opt-in engine keyword;
2 -> 5 consumes frozen context/policy; 3 -> 4 -> 5 consumes comparison v3.
Old versioned workflows and environments remain available as controls.
Evidence root: `/private/tmp/prosaic-sue-review-fixes-20261025`.

Task 1 complete: Castle aef05c5; watched 3 RED -> 49 engine GREEN,
75 standalone distribution checks. Actual archived case 4 stops at six accepted
turns under the opt-in guard (the first repeated answers differ in type).
Task 2 complete: Lab 836bf15; 5 RED -> 5 context GREEN, compatibility 12 GREEN,
full focused SUE 101 GREEN. Legacy requests without optional reviewPolicy retain
their old projection; all failed verification logs are preserved.
Task 3 complete: Lab 81ac3b2; missing compact projection RED -> 8 GREEN including
v2 compatibility; raw report untouched, distinct provenance and turn refs kept.
Task 4 complete: Lab f5bf54f; 2 RED -> 21 GREEN, receipts and incurred usage kept.
Task 5 diagnostics: e06af64 and f20cefb; 4 RED -> 8 GREEN, then reviewer-requested
three held-out real session/projection/final integrations GREEN. These are
scripted mechanics, not held-out model reasoning qualification. Installed suite
116 GREEN, synthetic matrix 24/24 with zero-call replay, PG16/18 six GREEN each
with cleanup. Native Linux and release qualification remain separate.

Ruling: the full legacy Castle suite is not green in this dependency environment.
Candidate 93 failures/38 errors/2478 passes has exactly the same 131 failing node
IDs as the pre-change snapshot (2475 passes). No assertions or skips changed;
this is differential non-regression evidence, not release qualification.
