# Public Evidence Checks Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for native implementation and a fresh final review.

**Goal:** Enforce explicit evidence completeness and draft-field comparisons, then rerun the bounded benchmark.

**Architecture:** Consumer-owned, deterministic validators parse the supported public task grammar and inspect only the current attempt's fetched records and public index. They return a typed completeness/condition assessment and field differences as retry feedback. The model still produces every accepted answer/review; validators never replace model output. The private expected answer is used only by the unchanged scorer.

**Tech Stack:** Python3.12, installed Runtime0.9.3+finalize.4/Harness0.8.2 public Validator API.

**Spec:** Approved architecture discussion in docs/verification/agent-quality-decisions-2026-10-16.md and the user's explicit implementation authorization.

## Global Constraints

Keep the original dataset, public schemas, scorer, SDK train, model settings, one lookup round and two attempts per agent. Fail closed for unsupported public task grammar, ambiguous latest revisions, missing current evidence and malformed records. Do not parse instructions embedded in record text. Preserve all prior reports/allowances, unrelated changes and released defaults. This is a new validated workflow track, not a prose-only raw-model comparison.

## Review Focus

- Public thresholds/fact names must be parsed, never copied from the private expected answer.
- A known current record omitted from the lookup cannot masquerade as a truly absent fact.
- Stale revisions and observer text cannot supply required evidence.
- Correct reject/insufficient drafts must pass; every wrong draft field must be listed.
- Retry feedback must use the current attempt and survive saved-receipt recovery.

## Task1: Public assessment and validation

Files: new lab_runner/quality/checks.py; modify execution.py, runner.py, agent prose; unit and functional quality tests.
Interface: assess_evidence(request,records) returns a typed public-derived table and clean answer; compare_fields(answer,draft) returns decision/facts/citations differences. Validator callbacks return issue strings only and inspect no private assertions.

- [x] Write tests for missing facts/current records, revision authority, changed public thresholds/names, field-set semantics, correct drafts and poisoned private expected answers; watch failures.
- [x] Implement closed grammar parser/assessment/field comparison and wire answer/review validators with current-attempt evidence and bounded feedback.
- [x] Validate missed-critic retry and wrong-decision retry through the real fixture HTTP provider; verify recovery and unchanged scoring.
- [x] Bind validator source/registration to workflow identity; full1051tests pass; fresh review findings reproduced and fixed.

## Task2: Artifact qualification and live comparison

- [x] Build immutable candidate0.5.0+checks.1 with unchanged SDK manifest; installed smoke,10fixtures,3recovery probes and3semantic/control trajectories pass.
- [x] Compute full worst-case reservation headroom. Starting retained597/166/554938 left7/74/428102 under604/240/983040;20sample8request/4tool schedule required160requests/80tools. Explicit153request/6tool increase approved before dispatch.
- [x] Receive explicit cumulative757request/246tool approval (token ceiling unchanged983040); preflight passed full20sample reservation headroom; live session94206 started.
- [x] Run fresh20sample schedule; all usage known, smaller8/10/larger10/10. Receipts/allowances preserved; all20rescored and provider-denied replay byte-identical. Remaining model failures reported without reruns or relabeling.

Ruling: Native execution and architecture are already explicitly authorized; do not add another design approval gate. Preserve work uncommitted because the branch contains unrelated copied changes. No release, merge or push.
