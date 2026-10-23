# Durable failure isolation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve uncertain bounded operations across crashes and require explicit recovery without redispatch.

**Architecture:** A private fsynced host journal with process locking surrounds public SDK operations. It reserves each complete case once, fences journal writers on isolation, and records host-authorized recovery without invoking a workflow.

**Tech Stack:** Python 3.12, POSIX locks, public installed Runtime/Harness, pytest.

**Spec:** `docs/superpowers/specs/2026-10-18-durable-failure-isolation.md`

## Global Constraints

- Per case: 4 provider requests / 2 tool calls / 8192 reported tokens / 600 seconds / 512 output tokens per response.
- Ceiling accounting stays 1558 / 637 / 1976623; charged 1509 / 610 / 1835168; 9 unknowns retained.
- Memory and correction remain experimental. No live run or SDK changes.
- New journal is containment within preauthorized reservations, with no refunds.

## Review Focus

- Lost acknowledgement during atomic admission must not permit reuse (subprocess test).
- A stale in-flight worker must not overwrite a recovery decision (token test).
- Changed scope or input must never recover another operation (binding test).
- Unknown counts must never become zero or a successful recovery (count test).
- A known overrun must block unrelated future admission (overrun test).

### Task 1: Durable consumer journal, adoption guide and offline qualification

**Files:**
- Create: `lab_runner/failure_isolation.py`
- Create: `tests/unit/test_failure_isolation.py`
- Create: `tests/functional/test_failure_isolation.py`
- Create: `scripts/failure_isolation_smoke.py`
- Create: `docs/failure-isolation.md`
- Modify: `docs/handoff.md`, `docs/verification/progress.md`, `README.md`

**Interfaces:**
- Consumes: `quality.allowance.private_write/private_directory/counts`, canonical digest/identifier helpers; public correction execution/recovery only in qualification.
- Produces: `FailureIsolation(path, identity=sha256, limits=counts)` with `admit(work_id, binding=sha256) -> writer_token`, `start(work_id, token)`, `complete(work_id, token, actual=counts, evidence_digest=sha256, outcome='completed'|'failed')`, `isolate(work_id, binding=sha256, decision_digest=sha256)`, `recover(work_id, binding=sha256, decision_digest=sha256, actual=counts|None, evidence_digest=sha256|None, outcome='completed'|'failed'|'unknown')`, `inspect(work_id)`, `status()`.

- [x] Write behavioral tests: crash at admitted/started/completed boundaries, duplicate and concurrent admission, revoked token, drift, invalid counts, deadline, unknown recovery and overrun. Assert 4/2/8192 retained per item; a second case fits only inside 8/4/16384 containment limits.
- [x] Run focused tests; expect missing journal assertion failure.
- [x] Implement minimal journal and validation; no dispatcher, executor callbacks, retries or mutable SDK state.
- [x] Run focused tests; expect all pass. Add both-wire public SDK isolation/recovery qualification and installed-package smoke; watch missing smoke fail before implementation.
- [x] Write adoption guide with trusted-host authority and local durability limits; run full source suite, build and installed smoke with recovery network denied.
- [x] Commit implementation; record qualification and one fresh final review. Fix material findings test-first in one pass, rerun full suite. Preserve evidence and historical accounting unchanged.
