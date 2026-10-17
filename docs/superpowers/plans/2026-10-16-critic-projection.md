# Critic Input Projection Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for the user's authorized native follow-up.

**Goal:** Test whether isolating correction input fixes the remaining critic, then run a new bounded comparison.

**Architecture:** Use public RuntimeAdapter(max_attempts=1) around an unmodified Runtime. Only the review-corrector with a valid publicCheck target receives caseId, typed correctionTarget and public recordIndex. Other invocations and missing-evidence corrections remain unchanged. No output substitution; Harness retains full original arguments and validates the real response against fresh evidence.

**Spec:** User request to fix remaining critic; prior verification docs/verification/agent-quality-feedback-2026-10-16.md.

## Constraints and review focus

Same models/profiles, SDK wheels, public schemas, scorer, suite, tool and per-case budgets. Host-generated targets only, no private answer key. Bad feedback must fail closed; missing-record feedback must not project an invented target. Adapter must preserve native tools, scope, cancellation, usage, events and receipts. Bind source to adapter/recovery/comparison identity. Native host adapter workflows are not exportable bundles; do not claim export support.

- [x] Write failing actual HTTP payload regression: projected corrector input omits task/draft/old artifacts, has typed target; full receipt retains original input and usage.
- [x] Implement projection and public adapter binding; test pass-through, malformed/no-target feedback, incorrect response rejection and positive control.
- [x] Full source suite, fresh review, immutable installed candidate, payload audit, fixtures/recovery and smoke.
- [x] Run bounded remaining critic + correct-draft control within current allowance; audit actual usage before any full-rerun budget request.
- [x] Prepare20samples, calculate all remaining request/tool/token headroom and obtain any required explicit extension; execute and prove offline replay. All20 executed;19passed, larger author deadline leaves1 full unknown reservation. See verification record.

Starting18ledgers retain723requests/229tools/707525tokens under765/250/983040; residual42/21/275515. No reset/retry of uncertain usage, SDK edits, fallback, publication or integration. Preserve unrelated changes and all old candidates/evidence.
