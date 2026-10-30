# Compact memory handoff implementation plan

> **For agentic workers:** Use superpowers:executing-plans; one fresh final review.

**Goal:** Remove repeated quotation/provenance text from model arguments while retaining exact canonical validation and raw failure evidence.

**Architecture:** Explicitly freeze `compact-citations-v1` as an optional generation profile; `canonical-v1` remains the default. Keep the full immutable host ReviewPacket. Send unchanged displayed text once, address-only paragraph and citation indexes, and compact draft references. Resolve model IDs deterministically to canonical evidence/citations, then run the unchanged ANSWER_SCHEMA and grounding validator before Harness accepts a stage. Receipts/checkpoints retain original wire responses; result candidates contain canonical resolved answers. Runtime executes, Harness owns state, Lab owns projection and validation. No Castle/Runtime/Harness source changes.

**Tech stack:** Python Lab, installed constrained-JSON Runtime candidate, public Harness API.

**Spec:** Maintainer-approved follow-up to `docs/verification/memory-benchmark-balanced-2026-10-26.md`: smaller model-facing packet, deterministic citation addressing, strict final validation and semantic scorer.

## Global constraints

- Memory and SUE defaults off; SOAR separate; no push/publication; prior archives and all four unknown reservations unchanged.
- Source text, retrieval queries/ranks/opens/context budgets and scope unchanged; no grading keys in model inputs.
- Legacy profile preserves its request/schema/validation behavior. New profile is frozen, never a run-time override.
- Unchanged canonical answer schema, critic schema/composition, 16 KiB canonical output, 4,096 output tokens, 60-second call deadline, three-call sample allowance. No retries or usage settlement for unknown calls.
- No text repair/fuzzy addressing: unknown IDs, extra fields, wrong references, cross-body quotes, unsafe preview citations and altered scope fail closed.

## Review focus

Unicode/CRLF addresses; preview versus whole-record citation authority; duplicate paragraphs and aliases; compact checkpoints versus canonical result tampering; empty evidence/abstention and unresolved resumes. Each has targeted tests below.

## Task 1 — Host-owned transport and strict resolution

Files: new `lab_runner/memory_benchmark/generation.py`, `tests/unit/test_memory_benchmark_compact.py`.

- [x] RED: exact-display, Unicode/CRLF, file/Castle roundtrip, preview authority, invalid IDs/fields/links/scope and empty-evidence tests fail before implementation.
- [x] Implement projection/schema/exact resolution and canonical draft encoding; unchanged final validation required before acceptance.
- [x] GREEN targeted tests, retaining RED logs.

## Task 2 — Frozen selection and actual SDK workflow

Files: `dataset.py`, `__main__.py`, `workflow.py`, `completeness_profile.py`, `runner.py`, fixture; candidate tests.

- [x] RED: freeze/profile arguments absent; SDK workflow integration absent. Canonical-result tamper rejected by replay-stage checker; resume and raw-receipt/unknown retention tested.
- [x] Integrate frozen profile, requests, schema, validators, canonical extraction and wire-to-canonical replay binding; legacy branches preserved.
- [x] GREEN: full2,159+73subtests; installed67+36subtests;210Python payloads match; defaults execute nothing. Fresh-review offline SDK import finding reproduced RED and fixed.

## Task 3 — Isolated Qwen qualification and evidence

- [x] Same three known cases / nine samples, sources/key/scorer/retrieval policy and allowance precommitted; artifacts/code pinned before inference. Old13copies/32,539files/fourreservations verified.
- [x] All300 old captures/6,169body spans preserve exact displays/addresses; argument bytes fall53.6%/58.0%/59.4%. Qwen first request still times out60.24s, one unknown/eightblocked, zeroaccepted/criticcalls. Normal replay confirms outcome; semantic assessment has no accepted output to grade.
- [x] Preflight fails: full100 model batch not launched; new3request/98,304token reservation held, all four older reservations unchanged.
- [x] Fresh final review/fix verification, docs and private archive collection complete; seal/manifest verification recorded with the study. No push/publication; all failures and earlier artifacts retained.
