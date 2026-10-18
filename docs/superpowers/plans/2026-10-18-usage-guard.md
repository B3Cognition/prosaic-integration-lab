# Usage guard implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the provider-neutral usage admission gap and publish a reviewable experimental Lab PR.

**Architecture:** A pure normalized-count reader is shared by observation admission and scoring. Raw SDK evidence remains authoritative and unchanged; the correction policy advances to v2.

**Tech Stack:** Python, pytest, installed Runtime/Harness, synthetic loopback HTTP.

**Spec:** `docs/superpowers/specs/2026-10-18-usage-guard.md`

## Global constraints

- Preserve per-arm 4 requests / 2 tools / 8,192 tokens / 600 seconds; output 512.
- Preserve cumulative ceilings 1,558 / 637 / 1,976,623 and historical evidence.
- Offline only; no SDK or default dependency changes; both features experimental.

## Review focus

- Unsupported pricing must not hide complete count breaches or erase role costs.
- Partial, boolean, contradictory and untrusted counts must not admit continuation.
- A breach at a final response must prevent acceptance even without another call.
- Recovery must perform no requests and preserve unknowns and latched decisions.
- Historical v1 evidence must not silently match v2 policy or be rewritten.

### Task 1: Guard and qualification

**Files:** `lab_runner/quality/usage_counts.py`, correction observer/scorer/fixture,
`tests/unit/test_usage_counts.py`, `tests/functional/test_bounded_correction.py`,
installed smoke script, package version and experimental documentation.

**Interfaces:** `complete_counts(usage) -> tuple[int,int,int] | None` accepts only
complete normalized counts with reported/unsupported status; no mutation.

- [x] Add count-contract and both-wire guard regressions; watch them fail.
- [x] Implement shared count interpretation, latch unavailable counts, revise policy and role scoring.
- [x] Run focused and full source suites; build and install a fresh candidate.
- [x] Run installed synthetic fault matrix, SDK/payload audits and immutable historical proof check.
- [x] Record exact results and limitations; commit; one fresh final review with any material fixes verified test-first.
- [x] Push reviewed branch, create and attach PR; no release or live dispatch.

Published as [draft PR #18](https://github.com/B3Cognition/prosaic-integration-lab/pull/18).
Offline qualification and independent review are recorded in the verification report.
