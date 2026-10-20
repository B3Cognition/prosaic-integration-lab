# Sandboxed tools implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Demonstrate adoptable required-mode CLI confinement, honest unsupported controls and evidence-grounded recovery.

**Architecture:** A consumer admission helper constrains public SDK configuration; separate bounded canaries and scripted providers qualify the existing execution boundary. Host approval covers a frozen prepared invocation, and public TurnEvidence feeds the existing safe trajectory report.

**Tech Stack:** Python3.12, public Runtime0.9.7/Harness0.9.4, Seatbelt/Bubblewrap, stdlib sockets/process inspection, pytest.

**Spec:** `docs/superpowers/specs/2026-10-20-sandboxed-tools.md`

## Global Constraints

- Keep4requests/2tools/8192tokens/600seconds/output512per case.
- Ceilings1558/637/1976623, charged1509/610/1835168, nine unknown reservations unchanged.
- No live requests, SDK source changes, fallback, model tuning or general hostile-code/resource-DoS certification.
- Memory/correction and this blueprint stay experimental.

## Review Focus

- Unsafe config/unsupported controls must deny before probes or provider dispatch.
- Positive controls and owned witnesses must prove CLI execution rather than trusting model output.
- Approval must bind the whole invocation and cannot be renewed during receipt-only inspection.
- Cleanup must target only owned canaries and distinguish same-group from detached processes.
- Backend absence must block/fail qualification; no skipped security gate or off-mode fallback.

### Task 1: Admission, bounded canaries and public SDK qualification

**Files:** Create `lab_runner/sandboxed_tools.py`, `lab_runner/sandbox_canary.py`, `lab_runner/sandbox_fixture.py`, `scripts/sandboxed_tools_smoke.py`, unit/functional tests and adoption/qualification docs. Update README/handoff/status/progress/version and required CI with narrowly scoped Bubblewrap setup.

**Interfaces:** `admit_sandbox(config, policy, *, workspace, manifest, required_controls)` returns closed admitted/reason/unsupportedControls; `qualify(output, provider, scenario)` runs one fresh synthetic case, returning a sanitized proof with public TurnEvidence-derived checks; `replay(root)` reads verified saved receipts/reports only. Standalone canary accepts fixed host arguments and returns bounded private JSON or intentionally exceeds a declared limit.

- [x] Write admission tests for off mode, grants/sockets/env/runtime roots, explicit controls and manifest bounds. Watch missing feature RED, implement minimal helper and focused GREEN.
- [x] Write actual both-wire confinement/approval/limit/replay tests and canary controls; watch missing feature RED. Implement using public prepare_turn/turn/evidence, owned socket/process witnesses and safe trajectories. Expected:12declared scenarios qualify, refused cases dispatch0; actual backend failure is not a pass.
- [x] Add operational Linux CI setup/gate and guide with unsupported-control boundaries. Run full suite, fresh wheel/sdist and isolated installed qualification/payload audit/public consumer adoption. Expected: all supported local operational cases pass; no live calls, skips, fallback or changed limits.
- [x] Commit and record task-done; run one fresh final review, fix material findings with watched RED→GREEN tests in one pass and repeat appropriate whole-suite/package qualification. Preserve evidence and retain local branch for later PR/CI.
