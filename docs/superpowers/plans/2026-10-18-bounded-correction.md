# Bounded correction blueprint implementation plan

> **For agentic workers:** Use superpowers:executing-plans; native selected.

**Goal:** Reusable bounded correction and matched no-critic measurement.
**Architecture:** Pure generic feedback/comparison helpers; separate rollout
consumer graph through public SDKs, one outer shared budget and nested caps.
**Tech Stack:** Python3.12, existing pinned SDKs, synthetic both-wire fixtures.
**Spec:** `docs/superpowers/specs/2026-10-18-bounded-correction-design.md`.

## Global Constraints

- No live calls or provider/model tuning; preserve SDKs, old APIs and evidence.
- Each arm:4requests/2tools/8192tokens/600seconds/output512; corrector1request/0tools.
- Current live ceilings1524/625/1976623 and charges1494/605/1805193 unchanged.
- One correction maximum; no new lookup/hidden expected answers; no push/release.

## Review Focus

- Raw critic content or hidden expected values cannot enter corrective feedback.
- A fresh nested budget cannot bypass outer limits, unknown usage or component breaches.
- Missing evidence, malformed artifacts and false critic advice never authorize acceptance.
- Matched comparison rejects different drafts, evidence, contracts, policies or limits.
- Recovery/duplicate execution cannot dispatch or erase costs and original outputs.

### Task 1: Generic feedback and matched comparison

**Files:** `lab_runner/bounded_correction.py`, `tests/unit/test_bounded_correction.py`.
**Interfaces:** `correction_feedback`, `compare_corrections` consume trusted
consumer diagnostics/bindings and evidence reports; never execute models.

- [x] RED→GREEN: sanitize feedback, bind draft/evidence, filter unsupported advice,
  separate warning from verification and reject unmatched/unknown comparisons.
- [x] Commit pure helpers and behavioral tests from an alternate domain.

### Task 2: One-shot consumer graph, offline proof and adoption guide

**Files:** `lab_runner/handoffs/correction.py`, `correction_fixture.py`,
`tests/functional/test_bounded_correction.py`, `scripts/bounded_correction_smoke.py`,
`docs/bounded-correction.md`, verification/handoff/version metadata.
**Interfaces:** `execute_correction`, `recover_correction`, `score_correction`
consume public SDK config and optional qualified token counter; use Task1 helpers.

- [x] RED→GREEN both arms: success/skip, bad/missing/unread drafts, partial/false
  critic, ignored/regressed correction, bad JSON/binding, unexpected tools,
  exhausted/unknown/overrun budgets, unchanged evidence and zero-call recovery.
- [x] Build graph/fixture/installed smoke, ensuring actual wire feedback has no
  gold and corrected results cannot bypass host checks.
- [x] Full source suite, build and exact installed payload audit in fresh env;
  synthetic both-wire smoke and immutable historical accounting verification.
- [x] One fresh final reviewer; material fixes in one RED→GREEN pass and green suite.
- [x] Preserve proof, document adoption/limits, commit locally and retain branch.
