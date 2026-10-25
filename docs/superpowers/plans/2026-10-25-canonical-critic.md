# Canonical Critic Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, then one fresh whole-change review.

**Goal:** Protect critic/author canonical output and qualify clean/citation fixes.
**Architecture:** Explicit consumer v5 wraps existing v3 composition. Harness owns
accepted state; Runtime owns generation; SUE candidates cannot promote themselves.
**Tech Stack:** Python3.12 and the already qualified installed candidate SDKs.
**Spec:** ../specs/2026-10-25-canonical-critic-design.md

## Global constraints

Strict final schema, scorer, source hashes, categories and old modes unchanged.
Defaults off. Public SDK APIs only; no output repair, SDK patch or old-evidence edit.

## Review focus

- Advice/foreign artifacts must fail before either canonical dispatch.
- Forged critic bindings or receipts cannot become a canonical capture.
- Clean results still require citations; grammar is not a semantic validator.
- Line addresses preserve exact source bytes, hashes and instruction boundaries.
- Advisory failure/resume must preserve canonical output and paid usage evidence.

## Task 1 — Protected critic composition and generation fixes

Files: new lab_runner/requirements_review_v5/{__init__,workflow}.py; additive
from_critic_harness method in requirements_review_v4/protection.py; new
tests/requirements_review_v5/test_canonical.py.

Consumes publicTask and existing v3 artifacts/schemas; produces
build_canonical_workflow(config,limits=None), project_canonical, source_lines,
candidate_messages and IndependentReview.from_critic_harness(task,harness).

- [x] Write/watch failing tests for critic→final binding/capture, no-advice scopes,
  strict schema/provenance, numbered CRLF/multiple sources and candidate isolation.
- [x] Implement v5 preserving v3 topology, unchanged schemas and bounded retries.
  Add only case-neutral evidence guidance, source addresses and public grammar.
- [x] Verify real public SDK fixture calls, invalid attempts, durable recovery and
  zero-call resume; reject forged binding/output/input and changed source identity.
- [x] Run old/new focused tests and full default pytest suite; commit locally.

## Task 2 — Frozen installed comparison

Scratch: /private/tmp/prosaic-sue-canonical-critic-20261025.

- [x] Build/rebuild wheel/sdist, prove source and installed payload identity in a
  new environment without modifying any previous wheel/environment.
- [x] Adapt prior schedule to new canonical critic vs unchanged v3 control; test
  fixtures, dependency reuse, grammar/wire joins, unknown and aggregate limits.
- [x] Review before live dispatch, freeze all measured inputs/scripts and prior
  evidence, then run exactly the same Qwen/scorer conditions serially.
- [x] Offline audit receipts, scopes, raw attempts, immutable finals and usage;
  report failed outcomes without retrying/tuning after seeing live results.

## Task 3 — Evidence and disposition

- [x] Seal a new archive and reverify all historic evidence and unknown reservation.
- [x] Record tests, actual quality/cost, clean/citation results, remaining failures
  and controlled-comparison limitations; update handoff and commit locally.

User explicitly requested implementation and rerun; native execution continues
without another design approval. Any measured semantic failure stays evidence,
not a reason to relax assertions or silently change the frozen run.

Execution status: Tasks1–3 and the necessary second frozen qualification below
are mechanically complete. Completed checkboxes record implementation and measurement;
measured semantic acceptance remains FAILED, not waived. Both runs and all
failed outcomes are sealed. See ../../verification/sue-canonical-critic-2026-10-25.md.

## Necessary second frozen qualification

The first complete run exposed a real input/response-limit mismatch in raw advice
preparation (six zero-call failures), persistent absence-statement-only citations,
and spurious contradictions/ordinary-connective findings. Preserve this run and
its original audit failure; reconcile preparation failures with separate offline
auditors rather than editing the frozen scripts.

- [x] Watch a >16 KB, <256 KB raw-handoff regression fail, then fix decoding to
  the existing input ceiling and retain rejection above 256 KB after composition.
- [x] Version the opt-in profile separately; clarify the existing public rules:
  absence of enforcement is not negation, absence findings cite trigger plus
  supplied gap, logical connectives are not business terms, subjective acceptance
  criteria differ from missing failure behavior. No fixture IDs/answer imports.
- [x] Rerun source/installed checks, full default suite and same frozen 138-cell
  comparison in a fresh directory/environment. Preserve the first profile/wheel,
  all failed outcomes and every prior reservation. Do not tune during either run.

## Protection-only completion after failed semantic qualification

- [x] Preserve exact existing critic native generation in a separate explicit
  build_protected_critic_workflow, with closed inputs and sealed canonical capture.
- [x] Watch missing API tests fail, then verify unchanged native projection,
  original consistency feedback, strict source rejection/retry and zero-call resume.
- [x] Independently review this separate subtask; no material findings. Review
  excludes model quality and historical integrity, which remain separate gates.
- [x] Replay103 recorded native requests exactly;55 final validations show zero
  additional provenance rejections. Replay is network-denied and makes no calls.
- [x] Verify43 installed review tests,4 released-SDK protection tests and2033
  full default tests; direct/sdist-rebuilt payloads and installed sources match.
- [x] Seal final mechanics evidence and update handoff; keep defaults off and
  semantic quality changes experimental. No push or release.
