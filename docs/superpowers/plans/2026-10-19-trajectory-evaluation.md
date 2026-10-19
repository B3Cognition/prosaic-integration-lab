# Trajectory evaluation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let consumers correlate safe observations and independently verified trajectory outcomes offline.

**Architecture:** One bounded consumer collector projects public SDK observations and trusted host annotations into a private report. A separate parcel-domain fixture demonstrates actual public Harness/Runtime integration and network-denied inspection.

**Tech Stack:** Python3.12, public Runtime0.9.7/Harness0.9.4, standard library, pytest.

**Spec:** `docs/superpowers/specs/2026-10-19-trajectory-evaluation.md`

## Global Constraints

- Per-case4requests/2tools/8192tokens/600seconds/output512.
- Ceilings1558/637/1976623; charges1509/610/1835168; nine unknowns retained.
- No live requests, SDK source changes, model tuning, vendor dependency or dispatch during inspection.
- Memory/correction and the new consumer blueprint stay experimental.

## Review Focus

- Forged completion must never override independently verified failed/incomplete outcomes.
- Foreign/duplicate/missing records must show monitoring limitations without changing execution authority.
- Unknown usage remains null; telemetry counts never become billed or measured usage.
- Secrets in identifiers/labels/unknown fields must not appear in exported reports.
- Inspection of saved output must deny network and avoid workflow execution.

### Task 1: Safe collector and second-domain public SDK qualification

**Files:** Create `lab_runner/trajectory.py`, `lab_runner/trajectory_fixture.py`, `scripts/trajectory_smoke.py`, `tests/unit/test_trajectory.py`, `tests/functional/test_trajectory.py`, `docs/trajectory-evaluation.md`, qualification; update README, handoff/progress/status and version.

**Interfaces:** `Trajectory(run_id, binding_digest, key)` with `observe(record)`, `annotate(step_id, kind, status, evidence_digest)`, `report(assessment)`; closed `assessment` contains bindingDigest/status/categories/evidenceDigest/usage. `save_report(path, report)` and `read_report(path, binding_digest)` are private validated offline operations. Fixture `qualify(output, provider, scenario)` exercises six declared scenarios under unchanged caps.

- [x] Write unit regressions for correlation, gap/loss detection, closed privacy projection, outcome separation, unknown usage and report corruption/binding/shape. Watch missing-feature RED; implement collector and strict report validation; focused GREEN.
- [x] Write functional regressions for six parcel cases on both wires plus subprocess installed replay. Watch missing-fixture RED, implement public SDK example; assert host decision/evidence, actual lookup effects, diagnostic attribution, measured usage, persistent approval and zero-call recovery.
- [x] Document adoption/authority boundaries and commands; run full source suite, build fresh artifacts and isolated installed smoke, reconcile package payloads and run public wheel/rebuilt-sdist adoption. Expected: all tests/12lanes/replays pass; zero live requests and limits unchanged.
- [x] Commit; record task-done with focused suite; run one fresh final branch review. Fix material findings in one watched RED→GREEN pass and repeat whole suite/package checks. Preserve evidence, then retain local branch for later PR/CI.
