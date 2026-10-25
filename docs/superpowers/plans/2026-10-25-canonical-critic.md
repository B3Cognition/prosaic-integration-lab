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

- [ ] Write/watch failing tests for critic→final binding/capture, no-advice scopes,
  strict schema/provenance, numbered CRLF/multiple sources and candidate isolation.
- [ ] Implement v5 preserving v3 topology, unchanged schemas and bounded retries.
  Add only case-neutral evidence guidance, source addresses and public grammar.
- [ ] Verify real public SDK fixture calls, invalid attempts, durable recovery and
  zero-call resume; reject forged binding/output/input and changed source identity.
- [ ] Run old/new focused tests and full default pytest suite; commit locally.

## Task 2 — Frozen installed comparison

Scratch: /private/tmp/prosaic-sue-canonical-critic-20261025.

- [ ] Build/rebuild wheel/sdist, prove source and installed payload identity in a
  new environment without modifying any previous wheel/environment.
- [ ] Adapt prior schedule to new canonical critic vs unchanged v3 control; test
  fixtures, dependency reuse, grammar/wire joins, unknown and aggregate limits.
- [ ] Review before live dispatch, freeze all measured inputs/scripts and prior
  evidence, then run exactly the same Qwen/scorer conditions serially.
- [ ] Offline audit receipts, scopes, raw attempts, immutable finals and usage;
  report failed outcomes without retrying/tuning after seeing live results.

## Task 3 — Evidence and disposition

- [ ] Seal a new archive and reverify all historic evidence and unknown reservation.
- [ ] Record tests, actual quality/cost, clean/citation results, remaining failures
  and controlled-comparison limitations; update handoff and commit locally.

User explicitly requested implementation and rerun; native execution continues
without another design approval. Any measured semantic failure stays evidence,
not a reason to relax assertions or silently change the frozen run.
