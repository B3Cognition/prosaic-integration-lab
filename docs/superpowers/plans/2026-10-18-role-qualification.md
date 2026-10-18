# Consumer role qualification implementation plan

> **For agentic workers:** Use superpowers:executing-plans; native already selected.

**Goal:** Adoptable provider-neutral role qualification and grounded diagnostics.
**Architecture:** Pure generic policy helpers plus a separate rollout adapter;
public installed SDKs remain unchanged. No transport or prompt tuning.
**Tech Stack:** Python3.12, jsonschema, existing Lab fixtures/build tools.
**Spec:** `docs/superpowers/specs/2026-10-18-role-qualification-design.md`.

## Global Constraints

- No live calls; existing per-case4/2/8192/600/output512 and cumulative ceilings
  1524/625/1976623 unchanged; preserve all evidence and8unknown reservations.
- No SDK edits, provider/model branches, retries, repair, push or release.
- Keep old installed environments immutable; build a new opt-in Lab candidate.

## Review Focus

- Synthetic or altered reports cannot qualify live use; domain claims aren't authorization.
- Schema, profile, policies, suite, adapter and budgets invalidate prior qualification.
- Missing scenarios, duplicate identities, abstention and unknown usage fail closed.
- Raw expected values and hostile schema references never escape diagnostics/resolve remotely.
- Journal corruption and wrong invocation cannot become trusted worker/critic evidence.

### Task 1: Generic consumer qualification primitives

**Files:** `lab_runner/role_qualification.py`, `tests/unit/test_role_qualification.py`.
**Interfaces:** `FieldCheck`, `assess_output`, `qualification_binding`,
`qualification_report`, `require_qualification`; all pure/no dispatch.

- [ ] Write failing tests: alternate-domain checks and sanitized diagnostics,
  malformed JSON/schema, abstention/unknown/budget failure, remote refs,
  complete coverage, changed binding, synthetic/stale/tampered reports.
- [ ] Run focused tests RED; implement minimal APIs; run GREEN and commit.

### Task 2: Scoped diagnostics adapter and adoptable offline blueprint

**Files:** `lab_runner/handoffs/diagnostics.py`,
`tests/functional/test_role_diagnostics.py`, `scripts/role_qualification_smoke.py`,
`docs/role-qualification.md`, version/docs/verification/handoff.
**Interfaces:** `diagnose_direct(case,evidence)` consumes unchanged direct-v2
receipts; uses Task1 field checks; never changes scoring, arguments or execution.

- [ ] Write/observe RED for complete worker/critic diagnostics, partial warnings,
  invalid output and scoped evidence corruption; implement and run GREEN.
- [ ] Add an installed-wheel synthetic smoke using both wire fixtures and a
  second domain's contract; demonstrate offline report cannot admit live use.
- [ ] Run full source suite, build/audit/install in fresh environment, smoke.
- [ ] One fresh whole-change review; fix material findings in one RED/GREEN pass.
- [ ] Record zero live calls and unchanged ledgers, adoption boundaries and
  limitations; commit locally and preserve branch/evidence.
