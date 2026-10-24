# Enabled Castle Linux qualification and release preparation

> **For agentic workers:** Use superpowers:executing-plans to execute this authorized qualification inline, with a fresh final review.

**Goal:** Qualify enabled FTS Castle on native Linux AMD64/ARM64 and PostgreSQL 16/18, then prepare reproducible worker and adapter release artifacts without publishing.

**Architecture:** Build the worker and adapter once from an exact Castle commit. Native Linux jobs consume those same wheel bytes with the unchanged public SDK family, install the Lab wheel, and execute its existing frozen-memory acceptance workflow with separate worker and host environments. Retain hashes, safe receipts, package metadata and source lineage.

**Tech stack:** Python 3.12, GitHub Actions native Ubuntu 24.04 runners, installed Python wheels/sdists, Docker PostgreSQL 16/18, existing public Runtime/Harness APIs.

**Spec:** Existing Castle optional-provider design at `cognitive-castle/docs/superpowers/specs/2026-10-23-prosaic-memory-provider-design.md`, and the user's 2026-10-24 qualification/release-preparation instruction.

## Global constraints

- Memory remains disabled by default; raw FTS ranking, recency opt-in and dense opt-in are unchanged.
- Preserve current Castle develop and Lab main behavior, all historical artifacts/evidence and unrelated checkouts.
- SUE, SOAR, generative calls and neural model loading stay outside the FTS provider path.
- Preserve scope, provenance, digest/revision, frozen owner/payer, resume and unavailable-memory checks; require zero skipped acceptance cases and verified cleanup.
- Published Runtime 0.9.7 supports host snapshots; model-facing memory tools retain their separate capability gate and must not be claimed compatible with that public version.
- Prepare artifact-only release material; do not tag, publish to an index, publish a GitHub release, or merge shared branches without additional authorization.

## Review focus

- A matrix label must not stand in for measured native Linux host, interpreter and PostgreSQL architecture.
- Every cell must consume the same exact adapter/worker bytes and public SDK pins, never editable or mutable source dependencies.
- Source archives must support rebuilding and reproducing their documented checks; historical same-version candidates must not be overwritten.
- Frozen snapshots must survive changed source, stopped workers, fresh processes and disabled-provider resume.
- Publication metadata must be uploadable and its optional model/tool prerequisites explicit rather than silently relaxed.

## Tasks

- [ ] Reconcile the isolated Castle candidate with current develop; resolve only actual conflicts while retaining both behaviors. Run the merged regression suite and preserve its coverage gate.
- [ ] Prepare worker 3.4.2 and adapter 0.1.0 packaging: synchronize version manifests, remove the PyPI-ineligible direct model URL with explicit provisioning documentation, fix adapter source-archive contents and compatible Harness extras. Add focused metadata/archive regressions, observe failures, then fix them.
- [ ] Add an artifact-only native Linux qualification workflow and supporting lineage/gate scripts in the isolated Lab branch from current main. Pin Castle source, build wheel/sdist bundles once, install separate worker/host environments, enforce measured architecture, installed payloads, forbidden-engine/network checks, exact acceptance counts and verified cleanup. Test rejection cases before implementation.
- [ ] Push review branches and draft PRs to run native CI. Investigate any failure from evidence; retain strict assertions. Execute all four enabled cells plus existing required regression lanes.
- [ ] Preserve sanitized receipts, exact artifact hashes, source/package versions and release notes/checklist. Verify rebuilt-sdist wheels, installed smoke checks, licenses and package checks. Keep original evidence intact and explicitly record unsupported model-tool/live/dense certification.
- [ ] Obtain fresh final review, fix any actionable regression, and report concrete artifact/PR links plus remaining publication prerequisites. Do not publish.

## Execution ledger

- Initial audit: current Castle develop is `c5944f7`; Lab main is `bfe7afc`. Existing isolated candidates are retained. Castle's historical 3.4.1 GitHub tag already exists; the new worker identity is 3.4.2. Public Runtime 0.9.7 lacks `custom_tool_errors_v1`; its existing adapter gate remains mandatory. Existing worker metadata contains a direct GitHub model dependency, and adapter sdists omit required fixtures/examples/scripts.
- Castle source `f4ef466`: merged all current develop behavior; focused merge checks 144 passed. The full worker suite passed 2,453 tests with 85.68% coverage (existing 85% gate), 11 existing platform/SOAR skips and two benchmark deselections. Full candidate-Runtime adapter suite passed 76 tests. Three release metadata/archive regressions were observed failing, then passed after fixes. Current public SDK model-tool capability is still deliberately rejected.
- Ruling: provision the spaCy language model explicitly rather than emitting a PyPI-ineligible direct dependency URL. Existing neural algorithms remain, no runtime download was added, and FTS requires no weights. Removing that packaging requirement makes initial NLP model setup explicit.
- Ruling: use existing native GitHub runner architecture labels only as scheduling inputs; also verify host interpreter, worker interpreter, Docker daemon and actual PostgreSQL image architectures. Every cell must consume the same once-built wheel bundle and keep current public SDK hashes.
- Native gate regressions: 21 passed after the missing gate was first observed failing; forbidden worker-engine/network guard regressions: five passed after missing bootstrap failures. The actual acceptance path now records any forbidden import/network attempt and asserts no such marker exists.
- Environment evidence: the first local full run used the wrong model cache and sandboxed process inspection, producing model lookup/pressure diagnostics. Reruns used the previously provisioned offline cache and required host inspection access; no assertions were relaxed. Two genuine integration failures (new explicit profile policy in a signed-score fixture and the stale README version badge) were fixed while preserving all original signed-score assertions.
- The artifact build reproduced Twine 6.2 rejecting valid Core Metadata 2.5 from Hatchling 1.32.4. The locked validator was updated to Twine 7.0.0, whose [upstream changelog](https://github.com/pypa/twine/blob/main/docs/changelog.rst#twine-700-2026-07-27) explicitly supports Metadata 2.5; metadata was not downgraded and validation was not removed.
- Source `6329ecf` adds a documentation clarification before native qualification: adapter setup starts with the supported public host API, and model-tool prerequisites are stated before the example. Local artifact construction at prior `f4ef466` already passed strict Twine 7 checks and both rebuilt-sdist payload comparisons; the final shared native bundle will be rebuilt from the new exact source.
- Full local Lab source suite passed 1,912 tests on the unchanged public SDK family. Fresh release review identified two P2 safeguards: exclude untracked/ignored build inputs by exporting both recorded Git commits before building, and trigger the enabled workflow on all direct source/dependency inputs. Both are addressed; the source-export regression failed before implementation, then all 32 focused qualification/guard/export checks passed. Source exports preserve local files without packaging them.
