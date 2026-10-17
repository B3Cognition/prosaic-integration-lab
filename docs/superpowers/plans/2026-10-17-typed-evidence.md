# Typed Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add provider-independent typed evidence and measure its separate effect on a fresh memory comparison.

**Architecture:** A pure bounded policy/index/fetched-record classifier feeds an opt-in native tool envelope. Existing validators retain decision authority. Raw/typed schedules share cases, corpus, profiles and limits, with immutable format-specific evidence.

**Tech Stack:** Python 3.12, public Core0.4.1/Runtime0.9.6/Harness0.9.0, pytest/jsonschema, existing native synthetic providers.

**Spec:** docs/superpowers/specs/2026-10-17-typed-evidence-design.md

## Global Constraints

- No Core/Runtime/Harness engine changes or new vendor-specific tuning.
- Raw lookup default and existing serialized/on-disk contracts remain compatible.
- Both formats retain all readable IDs and fetched raw decoys; no private answer/decision computation in summaries.
- Per case:4 requests/2 tools/8192 reported tokens/600s; existing profiles/output caps unchanged.
- Development freeze precedes fresh case authoring; all old usage/unknown reservations remain charged.
- Native execution, one final fresh-context review, no implementer delegation; no push/release implied.

## Review Focus

- Complete index versus missing fetch: unread evidence must not become absent.
- Partial index, conflicting identities and latest ties fail closed.
- Changed envelope/format must invalidate replay before retrieval/provider dispatch.
- Retained raw decoys and wrong decisions cannot be silently filtered or repaired.
- Factorial conditions must share exact frozen cases/corpus/settings and remain separately identifiable.

### Task 1: Pure evidence contract

**Files:** Create `lab_runner/memory/evidence.py`, `lab_runner/memory/data/evidence-summary.schema.json`, `tests/unit/test_typed_evidence.py`; update public build inventory.

**Interfaces:** `build_summary(*, authority, required_facts, record_index, records, index_complete)` returns bounded JSON; `summarize_lookup(request, records)` is the rollout public-grammar adapter.

- [ ] Write tests for absent/unread/verified, authority-before-revision, stale/observer retention, arbitrary renamed labels/three required facts, empty complete index, deterministic order, duplicate/tie/mismatch/nonfinite/partial-index rejection, no decisions/private data, schema validation.
- [ ] Run focused tests and observe missing-module RED; implement the pure contract and schema; run GREEN.
- [ ] Record checks and commit only Task1 files.

### Task 2: Native integration, provenance and recovery

**Files:** Modify memory execution/scoring/runner/context or contracts as needed, CLI, fixture; add focused unit/functional tests.

**Interfaces:** `evidence_format='raw'|'typed'` flows through preflight/execute/freeze/materials/execute_case/recover_case and identity. `--typed-evidence` opts in. Typed journal/result hashes and tool version are independently reconstructed by scoring.

- [ ] Add failing tests for typed native wire/schema, mode-bound identity, raw compatibility, summary tamper rejection, cross-format recovery blocked before dispatch, receipt-only replay and wrong-decision rejection.
- [ ] Implement minimal plumbing with unchanged raw default and limits; retain current public decision validation.
- [ ] Add a scripted provider scenario that consumes/validates the actual public summary, rather than using private expected answers for its reply.
- [ ] Run focused memory/CLI/recovery suites, then full suite; commit the independently tested change.

### Task 3: Freeze and qualify fresh factorial study

**Files:** Synthetic corpus/sources, fresh case bundle, study/audit scripts and verification documentation.

**Interfaces:** Existing runner schedules48 per format; two separately bound formats form96 samples with paired aggregate analysis. Exact installed candidate/SDK digests and corpus/case hashes bind both.

- [ ] Add new synthetic history topics and test old entries retained; finish code/prose qualification before development freeze.
- [ ] Freeze implementation/corpus, then author twelve fresh cases; freeze evaluation without subsequent tuning.
- [ ] Build/install immutable wheel/source artifacts in fresh environments; run all96 fixture samples and provider-denied replay; verify package payloads and audit result hashes.
- [ ] Fresh whole-change review, one bounded correction pass if needed; restart freeze/evaluation if implementation tuning occurs after case exposure.
- [ ] Compute all historic usage and worst-case reservations; request only necessary numerical live extension after offline preparation.

### Task 4: Live comparison and findings

**Files:** Private controlled study output; aggregate-only report/docs.

**Interfaces:** Approved cumulative allowance, unchanged models/settings; raw/typed memory arms, alternating format order by independently prepared case groups where runner scheduling permits.

- [ ] Dispatch only after allowance approval, preserve unknowns and all prior reservations, no hidden probes/retries.
- [ ] Audit all receipts/current-source joins/scoring/usage and socket-denied byte-identical replay.
- [ ] Explain observed summary versus memory effects and remaining roadmap gaps; do not label model improvement or provider portability beyond the evidence.
