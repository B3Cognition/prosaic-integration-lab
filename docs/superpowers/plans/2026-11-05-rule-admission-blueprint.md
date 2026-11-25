# Rule-admission blueprint implementation plan

**Goal:** Provide one small, copyable reference agent that uses Prosaic rule
admission end to end, with acceptance tests, so a team can copy the folder,
rename the agent and register its own guards.

**Architecture:** A separate candidate lane, like the reasoning lane. Core
`9d5a02f` and Runtime PR #16 `65ba15d` are rebuilt reproducibly from exact
commits and pinned by SHA-256 as local offline candidates. The blueprint is a
packaged Python folder holding prose under `.prosaic/`, `guards.py`, `host.py`,
`runtime.yml` and `coverage.py`. The tests drive real conversation turns against
an owned loopback OpenAI-compatible provider.

**Tech stack:** Python 3.12, pytest, public Core, Runtime and Lab APIs, YAML
and Markdown.

## Constraints

- Public installed SDK APIs only, with no private imports or monkey-patching.
- Synthetic data only: invented titles, `CAT-` record ids, EUR fees.
- No live calls or credentials. Draft until prosaic-runtime#16 merges.
- No Harness workflow, because Harness 0.9.7 and earlier reject `ruleViolation`.
- No change to `releases.json`, `releases-reasoning.json` or the Lab version.

## Tasks

- [x] Candidate manifest, hashed build-backend lock and exact-commit wheel
  builder. Check two identical local builds; the payload audit passes.
- [x] Tagged agent and companion prose. Inspection reports all four stages, one
  `prose-only` rule and zero issues.
- [x] Failing acceptance tests for all seven behaviours and candidate
  provenance. Observed 38 failures from the missing blueprint modules before
  implementation.
- [x] Lane module and synthetic provider; custom guard and registry; host
  composition; coverage command; blueprint README.
- [x] Package data and `MANIFEST.in`; wheel and sdist contents checked; the
  installed-wheel run matches the source run.
- [x] `rule-admission.yml` workflow: rebuild candidates in CI, Linux AMD64 and
  ARM64, not required.
- [x] Lane guide, README row, CHANGELOG (Unreleased), handoff, progress and
  verification ledger.
- [x] Adversarial review: a regression test for each defect found, observed
  failing (22 failures) before each fix.
- [x] CI on the draft PR: candidates rebuild byte-identically on Linux AMD64
  and ARM64.
- [x] Re-pin 1 to Runtime `65ba15d`: no blueprint test broke; the cross-file
  settings change is pinned by a new variant.
- [x] PR #45 review comments addressed test-first (34 failures observed before
  the fixes).
- [x] PR #45 re-review addressed test-first (15 failures observed before the
  fixes): required loan-check stages, desk-side limit, fee wording, README
  header, companion frontmatter. The lane has 123 tests, 3 of them strict
  expected failures.
- [ ] A maintainer dispatches `Publish SDK` on the pinned commits, if wanted.
- [ ] Re-pin to released Core and Runtime after #16 merges; see the lane guide.
