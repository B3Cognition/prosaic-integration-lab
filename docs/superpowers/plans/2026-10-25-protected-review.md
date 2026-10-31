# Protected Review Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline; a fresh reviewer checks the result.

**Goal:** Protect source-first accepted review and evaluate advisory handoffs.
**Architecture:** Consumer workflows and immutable source-bound results use public
Harness/Runtime APIs. Candidate reviews remain separate proposals.
**Tech Stack:** Python3.12, existing installed SDKs and unchanged strict scorer.
**Spec:** ../specs/2026-10-25-protected-review-design.md

## Global constraints

Memory/SUE disabled by default; no SDK/canonical SUE/scorer/pin changes. Preserve
all historic evidence and unknown reservations. Use apply_patch and public APIs.

## Review focus

- SUE or artifact leakage into the initial review must fail before dispatch.
- Mutating caller inputs or exported candidates cannot alter the accepted final.
- Wrong source hashes, invalid ranges, foreign tasks and failed reviews cannot be captured.
- Strong system instructions contain only verified host criteria, never source/advice.
- Candidate failure or unavailable advice cannot invalidate captured independent output.

## Task1 — Protected review API

Files: new `lab_runner/requirements_review_v4/{__init__,workflow,protection}.py`;
tests `tests/requirements_review_v4/test_protection.py`.

- [x] Write failing tests for closed source-only projection, immutable capture,
  candidate nonpromotion, source/range/consistency rejection and task binding.
- [x] Implement source-only WorkflowFactory with existing final guidance and
  additional citation validator. Implement `IndependentReview.capture(task,
  review, run_id=...)`, `.final`, `.task`, `.outcome(candidate=None)` as immutable
  owned bytes with independent run/task/source identity.
- [x] Implement `candidate_messages(independent, advice, handoff, boundary)` with
  host-verified criteria, raw/compact ownership and no source-to-system promotion.
- [x] Run focused tests and public SDK loopback execution/recovery fixtures;
  verify invalid candidates remain separate failures and old modes unchanged.
- [x] Run the full default Lab suite and record actual output before committing.

## Task2 — Installed candidate and controlled study

Experiment scripts/evidence: `/private/tmp/prosaic-sue-protected-20261025`.

- [x] Build wheel/sdist, install wheel in a fresh isolated environment and prove
  payload/source identity without editing any previous environment or wheel.
- [x] Test balanced138-sample schedule, frozen independent dependency reuse,
  advice representation and instruction partitions; reserve unknown usage in full.
- [x] Independent design review, then freeze cases/scorer/host keys, exact saved
  advice, prompts, scripts, installed sources and all previous evidence hashes.
- [x] Dispatch serially using public APIs and a fresh bounded allowance. Persist
  every Runtime result/receipt before candidate validation; retain all failures.
- [x] Offline strict grading and wire/receipt/source/allowance reconciliation;
  validate canonical final never changes and recovery dispatches no calls.

## Task3 — Evidence and recommendation

- [x] Fresh factual/code review; resolve material issues without changing assertions.
- [x] Seal a separate archive, reverify earlier evidence/reservations and document
  direct/critic baselines, candidate scores, canonical invariance and costs.
- [x] Update handoff and explain evidence for choosing critic versus optional SUE.
  No default enablement, model change, push or publication.

The user's request approves native execution of this described work. Routine
implementation choices are recorded here without adding another approval gate.

## Verified result

Implementation commit `db8d780`; all existing modes, SDKs, scorer and default
flags unchanged. Full default suite: 2,033 passed; candidate v4/v3: 25 passed;
installed protection: 14 passed; study safeguards/fixtures: 10 passed.

All 138 scheduled cells are accounted for: 145 requests / 219,943 tokens,
zero unknowns, overruns or tools. Both offline audits passed. All 60 executed
handoffs preserve the captured final; 30 remain zero-call dependency failures.
The new source-only profile scores 7/24 against critic 14/24; it stays an
experimental option and is not recommended as a replacement. Paired boundary
and handoff conclusions, costs, failed evidence and follow-up recommendations
are in `docs/verification/sue-protected-2026-10-25.md`.

The archive has 1,040 files, manifest SHA256
`d15198cf33cb8467f842e707fd4991a23cf3f62690bf3f883acd52bd0f350d87`.
All 11 prior archives / 5,426 files and the original unknown reservation verify
unchanged. No push, merge, enablement or release.
