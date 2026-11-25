# Latest SDK blueprints and Lab 0.9.8 implementation plan

> **For agentic workers:** Use superpowers:executing-plans for the maintainer-authorized native implementation and release. Steps use checkbox tracking.

**Goal:** Publish Lab 0.9.8 with Runtime 0.9.16, Harness 0.9.11 and runnable blueprints for every feature introduced by this adoption.

**Architecture:** Keep the established public-wheel consumer architecture and closed qualified SDK families. Add copyable host examples under `lab_runner/blueprints`, reuse the released Harness revision-review V1 policy, and extend the existing catalogue-desk fee examples. Each feature gets installed synthetic acceptance and a linked guide. No SDK execution engine is copied or patched.

**Tech Stack:** Python 3.12, public Core 0.5.0 / Runtime 0.9.16 / Harness 0.9.11 wheels, unchanged recorder 0.3.0/store 0.4.1, PostgreSQL 16/18 and Linux AMD64/ARM64.

**Spec:** The maintainer's request to release the latest SDK train and provide blueprints for each added feature; the approved `../specs/2026-10-09-prosaic-integration-lab-design.md` ownership and release boundaries.

## Global constraints

- Preserve old releases, tags, manifests, profiles, freezes, prompts, corpus, scoring and live evidence byte for byte. Archive the five active 0.9.7 records before advancing them.
- Consume only actual public wheels with exact URLs, source commits and SHA256; do not use rebuilt SDK candidates or sibling editables. Adapter witnesses attached to SDK releases are not the published adapters.
- No live inference or Cerebro application changes. Runtime workflow enforcement tags remain the separately documented V2 request.
- Every newly added capability must have a copyable blueprint, installed acceptance, and a linked guide/feature-map entry before release.
- Require final-head ordinary four-cell, rule four-cell, reasoning two-cell and new installed-feature coverage; no required infrastructure skips. Verify cleanup.
- Expected-head merge and identical tested/merged trees, original successful CI archives, then anonymous public downloads and fresh wheel/rebuilt-source consumers.

## Review focus

- A partial SDK upgrade must fail closed, while the exact old 0.9.7 family remains selectable and reproducible.
- Headers must reach real loopback HTTP requests, including a continuation, without entering prompt bodies or leaking to a later call; unsupported transports must refuse before dispatch.
- A revised review must use both accepted dependencies, refuse unrelated/removed/malformed IDs, bound repair, reject changed validator versions, and resume without duplicate requests.
- Current fee-format cases must become ordinary passing assertions against the value guard v2; historical expectations and signed/magnitude controls remain unchanged.
- Wheel and rebuilt source must contain every copyable resource, including dot-directories, and execute examples outside the checkout. No editable/private SDK imports.

## Task 1: Adopt and preserve the exact SDK train

**Files:** `dependencies/releases*.json`, `lab_runner/gates.py`, `lab_runner/quality/{suite.py,sdk_provenance.py,data/*.json}`, `lab_runner/memory/{freeze.py,data/*freeze*.json}`, `scripts/conversation_distribution_smoke.py`, affected current-train unit/installed assertions.

**Interfaces:** Existing five-artifact release manifests and `qualified_sdk(installed)` remain the consumer contracts. Add one exact family, retain every previous family, and archive the active 0.9.7 family as `pre-cerebro`.

- [x] Write a failing train/provenance regression covering complete admission, mixed refusal, old profile selection and preserved snapshot bytes.
- [x] Archive both active manifests, public provenance and two memory freezes; repin Runtime/Harness to their published bytes and register the exact family.
- [x] Register the archived profile as a packaged resource and freeze dependency; refresh only current freezes after final pins settle.
- [x] Watch the three existing fee assertions fail under the historical Runtime with `--runxfail`, then pass unchanged under 0.9.16; remove only their obsolete active-lane xfail marks.
- [x] Run focused adoption/freeze checks and installed dependency ownership/digest audits; retain actual logs.

## Task 2: Ship and exercise the feature blueprints

**Files:** `lab_runner/blueprints/{__init__.py,request_headers/,revision_review/,conversation_caps/}`, `tests/blueprint_acceptance/`, `docs/feature-blueprints.md`, package-data/MANIFEST declarations and installed CI/distribution smoke commands.

**Interfaces:** Blueprint resources are copyable directories, not another execution framework. Header host functions call public `ProsaicRuntime.run`/`turn` with host-owned options. Revision review uses public `Workflow`, `Harness`, `Validator` and `CheckContext`; input-cap host code constructs public conversation policies/bindings.

- [x] Write installed/copy-out acceptance before adding resources: missing blueprints fail. Assert real HTTP headers/body isolation, accepted/rejected earlier-output findings, bounded repair, explicit approval, content-version refusal and no-call replay.
- [x] Add the header blueprint and the released revision-review V1 resources with explicit provenance and application-owned policy. Include safe validation/default-inert entry points and opt-in live execution only.
- [x] Add a small conversation-cap example proving ordinary and interpreter limits through actual admission, and extend catalogue-desk fee examples/guide for all three fixed formats on both supported wires.
- [x] Add the feature-to-blueprint/test/guide map and the release checklist rule to AGENTS/release guidance. Preserve existing reasoning, terminal, native, sandbox and recovery blueprint links.
- [x] Integrate the installed feature lane into both architectures and wheel/rebuilt-source/public-consumer gates. Prove package data and copied examples work from a clean external directory.

## Task 3: Qualify, merge and publish 0.9.8

**Files:** `pyproject.toml`, version exports/assertions, README/current docs, CHANGELOG, `docs/release-0.9.8.md`, handoff/progress/verification ledger and release evidence tooling as required by the existing process.

**Interfaces:** Preserve the existing release process and its original CI archives/qualification JSON. Version availability was checked on GitHub/PyPI before implementation and must be checked again before tagging/publication.

- [ ] Run the complete source suite, build wheel/source and consumer image, run fresh installed feature/rule/reasoning suites and all mandatory owned-stack gates; record actual counts and limitations.
- [ ] Obtain a fresh branch review, fix findings with watched regressions, then commit/push the final reviewed tree once complete. Require exact-head overall GraphQL SUCCESS; do not cancel duplicate runs or ignore cancelled checks.
- [ ] Download and verify original CI archives and sanitized proof; merge only the expected head and verify tree equality.
- [ ] Publish the next free version using original qualified archives. Verify actual anonymous hashes, installed ownership, pip check and clean wheel/rebuilt-source blueprint consumers. Preserve historical assets and attach separate sanitized postpublication evidence.
- [ ] Confirm post-merge CI, publish meaningful version-specific release notes and report versions, links and qualification limits.
