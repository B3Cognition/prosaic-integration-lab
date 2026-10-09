# Release Train Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Commit all authorized repository changes and publish verified releases in dependency order.

**Architecture:** Integrate existing reviewed Runtime/Harness fixes into their main branches. Publish immutable GitHub release artifacts, then pin their exact bytes and commits in the integration blueprint before released-mode acceptance and publication.

**Tech Stack:** Python wheels/sdists, pytest, owned PostgreSQL/Docker fixtures, GitHub Actions and Releases.

**Spec:** Maintainer request: commit everything in all repositories, increase versions as needed, create new releases.

## Global Constraints

- Publication, shared-branch integration and all existing changes are explicitly authorized by the maintainer.
- Preserve historic red receipts and unrelated private/ignored data. Never publish secrets, private runs, databases or generated credentials.
- No paid inference. Keep public installed SDK boundaries and exact-owned cleanup.
- No force push or tag replacement; fetch and preserve remote work.
- Prosaic 0.3.1 is unchanged at its current release tag; verify it, avoid an unnecessary version bump.

## Review Focus

- Unreleased Anthropic behavior requires Runtime minor 0.7.0, not patch-only relabeling.
- Both PostgreSQL adapter artifacts must ship their reviewed 0.1.1 fixes and compatible core version constraints.
- Harness must pin the actual new immutable Runtime release commit.
- Lab must consume downloaded published wheels, reject payload tampering, and pass released-mode native gates.
- Billing work must be committed and verified without publishing private fixture evidence.

## Tasks

- [x] Fetch all remotes; integrate the clean Runtime/Harness fix branches and remote main changes.
- [x] Release Runtime 0.7.0 with recorder 0.1.1: version/CI/docs, full core + adapter tests, builds and installed wheel checks, commit/push, native CI, tagged GitHub assets/checksums.
- [x] Release Harness 0.6.1 with store 0.1.1: new Runtime commit pin, version/CI/docs, full core and owned adapter matrix, builds/installed checks, commit/push, native CI, tagged GitHub assets/checksums.
- [ ] Commit the complete lab including approved Lago work; release lab 0.2.0 with new immutable release manifest and updated provenance checks. Full local suite, released PostgreSQL 16/18 acceptance and Lago lanes, native matrix, source/wheel artifacts and checksums.
- [ ] Verify every remote release/asset, clean tracked checkouts and included upstream fixes; update issues and release ledger with actual evidence and outstanding deployment qualification.

Execute inline. User has already chosen publication; no additional menu or publication approval is required.

Source checkpoint: upstream releases are published; the lab's 239 host tests,
clean-wheel/source-archive checks and released 138-case integration gates on
both database majors pass. Final lab native CI, publication and issue status
are recorded in the release notes and `VERIFICATION-0.2.0.json` rather than
altering source after the immutable release commit is qualified.

## Execution rulings

- Runtime's first native matrix passed ten jobs and failed only the macOS 3.13
  heartbeat test. The original test assumed thread scheduling within 40 ms.
  Controlled 80 ms scheduling reproduced the failure; observed-heartbeat waiting
  and actual stopped-thread assertions replace the timing assumption. Preserve
  the failed CI run, keep its release draft unpublished, and qualify a new commit.
- Runtime's local adapter setup first failed two cases because the fixture role
  lacked CREATEDB and the Harness test helper was absent from PYTHONPATH. Correct
  the private driver setup; 39/39 then passed on both PostgreSQL majors. No
  production behavior change is needed for those setup failures.
- Harness registration coverage must use its upstream disposable database
  fixture rather than a lab-only DSN. The absent-DSN regression was watched fail
  before wiring it to db_admin_dsn and explicit fixture-owned initialization.
- Require the new Lago feature in the lab's native release gates: exact 25 cases,
  pinned Lago image, no skips and verified cleanup. Its 600-second inner pytest
  process needs a 900-second outer fixture budget. Missing gate and short outer
  timeout were reproduced before the narrow gate changes.
- Commit all previously shared Lago work now that the maintainer explicitly
  authorized all repository changes. Do not include ignored private evidence.
