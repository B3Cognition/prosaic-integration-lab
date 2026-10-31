# Observatory main port implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the Observatory onto current main, repair status and archive defects, qualify the result and publish a reviewable branch.

**Architecture:** Keep main's conversation, Explorer, release metadata and SDK pins. Add optional host-scoped observations and the existing host-only 3D launcher. Package the complete prototype in the sdist and test its extracted contents.

**Tech Stack:** Python 3.12, public released Runtime/Harness APIs, PostgreSQL 16/18, Three.js/GSAP, Blender GLB, pytest and existing Linux release matrix.

**Spec:** Maintainer's request to port onto current main, fix both reviewed issues, run release checks, commit and push; findings reproduced during the preceding readiness review.

## Global constraints

- Preserve main's version, release wheels/checksums and existing features.
- Keep owner authorization and frozen accounting attribution; no prompts in trace events.
- No automatic model/effect retries; no new real-model calls are required.
- Preserve the earlier branch and original dirty checkout.
- Commit/push are authorized; merging and publishing a release are outside this request.

## Review focus

- A lost workflow-start acknowledgement must remain needsResolution through both APIs.
- Archived source must include HTML, scripts, fonts, licenses, GLB and editable source.
- Existing chat defaults and Explorer behavior must remain compatible.
- Missing observations/unsupported usage must remain explicitly unqualified.
- Release checks must cover exact published source, supported Linux architectures and both PostgreSQL versions.

### Task 1: Port optional integration

Files: `prototypes/observatory/`, `lab_runner/observatory.py`, `lab_runner/chat.py`, `src/prosaic_integration_lab/{app,conversation_execution,observability,run_observations}.py`, related tests and `dependencies/public-build-inputs.json`.

- [ ] Install/audit main's exact released family and run the clean baseline suite.
- [ ] Restore only new Observatory files from the prior branch; apply optional hooks to main's existing code.
- [ ] Run focused observation/launcher/chat tests and all JavaScript regressions.

### Task 2: Preserve unresolved attachment status

Files: `tests/functional/test_run_observations.py`, `src/prosaic_integration_lab/conversation_execution.py`.

- [ ] Add a regression using the real synthetic lost-start-ack fixture; expect observation sessionStatus to equal ordinary needsResolution without additional dispatch.
- [ ] Observe failure, then use the existing public status projection in the observation read.
- [ ] Verify the regression, owner isolation and terminal-state regressions pass.

### Task 3: Complete source artifacts

Files: `MANIFEST.in`, `tests/unit/test_observatory_distribution.py`, distribution smoke and release workflow.

- [ ] Test the sdist inventory and extracted Observatory static shell; observe missing-assets failure.
- [ ] Include the prototype's complete code/assets/licenses in source artifacts; retain source-only host launcher boundary.
- [ ] Verify built wheel/sdist consumers and enforce Observatory distribution/JavaScript checks in CI.

### Task 4: Qualify and publish

Files: README/docs, verification ledger, existing release checks.

- [ ] Run full Python and frontend regressions, vendor/export digests, consumer build and local conversation acceptance.
- [ ] Request an independent read-only whole-branch review and fix important findings with regressions.
- [ ] Commit/push the main-based branch and run the existing four-cell release workflow on the exact source.
- [ ] Inspect all jobs/receipts, repair failures, and publish final evidence without changing the tested executable source.
