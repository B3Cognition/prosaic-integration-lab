# Review contract corrections implementation plan

> **For agentic workers:** Use superpowers:executing-plans for native execution.

**Goal:** Correct the critic's output contract and restore canonical SUE prompt
guidance, then repeat the authorized Qwen comparison without relaxing validation.

**Architecture:** Lab owns stage-specific instructions and evaluation. The
standalone pure SUE engine, Runtime execution and Harness acceptance remain
unchanged. Preserve requirements_review_v1 and the failed-run evidence; expose
the corrected critic through requirements_review_v2. Both use identical frozen
cases, direct-review prompts, final schemas, scorer, retries and limits.

**Tech stack:** Python 3.12, pinned installed public SDKs, standalone SUE 0.1.0.

**Spec:** The user's explicit fix-and-rerun request and
`docs/verification/sue-qwen-live-2026-10-24.md`.

## Constraints and review focus

- Memory and SUE stay independently disabled by default; no SOAR/model runners.
- Canonical instructions are prompt data, not a copied validator/state machine.
- Pin the canonical source hash; differential-test the exact instruction blocks.
- Critic receives frozen sources and issue definitions, its own feedback schema,
  and no competing final-stage schema/instructions. Final prompts remain exact.
- Invalid/missing fields, raw JSON fences, false quotes, future-turn references,
  unknown usage, stale identity and forged provenance remain rejected.
- Keep old candidate wheels/environments, source locks, ledgers and evidence.
- No time-limit increase, prompt tuning after observing new scores, push/release.

## Execution

1. Add failing critic wire-projection and canonical SUE guidance regressions;
   include negative acceptance cases from the failed pilot. Retain RED output.
2. Add versioned canonical prompt data and bind its digest into the SUE adapter
   identity/projection. Add v2's public workflow builder and deterministic critic
   projection using RuntimeAdapter; do not edit v1's locked files.
3. Run focused GREEN checks, existing SUE/v1/negative/recovery tests and the full
   enabled Lab suite. Build direct/rebuilt installed candidates, check hashes
   and run the existing installed PostgreSQL 16/18 lanes without skips.
4. Freeze a fresh v2 live plan/operator. Reuse the Qwen 7B model, common limits,
   task order and thinking-disabled profile; one 24-cell trial. Retain actual
   HTTP exchanges, Runtime/Harness receipts, unknown reservations and replay.
5. Audit the final diff, unchanged validators/defaults/v1 locks and prior
   manifests. Preserve a new evidence archive and report results and limits.

The user authorized native execution and a fresh Qwen rerun. This plan records
the implementation choices; it does not create publication authority.
