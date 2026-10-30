# Balanced Memory Comparison Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans; one final fresh-context review.

**Goal:** Remove the literal-phrase query confound and query-order open starvation, then qualify strict Qwen execution before another live comparison.

**Architecture:** Preserve the existing `literal-first-v1` behavior and introduce explicitly frozen `terms-round-robin-v2`. Public installed Runtime/Harness execute unchanged strict answer/critic contracts. Host-only query normalization and selection never read grading keys. A new private study preserves all old evidence and reservations.

**Tech stack:** Existing Python Lab, rg, public Castle adapter/worker, qualified constrained-JSON Runtime candidate.

**Spec:** Existing `docs/superpowers/specs/2026-10-26-memory-benchmark-design.md`, with the maintainer's follow-up authorization after the failed 100-question attempt.

## Constraints and decisions

- Keep memory/SUE defaults off, SUE/SOAR separate, raw FTS rank and recency off, dense off, no publication/push.
- Preserve source scope/provenance, exact offsets, strict schema/scorer, 32 KiB display, five opens and five raw Castle hits/query.
- New policy extracts unique Unicode alphanumeric words in first-occurrence order, no stop-word/key-dependent selection. Reject punctuation-only queries before freezing. File search uses case-insensitive whole-word literal OR; rank up to five matching line anchors/query by descending distinct query-word count, then path/line. Castle receives the same normalized word string with native FTS token-OR intent; analyzer/ranking differences remain explicit.
- New policy uses round-robin visible per-query candidates, preserving within-query ordering and deduplicating equivalent file path/line or Castle record identities. No extra model tools, queries or source grants.
- Existing dataset schema stays compatible; only explicit new-policy freezes add `retrievalPolicy`. Old freezes/environments/archives are untouched.
- Qwen preflight uses the unchanged strict answer and canonical-derived critic/repair, with finite separate allowance, no automatic retries, and stop on unknown. Start a new 100-question live run only if preflight has accepted semantically correct answers and revisions. A failed preflight remains a failure, not permission to weaken validation or release old reservations.

## Task 1 — Fair keyword interpretation

Files: new `lab_runner/memory_benchmark/retrieval_policy.py`; modify `dataset.py`, `__main__.py`, `retrieval.py`; new focused unit tests.

- [x] RED: multiword matches split across source words become eligible only under the new policy; whole-word boundaries and Unicode are respected; term-overlap ordering is deterministic; punctuation-only new-policy freeze rejects before output.
- [x] Implement explicit policy identity, normalized keywords and bounded top-five file candidates without changing legacy behavior.
- [x] GREEN: targeted policy/dataset/CLI/retrieval tests; retain failed and successful logs.

## Task 2 — Balanced opens

Files: `retrieval_policy.py`, `retrieval.py`, unit/candidate tests.

- [x] RED: first query has five hits, second has the relevant top hit; new selection opens both and retains rank within each query. Duplicate record/path-line candidates do not consume repeated slots. Expanded reuses exact raw results/selections.
- [x] Implement round-robin visible candidates with identical five-open cap in file/raw/expanded arms; legacy remains first-query-first.
- [x] GREEN: scope/provenance/snapshot/tamper/recovery regressions remain intact.

## Task 3 — Installed qualification and separate study

- [x] Full SDK-only suite: 2,142 passed + 73 subtests; installed candidate: 45 passed + 36 subtests. All 209 Python payloads match source/wheel/sdist/install. Fresh review findings reproduced and resolved; default and zero-call checks pass.
- [x] Freeze unchanged 100 questions/key/sources with explicit new policy/code identity. All 300 real retrieval captures and 6,169 displayed spans independently verified. All-reference visibility: file 87/90, raw Castle 60/90, expanded 90/90 supported cases; these are not answer scores.
- [x] Freeze three-case/nine-sample strict Qwen preflight. First request timed out at 60.35 seconds; unknown usage retained, eight samples blocked. Independent assessment confirms zero accepted answers/reviews and no critic calls. Semantic quality remains unmeasured.
- [x] Preflight failed: do not launch the 100-question model batch. Preserve the full separate three-request / 98,304-token unknown reservation; no retries or settlement.
- [x] Document results/limits and collect new private evidence for a checksummed archive. Old 11 archive copies / 31,547 indexed files and all three existing unknown reservations reverified unchanged. No publication or push. Archive seal/manifest verification is recorded alongside the private comparison report.
