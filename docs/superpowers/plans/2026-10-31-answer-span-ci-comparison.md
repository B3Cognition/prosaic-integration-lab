# Answer-span CI and comparison preparation plan

> **For agentic workers:** Use superpowers:executing-plans inline. The user authorized execution, a draft PR and CI qualification; no additional plan approval is required. Preserve one final independent review if new qualification code is added.

**Goal:** Make the pushed audit reproducible in public CI and prepare a private,
bounded comparison on existing frozen drafts without issuing model requests.

**Architecture:** Lab remains a consumer of installed public APIs. Released
regressions and the explicitly selected Runtime candidate run separately, with
complete collection coverage and no skipped assertions. Candidate source is
pinned and payload-verified. Private study inputs, labels, receipts and historical
reservations never enter public CI or Git.

**Tech stack:** Python 3.12, pinned GitHub Actions, verified wheels/source,
Linux AMD64/ARM64 synthetic fixtures, existing strict scorer and frozen answers.

**Spec:** `docs/answer-span-audit.md`,
`docs/verification/answer-span-audit-2026-10-30.md` and the previously approved
private `endpoint-audit-design-20261027/answer-span-audit-design.md`.

## Global constraints

- Memory and SUE stay independently disabled by default; SUE/SOAR stay separate.
- Keep canonical critic, scorer, provenance, exact spans and all size limits strict.
- Preserve every historical archive and held reservation; never retry old unknowns.
- Do not issue live inference, change serving, repair answers, merge the PR or
  publish packages to PyPI. The user authorized draft PR creation and pushes
  needed for its exact-source CI inputs.
- New audit execution retains two calls, 120 seconds per call, 270 seconds total,
  65536 tokens reserved, 4096 output tokens and 16384 output bytes per stage,
  zero tools/retries. Preparation grants no live execution authorization.

## Review focus

1. Every test removed from the released profile must run in the candidate profile;
   classification must fail closed on unassigned files rather than silently skip.
2. Candidate source, versions and installed payloads must match the qualified
   artifact; moving branches and same-version substitutions confer no trust.
3. Raw private study material, keys and historical operator evidence must never
   be uploaded to CI artifacts or the PR.
4. Aliased identical drafts are not independent samples; failed/unavailable
   originals retain their fixed denominator and provenance.
5. Study preparation must not dispatch, settle reservations, weaken labels or
   expose scoring keys in auditor arguments.

## Task 1: Draft PR and reproducible CI

**Files:** `.github/workflows/`, `scripts/`, `dependencies/`, regression tests,
and a new verification record. Keep original historical reports unchanged.

- [ ] Open and attach a draft PR against current main with existing verification
  and explicit unqualified gates. Inspect divergence/conflicts before integration.
- [ ] Make the already tested immutable Runtime candidate source available for
  CI without modifying released pins or publishing a package; verify its tree
  and package payloads against the sealed wheel.
- [ ] Reconcile current main as needed while preserving the tested memory/audit
  source and all unrelated upstream behavior.
- [ ] Watch failing tests for qualification helpers before implementation. Add
  released/candidate test-profile coverage checks and exact-wheel verification.
- [ ] Add a synthetic installed-wheel/source-rebuild audit lane on AMD64/ARM64;
  use pinned actions and locked dependencies, no credentials or live corpus.
- [ ] Push, inspect all PR checks and fix failures at their cause without weakened
  assertions. Preserve failed CI logs and receipts; report any genuine remaining
  external blocker honestly.

## Task 2: Prepare the small comparison

**Files:** Private new study directory, preparation helper/tests if needed, and
public protocol/verification documentation containing no corpus or raw outputs.

- [ ] Verify original archives before reading frozen drafts. Select the six
  declared questions, both retrieval arms and all three saved profiles from
  the controlled study. Freeze every scheduled cell and report missing/invalid
  outputs as such; do not regenerate originals.
- [ ] Freeze exact unique audit packets and map repeated aliases separately.
  Prepare correct and fault-injected controls with labels outside model inputs.
- [ ] Prepare disputed q022 source/judgment material for independent adjudication;
  preserve original labels and leave unresolved decisions visibly pending.
- [ ] Predeclare repeats, order seed, exact call/token ceilings, serving preflight,
  unknown-usage stop rules and independent semantic scoring requirements.
- [ ] Verify credential-free dry preparation dispatches zero calls, leaves all
  inputs/reservations untouched and keeps memory/SUE off. Live status remains
  not-authorized/not-started until the declared gates are satisfied.

## Task 3: Verification, evidence and handoff

- [ ] Run appropriate local regressions, builds and installed fixtures; obtain
  the fresh final review and fix substantive findings with watched regressions.
- [ ] Record exact CI runs, source identity, architecture and limitations.
- [ ] Preserve a new sealed private evidence archive and the prepared comparison;
  reverify old archive/reservation hashes. Commit and push authorized changes,
  leave the PR draft, and report the next live-comparison gate.
