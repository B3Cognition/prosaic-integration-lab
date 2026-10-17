# Compact Corrective Feedback Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for the already authorized native work.

**Goal:** Test whether a compact public-derived correction target fixes the smaller model's ignored retry feedback, then rerun the benchmark.

**Architecture:** Keep public evidence validation and model-produced receipts. Replace the nested full assessment in retry feedback with a small target JSON and exact mismatched fields. A missing-current-record error has no target, preventing stale evidence reuse. Existing native lookup and retry limits stay unchanged.

**Spec:** User request to fix ignored corrective feedback; prior approved public-checks architecture and docs/verification/agent-quality-public-checks-2026-10-16.md.

## Constraints and review focus

No private answer key, model/SDK/schema/scorer changes or host replacement of model output. Target comes only from public task plus actual current-attempt evidence. Verify target-free missing-record feedback, exact draft diffs, correct-draft control and recovery version binding. This is a hypothesis about feedback representation; do not claim a live fix from fixtures.

- [x] Write failing real-dispatch tests showing retries receive compact targets, not full nested assessments.
- [x] Implement compact feedback and exact mismatched fields; review finding reproduced RED/GREEN; source1055tests pass.
- [x] Qualify immutable feedback.2 with unchanged SDKs, installed fixtures10/10/recovery3/3; targeted missing-01 passes, repair-01 fails, correct-draft control passes. Known12requests/6tools/13757tokens.
- [x] Isolate critic correction in a native conditional check/correction stage; reject bad corrections before author. Dedicated regression RED/GREEN, fresh review clear, final source1057tests pass.
- [x] Qualify immutable feedback.3, installed fixtures10/10/recovery3/3; targeted repair-01 still fails, correct-draft control passes. Known8requests/4tools/8670tokens.
- [x] Offline audit all5diagnostic samples; preserve all17ledgers and candidate archives.
- [x] Prepare fresh20sample feedback.3 study and acyclic workflow reservation proof:96requests/48tools covers every permitted path, including common8request/4tool reservation per sample.
- [x] Receive explicit8request/4tool increase to cumulative765/250/983040; installed preflight passed and full live session21989 started.
- [x] Run fresh20samples and prove offline replay:19/20passed, smaller9/10/larger10/10, all usage known. Persistent repair-01 critic failure remains explicitly unresolved.

Starting retained649requests/192tools/618300tokens under approved757/246/983040. Diagnostics must not reset prior ledgers or consume capacity reserved elsewhere. Keep unrelated work and old evidence intact. No release or integration.

Ruling: compact feedback fixed the missing-fact case but the same critic instructions still ignored its target. Keep that measured reviewer improvement; replace same-agent critic retry with a short dedicated correction artifact behind a public-validator check. This changes workflow context, not model weights/SDKs/scoring, and uses at most the existing four invocations. It still failed the targeted critic case, so preserve it as a measured limitation and make no further speculative edits before the full comparison. Current usage669/202/640727, all new usage known;4prior unknown reservations remain charged.
